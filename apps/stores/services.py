"""Service helpers for TASK-003 store/cabinet behavior."""

from __future__ import annotations

import json
from contextlib import contextmanager
from contextvars import ContextVar

from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.identity_access.models import AccessEffect, StoreAccess
from apps.identity_access.services import has_permission

from .models import (
    ConnectionBlock,
    StoreAccount,
    StoreAccountChangeHistory,
    is_sensitive_metadata_key,
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
        for key, value in metadata.items():
            if is_sensitive_metadata_key(key):
                sanitized[key] = "[redacted]"
            else:
                sanitized[key] = _sanitize_metadata(value)
        return sanitized
    if isinstance(metadata, list):
        return [_sanitize_metadata(value) for value in metadata]
    return metadata


def connection_metadata_display(metadata) -> str:
    return _stringify(_sanitize_metadata(metadata))


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
    require_store_permission(actor, "stores.connection.edit", permission_store)
    if "protected_secret_ref" in fields:
        require_store_permission(actor, "stores.connection.secret_edit", permission_store)

    before = None
    if connection.pk:
        before = ConnectionBlock.objects.get(pk=connection.pk)
        old_values = {
            field: _connection_field_value(before, field) for field in CONNECTION_HISTORY_FIELDS
        }
    else:
        old_values = {field: "" for field in CONNECTION_HISTORY_FIELDS}
        old_values["protected_secret_ref"] = "[empty]"

    for field, value in fields.items():
        setattr(connection, field, value)
    connection.is_stage1_used = False
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
