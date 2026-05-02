"""Ozon Elastic Boosting calculation and result report generation."""

from __future__ import annotations

from io import BytesIO
import hashlib
import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from openpyxl import Workbook

from apps.audit.models import AuditActionCode, AuditSourceContext
from apps.audit.services import create_audit_record
from apps.discounts.ozon_shared.calculation import (
    decimal_to_json,
    decide_ozon_row,
    message_for_code,
    parse_decimal,
    problem_field_for_decision,
)
from apps.discounts.wb_api.redaction import assert_no_secret_like_values
from apps.files.models import FileObject
from apps.files.services import create_file_version
from apps.identity_access.services import has_permission
from apps.operations.models import (
    LaunchMethod,
    Marketplace,
    MessageLevel,
    Operation,
    OperationDetailRow,
    OperationMode,
    OperationModule,
    OperationStepCode,
    OperationType,
    OutputKind,
    ProcessStatus,
    RunStatus,
)
from apps.operations.listing_enrichment import enrich_detail_row_marketplace_listing
from apps.operations.services import ApiOperationResult, complete_api_operation, create_api_operation, start_operation
from apps.stores.models import StoreAccount
from apps.stores.services import require_ozon_store_for_ozon_api
from apps.techlog.models import TechLogSeverity
from apps.techlog.services import create_techlog_record

from .actions import get_selected_elastic_action_basis


LOGIC_VERSION = "ozon-api-elastic-calculation-v1"
RESULT_LOGICAL_NAME = "ozon_api_elastic_result_report.xlsx"
SUCCESSFUL_SOURCE_STATUSES = (
    ProcessStatus.COMPLETED_SUCCESS,
    ProcessStatus.COMPLETED_WITH_WARNINGS,
)
SOURCE_GROUP_ACTIVE = "active"
SOURCE_GROUP_CANDIDATE = "candidate"
SOURCE_GROUP_COLLISION = "candidate_and_active"
DEACTIVATE_REASON_CODES = {
    "missing_min_price",
    "no_stock",
    "no_boost_prices",
    "below_min_price_threshold",
    "insufficient_ozon_input_data",
}


def _checksum(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _latest_product_data_operation(*, store: StoreAccount, action_id: str) -> Operation | None:
    return (
        Operation.objects.filter(
            marketplace=Marketplace.OZON,
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.OZON_API_ELASTIC_PRODUCT_DATA_DOWNLOAD,
            store=store,
            status__in=SUCCESSFUL_SOURCE_STATUSES,
            summary__action_id=str(action_id),
        )
        .order_by("-finished_at", "-id")
        .first()
    )


def _selected_action_basis(store: StoreAccount) -> dict:
    basis = get_selected_elastic_action_basis(store)
    action_id = str((basis or {}).get("action_id") or "").strip()
    if not action_id:
        raise ValidationError("Selected Elastic Boosting action is required.")
    assert_no_secret_like_values(basis, field_name="Ozon selected action basis")
    return basis


def _selected_action_id(store: StoreAccount) -> str:
    return str(_selected_action_basis(store).get("action_id") or "").strip()


def _selected_action_name(basis: dict) -> str:
    action = basis.get("action") if isinstance(basis.get("action"), dict) else {}
    return str(action.get("title") or action.get("name") or "").strip()


def build_latest_calculation_basis(*, store: StoreAccount, action_id: str | None = None) -> dict:
    selected_basis = _selected_action_basis(store)
    selected_action_id = str(selected_basis.get("action_id") or "").strip()
    action_id = str(action_id or selected_action_id)
    if action_id != selected_action_id:
        raise ValidationError("Calculation action must match the selected Elastic Boosting action.")
    action_name = _selected_action_name(selected_basis)
    operation = _latest_product_data_operation(store=store, action_id=action_id)
    if operation is None:
        raise ValidationError("Successful Ozon Elastic product data snapshot is required.")
    summary = operation.summary if isinstance(operation.summary, dict) else {}
    rows = list(summary.get("canonical_rows") or [])
    if not rows:
        raise ValidationError("Successful Ozon Elastic product data snapshot has no canonical rows.")
    safe_snapshot = summary.get("safe_snapshot") if isinstance(summary.get("safe_snapshot"), dict) else {}
    source_basis = safe_snapshot.get("source_basis") if isinstance(safe_snapshot.get("source_basis"), dict) else {}
    source_rows_by_product = {
        str(row.get("product_id")): row
        for row in source_basis.get("rows", [])
        if isinstance(row, dict) and row.get("product_id")
    }
    basis = {
        "action_id": action_id,
        "action_name": action_name,
        "selected_action": {
            "action_id": action_id,
            "action_name": action_name,
            "source_operation_id": selected_basis.get("source_operation_id"),
            "source_operation_visible_id": selected_basis.get("source_operation_visible_id"),
            "selected_at": selected_basis.get("selected_at"),
        },
        "product_data_operation": {
            "operation_id": operation.pk,
            "operation_visible_id": operation.visible_id,
            "finished_at": operation.finished_at.isoformat() if operation.finished_at else "",
            "summary_source_checksum": safe_snapshot.get("source_checksum"),
        },
        "canonical_rows": rows,
        "source_rows_by_product": source_rows_by_product,
        "source_operations": summary.get("source_operations", {}),
        "basis_checksum": _checksum(
            {
                "operation_id": operation.pk,
                "operation_visible_id": operation.visible_id,
                "source_checksum": safe_snapshot.get("source_checksum"),
                "selected_action": {
                    "action_id": action_id,
                    "action_name": action_name,
                    "source_operation_id": selected_basis.get("source_operation_id"),
                },
                "canonical_rows": rows,
            }
        ),
    }
    assert_no_secret_like_values(basis, field_name="Ozon Elastic calculation basis")
    return basis


def _source_action_price(row: dict, source_row: dict) -> str | None:
    direct = source_row.get("action_price")
    if direct not in (None, ""):
        return str(direct)
    details = row.get("source_details") if isinstance(row.get("source_details"), dict) else {}
    active_row = details.get("active_row") if isinstance(details.get("active_row"), dict) else {}
    value = active_row.get("action_price")
    return None if value in (None, "") else str(value)


def _planned_action(*, source_group: str, upload_ready: bool, reason_code: str) -> tuple[str, bool, str, str]:
    if source_group == SOURCE_GROUP_CANDIDATE:
        if upload_ready:
            return "add_to_action", False, "", ""
        return "skip_candidate", False, "", ""
    if source_group in {SOURCE_GROUP_ACTIVE, SOURCE_GROUP_COLLISION}:
        if upload_ready:
            return "update_action_price", False, "", ""
        if reason_code in DEACTIVATE_REASON_CODES:
            return "deactivate_from_action", True, reason_code, message_for_code(reason_code)
        return "blocked", False, "", ""
    return "blocked", False, "", ""


def _calculation_row(row_no: int, row: dict, source_row: dict, *, action_name: str = "") -> dict:
    decision = decide_ozon_row(
        row_no=row_no,
        min_price=parse_decimal(row.get("J_min_price")),
        min_boost_price=parse_decimal(row.get("O_price_min_elastic")),
        max_boost_price=parse_decimal(row.get("P_price_max_elastic")),
        stock=parse_decimal(row.get("R_stock_present")),
    )
    source_group = str(row.get("source_group") or "")
    planned_action, deactivate_required, deactivate_reason_code, deactivate_reason = _planned_action(
        source_group=source_group,
        upload_ready=decision.participates,
        reason_code=decision.reason_code,
    )
    if planned_action == "blocked":
        message = "Ozon Elastic row is blocked by invalid technical state."
        upload_ready = False
        calculated_action_price = None
    else:
        message = message_for_code(decision.reason_code)
        upload_ready = decision.participates
        calculated_action_price = decision.final_price
    result = {
        "marketplace": Marketplace.OZON,
        "action_id": str(row.get("action_id") or ""),
        "action_name": action_name,
        "source_group": source_group,
        "source_details": row.get("source_details") or {},
        "product_id": str(row.get("product_id") or ""),
        "offer_id": row.get("offer_id") or source_row.get("offer_id") or "",
        "name": row.get("name") or source_row.get("name") or "",
        "current_action_price": _source_action_price(row, source_row),
        "J_min_price": decimal_to_json(decision.min_price),
        "O_price_min_elastic": decimal_to_json(decision.min_boost_price),
        "P_price_max_elastic": decimal_to_json(decision.max_boost_price),
        "R_stock_present": decimal_to_json(decision.stock),
        "current_boost": source_row.get("current_boost") or "",
        "min_boost": source_row.get("price_min_elastic") or row.get("O_price_min_elastic") or "",
        "max_boost": source_row.get("price_max_elastic") or row.get("P_price_max_elastic") or "",
        "reason_code": decision.reason_code,
        "reason": message_for_code(decision.reason_code),
        "planned_action": planned_action,
        "calculated_action_price": decimal_to_json(calculated_action_price),
        "upload_ready": upload_ready,
        "deactivate_required": deactivate_required,
        "deactivate_reason_code": deactivate_reason_code,
        "deactivate_reason": deactivate_reason,
        "diagnostics": row.get("diagnostics") or [],
        "missing_fields": row.get("missing_fields") or [],
        "row_status": "blocked" if planned_action == "blocked" else planned_action,
        "message": message,
    }
    assert_no_secret_like_values(result, field_name="Ozon Elastic calculation row")
    return result


def calculate_rows(basis: dict) -> list[dict]:
    source_rows = basis.get("source_rows_by_product") or {}
    action_name = str(basis.get("action_name") or "")
    rows = []
    for row_no, row in enumerate(basis.get("canonical_rows") or [], start=1):
        product_id = str(row.get("product_id") or "")
        source_row = source_rows.get(product_id) if isinstance(source_rows.get(product_id), dict) else {}
        rows.append(_calculation_row(row_no, row, source_row, action_name=action_name))
    return rows


def _summary_groups(rows: list[dict]) -> dict:
    groups = {
        "add_to_action": [],
        "update_action_price": [],
        "deactivate_from_action": [],
        "skip_candidate": [],
        "blocked": [],
    }
    for row in rows:
        groups[row["planned_action"]].append(row)
    return groups


def _write_result_report(*, rows: list[dict], store: StoreAccount, user, operation) -> object:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Result"
    headers = [
        "marketplace",
        "store",
        "action_id",
        "action name",
        "source_group",
        "source_details/collision note",
        "product_id",
        "offer_id",
        "name",
        "current action_price",
        "J/min_price",
        "O/price_min_elastic",
        "P/price_max_elastic",
        "R/stock_present",
        "current_boost",
        "min_boost",
        "max_boost",
        "reason_code",
        "human-readable reason",
        "planned action",
        "calculated action_price",
        "upload_ready",
        "deactivate_required",
        "deactivate_reason_code",
        "deactivate_reason",
    ]
    sheet.append(headers)
    for row in rows:
        source_details = row.get("source_details") if isinstance(row.get("source_details"), dict) else {}
        sheet.append(
            [
                row.get("marketplace"),
                store.visible_id or store.name,
                row.get("action_id"),
                row.get("action_name"),
                row.get("source_group"),
                source_details.get("collision_reason") or ("collision" if source_details.get("collision") else ""),
                row.get("product_id"),
                row.get("offer_id"),
                row.get("name"),
                row.get("current_action_price"),
                row.get("J_min_price"),
                row.get("O_price_min_elastic"),
                row.get("P_price_max_elastic"),
                row.get("R_stock_present"),
                row.get("current_boost"),
                row.get("min_boost"),
                row.get("max_boost"),
                row.get("reason_code"),
                row.get("reason"),
                row.get("planned_action"),
                row.get("calculated_action_price"),
                row.get("upload_ready"),
                row.get("deactivate_required"),
                row.get("deactivate_reason_code"),
                row.get("deactivate_reason"),
            ]
        )
    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()
    content = ContentFile(buffer.getvalue(), name=RESULT_LOGICAL_NAME)
    return create_file_version(
        store=store,
        uploaded_by=user,
        uploaded_file=content,
        scenario=FileObject.Scenario.OZON_API_ELASTIC_RESULT_REPORT,
        kind=FileObject.Kind.OUTPUT,
        logical_name=RESULT_LOGICAL_NAME,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        module=OperationModule.OZON_API,
        operation_ref=operation.visible_id,
        run_ref=operation.run.visible_id,
    )


def _persist_details(operation, rows: list[dict]) -> None:
    for row_no, row in enumerate(rows, start=1):
        blocked = row["planned_action"] == "blocked"
        detail_row = OperationDetailRow.objects.create(
            operation=operation,
            row_no=row_no,
            product_ref=row.get("product_id", ""),
            row_status=row["row_status"],
            reason_code=row["reason_code"],
            message_level=MessageLevel.ERROR if blocked else MessageLevel.INFO,
            message=row["message"],
            problem_field="source_group" if blocked else problem_field_for_decision(
                decide_ozon_row(
                    row_no=row_no,
                    min_price=parse_decimal(row.get("J_min_price")),
                    min_boost_price=parse_decimal(row.get("O_price_min_elastic")),
                    max_boost_price=parse_decimal(row.get("P_price_max_elastic")),
                    stock=parse_decimal(row.get("R_stock_present")),
                )
            ),
            final_value=row,
        )
        enrich_detail_row_marketplace_listing(detail_row)


def _record_failure(operation, actor, store, exc: Exception):
    create_techlog_record(
        severity=TechLogSeverity.ERROR,
        event_type="ozon_api_elastic_calculation_failed",
        source_component="apps.discounts.ozon_api.calculation",
        operation=operation,
        store=store,
        user=actor,
        entity_type="Operation",
        entity_id=operation.pk,
        safe_message=getattr(exc, "safe_message", "Ozon API Elastic calculation failed."),
        sensitive_details_ref="redacted:ozon-api-elastic-calculation",
    )


@transaction.atomic
def calculate_elastic_result(*, actor, store: StoreAccount):
    if not has_permission(actor, "ozon.api.elastic.calculate", store):
        raise PermissionDenied("No permission or object access for Ozon Elastic calculation.")
    require_ozon_store_for_ozon_api(store)
    action_id = _selected_action_id(store)
    basis = build_latest_calculation_basis(store=store, action_id=action_id)
    operation = create_api_operation(
        marketplace=Marketplace.OZON,
        store=store,
        initiator_user=actor,
        step_code=OperationStepCode.OZON_API_ELASTIC_CALCULATION,
        logic_version=LOGIC_VERSION,
        module=OperationModule.OZON_API,
        execution_context={
            "mode": OperationMode.API,
            "step_code": OperationStepCode.OZON_API_ELASTIC_CALCULATION,
            "selected_action": {"action_id": action_id},
            "basis": {
                "product_data_operation_id": basis["product_data_operation"]["operation_id"],
                "basis_checksum": basis["basis_checksum"],
            },
        },
        launch_method=LaunchMethod.MANUAL,
        enforce_permissions=False,
    )
    operation = start_operation(operation)
    try:
        rows = calculate_rows(basis)
        groups = _summary_groups(rows)
        _persist_details(operation, rows)
        report_version = _write_result_report(
            rows=rows,
            store=store,
            user=actor,
            operation=operation,
        )
        error_count = len(groups["blocked"])
        summary = {
            "result_code": "ozon_api_upload_ready",
            "action_id": action_id,
            "action_name": basis["action_name"],
            "basis": {
                "selected_action": basis["selected_action"],
                "product_data_operation": basis["product_data_operation"],
                "basis_checksum": basis["basis_checksum"],
            },
            "review_state": "not_reviewed",
            "deactivate_confirmation_status": (
                "pending" if groups["deactivate_from_action"] else "not_required"
            ),
            "accepted_basis_checksum": "",
            "rows_count": len(rows),
            "groups_count": {key: len(value) for key, value in groups.items()},
            "calculation_rows": rows,
            "accepted_basis_candidate": {
                "add_to_action": groups["add_to_action"],
                "update_action_price": groups["update_action_price"],
                "deactivate_from_action": groups["deactivate_from_action"],
            },
            "result_report_file_version_id": report_version.pk,
            "manual_upload_file_created": False,
        }
        assert_no_secret_like_values(summary, field_name="Ozon Elastic calculation summary")
        completed = complete_api_operation(
            operation,
            result=ApiOperationResult(
                summary=summary,
                status=ProcessStatus.COMPLETED_WITH_ERROR if error_count else ProcessStatus.COMPLETED_SUCCESS,
                error_count=error_count,
                warning_count=0,
                output_file_version=report_version,
                output_kind=OutputKind.OUTPUT_WORKBOOK,
            ),
        )
        create_audit_record(
            action_code=AuditActionCode.OZON_API_ELASTIC_CALCULATION_COMPLETED,
            entity_type="Operation",
            entity_id=completed.pk,
            user=actor,
            store=store,
            operation=completed,
            safe_message="Ozon API Elastic calculation completed.",
            after_snapshot={
                "status": completed.status,
                "action_id": action_id,
                "action_name": basis["action_name"],
                "groups_count": summary["groups_count"],
                "result_report_file_version_id": report_version.pk,
            },
            source_context=AuditSourceContext.SERVICE,
        )
        return completed
    except Exception as exc:
        _record_failure(operation, actor, store, exc)
        operation.status = ProcessStatus.INTERRUPTED_FAILED
        operation.summary = {
            "result_code": "ozon_api_response_invalid",
            "failure": getattr(exc, "safe_message", "Ozon API Elastic calculation failed."),
            "basis": {
                "product_data_operation": basis.get("product_data_operation"),
                "basis_checksum": basis.get("basis_checksum"),
            },
        }
        operation.finished_at = timezone.now()
        operation.save(update_fields=["status", "summary", "finished_at", "updated_at"])
        operation.run.status = RunStatus.INTERRUPTED_FAILED
        operation.run.save(update_fields=["status", "updated_at"])
        raise
