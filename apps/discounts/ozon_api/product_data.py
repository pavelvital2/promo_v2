"""Read-only Ozon Elastic Boosting product info/stocks join."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import hashlib
import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditActionCode, AuditSourceContext
from apps.audit.services import create_audit_record
from apps.discounts.wb_api.redaction import assert_no_secret_like_values, redact
from apps.identity_access.services import has_permission
from apps.operations.models import (
    LaunchMethod,
    Marketplace,
    MessageLevel,
    OperationDetailRow,
    OperationMode,
    OperationModule,
    OperationStepCode,
    ProcessStatus,
    RunStatus,
)
from apps.operations.listing_enrichment import enrich_detail_row_marketplace_listing
from apps.operations.services import ApiOperationResult, complete_api_operation, create_api_operation, start_operation
from apps.product_core.services import sync_ozon_elastic_stock_rows_to_product_core
from apps.stores.models import StoreAccount
from apps.stores.services import default_ozon_secret_resolver, require_ozon_store_for_ozon_api
from apps.techlog.models import TechLogSeverity
from apps.techlog.services import create_techlog_record

from .actions import _active_connection
from .client import OzonApiClient, OzonApiError, OzonApiInvalidResponseError
from .products import build_latest_product_source_basis


LOGIC_VERSION = "ozon-api-elastic-product-data-download-v1"
PRODUCT_INFO_ENDPOINT_CODE = "ozon_product_info_list"
STOCKS_ENDPOINT_CODE = "ozon_product_info_stocks"


def _checksum(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _chunks(values: list[str], size: int):
    for index in range(0, len(values), size):
        yield values[index : index + size]


def _decimal_or_none(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _json_number(value: Decimal | None):
    if value is None:
        return None
    normalized = value.normalize()
    return format(normalized, "f")


def _first_present(row: dict, aliases: tuple[str, ...]):
    for alias in aliases:
        if alias in row and row[alias] not in (None, ""):
            return row[alias]
    return None


def _extract_product_info_rows(response: dict) -> list[dict]:
    result = response.get("result")
    if isinstance(result, dict):
        rows = result.get("items") or result.get("products") or result.get("list")
    else:
        rows = result or response.get("items")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message)
    return rows


def _extract_stock_items(response: dict) -> list[dict]:
    result = response.get("result")
    if isinstance(result, dict):
        rows = result.get("items") or result.get("products") or result.get("list")
    else:
        rows = result or response.get("items")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message)
    return rows


def _safe_product_info_row(row: dict) -> dict:
    product_id = str(_first_present(row, ("id", "product_id", "sku")) or "").strip()
    safe = {
        "product_id": product_id,
        "offer_id": _first_present(row, ("offer_id", "offer")),
        "name": _first_present(row, ("name", "title")),
        "min_price": _first_present(row, ("min_price",)),
    }
    safe = redact({key: value for key, value in safe.items() if value not in (None, "")})
    assert_no_secret_like_values(safe, field_name="Ozon product info safe row")
    return safe


def _safe_stock_item(row: dict) -> dict:
    product_id = str(_first_present(row, ("product_id", "id", "sku")) or "").strip()
    stock_rows = row.get("stocks")
    if stock_rows is None:
        stock_rows = row.get("stock") or row.get("stock_rows") or []
    if isinstance(stock_rows, dict):
        stock_rows = [stock_rows]
    if not isinstance(stock_rows, list) or not all(isinstance(stock_row, dict) for stock_row in stock_rows):
        raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message)
    safe_stocks = []
    for stock_row in stock_rows:
        present = _decimal_or_none(_first_present(stock_row, ("present",)))
        reserved = _decimal_or_none(_first_present(stock_row, ("reserved",)))
        safe_stocks.append(
            {
                "type": _first_present(stock_row, ("type", "source", "warehouse_type")),
                "present": _json_number(present),
                "reserved": _json_number(reserved),
            }
        )
    safe = redact({"product_id": product_id, "stocks": safe_stocks})
    assert_no_secret_like_values(safe, field_name="Ozon stock safe row")
    return safe


def _fetch_product_info(*, client: OzonApiClient, product_ids: list[str]) -> tuple[dict[str, dict], list[dict]]:
    rows_by_product_id: dict[str, dict] = {}
    pages: list[dict] = []
    chunk_size = client.policy.read_page_size
    for chunk in _chunks(product_ids, chunk_size):
        response = client.product_info_list(product_ids=chunk)
        rows = [_safe_product_info_row(row) for row in _extract_product_info_rows(response)]
        for row in rows:
            if row.get("product_id"):
                rows_by_product_id[str(row["product_id"])] = row
        pages.append(
            {
                "endpoint_code": PRODUCT_INFO_ENDPOINT_CODE,
                "method": "POST",
                "request_safe": {"product_ids_count": len(chunk), "limit": chunk_size},
                "rows_count": len(rows),
                "checksum": _checksum({"result": rows}),
            }
        )
    return rows_by_product_id, pages


def _fetch_stocks(*, client: OzonApiClient, product_ids: list[str]) -> tuple[dict[str, dict], list[dict], int]:
    rows_by_product_id: dict[str, dict] = {}
    pages: list[dict] = []
    stock_rows_count = 0
    chunk_size = client.policy.read_page_size
    for chunk in _chunks(product_ids, chunk_size):
        response = client.product_info_stocks(product_ids=chunk)
        rows = [_safe_stock_item(row) for row in _extract_stock_items(response)]
        for row in rows:
            if row.get("product_id"):
                rows_by_product_id[str(row["product_id"])] = row
                stock_rows_count += len(row.get("stocks") or [])
        pages.append(
            {
                "endpoint_code": STOCKS_ENDPOINT_CODE,
                "method": "POST",
                "request_safe": {"product_ids_count": len(chunk), "limit": chunk_size},
                "items_count": len(rows),
                "stock_rows_count": sum(len(row.get("stocks") or []) for row in rows),
                "checksum": _checksum({"result": rows}),
            }
        )
    return rows_by_product_id, pages, stock_rows_count


def _stock_present_sum(stock_item: dict | None) -> Decimal | None:
    if not stock_item:
        return None
    total = Decimal("0")
    has_row = False
    for stock_row in stock_item.get("stocks") or []:
        present = _decimal_or_none(stock_row.get("present"))
        if present is None:
            continue
        total += present
        has_row = True
    return total if has_row else None


def _canonical_row(source_row: dict, product_info: dict | None, stock_item: dict | None, *, action_id: str) -> dict:
    product_id = str(source_row.get("product_id") or "").strip()
    min_price = _decimal_or_none((product_info or {}).get("min_price"))
    stock_present = _stock_present_sum(stock_item)
    price_min_elastic = _decimal_or_none(source_row.get("price_min_elastic"))
    price_max_elastic = _decimal_or_none(source_row.get("price_max_elastic"))
    diagnostics = []
    missing_fields = []

    if not product_info:
        diagnostics.append("ozon_api_missing_product_info")
        missing_fields.append("product_info")
    if min_price is None:
        missing_fields.append("J")
    if not stock_item:
        diagnostics.append("ozon_api_missing_stock_info")
        missing_fields.append("stock_info")
    if stock_present is None or stock_present <= 0:
        missing_fields.append("R")
    if price_min_elastic is None:
        missing_fields.append("O")
    if price_max_elastic is None:
        missing_fields.append("P")

    business_reason_code = ""
    if min_price is None:
        business_reason_code = "missing_min_price"
    elif stock_present is None or stock_present <= 0:
        business_reason_code = "no_stock"
    elif price_min_elastic is None and price_max_elastic is None:
        business_reason_code = "no_boost_prices"

    row = {
        "action_id": str(action_id),
        "product_id": product_id,
        "offer_id": (product_info or {}).get("offer_id") or source_row.get("offer_id"),
        "name": (product_info or {}).get("name") or source_row.get("name"),
        "source_group": source_row.get("source_group"),
        "source_details": source_row.get("source_details") or {},
        "J_min_price": _json_number(min_price),
        "O_price_min_elastic": _json_number(price_min_elastic),
        "P_price_max_elastic": _json_number(price_max_elastic),
        "R_stock_present": _json_number(stock_present),
        "business_reason_code": business_reason_code,
        "diagnostics": diagnostics,
        "missing_fields": list(dict.fromkeys(missing_fields)),
        "product_info": product_info or {},
        "stock_info": stock_item or {},
    }
    row = redact({key: value for key, value in row.items() if value not in (None, "")})
    assert_no_secret_like_values(row, field_name="Ozon canonical product data row")
    return row


def _detail_reason_code(row: dict) -> str:
    if row.get("diagnostics"):
        return row["diagnostics"][0]
    return row.get("business_reason_code") or ""


def _api_error_code_for_exception(exc: Exception) -> str:
    if isinstance(exc, ValueError):
        return "ozon_api_secret_redaction_violation"
    event_type = getattr(exc, "techlog_event_type", "")
    if event_type in {
        "ozon_api_auth_failed",
        "ozon_api_rate_limited",
        "ozon_api_timeout",
        "ozon_api_response_invalid",
        "ozon_api_secret_redaction_violation",
    }:
        return event_type
    return "ozon_api_response_invalid"


def _missing_source_basis_error(missing_groups: list[str]) -> ValidationError:
    exc = ValidationError("Ozon Elastic product data download requires active and candidate source snapshots.")
    exc.safe_message = (
        "Ozon Elastic product data download requires completed active and candidate product source snapshots."
    )
    exc.missing_groups = missing_groups
    return exc


def _record_failure(operation, actor, store, exc: Exception):
    safe_message = getattr(exc, "safe_message", "Ozon API Elastic product data download failed.")
    result_code = _api_error_code_for_exception(exc)
    event_type = result_code if result_code.startswith("ozon_api_") else "ozon_api_elastic_product_data_download_failed"
    create_techlog_record(
        severity=TechLogSeverity.ERROR,
        event_type=event_type,
        source_component="apps.discounts.ozon_api.product_data",
        operation=operation,
        store=store,
        user=actor,
        entity_type="Operation",
        entity_id=operation.pk,
        safe_message=safe_message,
        sensitive_details_ref="redacted:ozon-api-elastic-product-data-download",
    )
    create_audit_record(
        action_code=AuditActionCode.OZON_API_ELASTIC_PRODUCT_DATA_DOWNLOAD_COMPLETED,
        entity_type="Operation",
        entity_id=operation.pk,
        user=actor,
        store=store,
        operation=operation,
        safe_message=safe_message,
        after_snapshot={
            "status": ProcessStatus.INTERRUPTED_FAILED,
            "result_code": result_code,
        },
        source_context=AuditSourceContext.SERVICE,
    )
    return result_code


def _record_product_core_sync_failure(operation, actor, store, exc: Exception) -> None:
    create_techlog_record(
        severity=TechLogSeverity.ERROR,
        event_type="marketplace_sync.failed",
        source_component="apps.discounts.ozon_api.product_data.product_core",
        operation=operation,
        store=store,
        user=actor,
        entity_type="Operation",
        entity_id=operation.pk,
        safe_message=getattr(exc, "safe_message", "Product Core sync failed after Ozon product data download."),
        sensitive_details_ref="redacted:product-core-ozon-product-data-sync",
    )


@transaction.atomic
def _persist_success(
    *,
    actor,
    store,
    operation,
    action_id: str,
    source_basis: dict,
    product_info_pages: list[dict],
    stock_pages: list[dict],
    rows: list[dict],
    fetched_at,
    stock_rows_count: int,
    read_page_size: int,
    min_interval_seconds: float,
):
    warning_count = 0
    for row_no, row in enumerate(rows, start=1):
        reason_code = _detail_reason_code(row)
        warning_count += int(bool(reason_code))
        detail_row = OperationDetailRow.objects.create(
            operation=operation,
            row_no=row_no,
            product_ref=row.get("product_id", ""),
            row_status="canonical_row_with_diagnostics" if reason_code else "canonical_row_ready",
            reason_code=reason_code,
            message_level=MessageLevel.WARNING_INFO if reason_code else MessageLevel.INFO,
            message=(
                "Ozon canonical product data row has missing source fields."
                if reason_code
                else "Ozon canonical product data row joined."
            ),
            problem_field="/".join(row.get("missing_fields") or []),
            final_value=row,
        )
        enrich_detail_row_marketplace_listing(detail_row)

    diagnostics_counts = {
        "ozon_api_missing_product_info": sum(
            1 for row in rows if "ozon_api_missing_product_info" in row.get("diagnostics", [])
        ),
        "ozon_api_missing_stock_info": sum(
            1 for row in rows if "ozon_api_missing_stock_info" in row.get("diagnostics", [])
        ),
        "missing_min_price": sum(1 for row in rows if row.get("business_reason_code") == "missing_min_price"),
        "no_stock": sum(1 for row in rows if row.get("business_reason_code") == "no_stock"),
    }
    safe_snapshot = {
        "endpoint_codes": [PRODUCT_INFO_ENDPOINT_CODE, STOCKS_ENDPOINT_CODE],
        "method": "POST",
        "fetched_at": fetched_at.isoformat(),
        "action_id": str(action_id),
        "product_info_pages": product_info_pages,
        "stock_pages": stock_pages,
        "canonical_rows": rows,
        "source_checksum": _checksum(
            {
                "source_basis": source_basis,
                "product_info_pages": product_info_pages,
                "stock_pages": stock_pages,
                "canonical_rows": rows,
            }
        ),
    }
    summary = {
        "fetched_at": fetched_at.isoformat(),
        "action_id": str(action_id),
        "source_operations": source_basis.get("source_operations", {}),
        "source_rows_count": source_basis.get("rows_count", 0),
        "product_count": len(rows),
        "stock_rows_count": stock_rows_count,
        "page_count": len(product_info_pages) + len(stock_pages),
        "read_page_size": read_page_size,
        "min_interval_ms": int(min_interval_seconds * 1000),
        "diagnostics_counts": diagnostics_counts,
        "canonical_rows": rows,
        "safe_snapshot": safe_snapshot,
    }
    assert_no_secret_like_values(summary, field_name="Ozon Elastic product data operation summary")
    operation = complete_api_operation(
        operation,
        result=ApiOperationResult(
            summary=summary,
            status=ProcessStatus.COMPLETED_WITH_WARNINGS if warning_count else ProcessStatus.COMPLETED_SUCCESS,
            error_count=0,
            warning_count=warning_count,
        ),
    )
    create_audit_record(
        action_code=AuditActionCode.OZON_API_ELASTIC_PRODUCT_DATA_DOWNLOAD_COMPLETED,
        entity_type="Operation",
        entity_id=operation.pk,
        user=actor,
        store=store,
        operation=operation,
        safe_message="Ozon API Elastic product data download completed.",
        after_snapshot={
            "status": operation.status,
            "action_id": str(action_id),
            "product_count": len(rows),
            "stock_rows_count": stock_rows_count,
            "diagnostics_counts": diagnostics_counts,
        },
        source_context=AuditSourceContext.SERVICE,
    )
    from .review import mark_accepted_results_stale

    mark_accepted_results_stale(store=store, action_id=str(action_id), actor=actor)
    return operation


def download_product_data(
    *,
    actor,
    store: StoreAccount,
    client_factory=None,
    secret_resolver=default_ozon_secret_resolver,
):
    if not has_permission(actor, "ozon.api.elastic.product_data.download", store):
        raise PermissionDenied("No permission or object access for Ozon Elastic product data download.")
    require_ozon_store_for_ozon_api(store)
    connection = _active_connection(store)
    source_basis = build_latest_product_source_basis(store=store)
    action_id = str(source_basis.get("action_id") or "").strip()
    missing_required_groups = [
        group for group in source_basis.get("missing_groups", []) if group in {"active", "candidate"}
    ]
    product_ids = [str(row["product_id"]) for row in source_basis.get("rows", []) if row.get("product_id")]

    operation = create_api_operation(
        marketplace=Marketplace.OZON,
        store=store,
        initiator_user=actor,
        step_code=OperationStepCode.OZON_API_ELASTIC_PRODUCT_DATA_DOWNLOAD,
        logic_version=LOGIC_VERSION,
        module=OperationModule.OZON_API,
        execution_context={
            "mode": OperationMode.API,
            "step_code": OperationStepCode.OZON_API_ELASTIC_PRODUCT_DATA_DOWNLOAD,
            "connection_id": connection.pk,
            "has_protected_ref": True,
            "selected_action": {"action_id": action_id},
            "source_operation_ids": [
                value["operation_id"] for value in source_basis.get("source_operations", {}).values()
            ],
        },
        launch_method=LaunchMethod.MANUAL,
        enforce_permissions=False,
    )
    operation = start_operation(operation)
    try:
        if missing_required_groups:
            raise _missing_source_basis_error(missing_required_groups)
        assert_no_secret_like_values(connection.metadata, field_name="connection metadata")
        credentials = secret_resolver(connection.protected_secret_ref)
        factory = client_factory or OzonApiClient
        client = factory(
            credentials=credentials,
            store_scope=store.visible_id or str(store.pk),
        )
        product_info_by_id, product_info_pages = _fetch_product_info(client=client, product_ids=product_ids)
        stocks_by_id, stock_pages, stock_rows_count = _fetch_stocks(client=client, product_ids=product_ids)
        rows = [
            _canonical_row(
                source_row,
                product_info_by_id.get(str(source_row.get("product_id"))),
                stocks_by_id.get(str(source_row.get("product_id"))),
                action_id=action_id,
            )
            for source_row in source_basis.get("rows", [])
        ]
        operation = _persist_success(
            actor=actor,
            store=store,
            operation=operation,
            action_id=action_id,
            source_basis=source_basis,
            product_info_pages=product_info_pages,
            stock_pages=stock_pages,
            rows=rows,
            fetched_at=timezone.now(),
            stock_rows_count=stock_rows_count,
            read_page_size=client.policy.read_page_size,
            min_interval_seconds=client.policy.min_interval_seconds,
        )
        try:
            sync_ozon_elastic_stock_rows_to_product_core(
                store=store,
                rows=rows,
                action_id=action_id,
                operation=operation,
                requested_by=actor,
            )
        except Exception as sync_exc:
            _record_product_core_sync_failure(operation, actor, store, sync_exc)
        return operation
    except Exception as exc:
        result_code = _record_failure(operation, actor, store, exc)
        operation.status = ProcessStatus.INTERRUPTED_FAILED
        operation.summary = {
            "result_code": result_code,
            "failure": getattr(exc, "safe_message", "Ozon API Elastic product data download failed."),
            "missing_groups": getattr(exc, "missing_groups", []),
        }
        operation.finished_at = timezone.now()
        operation.save(update_fields=["status", "summary", "finished_at", "updated_at"])
        operation.run.status = RunStatus.INTERRUPTED_FAILED
        operation.run.save(update_fields=["status", "updated_at"])
        if isinstance(exc, OzonApiError | ValidationError | PermissionDenied):
            raise
        raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message) from exc
