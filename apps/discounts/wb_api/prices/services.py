"""Use case for TASK-012 WB API prices download."""

from __future__ import annotations

import hashlib
import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditActionCode, AuditSourceContext
from apps.audit.services import create_audit_record
from apps.discounts.wb_api.client import WBApiClient, WBApiError, WBApiInvalidResponseError
from apps.discounts.wb_api.redaction import assert_no_secret_like_values, redact
from apps.files.models import FileObject
from apps.files.services import create_file_version
from apps.identity_access.services import has_permission
from apps.marketplace_products.models import MarketplaceProduct, MarketplaceProductHistory
from apps.marketplace_products.services import sync_listing_from_legacy_product
from apps.operations.models import (
    LaunchMethod,
    Marketplace,
    MessageLevel,
    OperationDetailRow,
    OperationMode,
    OperationModule,
    OperationStepCode,
    OperationType,
    OutputKind,
    ProcessStatus,
    RunStatus,
)
from apps.operations.services import (
    ApiOperationResult,
    complete_api_operation,
    create_api_operation,
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

from .export import build_price_export_workbook
from .normalizers import (
    REASON_INVALID,
    REASON_SIZE_CONFLICT,
    ROW_STATUS_ERROR,
    ROW_STATUS_WARNING,
    normalize_price_good,
)


LOGIC_VERSION = "wb-api-prices-download-v1"
PRICES_LIMIT = 1000


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


def _goods_from_response(response: dict) -> list[dict]:
    data = response.get("data")
    if not isinstance(data, dict):
        raise WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message)
    goods = data.get("listGoods")
    if not isinstance(goods, list):
        raise WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message)
    if not all(isinstance(item, dict) for item in goods):
        raise WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message)
    return goods


def _checksum(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _fetch_all_goods(client: WBApiClient) -> tuple[list[dict], list[dict]]:
    goods: list[dict] = []
    pages: list[dict] = []
    offset = 0
    while True:
        response = client.list_goods_filter(limit=PRICES_LIMIT, offset=offset)
        page_goods = _goods_from_response(response)
        safe_response = redact({"data": {"listGoods": page_goods}})
        assert_no_secret_like_values(safe_response, field_name="WB prices safe response snapshot")
        pages.append(
            {
                "endpoint_code": "wb_prices_list_goods_filter",
                "method": "GET",
                "request_safe": {"limit": PRICES_LIMIT, "offset": offset},
                "response_safe": safe_response,
                "goods_count": len(page_goods),
                "checksum": _checksum(safe_response),
            },
        )
        if not page_goods:
            break
        goods.extend(page_goods)
        offset += PRICES_LIMIT
    return goods, pages


def _message_level(row) -> str:
    if row.row_status == ROW_STATUS_ERROR:
        return MessageLevel.ERROR
    if row.row_status == ROW_STATUS_WARNING:
        return MessageLevel.WARNING_INFO
    return MessageLevel.INFO


def _sync_product(*, store, operation, file_version, row, seen_at):
    defaults = {
        "external_ids": row.external_ids,
        "sku": row.nm_id,
        "last_values": row.last_values,
        "first_detected_at": seen_at,
        "last_seen_at": seen_at,
    }
    product, created = MarketplaceProduct.objects.select_for_update().get_or_create(
        marketplace=Marketplace.WB,
        store=store,
        sku=row.nm_id,
        defaults=defaults,
    )
    previous = {
        "external_ids": product.external_ids,
        "title": product.title,
        "sku": product.sku,
        "barcode": product.barcode,
        "status": product.status,
        "last_values": product.last_values,
    }
    changed_fields: list[str] = []
    if not created:
        if product.external_ids != row.external_ids:
            product.external_ids = row.external_ids
            changed_fields.append("external_ids")
        if product.last_values != row.last_values:
            product.last_values = row.last_values
            changed_fields.append("last_values")
        if product.status != MarketplaceProduct.Status.ACTIVE:
            product.status = MarketplaceProduct.Status.ACTIVE
            changed_fields.append("status")
        product.last_seen_at = seen_at
        changed_fields.append("last_seen_at")
        product.save()
    else:
        changed_fields = list(defaults)

    if created or changed_fields:
        MarketplaceProductHistory.objects.create(
            product=product,
            detected_at=seen_at,
            operation=operation,
            file_version=file_version,
            change_type=(
                MarketplaceProductHistory.ChangeType.DETECTED
                if created
                else MarketplaceProductHistory.ChangeType.UPDATED
            ),
            changed_fields=changed_fields,
            previous_values={} if created else previous,
            new_values={
                "external_ids": product.external_ids,
                "title": product.title,
                "sku": product.sku,
                "barcode": product.barcode,
                "status": product.status,
                "last_values": product.last_values,
                "last_seen_at": product.last_seen_at.isoformat() if product.last_seen_at else "",
                "source_operation": OperationStepCode.WB_API_PRICES_DOWNLOAD,
            },
        )
    sync_listing_from_legacy_product(product)
    return product


def _record_failure(operation, actor, store, exc: Exception):
    safe_message = getattr(exc, "safe_message", "WB API prices download failed.")
    event_type = getattr(exc, "techlog_event_type", "")
    if not event_type:
        event_type = "wb_api_secret_redaction_violation" if isinstance(exc, ValueError) else "wb_api_prices_download_failed"
    create_techlog_record(
        severity=TechLogSeverity.ERROR,
        event_type=event_type,
        source_component="apps.discounts.wb_api.prices",
        operation=operation,
        store=store,
        user=actor,
        entity_type="Operation",
        entity_id=operation.pk,
        safe_message=safe_message,
        sensitive_details_ref="redacted:wb-api-prices-download",
    )
    create_audit_record(
        action_code=AuditActionCode.WB_API_PRICES_DOWNLOAD_COMPLETED,
        entity_type="Operation",
        entity_id=operation.pk,
        user=actor,
        store=store,
        operation=operation,
        safe_message=safe_message,
        after_snapshot={"status": ProcessStatus.INTERRUPTED_FAILED, "result_code": "wb_api_price_download_failed"},
        source_context=AuditSourceContext.SERVICE,
    )


@transaction.atomic
def _persist_success(*, actor, store, operation, rows, pages, fetched_at):
    workbook = build_price_export_workbook(rows)
    file_version = create_file_version(
        store=store,
        uploaded_by=actor,
        uploaded_file=ContentFile(workbook.getvalue(), name="wb-api-prices.xlsx"),
        scenario=FileObject.Scenario.WB_DISCOUNTS_API_PRICE_EXPORT,
        kind=FileObject.Kind.OUTPUT,
        logical_name="wb_api_prices",
        module=OperationModule.WB_API,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        operation_ref=operation.visible_id,
        run_ref=operation.run.visible_id,
    )

    error_count = sum(1 for row in rows if row.reason_code == REASON_INVALID)
    warning_count = sum(1 for row in rows if row.reason_code == REASON_SIZE_CONFLICT)
    for row in rows:
        product = _sync_product(
            store=store,
            operation=operation,
            file_version=file_version,
            row=row,
            seen_at=fetched_at,
        )
        OperationDetailRow.objects.create(
            operation=operation,
            row_no=row.row_no,
            product_ref=row.nm_id,
            row_status=row.row_status,
            reason_code=row.reason_code,
            message_level=_message_level(row),
            message=row.safe_message,
            problem_field="sizes.price" if row.reason_code in {REASON_INVALID, REASON_SIZE_CONFLICT} else "",
            final_value={
                "nmID": row.nm_id,
                "vendorCode": row.vendor_code,
                "sizes_count": row.sizes_count,
                "derived_price": str(row.derived_price) if row.derived_price is not None else None,
                "discount": row.discount,
                "currency": row.currency,
                "size_conflict": row.size_conflict,
                "upload_ready": row.upload_ready,
            },
        )
        OperationDetailRow.objects.filter(operation=operation, row_no=row.row_no).update(
            product_ref=product.sku,
        )

    summary = {
        "result_code": "wb_api_price_download_success",
        "fetched_at": fetched_at.isoformat(),
        "page_count": len(pages),
        "goods_count": len(rows),
        "valid_count": sum(1 for row in rows if row.upload_ready),
        "size_conflict_count": warning_count,
        "invalid_count": error_count,
        "safe_snapshot": {
            "endpoint_code": "wb_prices_list_goods_filter",
            "page_count": len(pages),
            "goods_count": len(rows),
            "pages": [
                {
                    "method": page["method"],
                    "request_safe": page["request_safe"],
                    "goods_count": page["goods_count"],
                    "checksum": page["checksum"],
                }
                for page in pages
            ],
            "source_checksum": _checksum(pages),
        },
        "output_file_version_id": file_version.pk,
    }
    assert_no_secret_like_values(summary, field_name="WB prices operation summary")
    status = ProcessStatus.COMPLETED_WITH_WARNINGS if warning_count or error_count else ProcessStatus.COMPLETED_SUCCESS
    operation = complete_api_operation(
        operation,
        result=ApiOperationResult(
            summary=summary,
            status=status,
            error_count=error_count,
            warning_count=warning_count,
            output_file_version=file_version,
            output_kind=OutputKind.OUTPUT_WORKBOOK,
        ),
    )
    create_audit_record(
        action_code=AuditActionCode.WB_API_PRICES_DOWNLOAD_COMPLETED,
        entity_type="Operation",
        entity_id=operation.pk,
        user=actor,
        store=store,
        operation=operation,
        safe_message="WB API prices download completed.",
        after_snapshot={
            "status": operation.status,
            "goods_count": len(rows),
            "output_file_version_id": file_version.pk,
        },
        source_context=AuditSourceContext.SERVICE,
    )
    return operation


def download_wb_prices(
    *,
    actor,
    store: StoreAccount,
    client_factory=None,
    secret_resolver=default_secret_resolver,
):
    if not has_permission(actor, "wb.api.prices.download", store):
        raise PermissionDenied("No permission or object access for WB API prices download.")
    require_wb_store_for_wb_api(store)
    connection = _active_connection(store)

    operation = create_api_operation(
        marketplace=Marketplace.WB,
        store=store,
        initiator_user=actor,
        step_code=OperationStepCode.WB_API_PRICES_DOWNLOAD,
        logic_version=LOGIC_VERSION,
        module=OperationModule.WB_API,
        execution_context={
            "mode": OperationMode.API,
            "step_code": OperationStepCode.WB_API_PRICES_DOWNLOAD,
            "connection_id": connection.pk,
            "has_protected_ref": True,
        },
        launch_method=LaunchMethod.MANUAL,
        enforce_permissions=False,
    )
    create_audit_record(
        action_code=AuditActionCode.WB_API_PRICES_DOWNLOAD_STARTED,
        entity_type="Operation",
        entity_id=operation.pk,
        user=actor,
        store=store,
        operation=operation,
        safe_message="WB API prices download started.",
        after_snapshot={
            "mode": OperationMode.API,
            "marketplace": Marketplace.WB,
            "step_code": OperationStepCode.WB_API_PRICES_DOWNLOAD,
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
            store_scope=store.visible_id or str(store.pk),
        )
        goods, pages = _fetch_all_goods(client)
        rows = [normalize_price_good(good, row_no=index) for index, good in enumerate(goods, start=1)]
        return _persist_success(
            actor=actor,
            store=store,
            operation=operation,
            rows=rows,
            pages=pages,
            fetched_at=timezone.now(),
        )
    except Exception as exc:
        _record_failure(operation, actor, store, exc)
        operation.status = ProcessStatus.INTERRUPTED_FAILED
        operation.summary = {
            "result_code": "wb_api_price_download_failed",
            "failure": getattr(exc, "safe_message", "WB API prices download failed."),
        }
        operation.finished_at = timezone.now()
        operation.save(update_fields=["status", "summary", "finished_at", "updated_at"])
        operation.run.status = RunStatus.INTERRUPTED_FAILED
        operation.run.save(update_fields=["status", "updated_at"])
        if isinstance(exc, WBApiError | ValidationError | PermissionDenied):
            raise
        raise WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message) from exc
