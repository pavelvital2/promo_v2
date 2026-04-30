"""Read-only Ozon actions download and Elastic Boosting action selection."""

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
from apps.stores.models import ConnectionBlock, StoreAccount
from apps.stores.services import (
    OZON_API_CONNECTION_TYPE,
    OZON_API_MODULE,
    default_ozon_secret_resolver,
    require_ozon_store_for_ozon_api,
)
from apps.techlog.models import TechLogSeverity
from apps.techlog.services import create_techlog_record

from .client import OzonApiClient, OzonApiError, OzonApiInvalidResponseError


LOGIC_VERSION = "ozon-api-actions-download-v1"
ELASTIC_ACTION_TYPE = "MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT"
ELASTIC_TITLE_MARKER = "Эластичный бустинг"
SELECTED_ACTION_METADATA_KEY = "ozon_api_elastic_selected_action"


def _active_connection(store: StoreAccount) -> ConnectionBlock:
    connection = (
        ConnectionBlock.objects.filter(
            store=store,
            module=OZON_API_MODULE,
            connection_type=OZON_API_CONNECTION_TYPE,
            status=ConnectionBlock.Status.ACTIVE,
        )
        .order_by("-updated_at", "-id")
        .first()
    )
    if not connection or not connection.protected_secret_ref:
        raise PermissionDenied("Active Ozon API connection is required.")
    return connection


def _checksum(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _actions_from_response(response: dict) -> list[dict]:
    result = response.get("result")
    if isinstance(result, list):
        actions = result
    elif isinstance(result, dict):
        for key in ("actions", "items", "list"):
            if isinstance(result.get(key), list):
                actions = result[key]
                break
        else:
            raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message)
    else:
        raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message)
    if not all(isinstance(action, dict) for action in actions):
        raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message)
    return actions


def _safe_action(action: dict) -> dict:
    safe = {
        "action_id": str(action.get("id") or action.get("action_id") or "").strip(),
        "title": str(action.get("title") or action.get("name") or "").strip(),
        "action_type": str(action.get("action_type") or "").strip(),
        "status": action.get("status"),
        "date_start": action.get("date_start") or action.get("start_date"),
        "date_end": action.get("date_end") or action.get("end_date"),
        "active_products_count": action.get("active_products_count"),
        "candidates_count": action.get("candidates_count"),
    }
    return redact({key: value for key, value in safe.items() if value not in (None, "")})


def _classify_action(action: dict) -> str:
    action_type_matches = action.get("action_type") == ELASTIC_ACTION_TYPE
    title_matches = ELASTIC_TITLE_MARKER in str(action.get("title") or action.get("name") or "")
    if action_type_matches and title_matches:
        return "elastic"
    if action_type_matches or title_matches:
        return "ambiguous"
    return "non_elastic"


def filter_elastic_actions(actions: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    safe_elastic: list[dict] = []
    safe_ambiguous: list[dict] = []
    safe_non_elastic: list[dict] = []
    for action in actions:
        safe = _safe_action(action)
        assert_no_secret_like_values(safe, field_name="Ozon safe action")
        classification = _classify_action(action)
        safe["classification"] = classification
        if classification == "elastic":
            safe_elastic.append(safe)
        elif classification == "ambiguous":
            safe_ambiguous.append(safe)
        else:
            safe_non_elastic.append(safe)
    return safe_elastic, safe_ambiguous, safe_non_elastic


def _fetch_actions(client: OzonApiClient) -> tuple[list[dict], list[dict]]:
    all_actions: list[dict] = []
    pages: list[dict] = []
    limit = client.policy.read_page_size
    offset = 0
    while True:
        response = client.list_actions(limit=limit, offset=offset)
        actions = _actions_from_response(response)
        safe_actions = [_safe_action(action) for action in actions]
        safe_response = {"result": safe_actions}
        assert_no_secret_like_values(safe_response, field_name="Ozon actions safe response snapshot")
        pages.append(
            {
                "endpoint_code": "ozon_actions",
                "method": "GET",
                "request_safe": {"limit": limit, "offset": offset},
                "actions_count": len(actions),
                "checksum": _checksum(safe_response),
            },
        )
        all_actions.extend(actions)
        if len(actions) < limit:
            break
        offset += limit
    return all_actions, pages


def _record_failure(operation, actor, store, exc: Exception):
    safe_message = getattr(exc, "safe_message", "Ozon API actions download failed.")
    event_type = getattr(exc, "techlog_event_type", "")
    if not event_type:
        event_type = "ozon_api_secret_redaction_violation" if isinstance(exc, ValueError) else "ozon_api_actions_download_failed"
    create_techlog_record(
        severity=TechLogSeverity.ERROR,
        event_type=event_type,
        source_component="apps.discounts.ozon_api.actions",
        operation=operation,
        store=store,
        user=actor,
        entity_type="Operation",
        entity_id=operation.pk,
        safe_message=safe_message,
        sensitive_details_ref="redacted:ozon-api-actions-download",
    )
    create_audit_record(
        action_code=AuditActionCode.OZON_API_ACTIONS_DOWNLOAD_COMPLETED,
        entity_type="Operation",
        entity_id=operation.pk,
        user=actor,
        store=store,
        operation=operation,
        safe_message=safe_message,
        after_snapshot={
            "status": ProcessStatus.INTERRUPTED_FAILED,
            "result_code": "ozon_api_actions_download_failed",
        },
        source_context=AuditSourceContext.SERVICE,
    )


@transaction.atomic
def _persist_success(*, actor, store, operation, actions, pages, fetched_at):
    elastic_actions, ambiguous_actions, non_elastic_actions = filter_elastic_actions(actions)
    actions_by_id = {
        action["action_id"]: action
        for action in [*elastic_actions, *ambiguous_actions, *non_elastic_actions]
        if action.get("action_id")
    }
    row_no = 1
    for action in [*elastic_actions, *ambiguous_actions, *non_elastic_actions]:
        classification = action["classification"]
        OperationDetailRow.objects.create(
            operation=operation,
            row_no=row_no,
            product_ref=action.get("action_id", ""),
            row_status=classification,
            reason_code="",
            message_level=MessageLevel.INFO if classification == "elastic" else MessageLevel.WARNING_INFO,
            message=(
                "Ozon action matches approved Elastic Boosting identifiers."
                if classification == "elastic"
                else "Ozon action is not approved for Elastic Boosting selection."
            ),
            problem_field="" if classification == "elastic" else "action_type/title",
            final_value=action,
        )
        row_no += 1

    safe_snapshot = {
        "endpoint_code": "ozon_actions",
        "method": "GET",
        "fetched_at": fetched_at.isoformat(),
        "pages": pages,
        "actions": list(actions_by_id.values()),
        "source_checksum": _checksum({"pages": pages, "actions": list(actions_by_id.values())}),
    }
    summary = {
        "fetched_at": fetched_at.isoformat(),
        "page_count": len(pages),
        "actions_count": len(actions),
        "elastic_actions_count": len(elastic_actions),
        "ambiguous_actions_count": len(ambiguous_actions),
        "non_elastic_actions_count": len(non_elastic_actions),
        "elastic_actions": elastic_actions,
        "safe_snapshot": safe_snapshot,
        "selection_basis": {
            "source_operation_id": operation.pk,
            "source_operation_visible_id": operation.visible_id,
            "available_action_ids": [action["action_id"] for action in elastic_actions],
            "selected_action_id": None,
        },
    }
    assert_no_secret_like_values(summary, field_name="Ozon actions operation summary")
    operation = complete_api_operation(
        operation,
        result=ApiOperationResult(
            summary=summary,
            status=ProcessStatus.COMPLETED_SUCCESS,
            error_count=0,
            warning_count=len(ambiguous_actions),
        ),
    )
    create_audit_record(
        action_code=AuditActionCode.OZON_API_ACTIONS_DOWNLOAD_COMPLETED,
        entity_type="Operation",
        entity_id=operation.pk,
        user=actor,
        store=store,
        operation=operation,
        safe_message="Ozon API actions download completed.",
        after_snapshot={
            "status": operation.status,
            "actions_count": len(actions),
            "elastic_actions_count": len(elastic_actions),
            "ambiguous_actions_count": len(ambiguous_actions),
        },
        source_context=AuditSourceContext.SERVICE,
    )
    from .review import mark_accepted_results_stale

    mark_accepted_results_stale(store=store, actor=actor)
    return operation


def download_ozon_actions(
    *,
    actor,
    store: StoreAccount,
    client_factory=None,
    secret_resolver=default_ozon_secret_resolver,
):
    if not has_permission(actor, "ozon.api.actions.download", store):
        raise PermissionDenied("No permission or object access for Ozon API actions download.")
    require_ozon_store_for_ozon_api(store)
    connection = _active_connection(store)

    operation = create_api_operation(
        marketplace=Marketplace.OZON,
        store=store,
        initiator_user=actor,
        step_code=OperationStepCode.OZON_API_ACTIONS_DOWNLOAD,
        logic_version=LOGIC_VERSION,
        module=OperationModule.OZON_API,
        execution_context={
            "mode": OperationMode.API,
            "step_code": OperationStepCode.OZON_API_ACTIONS_DOWNLOAD,
            "connection_id": connection.pk,
            "has_protected_ref": True,
        },
        launch_method=LaunchMethod.MANUAL,
        enforce_permissions=False,
    )
    create_audit_record(
        action_code=AuditActionCode.OZON_API_ACTIONS_DOWNLOAD_STARTED,
        entity_type="Operation",
        entity_id=operation.pk,
        user=actor,
        store=store,
        operation=operation,
        safe_message="Ozon API actions download started.",
        after_snapshot={
            "mode": OperationMode.API,
            "marketplace": Marketplace.OZON,
            "step_code": OperationStepCode.OZON_API_ACTIONS_DOWNLOAD,
        },
        source_context=AuditSourceContext.SERVICE,
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
        actions, pages = _fetch_actions(client)
        return _persist_success(
            actor=actor,
            store=store,
            operation=operation,
            actions=actions,
            pages=pages,
            fetched_at=timezone.now(),
        )
    except Exception as exc:
        _record_failure(operation, actor, store, exc)
        operation.status = ProcessStatus.INTERRUPTED_FAILED
        operation.summary = {
            "result_code": "ozon_api_actions_download_failed",
            "failure": getattr(exc, "safe_message", "Ozon API actions download failed."),
        }
        operation.finished_at = timezone.now()
        operation.save(update_fields=["status", "summary", "finished_at", "updated_at"])
        operation.run.status = RunStatus.INTERRUPTED_FAILED
        operation.run.save(update_fields=["status", "updated_at"])
        if isinstance(exc, OzonApiError | ValidationError | PermissionDenied):
            raise
        raise OzonApiInvalidResponseError(OzonApiInvalidResponseError.safe_message) from exc


def select_elastic_action(*, actor, store: StoreAccount, action_id: str) -> dict:
    if not has_permission(actor, "ozon.api.actions.download", store):
        raise PermissionDenied("No permission or object access for Ozon API action selection.")
    require_ozon_store_for_ozon_api(store)
    connection = _active_connection(store)
    operation = (
        store.operations.filter(
            marketplace=Marketplace.OZON,
            mode=OperationMode.API,
            module=OperationModule.OZON_API,
            step_code=OperationStepCode.OZON_API_ACTIONS_DOWNLOAD,
            status=ProcessStatus.COMPLETED_SUCCESS,
        )
        .order_by("-finished_at", "-id")
        .first()
    )
    if not operation:
        raise ValidationError("Ozon actions must be downloaded before action selection.")

    normalized_action_id = str(action_id).strip()
    elastic_actions = operation.summary.get("elastic_actions", [])
    selected_action = next(
        (action for action in elastic_actions if str(action.get("action_id")) == normalized_action_id),
        None,
    )
    if not selected_action:
        raise ValidationError("Selected action is not an approved Elastic Boosting action from the latest snapshot.")

    basis = {
        "action_id": normalized_action_id,
        "action": selected_action,
        "source_operation_id": operation.pk,
        "source_operation_visible_id": operation.visible_id,
        "selected_at": timezone.now().isoformat(),
        "selected_by_user_id": actor.pk,
    }
    assert_no_secret_like_values(basis, field_name="Ozon selected action basis")
    metadata = dict(connection.metadata or {})
    metadata[SELECTED_ACTION_METADATA_KEY] = basis
    connection.metadata = metadata
    connection.save(update_fields=["metadata", "updated_at"])
    return basis


def get_selected_elastic_action_basis(store: StoreAccount) -> dict | None:
    connection = (
        ConnectionBlock.objects.filter(
            store=store,
            module=OZON_API_MODULE,
            connection_type=OZON_API_CONNECTION_TYPE,
            status=ConnectionBlock.Status.ACTIVE,
        )
        .order_by("-updated_at", "-id")
        .first()
    )
    if not connection:
        return None
    basis = (connection.metadata or {}).get(SELECTED_ACTION_METADATA_KEY)
    return basis if isinstance(basis, dict) else None
