"""Service helpers for TASK-003 store/cabinet behavior."""

from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager
from contextvars import ContextVar

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditActionCode, AuditSourceContext
from apps.audit.services import create_audit_record
from apps.discounts.ozon_api.client import (
    OzonApiClient,
    OzonApiCredentials,
    OzonApiError,
    OzonApiInvalidResponseError,
)
from apps.discounts.wb_api.client import WBApiError, WBApiClient, WBApiInvalidResponseError
from apps.discounts.wb_api.redaction import (
    assert_no_secret_like_values,
    contains_secret_like_value,
    is_secret_like_key,
    redact,
)
from apps.identity_access.models import AccessEffect, StoreAccess
from apps.identity_access.services import has_permission
from apps.operations.models import (
    Marketplace,
    OperationModule,
    OperationStepCode,
    ProcessStatus,
)
from apps.operations.services import (
    ApiOperationResult,
    complete_api_operation,
    create_api_operation,
    start_operation,
)
from apps.techlog.models import TechLogSeverity
from apps.techlog.services import create_techlog_record

from .models import (
    ConnectionBlock,
    StoreAccount,
    StoreAccountChangeHistory,
)


API_STAGE_2_NOTICE = "подготовлено для этапа 2, в этапе 1 не используется"
STORE_CHANGE_FIELDS = (
    "visible_id",
    "name",
    "group",
    "marketplace",
    "cabinet_type",
    "status",
    "comments",
)
CONNECTION_HISTORY_FIELDS = (
    "module",
    "connection_type",
    "status",
    "protected_secret_ref",
    "metadata",
)
WB_API_MODULE = "wb_api"
WB_API_CONNECTION_TYPE = "wb_header_api_key"
OZON_API_MODULE = "ozon_api"
OZON_API_CONNECTION_TYPE = "ozon_client_id_api_key"
LOCAL_ENV_SECRET_REF_PREFIX = "env://"
LOCAL_ENV_SECRET_REF_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")

_history_context = ContextVar("store_history_context", default=(None, "system"))


@contextmanager
def store_history_context(actor=None, source: str = "system"):
    token = _history_context.set((actor, source))
    try:
        yield
    finally:
        _history_context.reset(token)


def _current_history_context():
    return _history_context.get()


def _stringify(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return str(value)


def _store_field_value(store: StoreAccount, field_code: str) -> str:
    if field_code == "group":
        if not store.group_id:
            return ""
        return f"{store.group.visible_id or store.group_id} {store.group.name}"
    return _stringify(getattr(store, field_code))


def _redacted_secret_ref(value: str | None) -> str:
    return "[ref-set]" if value else "[empty]"


def _sanitize_metadata(metadata):
    if not metadata:
        return {} if metadata is None else metadata
    if isinstance(metadata, dict):
        sanitized = {}
        redacted_index = 1
        for key, value in metadata.items():
            if is_secret_like_key(key):
                sanitized[f"redacted_field_{redacted_index}"] = "[redacted]"
                redacted_index += 1
            else:
                sanitized[key] = _sanitize_metadata(value)
        return sanitized
    if isinstance(metadata, list):
        return [_sanitize_metadata(value) for value in metadata]
    if contains_secret_like_value(metadata):
        return "[redacted]"
    return metadata


def connection_metadata_display(metadata) -> str:
    return _stringify(_sanitize_metadata(metadata))


def store_history_value_display(field_code: str, value) -> str:
    if field_code == "connection.metadata":
        return _stringify(_sanitize_metadata(value))
    return _stringify(value)


def _connection_field_value(connection: ConnectionBlock, field_code: str) -> str:
    if field_code == "protected_secret_ref":
        return _redacted_secret_ref(connection.protected_secret_ref)
    if field_code == "metadata":
        return connection_metadata_display(connection.metadata)
    return _stringify(getattr(connection, field_code))


def record_store_change(
    store: StoreAccount,
    field_code: str,
    old_value,
    new_value,
    actor=None,
    source: str = "system",
):
    if field_code == "connection.metadata":
        old_value = _sanitize_metadata(old_value)
        new_value = _sanitize_metadata(new_value)
    old_text = _stringify(old_value)
    new_text = _stringify(new_value)
    if old_text == new_text:
        return None
    return StoreAccountChangeHistory.objects.create(
        store=store,
        changed_by=actor,
        field_code=field_code,
        old_value=old_text,
        new_value=new_text,
        source=source,
    )


def _allowed_store_ids(user) -> set[int]:
    rows = StoreAccess.objects.filter(user=user, is_active=True).values_list("store_id", "effect")
    allowed = {store_id for store_id, effect in rows if effect == AccessEffect.ALLOW}
    denied = {store_id for store_id, effect in rows if effect == AccessEffect.DENY}
    return allowed - denied


def visible_stores_queryset(user):
    base = StoreAccount.objects.select_related("group")
    if not user or not getattr(user, "is_authenticated", False) or not user.is_active:
        return base.none()

    candidate_ids = set(base.values_list("id", flat=True))
    if not candidate_ids:
        return base.none()

    allowed_ids = {
        store.pk
        for store in base.filter(pk__in=candidate_ids)
        if has_permission(user, "stores.list.view", store)
    }
    return base.filter(pk__in=allowed_ids)


def require_store_permission(user, permission_code: str, store: StoreAccount):
    if not has_permission(user, permission_code, store):
        raise PermissionDenied("No permission or object access for this store/cabinet.")


def require_wb_store_for_wb_api(store: StoreAccount):
    if store.marketplace != StoreAccount.Marketplace.WB:
        raise PermissionDenied("WB API connection is available only for WB stores.")


def require_ozon_store_for_ozon_api(store: StoreAccount):
    if store.marketplace != StoreAccount.Marketplace.OZON:
        raise PermissionDenied("Ozon API connection is available only for Ozon stores.")


def _validate_connection_marketplace_compatibility(
    *,
    store: StoreAccount,
    module: str,
    connection_type: str,
) -> None:
    if module == WB_API_MODULE or connection_type == WB_API_CONNECTION_TYPE:
        require_wb_store_for_wb_api(store)
    if module == OZON_API_MODULE or connection_type == OZON_API_CONNECTION_TYPE:
        require_ozon_store_for_ozon_api(store)
    if module == WB_API_MODULE and connection_type != WB_API_CONNECTION_TYPE:
        raise ValidationError("WB API connection requires WB API connection type.")
    if module == OZON_API_MODULE and connection_type != OZON_API_CONNECTION_TYPE:
        raise ValidationError("Ozon API connection requires Ozon API connection type.")


@transaction.atomic
def create_store_account(actor, **fields) -> StoreAccount:
    if not has_permission(actor, "stores.create"):
        raise PermissionDenied("Actor cannot create stores/cabinets.")
    store = StoreAccount.objects.create(**fields)
    record_store_change(store, "created", "", store.visible_id, actor=actor, source="service")
    return store


@transaction.atomic
def update_store_account(actor, store: StoreAccount, **fields) -> StoreAccount:
    require_store_permission(actor, "stores.edit", store)
    before = StoreAccount.objects.select_related("group").get(pk=store.pk)
    old_values = {field: _store_field_value(before, field) for field in STORE_CHANGE_FIELDS}

    for field, value in fields.items():
        setattr(store, field, value)
    store.save()
    store.refresh_from_db()

    for field in STORE_CHANGE_FIELDS:
        new_value = _store_field_value(store, field)
        record_store_change(
            store,
            field,
            old_values[field],
            new_value,
            actor=actor,
            source="service",
        )
    return store


@transaction.atomic
def save_connection_block(actor, connection: ConnectionBlock, **fields) -> ConnectionBlock:
    permission_store = connection.store
    target_module = fields.get("module", connection.module)
    target_connection_type = fields.get("connection_type", connection.connection_type)
    _validate_connection_marketplace_compatibility(
        store=permission_store,
        module=target_module,
        connection_type=target_connection_type,
    )
    if target_module == WB_API_MODULE:
        require_wb_store_for_wb_api(permission_store)
    if target_module == OZON_API_MODULE:
        require_ozon_store_for_ozon_api(permission_store)
    if fields.get("status") == ConnectionBlock.Status.ACTIVE:
        raise ValidationError("Active status is service-owned and can be set only by a successful check.")

    if target_module == WB_API_MODULE:
        manage_permission = "wb.api.connection.manage"
    elif target_module == OZON_API_MODULE:
        manage_permission = "ozon.api.connection.manage"
    else:
        manage_permission = "stores.connection.edit"
    require_store_permission(actor, manage_permission, permission_store)
    if "protected_secret_ref" in fields:
        require_store_permission(actor, manage_permission, permission_store)

    before = None
    if connection.pk:
        before = ConnectionBlock.objects.get(pk=connection.pk)
        old_values = {
            field: _connection_field_value(before, field) for field in CONNECTION_HISTORY_FIELDS
        }
    else:
        old_values = {field: "" for field in CONNECTION_HISTORY_FIELDS}
        old_values["protected_secret_ref"] = "[empty]"

    protected_secret_ref_changed = False
    for field, value in fields.items():
        if field == "protected_secret_ref":
            protected_secret_ref_changed = connection.protected_secret_ref != value
        setattr(connection, field, value)
    connection.is_stage1_used = False
    if connection.module == WB_API_MODULE:
        connection.connection_type = connection.connection_type or WB_API_CONNECTION_TYPE
        connection.is_stage2_1_used = True
        if protected_secret_ref_changed and connection.protected_secret_ref:
            connection.status = ConnectionBlock.Status.CONFIGURED
        elif connection.protected_secret_ref and connection.status == ConnectionBlock.Status.NOT_CONFIGURED:
            connection.status = ConnectionBlock.Status.CONFIGURED
    if connection.module == OZON_API_MODULE:
        connection.connection_type = connection.connection_type or OZON_API_CONNECTION_TYPE
        if protected_secret_ref_changed and connection.protected_secret_ref:
            connection.status = ConnectionBlock.Status.CONFIGURED
        elif connection.protected_secret_ref and connection.status == ConnectionBlock.Status.NOT_CONFIGURED:
            connection.status = ConnectionBlock.Status.CONFIGURED
    connection.save()
    connection.refresh_from_db()

    for field in CONNECTION_HISTORY_FIELDS:
        record_store_change(
            connection.store,
            f"connection.{field}",
            old_values[field],
            _connection_field_value(connection, field),
            actor=actor,
            source="service",
        )
    if before is None:
        record_store_change(
            connection.store,
            "connection.stage",
            "",
            API_STAGE_2_NOTICE,
            actor=actor,
            source="service",
        )
    action_code = (
        AuditActionCode.WB_API_CONNECTION_CREATED
        if before is None and connection.module == WB_API_MODULE
        else AuditActionCode.WB_API_CONNECTION_UPDATED
        if connection.module == WB_API_MODULE
        else AuditActionCode.OZON_API_CONNECTION_CREATED
        if before is None and connection.module == OZON_API_MODULE
        else AuditActionCode.OZON_API_CONNECTION_UPDATED
        if connection.module == OZON_API_MODULE
        else None
    )
    if action_code:
        marketplace_label = "WB" if connection.module == WB_API_MODULE else "Ozon"
        create_audit_record(
            action_code=action_code,
            entity_type="ConnectionBlock",
            entity_id=connection.pk,
            user=actor,
            store=connection.store,
            safe_message=f"{marketplace_label} API connection saved without exposing protected secret.",
            before_snapshot=redact({"status": old_values.get("status", "")}),
            after_snapshot=redact(
                {
                    "module": connection.module,
                    "connection_type": connection.connection_type,
                    "status": connection.status,
                    "has_protected_ref": bool(connection.protected_secret_ref),
                    "metadata": connection.metadata,
                },
            ),
            source_context=AuditSourceContext.UI,
        )
    return connection


def default_secret_resolver(protected_secret_ref: str) -> str:
    """Resolve local TASK-011 protected refs in the deterministic env://ENV_VAR_NAME format."""
    if not protected_secret_ref.startswith(LOCAL_ENV_SECRET_REF_PREFIX):
        raise WBApiInvalidResponseError("Protected secret reference cannot be resolved by the local resolver.")
    env_name = protected_secret_ref.removeprefix(LOCAL_ENV_SECRET_REF_PREFIX)
    if not LOCAL_ENV_SECRET_REF_PATTERN.fullmatch(env_name):
        raise WBApiInvalidResponseError("Protected secret reference has an invalid local resolver format.")
    token = os.environ.get(env_name, "")
    if not token:
        raise WBApiInvalidResponseError("Protected secret reference is not configured.")
    return token


def default_ozon_secret_resolver(protected_secret_ref: str) -> OzonApiCredentials:
    """Resolve local Ozon protected refs from env://ENV_VAR_NAME JSON value."""
    if not protected_secret_ref.startswith(LOCAL_ENV_SECRET_REF_PREFIX):
        raise OzonApiInvalidResponseError("Protected secret reference cannot be resolved by the local resolver.")
    env_name = protected_secret_ref.removeprefix(LOCAL_ENV_SECRET_REF_PREFIX)
    if not LOCAL_ENV_SECRET_REF_PATTERN.fullmatch(env_name):
        raise OzonApiInvalidResponseError("Protected secret reference has an invalid local resolver format.")
    raw_value = os.environ.get(env_name, "")
    if not raw_value:
        raise OzonApiInvalidResponseError("Protected secret reference is not configured.")
    try:
        data = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise OzonApiInvalidResponseError("Protected secret reference payload is invalid.") from exc
    if not isinstance(data, dict):
        raise OzonApiInvalidResponseError("Protected secret reference payload is invalid.")
    client_id = str(data.get("client_id", "")).strip()
    api_key = str(data.get("api_key", "")).strip()
    if not client_id or not api_key:
        raise OzonApiInvalidResponseError("Protected secret reference payload is incomplete.")
    return OzonApiCredentials(client_id=client_id, api_key=api_key)


def _create_ozon_connection_check_operation(actor, connection: ConnectionBlock):
    return create_api_operation(
        marketplace=Marketplace.OZON,
        module=OperationModule.OZON_API,
        store=connection.store,
        initiator_user=actor,
        step_code=OperationStepCode.OZON_API_CONNECTION_CHECK,
        logic_version="task-019",
        execution_context={"connection_block_id": connection.pk},
        launch_method="manual",
    )


def _complete_ozon_connection_check_operation(
    operation,
    *,
    status: str,
    summary: dict,
    error_count: int = 0,
) -> None:
    started = start_operation(operation)
    complete_api_operation(
        started,
        result=ApiOperationResult(
            status=status,
            summary=summary,
            error_count=error_count,
        ),
    )


@transaction.atomic
def check_wb_api_connection(
    actor,
    connection: ConnectionBlock,
    *,
    client_factory=None,
    secret_resolver=default_secret_resolver,
):
    require_store_permission(actor, "wb.api.connection.manage", connection.store)
    require_wb_store_for_wb_api(connection.store)
    if connection.module != WB_API_MODULE:
        raise PermissionDenied("Only WB API connection can be checked by this flow.")
    if connection.status in {ConnectionBlock.Status.DISABLED, ConnectionBlock.Status.ARCHIVED}:
        raise PermissionDenied("Disabled or archived connection cannot be checked.")
    if not connection.protected_secret_ref:
        connection.status = ConnectionBlock.Status.NOT_CONFIGURED
        connection.last_checked_at = timezone.now()
        connection.last_check_status = "not_configured"
        connection.last_check_message = "Protected secret reference is not configured."
        connection.save(
            update_fields=[
                "status",
                "last_checked_at",
                "last_check_status",
                "last_check_message",
                "updated_at",
            ],
        )
        create_audit_record(
            action_code=AuditActionCode.WB_API_CONNECTION_CHECKED,
            entity_type="ConnectionBlock",
            entity_id=connection.pk,
            user=actor,
            store=connection.store,
            safe_message=connection.last_check_message,
            after_snapshot={
                "status": connection.status,
                "last_check_status": connection.last_check_status,
                "has_protected_ref": False,
            },
            source_context=AuditSourceContext.UI,
        )
        return connection

    try:
        token = secret_resolver(connection.protected_secret_ref)
    except WBApiError as exc:
        checked_at = timezone.now()
        connection.status = ConnectionBlock.Status.CHECK_FAILED
        connection.last_checked_at = checked_at
        connection.last_check_status = "failed"
        connection.last_check_message = exc.safe_message
        connection.save(
            update_fields=[
                "status",
                "last_checked_at",
                "last_check_status",
                "last_check_message",
                "updated_at",
            ],
        )
        create_techlog_record(
            severity=TechLogSeverity.ERROR,
            event_type=exc.techlog_event_type,
            source_component="apps.stores.wb_api_connection",
            store=connection.store,
            user=actor,
            entity_type="ConnectionBlock",
            entity_id=connection.pk,
            safe_message=exc.safe_message,
            sensitive_details_ref="redacted:wba-connection-check",
        )
        create_audit_record(
            action_code=AuditActionCode.WB_API_CONNECTION_CHECKED,
            entity_type="ConnectionBlock",
            entity_id=connection.pk,
            user=actor,
            store=connection.store,
            safe_message=connection.last_check_message,
            after_snapshot={
                "status": connection.status,
                "last_check_status": connection.last_check_status,
                "has_protected_ref": bool(connection.protected_secret_ref),
            },
            source_context=AuditSourceContext.UI,
        )
        return connection
    assert_no_secret_like_values(connection.metadata, field_name="connection metadata")
    factory = client_factory or WBApiClient
    client = factory(
        token=token,
        store_scope=connection.store.visible_id or str(connection.store_id),
    )

    checked_at = timezone.now()
    safe_message = "WB API connection check succeeded."
    try:
        client.check_connection()
    except WBApiError as exc:
        safe_message = exc.safe_message
        connection.status = ConnectionBlock.Status.CHECK_FAILED
        connection.last_check_status = "failed"
        connection.last_check_message = safe_message
        connection.last_checked_at = checked_at
        connection.save(
            update_fields=[
                "status",
                "last_check_status",
                "last_check_message",
                "last_checked_at",
                "updated_at",
            ],
        )
        create_techlog_record(
            severity=TechLogSeverity.WARNING,
            event_type=exc.techlog_event_type,
            source_component="apps.stores.wb_api_connection",
            store=connection.store,
            user=actor,
            entity_type="ConnectionBlock",
            entity_id=connection.pk,
            safe_message=safe_message,
            sensitive_details_ref="redacted:wba-connection-check",
        )
    else:
        connection.status = ConnectionBlock.Status.ACTIVE
        connection.last_check_status = "success"
        connection.last_check_message = safe_message
        connection.last_checked_at = checked_at
        connection.save(
            update_fields=[
                "status",
                "last_check_status",
                "last_check_message",
                "last_checked_at",
                "updated_at",
            ],
        )

    create_audit_record(
        action_code=AuditActionCode.WB_API_CONNECTION_CHECKED,
        entity_type="ConnectionBlock",
        entity_id=connection.pk,
        user=actor,
        store=connection.store,
        safe_message=connection.last_check_message,
        after_snapshot={
            "status": connection.status,
            "last_check_status": connection.last_check_status,
            "has_protected_ref": bool(connection.protected_secret_ref),
        },
        source_context=AuditSourceContext.UI,
    )
    return connection


@transaction.atomic
def check_ozon_api_connection(
    actor,
    connection: ConnectionBlock,
    *,
    client_factory=None,
    secret_resolver=default_ozon_secret_resolver,
):
    require_store_permission(actor, "ozon.api.connection.manage", connection.store)
    require_ozon_store_for_ozon_api(connection.store)
    if connection.module != OZON_API_MODULE:
        raise PermissionDenied("Only Ozon API connection can be checked by this flow.")
    if connection.status in {ConnectionBlock.Status.DISABLED, ConnectionBlock.Status.ARCHIVED}:
        raise PermissionDenied("Disabled or archived connection cannot be checked.")
    operation = _create_ozon_connection_check_operation(actor, connection)
    if not connection.protected_secret_ref:
        connection.status = ConnectionBlock.Status.NOT_CONFIGURED
        connection.last_checked_at = timezone.now()
        connection.last_check_status = "not_configured"
        connection.last_check_message = "Protected secret reference is not configured."
        connection.save(
            update_fields=[
                "status",
                "last_checked_at",
                "last_check_status",
                "last_check_message",
                "updated_at",
            ],
        )
        create_audit_record(
            action_code=AuditActionCode.OZON_API_CONNECTION_CHECKED,
            entity_type="ConnectionBlock",
            entity_id=connection.pk,
            user=actor,
            store=connection.store,
            operation=operation,
            safe_message=connection.last_check_message,
            after_snapshot={
                "status": connection.status,
                "last_check_status": connection.last_check_status,
                "has_protected_ref": False,
            },
            source_context=AuditSourceContext.UI,
        )
        _complete_ozon_connection_check_operation(
            operation,
            status=ProcessStatus.COMPLETED_WITH_ERROR,
            summary={
                "status": connection.status,
                "last_check_status": connection.last_check_status,
                "has_protected_ref": False,
            },
            error_count=1,
        )
        return connection

    try:
        credentials = secret_resolver(connection.protected_secret_ref)
    except OzonApiError as exc:
        checked_at = timezone.now()
        connection.status = ConnectionBlock.Status.CHECK_FAILED
        connection.last_checked_at = checked_at
        connection.last_check_status = exc.check_status
        connection.last_check_message = exc.safe_message
        connection.save(
            update_fields=[
                "status",
                "last_checked_at",
                "last_check_status",
                "last_check_message",
                "updated_at",
            ],
        )
        create_techlog_record(
            severity=TechLogSeverity.ERROR,
            event_type=exc.techlog_event_type,
            source_component="apps.stores.ozon_api_connection",
            operation=operation,
            store=connection.store,
            user=actor,
            entity_type="ConnectionBlock",
            entity_id=connection.pk,
            safe_message=exc.safe_message,
            sensitive_details_ref="redacted:ozon-connection-check",
        )
        create_audit_record(
            action_code=AuditActionCode.OZON_API_CONNECTION_CHECKED,
            entity_type="ConnectionBlock",
            entity_id=connection.pk,
            user=actor,
            store=connection.store,
            operation=operation,
            safe_message=connection.last_check_message,
            after_snapshot={
                "status": connection.status,
                "last_check_status": connection.last_check_status,
                "has_protected_ref": bool(connection.protected_secret_ref),
            },
            source_context=AuditSourceContext.UI,
        )
        _complete_ozon_connection_check_operation(
            operation,
            status=ProcessStatus.COMPLETED_WITH_ERROR,
            summary={
                "status": connection.status,
                "last_check_status": connection.last_check_status,
                "has_protected_ref": bool(connection.protected_secret_ref),
            },
            error_count=1,
        )
        return connection

    assert_no_secret_like_values(connection.metadata, field_name="connection metadata")
    factory = client_factory or OzonApiClient
    client = factory(
        credentials=credentials,
        store_scope=connection.store.visible_id or str(connection.store_id),
    )

    checked_at = timezone.now()
    safe_message = "Ozon API connection check succeeded."
    try:
        client.check_connection()
    except OzonApiError as exc:
        safe_message = exc.safe_message
        connection.status = ConnectionBlock.Status.CHECK_FAILED
        connection.last_check_status = exc.check_status
        connection.last_check_message = safe_message
        connection.last_checked_at = checked_at
        connection.save(
            update_fields=[
                "status",
                "last_check_status",
                "last_check_message",
                "last_checked_at",
                "updated_at",
            ],
        )
        severity = (
            TechLogSeverity.WARNING
            if exc.techlog_event_type in {"ozon_api_rate_limited", "ozon_api_timeout"}
            else TechLogSeverity.ERROR
        )
        create_techlog_record(
            severity=severity,
            event_type=exc.techlog_event_type,
            source_component="apps.stores.ozon_api_connection",
            operation=operation,
            store=connection.store,
            user=actor,
            entity_type="ConnectionBlock",
            entity_id=connection.pk,
            safe_message=safe_message,
            sensitive_details_ref="redacted:ozon-connection-check",
        )
    else:
        connection.status = ConnectionBlock.Status.ACTIVE
        connection.last_check_status = "success"
        connection.last_check_message = safe_message
        connection.last_checked_at = checked_at
        connection.save(
            update_fields=[
                "status",
                "last_check_status",
                "last_check_message",
                "last_checked_at",
                "updated_at",
            ],
        )

    create_audit_record(
        action_code=AuditActionCode.OZON_API_CONNECTION_CHECKED,
        entity_type="ConnectionBlock",
        entity_id=connection.pk,
        user=actor,
        store=connection.store,
        operation=operation,
        safe_message=connection.last_check_message,
        after_snapshot={
            "status": connection.status,
            "last_check_status": connection.last_check_status,
            "has_protected_ref": bool(connection.protected_secret_ref),
        },
        source_context=AuditSourceContext.UI,
    )
    _complete_ozon_connection_check_operation(
        operation,
        status=(
            ProcessStatus.COMPLETED_SUCCESS
            if connection.last_check_status == "success"
            else ProcessStatus.COMPLETED_WITH_ERROR
        ),
        summary={
            "status": connection.status,
            "last_check_status": connection.last_check_status,
            "has_protected_ref": bool(connection.protected_secret_ref),
        },
        error_count=0 if connection.last_check_status == "success" else 1,
    )
    return connection


def record_store_access_change(access: StoreAccess, old_value: str = "", source: str = "system"):
    actor, context_source = _current_history_context()
    new_value = (
        f"user={access.user.visible_id or access.user_id}; "
        f"level={access.access_level}; effect={access.effect}; active={access.is_active}"
    )
    return record_store_change(
        access.store,
        "access.user",
        old_value,
        new_value,
        actor=actor,
        source=source or context_source,
    )
