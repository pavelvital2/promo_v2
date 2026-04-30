"""Read-only Ozon Elastic Boosting active/candidate product downloads."""

from __future__ import annotations

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
from apps.operations.services import ApiOperationResult, complete_api_operation, create_api_operation, start_operation
from apps.stores.models import StoreAccount
from apps.stores.services import default_ozon_secret_resolver, require_ozon_store_for_ozon_api
from apps.techlog.models import TechLogSeverity
from apps.techlog.services import create_techlog_record

from .actions import ELASTIC_ACTION_TYPE, ELASTIC_TITLE_MARKER, _active_connection, get_selected_elastic_action_basis
from .client import OzonApiClient, OzonApiError, OzonApiInvalidResponseError


LOGIC_VERSION = "ozon-api-elastic-products-download-v1"
ACTIVE_SOURCE_GROUP = "active"
CANDIDATE_SOURCE_GROUP = "candidate"
COLLISION_SOURCE_GROUP = "candidate_and_active"


class OzonElasticActionSelectionError(ValidationError):
    safe_message = "Selected Ozon action is missing or is not an approved Elastic Boosting action."


class OzonElasticMissingFieldsError(ValidationError):
    safe_message = "Ozon action product row is missing required Elastic Boosting fields."
    techlog_event_type = "ozon_api_response_invalid"


def _checksum(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _response_products(response: dict) -> tuple[list[dict], int | None, str]:
    result = response.get("result")
    if not isinstance(result, dict):
        raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message)
    products = result.get("products")
    if not isinstance(products, list) or not all(isinstance(row, dict) for row in products):
        raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message)
    total = result.get("total")
    if total is not None:
        try:
            total = int(total)
        except (TypeError, ValueError) as exc:
            raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message) from exc
    last_id = str(result.get("last_id") or "").strip()
    return products, total, last_id


def _first_present(row: dict, aliases: tuple[str, ...]):
    for alias in aliases:
        if alias in row and row[alias] not in (None, ""):
            return row[alias]
    return None


def _safe_product_row(row: dict, *, source_group: str, action_id: str) -> dict:
    product_id = _first_present(row, ("id", "product_id", "sku"))
    action_price = _first_present(row, ("action_price", "current_action_price"))
    price_min_elastic = _first_present(
        row,
        ("price_min_elastic", "min_action_price", "min_boost_price", "min_price_for_action"),
    )
    price_max_elastic = _first_present(
        row,
        ("price_max_elastic", "max_action_price", "max_boost_price", "max_price_for_action"),
    )
    safe = {
        "action_id": str(action_id),
        "source_group": source_group,
        "product_id": str(product_id or "").strip(),
        "offer_id": _first_present(row, ("offer_id", "offer")),
        "name": _first_present(row, ("name", "title")),
        "price": _first_present(row, ("price", "current_price")),
        "action_price": action_price,
        "price_min_elastic": price_min_elastic,
        "price_max_elastic": price_max_elastic,
        "stock": _first_present(row, ("stock",)),
        "min_stock": _first_present(row, ("min_stock",)),
        "add_mode": _first_present(row, ("add_mode",)),
        "source_details": {
            "source_group": source_group,
            "raw_field_aliases": {
                "product_id": "id/product_id/sku",
                "price_min_elastic": "price_min_elastic/min_action_price/min_boost_price/min_price_for_action",
                "price_max_elastic": "price_max_elastic/max_action_price/max_boost_price/max_price_for_action",
            },
        },
    }
    safe = redact({key: value for key, value in safe.items() if value not in (None, "")})
    assert_no_secret_like_values(safe, field_name="Ozon safe action product row")
    return safe


def _row_has_missing_elastic_fields(safe_row: dict) -> bool:
    return not safe_row.get("product_id") or (
        safe_row.get("price_min_elastic") is None and safe_row.get("price_max_elastic") is None
    )


def _validate_selected_basis(store: StoreAccount) -> dict:
    basis = get_selected_elastic_action_basis(store)
    if not basis or not str(basis.get("action_id") or "").strip():
        raise OzonElasticActionSelectionError("Selected Elastic Boosting action is required.")
    action = basis.get("action") if isinstance(basis.get("action"), dict) else {}
    action_type = action.get("action_type")
    title = str(action.get("title") or action.get("name") or "")
    if action_type != ELASTIC_ACTION_TYPE or ELASTIC_TITLE_MARKER not in title:
        raise OzonElasticActionSelectionError("Selected action is not an approved Elastic Boosting action.")
    assert_no_secret_like_values(basis, field_name="Ozon selected action basis")
    return basis


def _fetch_product_group(*, client: OzonApiClient, action_id: str, source_group: str) -> tuple[list[dict], list[dict]]:
    if source_group == ACTIVE_SOURCE_GROUP:
        fetch_page = client.list_action_products
        endpoint_code = "ozon_actions_products"
        method = "POST"
    elif source_group == CANDIDATE_SOURCE_GROUP:
        fetch_page = client.list_action_candidates
        endpoint_code = "ozon_actions_candidates"
        method = "POST"
    else:
        raise ValidationError("Unsupported Ozon Elastic source group.")

    rows: list[dict] = []
    pages: list[dict] = []
    limit = client.policy.read_page_size
    offset = 0
    last_id = ""

    while True:
        response = fetch_page(action_id=action_id, limit=limit, offset=offset, last_id=last_id)
        products, total, next_last_id = _response_products(response)
        safe_rows = [
            _safe_product_row(row, source_group=source_group, action_id=action_id)
            for row in products
        ]
        safe_response = {
            "result": {
                "products": safe_rows,
                "total": total,
                "last_id": next_last_id,
            }
        }
        assert_no_secret_like_values(safe_response, field_name="Ozon product safe response snapshot")
        pages.append(
            {
                "endpoint_code": endpoint_code,
                "method": method,
                "request_safe": {
                    "action_id": str(action_id),
                    "limit": limit,
                    "offset": offset,
                    "last_id": last_id,
                },
                "products_count": len(products),
                "total": total,
                "next_last_id": next_last_id,
                "checksum": _checksum(safe_response),
            }
        )
        rows.extend(safe_rows)
        if total is not None and len(rows) >= total:
            break
        if total is None and len(products) < limit:
            break
        if next_last_id:
            if next_last_id == last_id:
                raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message)
            last_id = next_last_id
        else:
            offset += limit
    return rows, pages


def _audit_code_for_group(source_group: str):
    if source_group == ACTIVE_SOURCE_GROUP:
        return AuditActionCode.OZON_API_ELASTIC_ACTIVE_DOWNLOAD_COMPLETED
    return AuditActionCode.OZON_API_ELASTIC_CANDIDATES_DOWNLOAD_COMPLETED


def _step_code_for_group(source_group: str):
    if source_group == ACTIVE_SOURCE_GROUP:
        return OperationStepCode.OZON_API_ELASTIC_ACTIVE_PRODUCTS_DOWNLOAD
    return OperationStepCode.OZON_API_ELASTIC_CANDIDATE_PRODUCTS_DOWNLOAD


def _permission_for_group(source_group: str) -> str:
    if source_group == ACTIVE_SOURCE_GROUP:
        return "ozon.api.elastic.active_products.download"
    return "ozon.api.elastic.candidates.download"


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
    if isinstance(exc, OzonElasticActionSelectionError):
        message = str(exc)
        if "not an approved Elastic Boosting action" in message:
            return "ozon_api_action_not_elastic"
        return "ozon_api_action_not_found"
    return "ozon_api_response_invalid"


def _record_failure(operation, actor, store, exc: Exception, *, source_group: str):
    safe_message = getattr(exc, "safe_message", "Ozon API Elastic products download failed.")
    result_code = _api_error_code_for_exception(exc)
    create_techlog_record(
        severity=TechLogSeverity.ERROR,
        event_type=result_code,
        source_component="apps.discounts.ozon_api.products",
        operation=operation,
        store=store,
        user=actor,
        entity_type="Operation",
        entity_id=operation.pk,
        safe_message=safe_message,
        sensitive_details_ref=f"redacted:ozon-api-elastic-{source_group}-download",
    )
    create_audit_record(
        action_code=_audit_code_for_group(source_group),
        entity_type="Operation",
        entity_id=operation.pk,
        user=actor,
        store=store,
        operation=operation,
        safe_message=safe_message,
        after_snapshot={
            "status": ProcessStatus.INTERRUPTED_FAILED,
            "source_group": source_group,
            "result_code": result_code,
        },
        source_context=AuditSourceContext.SERVICE,
    )
    return result_code


@transaction.atomic
def _persist_success(*, actor, store, operation, action_id: str, source_group: str, rows, pages, fetched_at):
    row_no = 1
    missing_count = 0
    for row in rows:
        missing = _row_has_missing_elastic_fields(row)
        missing_count += int(missing)
        source_details = dict(row.get("source_details") or {})
        source_details["missing_elastic_fields"] = missing
        row["source_details"] = source_details
        OperationDetailRow.objects.create(
            operation=operation,
            row_no=row_no,
            product_ref=row.get("product_id", ""),
            row_status="missing_elastic_fields" if missing else "source_row_valid",
            reason_code="ozon_api_missing_elastic_fields" if missing else "",
            message_level=MessageLevel.WARNING_INFO if missing else MessageLevel.INFO,
            message=(
                "Ozon action product row is missing required Elastic Boosting fields."
                if missing
                else "Ozon action product row downloaded."
            ),
            problem_field="product_id/price_min_elastic/price_max_elastic" if missing else "",
            final_value=row,
        )
        row_no += 1

    safe_snapshot = {
        "endpoint_code": "ozon_actions_products" if source_group == ACTIVE_SOURCE_GROUP else "ozon_actions_candidates",
        "method": "POST",
        "fetched_at": fetched_at.isoformat(),
        "action_id": str(action_id),
        "source_group": source_group,
        "pages": pages,
        "products": rows,
        "source_checksum": _checksum({"pages": pages, "products": rows}),
    }
    summary = {
        "fetched_at": fetched_at.isoformat(),
        "action_id": str(action_id),
        "source_group": source_group,
        "page_count": len(pages),
        "products_count": len(rows),
        "missing_elastic_fields_count": missing_count,
        "products": rows,
        "safe_snapshot": safe_snapshot,
        "downstream_basis_source": {
            "source_operation_id": operation.pk,
            "source_operation_visible_id": operation.visible_id,
            "source_group": source_group,
            "action_id": str(action_id),
        },
    }
    assert_no_secret_like_values(summary, field_name="Ozon Elastic products operation summary")
    operation = complete_api_operation(
        operation,
        result=ApiOperationResult(
            summary=summary,
            status=ProcessStatus.COMPLETED_WITH_WARNINGS if missing_count else ProcessStatus.COMPLETED_SUCCESS,
            error_count=0,
            warning_count=missing_count,
        ),
    )
    create_audit_record(
        action_code=_audit_code_for_group(source_group),
        entity_type="Operation",
        entity_id=operation.pk,
        user=actor,
        store=store,
        operation=operation,
        safe_message="Ozon API Elastic products download completed.",
        after_snapshot={
            "status": operation.status,
            "action_id": str(action_id),
            "source_group": source_group,
            "products_count": len(rows),
            "missing_elastic_fields_count": missing_count,
        },
        source_context=AuditSourceContext.SERVICE,
    )
    from .review import mark_accepted_results_stale

    mark_accepted_results_stale(store=store, action_id=str(action_id), actor=actor)
    return operation


def download_elastic_products(
    *,
    actor,
    store: StoreAccount,
    source_group: str,
    client_factory=None,
    secret_resolver=default_ozon_secret_resolver,
):
    if source_group not in {ACTIVE_SOURCE_GROUP, CANDIDATE_SOURCE_GROUP}:
        raise ValidationError("Unsupported Ozon Elastic source group.")
    if not has_permission(actor, _permission_for_group(source_group), store):
        raise PermissionDenied("No permission or object access for Ozon Elastic products download.")
    require_ozon_store_for_ozon_api(store)
    connection = _active_connection(store)
    basis = _validate_selected_basis(store)
    action_id = str(basis["action_id"])

    step_code = _step_code_for_group(source_group)
    operation = create_api_operation(
        marketplace=Marketplace.OZON,
        store=store,
        initiator_user=actor,
        step_code=step_code,
        logic_version=LOGIC_VERSION,
        module=OperationModule.OZON_API,
        execution_context={
            "mode": OperationMode.API,
            "step_code": step_code,
            "connection_id": connection.pk,
            "has_protected_ref": True,
            "selected_action": {
                "action_id": action_id,
                "source_operation_id": basis.get("source_operation_id"),
            },
            "source_group": source_group,
        },
        launch_method=LaunchMethod.MANUAL,
        enforce_permissions=False,
    )
    operation = start_operation(operation)
    try:
        assert_no_secret_like_values(connection.metadata, field_name="connection metadata")
        credentials = secret_resolver(connection.protected_secret_ref)
        factory = client_factory or OzonApiClient
        client = factory(
            credentials=credentials,
            store_scope=store.visible_id or str(store.pk),
        )
        rows, pages = _fetch_product_group(
            client=client,
            action_id=action_id,
            source_group=source_group,
        )
        return _persist_success(
            actor=actor,
            store=store,
            operation=operation,
            action_id=action_id,
            source_group=source_group,
            rows=rows,
            pages=pages,
            fetched_at=timezone.now(),
        )
    except Exception as exc:
        result_code = _record_failure(operation, actor, store, exc, source_group=source_group)
        operation.status = ProcessStatus.INTERRUPTED_FAILED
        operation.summary = {
            "result_code": result_code,
            "source_group": source_group,
            "failure": getattr(exc, "safe_message", "Ozon API Elastic products download failed."),
        }
        operation.finished_at = timezone.now()
        operation.save(update_fields=["status", "summary", "finished_at", "updated_at"])
        operation.run.status = RunStatus.INTERRUPTED_FAILED
        operation.run.save(update_fields=["status", "updated_at"])
        if isinstance(exc, OzonApiError | ValidationError | PermissionDenied):
            raise
        raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message) from exc


def download_active_products(**kwargs):
    return download_elastic_products(source_group=ACTIVE_SOURCE_GROUP, **kwargs)


def download_candidate_products(**kwargs):
    return download_elastic_products(source_group=CANDIDATE_SOURCE_GROUP, **kwargs)


def latest_product_source_operation(*, store: StoreAccount, action_id: str, source_group: str):
    step_code = _step_code_for_group(source_group)
    return (
        store.operations.filter(
            marketplace=Marketplace.OZON,
            mode=OperationMode.API,
            module=OperationModule.OZON_API,
            step_code=step_code,
            status__in=[ProcessStatus.COMPLETED_SUCCESS, ProcessStatus.COMPLETED_WITH_WARNINGS],
            summary__action_id=str(action_id),
            summary__source_group=source_group,
        )
        .order_by("-finished_at", "-id")
        .first()
    )


def build_latest_product_source_basis(*, store: StoreAccount, action_id: str | None = None) -> dict:
    if action_id is None:
        basis = get_selected_elastic_action_basis(store)
        if not basis:
            raise ValidationError("Selected Elastic Boosting action is required.")
        action_id = str(basis.get("action_id") or "")
    active_operation = latest_product_source_operation(
        store=store,
        action_id=str(action_id),
        source_group=ACTIVE_SOURCE_GROUP,
    )
    candidate_operation = latest_product_source_operation(
        store=store,
        action_id=str(action_id),
        source_group=CANDIDATE_SOURCE_GROUP,
    )
    merged: dict[str, dict] = {}
    source_operations = {}

    for operation, source_group in (
        (active_operation, ACTIVE_SOURCE_GROUP),
        (candidate_operation, CANDIDATE_SOURCE_GROUP),
    ):
        if not operation:
            continue
        source_operations[source_group] = {
            "operation_id": operation.pk,
            "operation_visible_id": operation.visible_id,
            "products_count": operation.summary.get("products_count", 0),
        }
        for row in operation.summary.get("products", []):
            product_id = str(row.get("product_id") or "").strip()
            if not product_id:
                continue
            if product_id not in merged:
                merged[product_id] = {
                    **row,
                    "source_group": source_group,
                    "source_details": {
                        "source_groups": [source_group],
                        "source_operation_ids": [operation.pk],
                        "collision": False,
                    },
                }
                continue
            existing = merged[product_id]
            active_row = {
                key: value
                for key, value in existing.items()
                if key not in {"source_details"}
            }
            candidate_row = {
                key: value
                for key, value in row.items()
                if key not in {"source_details"}
            }
            groups = list(dict.fromkeys([*existing["source_details"]["source_groups"], source_group]))
            existing["source_group"] = COLLISION_SOURCE_GROUP
            existing["source_details"] = {
                "source_groups": groups,
                "source_operation_ids": list(
                    dict.fromkeys([*existing["source_details"]["source_operation_ids"], operation.pk])
                ),
                "collision": True,
                "collision_reason": "product_present_in_active_and_candidate_sources",
                "active_row": active_row,
                "candidate_row": candidate_row,
            }

    rows = list(merged.values())
    result = {
        "action_id": str(action_id),
        "source_operations": source_operations,
        "rows": rows,
        "rows_count": len(rows),
        "collision_count": sum(1 for row in rows if row.get("source_group") == COLLISION_SOURCE_GROUP),
        "missing_groups": [
            group
            for group, operation in (
                (ACTIVE_SOURCE_GROUP, active_operation),
                (CANDIDATE_SOURCE_GROUP, candidate_operation),
            )
            if operation is None
        ],
    }
    assert_no_secret_like_values(result, field_name="Ozon Elastic product source basis")
    return result
