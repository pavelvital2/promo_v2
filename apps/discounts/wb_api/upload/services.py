"""Safe WB API discount upload for TASK-015 / Stage 2.1.4."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.db import transaction

from apps.audit.models import AuditActionCode, AuditSourceContext
from apps.audit.services import create_audit_record
from apps.discounts.wb_api.client import (
    WBApiAlreadyExistsError,
    WBApiClient,
    WBApiError,
    WBApiInvalidResponseError,
)
from apps.discounts.wb_api.prices.normalizers import REASON_SIZE_CONFLICT, normalize_price_good
from apps.discounts.wb_api.redaction import (
    assert_no_secret_like_values,
    contains_secret_like,
    is_secret_like_key,
    redact,
)
from apps.files.models import FileObject
from apps.files.services import create_file_version
from apps.identity_access.services import has_permission
from apps.operations.models import (
    LaunchMethod,
    Marketplace,
    MessageLevel,
    Operation,
    OperationDetailRow,
    OperationInputFile,
    OperationMode,
    OperationModule,
    OperationStepCode,
    OperationType,
    OutputKind,
    ProcessStatus,
)
from apps.operations.services import (
    ApiOperationResult,
    complete_api_operation,
    create_api_operation,
    mark_operation_interrupted_failed,
    start_operation,
)
from apps.stores.models import ConnectionBlock, StoreAccount
from apps.stores.services import (
    WB_API_CONNECTION_TYPE,
    WB_API_MODULE,
    default_secret_resolver,
    require_wb_store_for_wb_api,
)
from apps.techlog.models import TechLogSeverity
from apps.techlog.services import create_techlog_record


LOGIC_VERSION = "wb-api-discount-upload-v1"
CONFIRMATION_PHRASE = "Я понимаю, что скидки будут отправлены в WB по API."
UPLOAD_BATCH_SIZE = 1000
RESULT_INPUT_ROLE = "api_result_excel"
TERMINAL_WB_STATUSES = {3, 4, 5, 6}


@dataclass(frozen=True)
class UploadRow:
    row_no: int
    nm_id: str
    requested_discount: int
    calculation_price: Decimal


@dataclass(frozen=True)
class BatchOutcome:
    batch_no: int
    payload_checksum: str
    goods_count: int
    upload_id: str
    wb_status: int | None
    result_code: str
    details: list[dict]
    quarantine_rows: list[dict]
    safe_snapshot: dict


def _checksum(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _chunks(rows: list[UploadRow], size: int = UPLOAD_BATCH_SIZE):
    for index in range(0, len(rows), size):
        yield rows[index : index + size]


def _active_connection(store: StoreAccount) -> ConnectionBlock:
    connection = (
        ConnectionBlock.objects.filter(
            store=store,
            module=WB_API_MODULE,
            connection_type=WB_API_CONNECTION_TYPE,
            status=ConnectionBlock.Status.ACTIVE,
            is_stage2_1_used=True,
        )
        .order_by("-updated_at", "-id")
        .first()
    )
    if not connection or not connection.protected_secret_ref:
        raise PermissionDenied("Active WB API connection is required.")
    return connection


def _upload_result_file(calculation_operation: Operation):
    link = (
        calculation_operation.output_files.select_related("file_version", "file_version__file")
        .filter(file_version__file__scenario=FileObject.Scenario.WB_DISCOUNTS_API_RESULT_EXCEL)
        .order_by("file_version_id")
        .first()
    )
    if link is None:
        raise ValidationError("Successful WB API calculation result Excel is required for upload.")
    return link.file_version


def _require_successful_calculation(calculation_operation: Operation, store: StoreAccount) -> None:
    if calculation_operation.store_id != store.pk:
        raise ValidationError("WB API upload calculation basis must belong to selected store.")
    if calculation_operation.marketplace != Marketplace.WB or calculation_operation.mode != OperationMode.API:
        raise ValidationError("WB API upload requires a WB API calculation operation.")
    if calculation_operation.operation_type != OperationType.NOT_APPLICABLE:
        raise ValidationError("WB API upload calculation must not be a check/process operation.")
    if calculation_operation.step_code != OperationStepCode.WB_API_DISCOUNT_CALCULATION:
        raise ValidationError("WB API upload requires a discount calculation operation.")
    if calculation_operation.status != ProcessStatus.COMPLETED_SUCCESS:
        raise ValidationError("WB API upload requires successful calculation without errors or warnings.")
    if calculation_operation.error_count:
        raise ValidationError("WB API upload is blocked by calculation errors.")


def _rows_from_calculation(calculation_operation: Operation) -> list[UploadRow]:
    rows: list[UploadRow] = []
    for detail in calculation_operation.detail_rows.filter(
        row_status="ok",
        reason_code="wb_api_calculated_from_api_sources",
    ).order_by("row_no", "id"):
        final_value = detail.final_value or {}
        if not final_value.get("upload_ready", False):
            continue
        discount = final_value.get("final_discount")
        price = final_value.get("current_price")
        if discount is None or price in (None, ""):
            raise ValidationError("WB API upload row is missing calculated discount or price basis.")
        rows.append(
            UploadRow(
                row_no=detail.row_no,
                nm_id=str(detail.product_ref),
                requested_discount=int(discount),
                calculation_price=Decimal(str(price)),
            )
        )
    if not rows:
        raise ValidationError("WB API upload requires upload-ready calculated rows.")
    return rows


def _goods_from_response(response: dict) -> list[dict]:
    data = response.get("data")
    candidates = []
    if isinstance(data, dict):
        candidates.extend([data.get("listGoods"), data.get("goods")])
    candidates.extend([response.get("listGoods"), response.get("goods")])
    for candidate in candidates:
        if isinstance(candidate, list) and all(isinstance(item, dict) for item in candidate):
            return candidate
    raise WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message)


def _validate_confirmation(confirmation_phrase: str) -> None:
    if confirmation_phrase != CONFIRMATION_PHRASE:
        raise ValidationError("WB API upload requires exact explicit confirmation phrase.")


def _drift_check(client, rows: list[UploadRow]) -> tuple[list[dict], list[dict]]:
    drift_rows: list[dict] = []
    snapshots: list[dict] = []
    for batch_no, batch in enumerate(_chunks(rows), start=1):
        nm_list = [row.nm_id for row in batch]
        response = client.list_goods_filter_by_nm_list(nm_list=nm_list)
        goods = _goods_from_response(response)
        found = {str(good.get("nmID")): good for good in goods}
        safe_response = redact({"data": {"listGoods": goods}})
        assert_no_secret_like_values(safe_response, field_name="WB upload drift safe snapshot")
        snapshots.append(
            {
                "batch_no": batch_no,
                "endpoint_code": "wb_prices_list_goods_filter_drift",
                "method": "POST",
                "request_safe": {"nmList": nm_list},
                "goods_count": len(goods),
                "checksum": _checksum(safe_response),
            }
        )
        for row in batch:
            good = found.get(row.nm_id)
            if good is None:
                drift_rows.append(
                    {
                        "row_no": row.row_no,
                        "nmID": row.nm_id,
                        "reason": "missing",
                        "expected_price": str(row.calculation_price),
                        "actual_price": None,
                    }
                )
                continue
            normalized = normalize_price_good(good, row_no=row.row_no)
            if not normalized.upload_ready:
                drift_rows.append(
                    {
                        "row_no": row.row_no,
                        "nmID": row.nm_id,
                        "reason": "size_conflict" if normalized.reason_code == REASON_SIZE_CONFLICT else "invalid",
                        "expected_price": str(row.calculation_price),
                        "actual_price": str(normalized.derived_price) if normalized.derived_price is not None else None,
                    }
                )
            elif normalized.derived_price != row.calculation_price:
                drift_rows.append(
                    {
                        "row_no": row.row_no,
                        "nmID": row.nm_id,
                        "reason": "price_changed",
                        "expected_price": str(row.calculation_price),
                        "actual_price": str(normalized.derived_price),
                    }
                )
    assert_no_secret_like_values(snapshots, field_name="WB upload drift snapshots")
    return drift_rows, snapshots


def _upload_payload(batch: list[UploadRow]) -> list[dict]:
    payload = [{"nmID": int(row.nm_id), "discount": row.requested_discount} for row in batch]
    for item in payload:
        if set(item) != {"nmID", "discount"}:
            raise ValidationError("WB API upload payload must contain only nmID and discount.")
    return payload


def _extract_upload_id(response: dict) -> str:
    candidates = [
        response.get("uploadID"),
        response.get("uploadId"),
        response.get("id"),
    ]
    data = response.get("data")
    if isinstance(data, dict):
        candidates.extend([data.get("uploadID"), data.get("uploadId"), data.get("id")])
    for candidate in candidates:
        if candidate not in (None, ""):
            return str(candidate)
    raise WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message)


def _extract_status(response: dict) -> int | None:
    candidates = []
    data = response.get("data")
    if isinstance(data, dict):
        candidates.extend([data.get("status"), data.get("statusID"), data.get("statusId")])
        tasks = data.get("tasks")
        if isinstance(tasks, list) and tasks and isinstance(tasks[0], dict):
            candidates.extend([tasks[0].get("status"), tasks[0].get("statusID"), tasks[0].get("statusId")])
    candidates.extend([response.get("status"), response.get("statusID"), response.get("statusId")])
    for candidate in candidates:
        if candidate in (None, ""):
            continue
        try:
            return int(candidate)
        except (TypeError, ValueError):
            continue
    return None


def _list_values(response: dict) -> list[dict]:
    data = response.get("data")
    candidates = []
    if isinstance(data, dict):
        candidates.extend([data.get("listGoods"), data.get("goods"), data.get("items"), data.get("data")])
    candidates.extend([response.get("listGoods"), response.get("goods"), response.get("items")])
    for candidate in candidates:
        if isinstance(candidate, list) and all(isinstance(item, dict) for item in candidate):
            return candidate
    return []


def _safe_goods_error_text(value) -> str:
    if value in (None, ""):
        return ""
    safe_value = redact(value)
    if safe_value != value or contains_secret_like(safe_value):
        safe_value = "[redacted]"
    assert_no_secret_like_values(safe_value, field_name="WB upload goods error text")
    return str(safe_value)


def _safe_goods_detail(detail: dict) -> dict:
    safe_detail = {}
    redacted_index = 1
    for key, value in detail.items():
        if key in {"errorText", "error"}:
            safe_detail[key] = _safe_goods_error_text(value)
        elif is_secret_like_key(key) or contains_secret_like(value):
            safe_detail[f"redacted_field_{redacted_index}"] = "[redacted]"
            redacted_index += 1
        else:
            safe_detail[key] = redact(value)
    assert_no_secret_like_values(safe_detail, field_name="WB upload goods detail")
    return safe_detail


def _poll_batch_status(
    client,
    *,
    upload_id: str,
    nm_list: list[str],
    max_attempts: int,
) -> tuple[int | None, dict, list[dict], list[dict]]:
    snapshots: list[dict] = []
    wb_status: int | None = None
    for _attempt in range(max_attempts):
        history_response = client.history_tasks(upload_id=upload_id)
        history_status = _extract_status(history_response)
        snapshots.append({"endpoint_code": "wb_upload_history_tasks", "status": history_status})
        if history_status in TERMINAL_WB_STATUSES:
            wb_status = history_status
            break
        buffer_response = client.buffer_tasks(upload_id=upload_id)
        buffer_status = _extract_status(buffer_response)
        snapshots.append({"endpoint_code": "wb_upload_buffer_tasks", "status": buffer_status})
        if buffer_status in TERMINAL_WB_STATUSES:
            wb_status = buffer_status
            break
    details = []
    try:
        details.extend(_list_values(client.history_goods_task(upload_id=upload_id)))
        details.extend(_list_values(client.buffer_goods_task(upload_id=upload_id)))
    except WBApiError:
        details = []
    quarantine_rows = _list_values(client.quarantine_goods(nm_list=nm_list))
    safe_details = [_safe_goods_detail(detail) for detail in details]
    safe_snapshot = redact(
        {
            "uploadID": upload_id,
            "task_snapshots": snapshots,
            "details": safe_details,
            "quarantine": quarantine_rows,
        }
    )
    assert_no_secret_like_values(safe_snapshot, field_name="WB upload status safe snapshot")
    return wb_status, safe_snapshot, safe_details, quarantine_rows


def _result_code_for_status(wb_status: int | None, *, has_quarantine: bool = False) -> str:
    if has_quarantine:
        return "wb_api_upload_quarantine"
    return {
        3: "wb_api_upload_success",
        4: "wb_api_upload_canceled",
        5: "wb_api_upload_partial_error",
        6: "wb_api_upload_all_error",
    }.get(wb_status, "wb_api_upload_status_unknown")


def _row_result_code_for_status(wb_status: int | None, *, quarantine: bool, has_row_error: bool) -> str:
    if quarantine:
        return "wb_api_upload_quarantine"
    if wb_status == 5:
        return "wb_api_upload_partial_error" if has_row_error else "wb_api_upload_success"
    return _result_code_for_status(wb_status)


def _row_status_for_status(wb_status: int | None, *, quarantine: bool, has_row_error: bool) -> str:
    if quarantine:
        return "warning"
    if wb_status == 3:
        return "ok"
    if wb_status == 5:
        return "warning" if has_row_error else "ok"
    return "error"


def _operation_status(outcomes: list[BatchOutcome]) -> str:
    statuses = [outcome.wb_status for outcome in outcomes]
    if statuses and all(status == 3 for status in statuses):
        return ProcessStatus.COMPLETED_SUCCESS
    if any(status == 5 for status in statuses):
        return ProcessStatus.COMPLETED_WITH_WARNINGS
    if any(outcome.quarantine_rows for outcome in outcomes) and any(status == 3 for status in statuses):
        return ProcessStatus.COMPLETED_WITH_WARNINGS
    return ProcessStatus.COMPLETED_WITH_ERROR


def _aggregate_result_code(outcomes: list[BatchOutcome], operation_status: str) -> str:
    if operation_status == ProcessStatus.COMPLETED_SUCCESS:
        return "wb_api_upload_success"
    if operation_status == ProcessStatus.COMPLETED_WITH_WARNINGS:
        return "wb_api_upload_partial_error"
    statuses = {outcome.wb_status for outcome in outcomes}
    if statuses == {6}:
        return "wb_api_upload_all_error"
    if 4 in statuses:
        return "wb_api_upload_canceled"
    return "wb_api_upload_status_unknown"


def _record_techlog(*, operation, actor, store, event_type: str, severity: str, safe_message: str, upload_id: str = ""):
    create_techlog_record(
        severity=severity,
        event_type=event_type,
        source_component="apps.discounts.wb_api.upload",
        operation=operation,
        store=store,
        user=actor,
        entity_type="Operation",
        entity_id=operation.pk,
        safe_message=safe_message,
        sensitive_details_ref=f"redacted:wb-api-discount-upload:{upload_id}" if upload_id else "redacted:wb-api-discount-upload",
    )


def _mark_interrupted_with_failed_audit(*, operation, actor, store, summary: dict):
    marked = mark_operation_interrupted_failed(operation, summary=summary)
    create_audit_record(
        action_code=AuditActionCode.WB_API_DISCOUNT_UPLOAD_FAILED,
        entity_type="Operation",
        entity_id=marked.pk,
        user=actor,
        store=store,
        operation=marked,
        safe_message="WB API discount upload failed.",
        after_snapshot={"status": marked.status, "result_code": summary.get("result_code")},
        source_context=AuditSourceContext.SERVICE,
    )
    return marked


def _create_upload_report(*, actor, store, operation, summary: dict):
    content = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True, default=str).encode("utf-8")
    return create_file_version(
        store=store,
        uploaded_by=actor,
        uploaded_file=ContentFile(content, name="wb-api-upload-report.json"),
        scenario=FileObject.Scenario.WB_DISCOUNTS_API_UPLOAD_REPORT,
        kind=FileObject.Kind.OUTPUT,
        logical_name="wb_api_upload_report",
        module=OperationModule.WB_API,
        content_type="application/json",
        operation_ref=operation.visible_id,
        run_ref=operation.run.visible_id,
    )


def _complete_blocked_by_drift(*, operation, actor, store, calculation_operation, result_file, rows, drift_rows, drift_snapshots):
    for row in rows:
        drift = next((item for item in drift_rows if item["nmID"] == row.nm_id), None)
        OperationDetailRow.objects.create(
            operation=operation,
            row_no=row.row_no,
            product_ref=row.nm_id,
            row_status="error" if drift else "valid",
            reason_code="wb_api_upload_blocked_by_drift" if drift else "wb_api_upload_ready",
            message_level=MessageLevel.ERROR if drift else MessageLevel.INFO,
            message="WB API upload blocked by pre-upload drift." if drift else "WB API upload row was ready before drift block.",
            problem_field="price" if drift else "",
            final_value={
                "requested_discount": row.requested_discount,
                "drift": drift,
            },
        )
    summary = {
        "result_code": "wb_api_upload_blocked_by_drift",
        "calculation_operation_id": calculation_operation.pk,
        "result_file_version_id": result_file.pk,
        "drift_count": len(drift_rows),
        "drift_rows": drift_rows,
        "drift_check": {"batches": drift_snapshots},
    }
    assert_no_secret_like_values(summary, field_name="WB upload drift summary")
    report = _create_upload_report(actor=actor, store=store, operation=operation, summary=summary)
    completed = complete_api_operation(
        operation,
        result=ApiOperationResult(
            summary={**summary, "upload_report_file_version_id": report.pk},
            status=ProcessStatus.COMPLETED_WITH_ERROR,
            error_count=len(drift_rows),
            output_file_version=report,
            output_kind=OutputKind.DETAIL_REPORT,
        ),
    )
    create_audit_record(
        action_code=AuditActionCode.WB_API_DISCOUNT_UPLOAD_FAILED,
        entity_type="Operation",
        entity_id=completed.pk,
        user=actor,
        store=store,
        operation=completed,
        safe_message="WB API discount upload blocked by drift.",
        after_snapshot={"status": completed.status, "result_code": "wb_api_upload_blocked_by_drift"},
        source_context=AuditSourceContext.SERVICE,
    )
    return completed


@transaction.atomic
def upload_wb_api_discounts(
    *,
    actor,
    store: StoreAccount,
    calculation_operation: Operation,
    confirmation_phrase: str,
    client_factory=None,
    secret_resolver=default_secret_resolver,
    max_poll_attempts: int = 3,
) -> Operation:
    if not has_permission(actor, "wb.api.discounts.upload", store):
        raise PermissionDenied("No permission or object access for WB API discount upload.")
    if not has_permission(actor, "wb.api.discounts.upload.confirm", store):
        raise PermissionDenied("No permission or object access for WB API discount upload confirmation.")
    _validate_confirmation(confirmation_phrase)
    require_wb_store_for_wb_api(store)
    _require_successful_calculation(calculation_operation, store)
    result_file = _upload_result_file(calculation_operation)
    rows = _rows_from_calculation(calculation_operation)
    connection = _active_connection(store)

    operation = create_api_operation(
        marketplace=Marketplace.WB,
        store=store,
        initiator_user=actor,
        step_code=OperationStepCode.WB_API_DISCOUNT_UPLOAD,
        logic_version=LOGIC_VERSION,
        module=OperationModule.WB_API,
        execution_context={
            "mode": OperationMode.API,
            "step_code": OperationStepCode.WB_API_DISCOUNT_UPLOAD,
            "calculation_operation_id": calculation_operation.pk,
            "connection_id": connection.pk,
            "has_protected_ref": True,
        },
        launch_method=LaunchMethod.MANUAL,
        enforce_permissions=False,
    )
    OperationInputFile.objects.create(
        operation=operation,
        file_version=result_file,
        role_in_operation=RESULT_INPUT_ROLE,
        ordinal_no=1,
    )
    create_audit_record(
        action_code=AuditActionCode.WB_API_DISCOUNT_UPLOAD_CONFIRMED,
        entity_type="Operation",
        entity_id=operation.pk,
        user=actor,
        store=store,
        operation=operation,
        safe_message="WB API discount upload explicitly confirmed.",
        after_snapshot={
            "confirmation_phrase": "[confirmed]",
            "calculation_operation_id": calculation_operation.pk,
            "result_file_version_id": result_file.pk,
        },
        source_context=AuditSourceContext.SERVICE,
    )
    operation = start_operation(operation)

    token = secret_resolver(connection.protected_secret_ref)
    client = (client_factory or WBApiClient)(token=token, store_scope=store.visible_id or str(store.pk))
    try:
        drift_rows, drift_snapshots = _drift_check(client, rows)
        if drift_rows:
            return _complete_blocked_by_drift(
                operation=operation,
                actor=actor,
                store=store,
                calculation_operation=calculation_operation,
                result_file=result_file,
                rows=rows,
                drift_rows=drift_rows,
                drift_snapshots=drift_snapshots,
            )

        create_audit_record(
            action_code=AuditActionCode.WB_API_DISCOUNT_UPLOAD_STARTED,
            entity_type="Operation",
            entity_id=operation.pk,
            user=actor,
            store=store,
            operation=operation,
            safe_message="WB API discount upload started.",
            after_snapshot={"batch_count": len(list(_chunks(rows))), "goods_count": len(rows)},
            source_context=AuditSourceContext.SERVICE,
        )

        outcomes: list[BatchOutcome] = []
        for batch_no, batch in enumerate(_chunks(rows), start=1):
            payload = _upload_payload(batch)
            payload_checksum = _checksum(payload)
            try:
                response = client.upload_discount_task(data=payload)
                upload_id = _extract_upload_id(response)
            except WBApiAlreadyExistsError as exc:
                upload_id = ""
                try:
                    upload_id = _extract_upload_id(exc.response)
                except WBApiInvalidResponseError:
                    pass
                if not upload_id:
                    _record_techlog(
                        operation=operation,
                        actor=actor,
                        store=store,
                        event_type="wb_api_upload_failed",
                        severity=TechLogSeverity.ERROR,
                        safe_message="WB API returned 208 already exists without safe uploadID.",
                    )
                    return _mark_interrupted_with_failed_audit(
                        operation=operation,
                        actor=actor,
                        store=store,
                        summary={
                            "result_code": "wb_api_upload_status_unknown",
                            "failure": "WB API upload task already exists, but uploadID was not available.",
                            "batch_no": batch_no,
                            "payload_checksum": payload_checksum,
                        },
                    )
            except WBApiError as exc:
                _record_techlog(
                    operation=operation,
                    actor=actor,
                    store=store,
                    event_type=getattr(exc, "techlog_event_type", "wb_api_upload_failed"),
                    severity=TechLogSeverity.ERROR,
                    safe_message=getattr(exc, "safe_message", "WB API upload failed."),
                )
                return _mark_interrupted_with_failed_audit(
                    operation=operation,
                    actor=actor,
                    store=store,
                    summary={
                        "result_code": "wb_api_upload_status_unknown",
                        "failure": getattr(exc, "safe_message", "WB API upload failed."),
                        "batch_no": batch_no,
                        "payload_checksum": payload_checksum,
                    },
                )

            try:
                wb_status, safe_snapshot, details, quarantine_rows = _poll_batch_status(
                    client,
                    upload_id=upload_id,
                    nm_list=[row.nm_id for row in batch],
                    max_attempts=max_poll_attempts,
                )
            except WBApiError as exc:
                _record_techlog(
                    operation=operation,
                    actor=actor,
                    store=store,
                    event_type="wb_api_upload_status_poll_failed",
                    severity=TechLogSeverity.ERROR,
                    safe_message=getattr(exc, "safe_message", "WB API upload status polling failed."),
                    upload_id=upload_id,
                )
                wb_status = None
                details = []
                quarantine_rows = []
                safe_snapshot = {"uploadID": upload_id, "polling_failure": "WB API upload status polling failed."}

            result_code = _result_code_for_status(wb_status, has_quarantine=bool(quarantine_rows))
            outcome = BatchOutcome(
                batch_no=batch_no,
                payload_checksum=payload_checksum,
                goods_count=len(batch),
                upload_id=upload_id,
                wb_status=wb_status,
                result_code=result_code,
                details=details,
                quarantine_rows=quarantine_rows,
                safe_snapshot=safe_snapshot,
            )
            outcomes.append(outcome)
            for row in batch:
                item_detail = next((item for item in details if str(item.get("nmID")) == row.nm_id), {})
                quarantine = any(str(item.get("nmID")) == row.nm_id for item in quarantine_rows)
                has_row_error = bool(item_detail.get("errorText") or item_detail.get("error"))
                error_text_safe = _safe_goods_error_text(
                    item_detail.get("errorText") or item_detail.get("error") or ""
                )
                row_result_code = _row_result_code_for_status(
                    wb_status,
                    quarantine=quarantine,
                    has_row_error=has_row_error,
                )
                row_status = _row_status_for_status(
                    wb_status,
                    quarantine=quarantine,
                    has_row_error=has_row_error,
                )
                OperationDetailRow.objects.create(
                    operation=operation,
                    row_no=row.row_no,
                    product_ref=row.nm_id,
                    row_status=row_status,
                    reason_code=row_result_code,
                    message_level=MessageLevel.INFO if row_status == "ok" else MessageLevel.WARNING_INFO if row_status == "warning" else MessageLevel.ERROR,
                    message="WB API upload status resolved by polling.",
                    problem_field="",
                    final_value={
                        "batch_no": batch_no,
                        "uploadID": upload_id,
                        "requested_discount": row.requested_discount,
                        "wb_status": wb_status,
                        "errorText_safe": error_text_safe,
                        "quarantine": quarantine,
                    },
                )
            if wb_status == 5:
                _record_techlog(
                    operation=operation,
                    actor=actor,
                    store=store,
                    event_type="wb_api_upload_partial_errors",
                    severity=TechLogSeverity.WARNING,
                    safe_message="WB API upload completed with partial errors.",
                    upload_id=upload_id,
                )
            if quarantine_rows:
                _record_techlog(
                    operation=operation,
                    actor=actor,
                    store=store,
                    event_type="wb_api_quarantine_detected",
                    severity=TechLogSeverity.WARNING,
                    safe_message="WB API upload quarantine rows detected.",
                    upload_id=upload_id,
                )

        operation_status = _operation_status(outcomes)
        summary = {
            "result_code": _aggregate_result_code(outcomes, operation_status),
            "calculation_operation_id": calculation_operation.pk,
            "result_file_version_id": result_file.pk,
            "goods_count": len(rows),
            "batch_count": len(outcomes),
            "batches": [
                {
                    "batch_no": outcome.batch_no,
                    "goods_count": outcome.goods_count,
                    "payload_checksum": outcome.payload_checksum,
                    "uploadID": outcome.upload_id,
                    "wb_status": outcome.wb_status,
                    "result_code": outcome.result_code,
                    "safe_snapshot_checksum": _checksum(outcome.safe_snapshot),
                    "quarantine_count": len(outcome.quarantine_rows),
                }
                for outcome in outcomes
            ],
        }
        assert_no_secret_like_values(summary, field_name="WB upload operation summary")
        report = _create_upload_report(actor=actor, store=store, operation=operation, summary=summary)
        completed = complete_api_operation(
            operation,
            result=ApiOperationResult(
                summary={**summary, "upload_report_file_version_id": report.pk},
                status=operation_status,
                error_count=sum(1 for outcome in outcomes if outcome.wb_status in {4, 6, None}),
                warning_count=sum(1 for outcome in outcomes if outcome.wb_status == 5 or outcome.quarantine_rows),
                output_file_version=report,
                output_kind=OutputKind.DETAIL_REPORT,
            ),
        )
        create_audit_record(
            action_code=(
                AuditActionCode.WB_API_DISCOUNT_UPLOAD_COMPLETED
                if completed.status != ProcessStatus.COMPLETED_WITH_ERROR
                else AuditActionCode.WB_API_DISCOUNT_UPLOAD_FAILED
            ),
            entity_type="Operation",
            entity_id=completed.pk,
            user=actor,
            store=store,
            operation=completed,
            safe_message="WB API discount upload completed.",
            after_snapshot={"status": completed.status, "batch_count": len(outcomes)},
            source_context=AuditSourceContext.SERVICE,
        )
        return completed
    except Exception as exc:
        if isinstance(exc, ValidationError):
            raise
        _record_techlog(
            operation=operation,
            actor=actor,
            store=store,
            event_type=getattr(exc, "techlog_event_type", "wb_api_upload_failed"),
            severity=TechLogSeverity.ERROR,
            safe_message=getattr(exc, "safe_message", "WB API discount upload failed."),
        )
        return _mark_interrupted_with_failed_audit(
            operation=operation,
            actor=actor,
            store=store,
            summary={"result_code": "wb_api_upload_status_unknown", "failure": "WB API discount upload failed."},
        )
