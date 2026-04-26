"""Use case for TASK-013 WB API current promotions download."""

from __future__ import annotations

from datetime import UTC, timedelta
import hashlib
import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditActionCode, AuditSourceContext
from apps.audit.services import create_audit_record
from apps.discounts.wb_api.client import (
    WBApiClient,
    WBApiError,
    WBApiInvalidResponseError,
    WB_PROMOTIONS_API_BASE_URL,
)
from apps.discounts.wb_api.redaction import assert_no_secret_like_values, redact
from apps.files.models import FileObject
from apps.files.services import create_file_version
from apps.identity_access.services import has_permission
from apps.operations.models import (
    LaunchMethod,
    Marketplace,
    MessageLevel,
    OperationDetailRow,
    OperationMode,
    OperationModule,
    OperationOutputFile,
    OperationStepCode,
    OutputKind,
    ProcessStatus,
    RunStatus,
)
from apps.operations.services import ApiOperationResult, complete_api_operation, create_api_operation, start_operation
from apps.stores.models import ConnectionBlock, StoreAccount
from apps.stores.services import (
    WB_API_CONNECTION_TYPE,
    WB_API_MODULE,
    default_secret_resolver,
    require_wb_store_for_wb_api,
)
from apps.techlog.models import TechLogSeverity
from apps.techlog.services import create_techlog_record

from .export import build_promotion_export_workbook
from .models import WBPromotion, WBPromotionExportFile, WBPromotionProduct, WBPromotionSnapshot
from .normalizers import (
    REASON_AUTO,
    REASON_CURRENT,
    REASON_NOT_CURRENT,
    REASON_PRODUCT_INVALID,
    REASON_REGULAR,
    ROW_STATUS_BLOCKED,
    ROW_STATUS_INVALID,
    normalize_product,
    normalize_promotion,
)


LOGIC_VERSION = "wb-api-promotions-download-v1"
PROMOTIONS_LIMIT = 1000
NOMENCLATURES_LIMIT = 1000
DETAILS_BATCH_SIZE = 100


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


def _checksum(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _dt_param(value) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _list_from_response(response: dict, *path_options: tuple[str, ...]) -> list[dict]:
    for path in path_options:
        value = response
        for key in path:
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(key)
        if isinstance(value, list) and all(isinstance(item, dict) for item in value):
            return value
    raise WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message)


def _fetch_promotions_list(client, *, window_start, window_end) -> tuple[list[dict], list[dict]]:
    promotions: list[dict] = []
    pages: list[dict] = []
    offset = 0
    while True:
        response = client.list_promotions(
            start_datetime=_dt_param(window_start),
            end_datetime=_dt_param(window_end),
            all_promo=True,
            limit=PROMOTIONS_LIMIT,
            offset=offset,
        )
        page_promotions = _list_from_response(response, ("data", "promotions"), ("promotions",), ("data",))
        safe_response = redact({"data": {"promotions": page_promotions}})
        assert_no_secret_like_values(safe_response, field_name="WB promotions list safe snapshot")
        pages.append(
            {
                "endpoint_code": "wb_promotions_list",
                "method": "GET",
                "request_safe": {
                    "startDateTime": _dt_param(window_start),
                    "endDateTime": _dt_param(window_end),
                    "allPromo": True,
                    "limit": PROMOTIONS_LIMIT,
                    "offset": offset,
                },
                "promotions_count": len(page_promotions),
                "checksum": _checksum(safe_response),
            },
        )
        if not page_promotions:
            break
        promotions.extend(page_promotions)
        offset += PROMOTIONS_LIMIT
    return promotions, pages


def _batch_ids(promotion_ids: list[int]) -> list[list[int]]:
    unique_ids = list(dict.fromkeys(promotion_ids))
    return [unique_ids[index : index + DETAILS_BATCH_SIZE] for index in range(0, len(unique_ids), DETAILS_BATCH_SIZE)]


def _fetch_details(client, promotion_ids: list[int]) -> tuple[dict[int, dict], list[dict]]:
    if not promotion_ids:
        return {}, []
    details_by_id: dict[int, dict] = {}
    batches: list[dict] = []
    for batch in _batch_ids(promotion_ids):
        response = client.promotion_details(promotion_ids=batch)
        details = _list_from_response(response, ("data", "promotions"), ("promotions",), ("data",))
        for detail in details:
            if detail.get("id") is not None:
                details_by_id[int(detail["id"])] = detail
        safe_response = redact({"data": {"promotions": details}})
        assert_no_secret_like_values(safe_response, field_name="WB promotion details safe snapshot")
        batches.append(
            {
                "endpoint_code": "wb_promotions_details",
                "method": "GET",
                "request_safe": {"promotionIDs": batch},
                "ids_count": len(batch),
                "details_count": len(details),
                "checksum": _checksum(safe_response),
            },
        )
    return details_by_id, batches


def _fetch_nomenclatures(client, *, promotion_id: int, in_action: bool) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    pages: list[dict] = []
    offset = 0
    while True:
        response = client.promotion_nomenclatures(
            promotion_id=promotion_id,
            in_action=in_action,
            limit=NOMENCLATURES_LIMIT,
            offset=offset,
        )
        page_rows = _list_from_response(
            response,
            ("data", "nomenclatures"),
            ("nomenclatures",),
            ("data",),
        )
        safe_response = redact({"data": {"nomenclatures": page_rows}})
        assert_no_secret_like_values(safe_response, field_name="WB promotion nomenclatures safe snapshot")
        pages.append(
            {
                "endpoint_code": "wb_promotions_nomenclatures",
                "method": "GET",
                "request_safe": {
                    "promotionID": promotion_id,
                    "inAction": in_action,
                    "limit": NOMENCLATURES_LIMIT,
                    "offset": offset,
                },
                "products_count": len(page_rows),
                "checksum": _checksum(safe_response),
            },
        )
        if not page_rows:
            break
        rows.extend(page_rows)
        offset += NOMENCLATURES_LIMIT
    return rows, pages


def _message_level(row_status: str) -> str:
    if row_status == ROW_STATUS_INVALID:
        return MessageLevel.ERROR
    if row_status == ROW_STATUS_BLOCKED:
        return MessageLevel.WARNING_INFO
    return MessageLevel.INFO


def _record_failure(operation, actor, store, exc: Exception):
    safe_message = getattr(exc, "safe_message", "WB API promotions download failed.")
    event_type = getattr(exc, "techlog_event_type", "")
    if not event_type:
        event_type = "wb_api_secret_redaction_violation" if isinstance(exc, ValueError) else "wb_api_promotions_download_failed"
    create_techlog_record(
        severity=TechLogSeverity.ERROR,
        event_type=event_type,
        source_component="apps.discounts.wb_api.promotions",
        operation=operation,
        store=store,
        user=actor,
        entity_type="Operation",
        entity_id=operation.pk,
        safe_message=safe_message,
        sensitive_details_ref="redacted:wb-api-promotions-download",
    )
    create_audit_record(
        action_code=AuditActionCode.WB_API_PROMOTIONS_DOWNLOAD_COMPLETED,
        entity_type="Operation",
        entity_id=operation.pk,
        user=actor,
        store=store,
        operation=operation,
        safe_message=safe_message,
        after_snapshot={
            "status": ProcessStatus.INTERRUPTED_FAILED,
            "result_code": "wb_api_promotion_download_failed",
        },
        source_context=AuditSourceContext.SERVICE,
    )


@transaction.atomic
def _persist_success(
    *,
    actor,
    store,
    operation,
    now_utc,
    window_start,
    window_end,
    promotions,
    current_promotions,
    details_by_id,
    list_pages,
    detail_batches,
    products_by_promotion,
    nomenclature_pages,
):
    regular_promotions = [promotion for promotion in current_promotions if not promotion.is_auto]
    auto_count = len(current_promotions) - len(regular_promotions)
    products_by_regular_promotion = {
        promotion.wb_promotion_id: products_by_promotion.get(promotion.wb_promotion_id, [])
        for promotion in regular_promotions
    }
    product_count = sum(len(products) for products in products_by_regular_promotion.values())
    invalid_product_count = sum(
        1
        for products in products_by_regular_promotion.values()
        for product in products
        if product.reason_code == REASON_PRODUCT_INVALID
    )
    safe_snapshot = {
        "endpoint_code": "wb_promotions_calendar",
        "window": {
            "startDateTime": _dt_param(window_start),
            "endDateTime": _dt_param(window_end),
            "allPromo": True,
        },
        "current_filter_timestamp": now_utc.isoformat(),
        "promotions": [promotion.raw_safe for promotion in promotions],
        "current_details": {
            str(promotion_id): redact(details_by_id.get(promotion_id, {}))
            for promotion_id in sorted(promotion.wb_promotion_id for promotion in current_promotions)
        },
        "list_pages": list_pages,
        "detail_batches": detail_batches,
        "nomenclature_pages": nomenclature_pages,
        "source_checksum": _checksum(
            {
                "list_pages": list_pages,
                "detail_batches": detail_batches,
                "nomenclature_pages": nomenclature_pages,
            },
        ),
    }
    assert_no_secret_like_values(safe_snapshot, field_name="WB promotion dedicated snapshot")
    snapshot = WBPromotionSnapshot.objects.create(
        operation=operation,
        store=store,
        fetched_at=now_utc,
        api_window_start=window_start,
        api_window_end=window_end,
        current_filter_timestamp=now_utc,
        raw_response_safe_snapshot=safe_snapshot,
        promotions_count=len(promotions),
        current_promotions_count=len(current_promotions),
        regular_current_promotions_count=len(regular_promotions),
        auto_current_promotions_count=auto_count,
        promotion_products_count=product_count,
        invalid_product_count=invalid_product_count,
    )
    persisted_promotions: dict[int, WBPromotion] = {}
    for promotion in promotions:
        persisted_promotion, _created = WBPromotion.objects.update_or_create(
            store=store,
            wb_promotion_id=promotion.wb_promotion_id,
            defaults={
                "name": promotion.name,
                "type": promotion.promotion_type,
                "start_datetime": promotion.start_datetime,
                "end_datetime": promotion.end_datetime,
                "is_current_at_fetch": promotion.is_current_at_fetch,
                "last_seen_at": now_utc,
                "snapshot_ref": snapshot,
            },
        )
        persisted_promotions[promotion.wb_promotion_id] = persisted_promotion

    row_no = 1
    for promotion in promotions:
        OperationDetailRow.objects.create(
            operation=operation,
            row_no=row_no,
            product_ref=str(promotion.wb_promotion_id),
            row_status="valid" if promotion.is_current_at_fetch else "filtered",
            reason_code=REASON_CURRENT if promotion.is_current_at_fetch else REASON_NOT_CURRENT,
            message_level=MessageLevel.INFO,
            message=(
                "WB API promotion passed current filter."
                if promotion.is_current_at_fetch
                else "WB API promotion was filtered out by current filter."
            ),
            problem_field="",
            final_value={
                "wb_promotion_id": promotion.wb_promotion_id,
                "name": promotion.name,
                "type": promotion.promotion_type,
                "start_datetime": promotion.start_datetime.isoformat(),
                "end_datetime": promotion.end_datetime.isoformat(),
                "is_current_at_fetch": promotion.is_current_at_fetch,
                "details": redact(details_by_id.get(promotion.wb_promotion_id, {})),
            },
        )
        row_no += 1

    output_file_ids: list[int] = []
    regular_count = 0
    timestamp = now_utc.strftime("%Y%m%d_%H%M%S_UTC")

    for promotion in current_promotions:
        persisted_promotion = persisted_promotions[promotion.wb_promotion_id]
        if promotion.is_auto:
            OperationDetailRow.objects.create(
                operation=operation,
                row_no=row_no,
                product_ref=str(promotion.wb_promotion_id),
                row_status=ROW_STATUS_BLOCKED,
                reason_code=REASON_AUTO,
                message_level=MessageLevel.WARNING_INFO,
                message="WB API auto promotion has no nomenclatures endpoint rows; no products were invented.",
                problem_field="nomenclatures",
                final_value={
                    "wb_promotion_id": promotion.wb_promotion_id,
                    "type": promotion.promotion_type,
                    "details": redact(details_by_id.get(promotion.wb_promotion_id, {})),
                },
            )
            row_no += 1
            continue

        regular_count += 1
        products = products_by_regular_promotion.get(promotion.wb_promotion_id, [])
        workbook = build_promotion_export_workbook(products)
        filename = f"wb_promo_{promotion.wb_promotion_id}_{timestamp}.xlsx"
        file_version = create_file_version(
            store=store,
            uploaded_by=actor,
            uploaded_file=ContentFile(workbook.getvalue(), name=filename),
            scenario=FileObject.Scenario.WB_DISCOUNTS_API_PROMOTION_EXPORT,
            kind=FileObject.Kind.OUTPUT,
            logical_name=f"wb_promo_{promotion.wb_promotion_id}",
            module=OperationModule.WB_API,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            operation_ref=operation.visible_id,
            run_ref=operation.run.visible_id,
        )
        OperationOutputFile.objects.create(
            operation=operation,
            file_version=file_version,
            output_kind=OutputKind.PROMOTION_EXPORT,
        )
        WBPromotionExportFile.objects.create(
            promotion=persisted_promotion,
            operation=operation,
            file_version=file_version,
        )
        output_file_ids.append(file_version.pk)
        OperationDetailRow.objects.create(
            operation=operation,
            row_no=row_no,
            product_ref=str(promotion.wb_promotion_id),
            row_status="valid",
            reason_code=REASON_REGULAR,
            message_level=MessageLevel.INFO,
            message="WB API regular promotion was processed with nomenclatures and Excel export.",
            problem_field="",
            final_value={
                "wb_promotion_id": promotion.wb_promotion_id,
                "products_count": len(products),
                "output_file_version_id": file_version.pk,
                "details": redact(details_by_id.get(promotion.wb_promotion_id, {})),
            },
        )
        row_no += 1
        for product in products:
            OperationDetailRow.objects.create(
                operation=operation,
                row_no=row_no,
                product_ref=product.nm_id,
                row_status=product.row_status,
                reason_code=product.reason_code,
                message_level=_message_level(product.row_status),
                message=product.safe_message,
                problem_field=(
                    "planPrice/planDiscount"
                    if product.reason_code == REASON_PRODUCT_INVALID
                    else ""
                ),
                final_value={
                    "wb_promotion_id": product.promotion_id,
                    "nmID": product.nm_id,
                    "inAction": product.in_action,
                    "price": str(product.price) if product.price is not None else None,
                    "currencyCode": product.currency_code,
                    "planPrice": str(product.plan_price) if product.plan_price is not None else None,
                    "discount": product.discount,
                    "planDiscount": product.plan_discount,
                },
            )
            WBPromotionProduct.objects.create(
                promotion=persisted_promotion,
                nmID=product.nm_id,
                inAction=product.in_action,
                price=product.price,
                currencyCode=product.currency_code,
                planPrice=product.plan_price,
                discount=product.discount,
                planDiscount=product.plan_discount,
                source_snapshot=snapshot,
                row_status=product.row_status,
                reason_code=product.reason_code,
            )
            row_no += 1

    summary = {
        "result_code": "wb_api_promotions_download_success",
        "fetched_at": now_utc.isoformat(),
        "api_window_start": window_start.isoformat(),
        "api_window_end": window_end.isoformat(),
        "current_filter_timestamp": now_utc.isoformat(),
        "allPromo": True,
        "promotions_count": len(promotions),
        "current_promotions_count": len(current_promotions),
        "regular_current_promotions_count": regular_count,
        "auto_current_promotions_count": auto_count,
        "promotion_products_count": product_count,
        "invalid_product_count": invalid_product_count,
        "output_file_version_ids": output_file_ids,
        "wb_promotion_snapshot_id": snapshot.pk,
        "safe_snapshot": safe_snapshot,
    }
    assert_no_secret_like_values(summary, field_name="WB promotions operation summary")
    status = (
        ProcessStatus.COMPLETED_WITH_WARNINGS
        if auto_count or invalid_product_count
        else ProcessStatus.COMPLETED_SUCCESS
    )
    operation = complete_api_operation(
        operation,
        result=ApiOperationResult(
            summary=summary,
            status=status,
            error_count=invalid_product_count,
            warning_count=auto_count,
        ),
    )
    create_audit_record(
        action_code=AuditActionCode.WB_API_PROMOTIONS_DOWNLOAD_COMPLETED,
        entity_type="Operation",
        entity_id=operation.pk,
        user=actor,
        store=store,
        operation=operation,
        safe_message="WB API promotions download completed.",
        after_snapshot={
            "status": operation.status,
            "current_promotions_count": len(current_promotions),
            "output_file_version_ids": output_file_ids,
        },
        source_context=AuditSourceContext.SERVICE,
    )
    return operation


def download_wb_current_promotions(
    *,
    actor,
    store: StoreAccount,
    client_factory=None,
    secret_resolver=default_secret_resolver,
    now_utc=None,
):
    if not has_permission(actor, "wb.api.promotions.download", store):
        raise PermissionDenied("No permission or object access for WB API promotions download.")
    require_wb_store_for_wb_api(store)
    connection = _active_connection(store)

    now_utc = (now_utc or timezone.now()).astimezone(UTC)
    window_start = now_utc - timedelta(hours=24)
    window_end = now_utc + timedelta(hours=24)
    if not (window_start <= now_utc <= window_end):
        raise ValidationError("WB promotions API window does not cover current timestamp.")

    operation = create_api_operation(
        marketplace=Marketplace.WB,
        store=store,
        initiator_user=actor,
        step_code=OperationStepCode.WB_API_PROMOTIONS_DOWNLOAD,
        logic_version=LOGIC_VERSION,
        module=OperationModule.WB_API,
        execution_context={
            "mode": OperationMode.API,
            "step_code": OperationStepCode.WB_API_PROMOTIONS_DOWNLOAD,
            "connection_id": connection.pk,
            "has_protected_ref": True,
        },
        launch_method=LaunchMethod.MANUAL,
        enforce_permissions=False,
    )
    create_audit_record(
        action_code=AuditActionCode.WB_API_PROMOTIONS_DOWNLOAD_STARTED,
        entity_type="Operation",
        entity_id=operation.pk,
        user=actor,
        store=store,
        operation=operation,
        safe_message="WB API promotions download started.",
        after_snapshot={
            "mode": OperationMode.API,
            "marketplace": Marketplace.WB,
            "step_code": OperationStepCode.WB_API_PROMOTIONS_DOWNLOAD,
        },
        source_context=AuditSourceContext.SERVICE,
    )
    operation = start_operation(operation)
    try:
        assert_no_secret_like_values(connection.metadata, field_name="connection metadata")
        token = secret_resolver(connection.protected_secret_ref)
        factory = client_factory or WBApiClient
        client = factory(
            token=token,
            base_url=WB_PROMOTIONS_API_BASE_URL,
            store_scope=store.visible_id or str(store.pk),
        )
        raw_promotions, list_pages = _fetch_promotions_list(
            client,
            window_start=window_start,
            window_end=window_end,
        )
        promotions = [normalize_promotion(raw, now_utc=now_utc) for raw in raw_promotions]
        current_promotions = list(
            {
                promotion.wb_promotion_id: promotion
                for promotion in promotions
                if promotion.is_current_at_fetch
            }.values(),
        )
        details_by_id, detail_batches = _fetch_details(
            client,
            [promotion.wb_promotion_id for promotion in current_promotions],
        )
        products_by_promotion = {}
        nomenclature_pages = []
        for promotion in current_promotions:
            if promotion.is_auto:
                continue
            product_rows = []
            for in_action in (True, False):
                raw_rows, pages = _fetch_nomenclatures(
                    client,
                    promotion_id=promotion.wb_promotion_id,
                    in_action=in_action,
                )
                nomenclature_pages.extend(pages)
                start_no = len(product_rows) + 1
                product_rows.extend(
                    normalize_product(
                        raw,
                        row_no=start_no + index,
                        promotion_id=promotion.wb_promotion_id,
                        in_action=in_action,
                    )
                    for index, raw in enumerate(raw_rows)
                )
            products_by_promotion[promotion.wb_promotion_id] = product_rows
        return _persist_success(
            actor=actor,
            store=store,
            operation=operation,
            now_utc=now_utc,
            window_start=window_start,
            window_end=window_end,
            promotions=promotions,
            current_promotions=current_promotions,
            details_by_id=details_by_id,
            list_pages=list_pages,
            detail_batches=detail_batches,
            products_by_promotion=products_by_promotion,
            nomenclature_pages=nomenclature_pages,
        )
    except Exception as exc:
        _record_failure(operation, actor, store, exc)
        operation.status = ProcessStatus.INTERRUPTED_FAILED
        operation.summary = {
            "result_code": "wb_api_promotions_download_failed",
            "failure": getattr(exc, "safe_message", "WB API promotions download failed."),
        }
        operation.finished_at = timezone.now()
        operation.save(update_fields=["status", "summary", "finished_at", "updated_at"])
        operation.run.status = RunStatus.INTERRUPTED_FAILED
        operation.run.save(update_fields=["status", "updated_at"])
        if isinstance(exc, WBApiError | ValidationError | PermissionDenied):
            raise
        raise WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message) from exc
