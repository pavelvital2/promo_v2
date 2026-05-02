"""Ozon Elastic Boosting activate/deactivate upload flow."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
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
from apps.discounts.wb_api.redaction import assert_no_secret_like_values, redact
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
)
from apps.operations.listing_enrichment import enrich_detail_row_marketplace_listing
from apps.operations.services import ApiOperationResult, complete_api_operation, create_api_operation, start_operation
from apps.stores.models import StoreAccount
from apps.stores.services import default_ozon_secret_resolver, require_ozon_store_for_ozon_api
from apps.techlog.models import TechLogSeverity
from apps.techlog.services import create_techlog_record

from .actions import ELASTIC_ACTION_TYPE, ELASTIC_TITLE_MARKER, _active_connection
from .client import OzonApiClient, OzonApiError
from .product_data import (
    _extract_product_info_rows,
    _extract_stock_items,
    _safe_product_info_row,
    _safe_stock_item,
    _stock_present_sum,
)
from .products import _response_products, _safe_product_row
from .review import (
    DEACTIVATE_PENDING,
    REVIEW_ACCEPTED,
    REVIEW_PENDING_DEACTIVATE_CONFIRMATION,
)


LOGIC_VERSION = "ozon-api-elastic-upload-v1"
UPLOAD_REPORT_LOGICAL_NAME = "ozon_api_elastic_upload_report.xlsx"


class OzonElasticUploadBlocked(ValidationError):
    result_code = "ozon_api_upload_rejected"


class OzonElasticDeactivateUnconfirmed(OzonElasticUploadBlocked):
    result_code = "ozon_api_upload_blocked_deactivate_unconfirmed"


class OzonElasticDriftDetected(OzonElasticUploadBlocked):
    result_code = "ozon_api_upload_blocked_by_drift"


def _checksum(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _decimal_or_none(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _same_decimal(left, right) -> bool:
    left_decimal = _decimal_or_none(left)
    right_decimal = _decimal_or_none(right)
    if left_decimal is None and right_decimal is None:
        return True
    return left_decimal is not None and right_decimal is not None and left_decimal == right_decimal


def _calculation_summary(operation: Operation) -> dict:
    if not (
        operation.marketplace == Marketplace.OZON
        and operation.module == OperationModule.OZON_API
        and operation.mode == OperationMode.API
        and operation.operation_type == OperationType.NOT_APPLICABLE
        and operation.step_code == OperationStepCode.OZON_API_ELASTIC_CALCULATION
    ):
        raise ValidationError("Accepted Ozon Elastic calculation operation is required.")
    return dict(operation.summary or {})


def _accepted_snapshot(summary: dict) -> dict:
    snapshot = summary.get("accepted_calculation_snapshot")
    if not isinstance(snapshot, dict) or not snapshot.get("calculation_rows"):
        raise OzonElasticUploadBlocked("Accepted Ozon Elastic calculation snapshot is required.")
    assert_no_secret_like_values(snapshot, field_name="Ozon Elastic accepted upload snapshot")
    return snapshot


def _add_update_rows(snapshot: dict) -> list[dict]:
    return [
        row
        for row in snapshot.get("calculation_rows", [])
        if row.get("planned_action") in {"add_to_action", "update_action_price"}
    ]


def _deactivate_rows(snapshot: dict) -> list[dict]:
    return [
        row
        for row in snapshot.get("calculation_rows", [])
        if row.get("planned_action") == "deactivate_from_action"
    ]


def deactivate_confirmation_preview(operation: Operation) -> list[dict]:
    summary = _calculation_summary(operation)
    snapshot = _accepted_snapshot(summary)
    rows = []
    for row in _deactivate_rows(snapshot):
        rows.append(
            {
                "product_id": row.get("product_id"),
                "offer_id": row.get("offer_id"),
                "name": row.get("name"),
                "current_action_price": row.get("current_action_price"),
                "source_group": row.get("source_group"),
                "reason_code": row.get("reason_code"),
                "reason": row.get("reason"),
                "deactivate_reason_code": row.get("deactivate_reason_code"),
                "deactivate_reason": row.get("deactivate_reason"),
            }
        )
    assert_no_secret_like_values(rows, field_name="Ozon deactivate confirmation preview")
    return rows


def _save_calculation_summary(operation: Operation, summary: dict) -> Operation:
    Operation._base_manager.filter(pk=operation.pk).update(summary=summary, updated_at=timezone.now())
    operation.refresh_from_db()
    return operation


@transaction.atomic
def confirm_deactivate_group(*, actor, operation: Operation) -> Operation:
    operation = Operation.objects.select_for_update().select_related("store").get(pk=operation.pk)
    require_ozon_store_for_ozon_api(operation.store)
    if not has_permission(actor, "ozon.api.elastic.deactivate.confirm", operation.store):
        raise PermissionDenied("No permission or object access for Ozon Elastic deactivate confirmation.")
    summary = _calculation_summary(operation)
    snapshot = _accepted_snapshot(summary)
    rows = _deactivate_rows(snapshot)
    if not rows:
        summary["deactivate_confirmation_status"] = "not_required"
        return _save_calculation_summary(operation, summary)
    missing_reason = [
        row.get("product_id")
        for row in rows
        if not row.get("deactivate_reason_code") or not row.get("deactivate_reason")
    ]
    if missing_reason:
        raise ValidationError("Deactivate rows require row-level reasons before confirmation.")
    previous_state = summary.get("review_state")
    previous_status = summary.get("deactivate_confirmation_status")
    summary["deactivate_confirmation_status"] = "confirmed"
    summary["review_state"] = REVIEW_ACCEPTED
    summary["deactivate_confirmed_by_user_id"] = actor.pk
    summary["deactivate_confirmed_at"] = timezone.now().isoformat()
    summary["deactivate_confirmation_rows"] = deactivate_confirmation_preview(operation)
    assert_no_secret_like_values(summary, field_name="Ozon Elastic deactivate confirmed summary")
    operation = _save_calculation_summary(operation, summary)
    create_audit_record(
        action_code=AuditActionCode.OZON_API_ELASTIC_DEACTIVATE_GROUP_CONFIRMED,
        entity_type="CalculationResult",
        entity_id=operation.pk,
        user=actor,
        store=operation.store,
        operation=operation,
        safe_message="Ozon API Elastic deactivate group confirmed.",
        before_snapshot={
            "review_state": previous_state,
            "deactivate_confirmation_status": previous_status,
        },
        after_snapshot={
            "review_state": REVIEW_ACCEPTED,
            "deactivate_confirmation_status": "confirmed",
            "deactivate_rows_count": len(rows),
            "result_code": "ozon_api_deactivate_group_confirmed",
        },
        source_context=AuditSourceContext.SERVICE,
    )
    return operation


def _assert_upload_permissions(actor, store: StoreAccount, *, deactivate_rows: list[dict]) -> None:
    if not has_permission(actor, "ozon.api.elastic.upload", store):
        raise PermissionDenied("No permission or object access for Ozon Elastic upload.")
    if not has_permission(actor, "ozon.api.elastic.upload.confirm", store):
        raise PermissionDenied("No permission or object access for Ozon Elastic upload confirmation.")
    if deactivate_rows and not has_permission(actor, "ozon.api.elastic.deactivate.confirm", store):
        raise PermissionDenied("No permission or object access for Ozon Elastic deactivate confirmation.")


def _assert_upload_basis(operation: Operation) -> tuple[dict, dict, list[dict], list[dict]]:
    summary = _calculation_summary(operation)
    if summary.get("review_state") not in {REVIEW_ACCEPTED, REVIEW_PENDING_DEACTIVATE_CONFIRMATION}:
        raise OzonElasticUploadBlocked("Accepted non-stale Ozon Elastic result is required for upload.")
    if not summary.get("accepted_basis_checksum"):
        raise OzonElasticUploadBlocked("Accepted Ozon Elastic basis checksum is required for upload.")
    snapshot = _accepted_snapshot(summary)
    add_update_rows = _add_update_rows(snapshot)
    deactivate_rows = _deactivate_rows(snapshot)
    if not add_update_rows and not deactivate_rows:
        raise OzonElasticUploadBlocked("Ozon Elastic upload has no confirmed write rows.")
    return summary, snapshot, add_update_rows, deactivate_rows


def _mark_deactivate_pending(*, actor, operation: Operation, summary: dict, deactivate_count: int) -> None:
    summary["review_state"] = REVIEW_PENDING_DEACTIVATE_CONFIRMATION
    summary["deactivate_confirmation_status"] = DEACTIVATE_PENDING
    summary["upload_blocked"] = True
    summary["upload_blocked_reason_code"] = "ozon_api_upload_blocked_deactivate_unconfirmed"
    _save_calculation_summary(operation, summary)
    create_audit_record(
        action_code=AuditActionCode.OZON_API_ELASTIC_UPLOAD_BLOCKED_DEACTIVATE_UNCONFIRMED,
        entity_type="CalculationResult",
        entity_id=operation.pk,
        user=actor,
        store=operation.store,
        operation=operation,
        safe_message="Ozon API Elastic upload blocked because deactivate group is not confirmed.",
        after_snapshot={
            "review_state": REVIEW_PENDING_DEACTIVATE_CONFIRMATION,
            "deactivate_confirmation_status": DEACTIVATE_PENDING,
            "deactivate_rows_count": deactivate_count,
            "result_code": "ozon_api_upload_blocked_deactivate_unconfirmed",
        },
        source_context=AuditSourceContext.SERVICE,
    )


def _actions_from_response(response: dict) -> list[dict]:
    result = response.get("result")
    if isinstance(result, list):
        return [row for row in result if isinstance(row, dict)]
    if isinstance(result, dict):
        for key in ("actions", "items", "list"):
            value = result.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def _action_matches(action: dict, action_id: str) -> bool:
    current_id = str(action.get("id") or action.get("action_id") or "").strip()
    title = str(action.get("title") or action.get("name") or "")
    return (
        current_id == str(action_id)
        and action.get("action_type") == ELASTIC_ACTION_TYPE
        and ELASTIC_TITLE_MARKER in title
    )


def _read_page_size(policy) -> int:
    try:
        configured = int(getattr(policy, "read_page_size", 100) or 100)
    except (TypeError, ValueError):
        configured = 100
    return max(1, min(configured, 100))


def _write_batch_size(policy) -> int:
    try:
        configured = int(getattr(policy, "write_batch_size", 100) or 100)
    except (TypeError, ValueError):
        configured = 100
    return max(1, min(configured, 100))


def _find_action_or_raise(*, client: OzonApiClient, action_id: str) -> None:
    limit = _read_page_size(client.policy)
    offset = 0
    while True:
        actions = _actions_from_response(client.list_actions(limit=limit, offset=offset))
        if any(_action_matches(action, action_id) for action in actions):
            return
        if len(actions) < limit:
            break
        offset += limit
    raise OzonElasticDriftDetected("Ozon Elastic action identity drift detected.")


def _fetch_membership_rows_until(
    *,
    client: OzonApiClient,
    action_id: str,
    source_group: str,
    relevant_product_ids: set[str],
) -> dict[str, dict]:
    if not relevant_product_ids:
        return {}
    if source_group == "active":
        fetch_page = client.list_action_products
    elif source_group == "candidate":
        fetch_page = client.list_action_candidates
    else:
        raise ValidationError("Unsupported Ozon Elastic source group.")

    rows: dict[str, dict] = {}
    limit = _read_page_size(client.policy)
    offset = 0
    last_id = ""
    while True:
        response = fetch_page(action_id=action_id, limit=limit, offset=offset, last_id=last_id)
        products, total, next_last_id = _response_products(response)
        for product in products:
            safe = _safe_product_row(product, source_group=source_group, action_id=action_id)
            product_id = str(safe.get("product_id") or "")
            if product_id and product_id in relevant_product_ids:
                rows[product_id] = safe
        if relevant_product_ids.issubset(rows.keys()):
            break
        if total is not None and offset + len(products) >= total:
            break
        if total is None and len(products) < limit:
            break
        if next_last_id:
            if next_last_id == last_id:
                break
            last_id = next_last_id
        else:
            offset += limit
    return rows


def _current_product_info(client: OzonApiClient, product_ids: list[str]) -> tuple[dict[str, dict], dict[str, dict]]:
    info = {}
    stocks = {}
    chunk_size = _read_page_size(client.policy)
    for chunk in _chunks(product_ids, chunk_size):
        info_response = client.product_info_list(product_ids=chunk)
        for row in _extract_product_info_rows(info_response):
            safe = _safe_product_info_row(row)
            if safe.get("product_id"):
                info[str(safe["product_id"])] = safe
    for chunk in _chunks(product_ids, chunk_size):
        stock_response = client.product_info_stocks(product_ids=chunk)
        for row in _extract_stock_items(stock_response):
            safe = _safe_stock_item(row)
            if safe.get("product_id"):
                stocks[str(safe["product_id"])] = safe
    return info, stocks


def _drift_check(*, client: OzonApiClient, snapshot: dict) -> dict:
    action_id = str(snapshot.get("action_id") or "")
    _find_action_or_raise(client=client, action_id=action_id)

    rows = list(snapshot.get("calculation_rows") or [])
    product_ids = [str(row.get("product_id")) for row in rows if row.get("product_id")]
    info_by_id, stocks_by_id = _current_product_info(client, product_ids)
    active_relevant_ids = {
        str(row.get("product_id"))
        for row in rows
        if row.get("product_id") and row.get("planned_action") in {"update_action_price", "deactivate_from_action"}
    }
    candidate_relevant_ids = {
        str(row.get("product_id"))
        for row in rows
        if row.get("product_id") and row.get("planned_action") == "add_to_action"
    }
    active_rows = _fetch_membership_rows_until(
        client=client,
        action_id=action_id,
        source_group="active",
        relevant_product_ids=active_relevant_ids,
    )
    candidate_rows = _fetch_membership_rows_until(
        client=client,
        action_id=action_id,
        source_group="candidate",
        relevant_product_ids=candidate_relevant_ids,
    )
    drift = []
    for row in rows:
        product_id = str(row.get("product_id") or "")
        info = info_by_id.get(product_id)
        stock = stocks_by_id.get(product_id)
        if not info or not _same_decimal(row.get("J_min_price"), info.get("min_price")):
            drift.append({"product_id": product_id, "field": "J_min_price"})
        stock_present = _stock_present_sum(stock)
        if stock_present is None or not _same_decimal(row.get("R_stock_present"), stock_present):
            drift.append({"product_id": product_id, "field": "R_stock_present"})
        planned = row.get("planned_action")
        current_action_row = None
        if planned in {"update_action_price", "deactivate_from_action"} and product_id not in active_rows:
            drift.append({"product_id": product_id, "field": "membership_active"})
        elif planned in {"update_action_price", "deactivate_from_action"}:
            current_action_row = active_rows.get(product_id)
        if planned == "add_to_action" and product_id not in candidate_rows:
            drift.append({"product_id": product_id, "field": "membership_candidate"})
        elif planned == "add_to_action":
            current_action_row = candidate_rows.get(product_id)
        if current_action_row is not None:
            if not _same_decimal(row.get("O_price_min_elastic"), current_action_row.get("price_min_elastic")):
                drift.append({"product_id": product_id, "field": "O_price_min_elastic"})
            if not _same_decimal(row.get("P_price_max_elastic"), current_action_row.get("price_max_elastic")):
                drift.append({"product_id": product_id, "field": "P_price_max_elastic"})
    if drift:
        raise OzonElasticDriftDetected("Ozon Elastic accepted basis drift detected.")
    result = {
        "result_code": "ozon_api_upload_ready",
        "checked_at": timezone.now().isoformat(),
        "action_id": action_id,
        "rows_checked": len(rows),
        "source_relevance": "passed",
    }
    assert_no_secret_like_values(result, field_name="Ozon Elastic drift-check result")
    return result


def _chunks(rows: list[dict], size: int):
    for index in range(0, len(rows), size):
        yield rows[index : index + size]


def _product_payload(row: dict, *, include_price: bool) -> dict:
    payload = {"product_id": str(row.get("product_id") or "")}
    if row.get("offer_id"):
        payload["offer_id"] = str(row.get("offer_id"))
    if include_price:
        payload["action_price"] = str(row.get("calculated_action_price") or "")
    return payload


def _extract_rejected(response: dict) -> dict[str, str]:
    result = response.get("result") if isinstance(response.get("result"), dict) else response
    rejected_rows = result.get("rejected") or result.get("errors") or result.get("failed") or []
    rejected = {}
    if isinstance(rejected_rows, list):
        for row in rejected_rows:
            if not isinstance(row, dict):
                continue
            product_id = str(row.get("product_id") or row.get("id") or row.get("sku") or "")
            reason = str(row.get("reason") or row.get("error") or row.get("message") or "Rejected by Ozon.")
            if product_id:
                rejected[product_id] = reason
    return rejected


def _write_rows_into(
    *,
    client: OzonApiClient,
    action_id: str,
    rows: list[dict],
    operation_kind: str,
    batch_rows: list[dict],
    detail_rows: list[dict],
    batch_no_offset: int,
) -> None:
    include_price = operation_kind == "activate"
    write_batch_size = _write_batch_size(client.policy)
    for batch_no, chunk in enumerate(_chunks(rows, write_batch_size), start=batch_no_offset + 1):
        products = [_product_payload(row, include_price=include_price) for row in chunk]
        request_safe = {
            "action_id": action_id,
            "products": products,
            "rows_count": len(products),
        }
        assert_no_secret_like_values(request_safe, field_name="Ozon Elastic write request")
        if operation_kind == "activate":
            response = client.activate_action_products(action_id=action_id, products=products)
        else:
            response = client.deactivate_action_products(action_id=action_id, products=products)
        safe_response = redact(response)
        assert_no_secret_like_values(safe_response, field_name="Ozon Elastic write response")
        rejected = _extract_rejected(response)
        batch_status = "success" if not rejected else "partial_rejected"
        batch_rows.append(
            {
                "batch_no": batch_no,
                "operation_kind": operation_kind,
                "rows_count": len(products),
                "payload_checksum": _checksum(request_safe),
                "result_status": batch_status,
                "safe_snapshot": {
                    "endpoint_code": (
                        "ozon_actions_products_activate"
                        if operation_kind == "activate"
                        else "ozon_actions_products_deactivate"
                    ),
                    "method": "POST",
                    "request_safe": {
                        "action_id": action_id,
                        "rows_count": len(products),
                        "products": products,
                    },
                    "response_safe": safe_response,
                },
            }
        )
        for row in chunk:
            product_id = str(row.get("product_id") or "")
            rejected_reason = rejected.get(product_id)
            result_status = "rejected" if rejected_reason else "success"
            detail_rows.append(
                {
                    "batch_no": batch_no,
                    "operation_kind": operation_kind,
                    "product_id": product_id,
                    "offer_id": row.get("offer_id") or "",
                    "requested_action_price": row.get("calculated_action_price") if include_price else "",
                    "result_status": result_status,
                    "reason_code": (
                        "ozon_api_upload_rejected" if rejected_reason else "ozon_api_upload_success"
                    ),
                    "error_safe": rejected_reason or "",
                    "planned_action": row.get("planned_action"),
                }
            )


def _write_upload_report(*, store: StoreAccount, actor, operation: Operation, detail_rows: list[dict]):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Upload"
    headers = [
        "batch_no",
        "operation_kind",
        "product_id",
        "offer_id",
        "planned_action",
        "requested_action_price",
        "result_status",
        "reason_code",
        "error_safe",
    ]
    sheet.append(headers)
    for row in detail_rows:
        sheet.append([row.get(header) for header in headers])
    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()
    return create_file_version(
        store=store,
        uploaded_by=actor,
        uploaded_file=ContentFile(buffer.getvalue(), name=UPLOAD_REPORT_LOGICAL_NAME),
        scenario=FileObject.Scenario.OZON_API_ELASTIC_UPLOAD_REPORT,
        kind=FileObject.Kind.OUTPUT,
        logical_name=UPLOAD_REPORT_LOGICAL_NAME,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        module=OperationModule.OZON_API,
        operation_ref=operation.visible_id,
        run_ref=operation.run.visible_id,
    )


def _persist_upload_details(operation: Operation, detail_rows: list[dict]) -> None:
    for row_no, row in enumerate(detail_rows, start=1):
        rejected = row["result_status"] == "rejected"
        detail_row = OperationDetailRow.objects.create(
            operation=operation,
            row_no=row_no,
            product_ref=row["product_id"],
            row_status=row["result_status"],
            reason_code=row["reason_code"],
            message_level=MessageLevel.WARNING_INFO if rejected else MessageLevel.INFO,
            message=row["error_safe"] or "Ozon Elastic upload row completed.",
            problem_field="ozon_response" if rejected else "",
            final_value=row,
        )
        enrich_detail_row_marketplace_listing(detail_row)


def _record_upload_failure(operation, actor, store, exc: Exception) -> None:
    result_code = getattr(exc, "result_code", None) or getattr(exc, "techlog_event_type", None) or "ozon_api_response_invalid"
    event_type = result_code if result_code in {
        "ozon_api_auth_failed",
        "ozon_api_rate_limited",
        "ozon_api_timeout",
        "ozon_api_response_invalid",
        "ozon_api_secret_redaction_violation",
    } else "ozon_api_elastic_upload_failed"
    create_techlog_record(
        severity=TechLogSeverity.ERROR,
        event_type=event_type,
        source_component="apps.discounts.ozon_api.upload",
        operation=operation,
        store=store,
        user=actor,
        entity_type="Operation",
        entity_id=operation.pk,
        safe_message=getattr(exc, "safe_message", str(exc) or "Ozon API Elastic upload failed."),
        sensitive_details_ref="redacted:ozon-api-elastic-upload",
    )


def upload_elastic_result(
    *,
    actor,
    operation: Operation,
    add_update_confirmed: bool,
    client_factory=None,
    secret_resolver=default_ozon_secret_resolver,
) -> Operation:
    operation = Operation.objects.select_related("store").get(pk=operation.pk)
    require_ozon_store_for_ozon_api(operation.store)
    summary, snapshot, add_update_rows, deactivate_rows = _assert_upload_basis(operation)
    _assert_upload_permissions(actor, operation.store, deactivate_rows=deactivate_rows)
    if add_update_rows and not add_update_confirmed:
        raise OzonElasticUploadBlocked("Ozon Elastic add/update confirmation is required.")
    if deactivate_rows and summary.get("deactivate_confirmation_status") != "confirmed":
        _mark_deactivate_pending(
            actor=actor,
            operation=operation,
            summary=summary,
            deactivate_count=len(deactivate_rows),
        )
        raise OzonElasticDeactivateUnconfirmed("Ozon Elastic deactivate group confirmation is required.")

    connection = _active_connection(operation.store)
    assert_no_secret_like_values(connection.metadata, field_name="connection metadata")
    credentials = secret_resolver(connection.protected_secret_ref)
    factory = client_factory or OzonApiClient
    client = factory(credentials=credentials, store_scope=operation.store.visible_id or str(operation.store_id))

    upload_operation = create_api_operation(
        marketplace=Marketplace.OZON,
        store=operation.store,
        initiator_user=actor,
        step_code=OperationStepCode.OZON_API_ELASTIC_UPLOAD,
        logic_version=LOGIC_VERSION,
        module=OperationModule.OZON_API,
        execution_context={
            "mode": OperationMode.API,
            "step_code": OperationStepCode.OZON_API_ELASTIC_UPLOAD,
            "calculation_operation_id": operation.pk,
            "accepted_basis_checksum": summary.get("accepted_basis_checksum"),
            "connection_id": connection.pk,
            "has_protected_ref": True,
            "confirmations": {
                "add_update_confirmed": bool(add_update_confirmed),
                "deactivate_confirmation_status": summary.get("deactivate_confirmation_status"),
            },
        },
        launch_method=LaunchMethod.MANUAL,
        enforce_permissions=False,
    )
    create_audit_record(
        action_code=AuditActionCode.OZON_API_ELASTIC_UPLOAD_CONFIRMED,
        entity_type="Operation",
        entity_id=upload_operation.pk,
        user=actor,
        store=operation.store,
        operation=upload_operation,
        safe_message="Ozon API Elastic upload confirmed.",
        after_snapshot={
            "calculation_operation_id": operation.pk,
            "add_update_rows_count": len(add_update_rows),
            "deactivate_rows_count": len(deactivate_rows),
        },
        source_context=AuditSourceContext.SERVICE,
    )
    upload_operation = start_operation(upload_operation)
    batches = []
    detail_rows = []
    details_persisted = False
    report_version = None
    drift_result = None
    try:
        previous_upload = Operation.objects.filter(
            marketplace=Marketplace.OZON,
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            step_code=OperationStepCode.OZON_API_ELASTIC_UPLOAD,
            store=operation.store,
            execution_context__calculation_operation_id=operation.pk,
            execution_context__accepted_basis_checksum=summary.get("accepted_basis_checksum"),
            status__in=[ProcessStatus.COMPLETED_SUCCESS, ProcessStatus.COMPLETED_WITH_WARNINGS],
        ).exclude(pk=upload_operation.pk)
        if previous_upload.exists():
            raise OzonElasticUploadBlocked("Ozon Elastic accepted result was already uploaded.")

        drift_result = _drift_check(client=client, snapshot=snapshot)
        create_audit_record(
            action_code=AuditActionCode.OZON_API_ELASTIC_UPLOAD_STARTED,
            entity_type="Operation",
            entity_id=upload_operation.pk,
            user=actor,
            store=operation.store,
            operation=upload_operation,
            safe_message="Ozon API Elastic upload started after drift-check.",
            after_snapshot=drift_result,
            source_context=AuditSourceContext.SERVICE,
        )
        if add_update_rows:
            _write_rows_into(
                client=client,
                action_id=snapshot["action_id"],
                rows=add_update_rows,
                operation_kind="activate",
                batch_rows=batches,
                detail_rows=detail_rows,
                batch_no_offset=len(batches),
            )
        if deactivate_rows:
            _write_rows_into(
                client=client,
                action_id=snapshot["action_id"],
                rows=deactivate_rows,
                operation_kind="deactivate",
                batch_rows=batches,
                detail_rows=detail_rows,
                batch_no_offset=len(batches),
            )
        _persist_upload_details(upload_operation, detail_rows)
        details_persisted = True
        report_version = _write_upload_report(
            store=operation.store,
            actor=actor,
            operation=upload_operation,
            detail_rows=detail_rows,
        )
        rejected_count = sum(1 for row in detail_rows if row["result_status"] == "rejected")
        success_count = len(detail_rows) - rejected_count
        result_code = (
            "ozon_api_upload_partial_rejected"
            if rejected_count and success_count
            else "ozon_api_upload_rejected"
            if rejected_count
            else "ozon_api_upload_success"
        )
        upload_summary = {
            "result_code": result_code,
            "calculation_operation_id": operation.pk,
            "accepted_basis_checksum": summary.get("accepted_basis_checksum"),
            "drift_check": drift_result,
            "confirmations": {
                "add_update_confirmed": bool(add_update_confirmed),
                "deactivate_confirmation_status": summary.get("deactivate_confirmation_status"),
            },
            "batches": batches,
            "detail_rows": detail_rows,
            "success_count": success_count,
            "rejected_count": rejected_count,
            "write_batch_size": _write_batch_size(client.policy),
            "min_interval_ms": int(client.policy.min_interval_seconds * 1000),
            "upload_report_file_version_id": report_version.pk,
        }
        assert_no_secret_like_values(upload_summary, field_name="Ozon Elastic upload summary")
        completed = complete_api_operation(
            upload_operation,
            result=ApiOperationResult(
                summary=upload_summary,
                status=ProcessStatus.COMPLETED_WITH_WARNINGS if rejected_count else ProcessStatus.COMPLETED_SUCCESS,
                error_count=0,
                warning_count=rejected_count,
                output_file_version=report_version,
                output_kind=OutputKind.DETAIL_REPORT,
            ),
        )
        if rejected_count:
            create_techlog_record(
                severity=TechLogSeverity.WARNING,
                event_type="ozon_api_elastic_upload_partial_errors",
                source_component="apps.discounts.ozon_api.upload",
                operation=completed,
                store=operation.store,
                user=actor,
                entity_type="Operation",
                entity_id=completed.pk,
                safe_message="Ozon API Elastic upload completed with row-level rejections.",
                sensitive_details_ref="redacted:ozon-api-elastic-upload-partial",
            )
        create_audit_record(
            action_code=AuditActionCode.OZON_API_ELASTIC_UPLOAD_COMPLETED,
            entity_type="Operation",
            entity_id=completed.pk,
            user=actor,
            store=operation.store,
            operation=completed,
            safe_message="Ozon API Elastic upload completed.",
            after_snapshot={
                "result_code": result_code,
                "success_count": success_count,
                "rejected_count": rejected_count,
            },
            source_context=AuditSourceContext.SERVICE,
        )
        return completed
    except Exception as exc:
        _record_upload_failure(upload_operation, actor, operation.store, exc)
        result_code = getattr(exc, "result_code", None) or getattr(exc, "techlog_event_type", None) or "ozon_api_response_invalid"
        partial_summary = {}
        if detail_rows:
            if not details_persisted:
                _persist_upload_details(upload_operation, detail_rows)
                details_persisted = True
            if report_version is None:
                report_version = _write_upload_report(
                    store=operation.store,
                    actor=actor,
                    operation=upload_operation,
                    detail_rows=detail_rows,
                )
            partial_summary = {
                "batches": batches,
                "detail_rows": detail_rows,
                "success_count": sum(1 for row in detail_rows if row["result_status"] == "success"),
                "rejected_count": sum(1 for row in detail_rows if row["result_status"] == "rejected"),
                "sent_batches_count": len(batches),
                "partial_evidence_persisted": True,
                "upload_report_file_version_id": report_version.pk,
            }
            assert_no_secret_like_values(
                partial_summary,
                field_name="Ozon Elastic failed upload partial evidence",
            )
        failed = complete_api_operation(
            upload_operation,
            result=ApiOperationResult(
                summary={
                    "result_code": result_code,
                    "calculation_operation_id": operation.pk,
                    "accepted_basis_checksum": summary.get("accepted_basis_checksum"),
                    "drift_check": drift_result or {},
                    "write_batch_size": _write_batch_size(client.policy),
                    "failure": getattr(exc, "safe_message", str(exc) or "Ozon API Elastic upload failed."),
                    **partial_summary,
                },
                status=ProcessStatus.COMPLETED_WITH_ERROR,
                error_count=1,
                warning_count=0,
                output_file_version=report_version,
                output_kind=OutputKind.DETAIL_REPORT if report_version is not None else "",
            ),
        )
        create_audit_record(
            action_code=AuditActionCode.OZON_API_ELASTIC_UPLOAD_FAILED,
            entity_type="Operation",
            entity_id=failed.pk,
            user=actor,
            store=operation.store,
            operation=failed,
            safe_message="Ozon API Elastic upload failed.",
            after_snapshot={"result_code": result_code},
            source_context=AuditSourceContext.SERVICE,
        )
        if isinstance(exc, OzonApiError | ValidationError | PermissionDenied):
            raise
        raise
