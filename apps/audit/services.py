"""Service helpers for audit creation, visibility and retention."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.identity_access.models import AccessEffect, StoreAccess
from apps.identity_access.services import has_full_object_scope, has_permission
from apps.stores.models import StoreAccount
from apps.discounts.wb_api.redaction import assert_no_secret_like_values

from .models import (
    AuditRecord,
    AuditSourceContext,
    AuditVisibleScope,
    allow_audit_retention_cleanup_delete,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuditCleanupResult:
    deleted_count: int
    cutoff_at: object


@transaction.atomic
def create_audit_record(
    *,
    action_code: str,
    entity_type: str,
    entity_id: str = "",
    user=None,
    store=None,
    operation=None,
    safe_message: str = "",
    before_snapshot: dict | None = None,
    after_snapshot: dict | None = None,
    source_context: str = AuditSourceContext.SERVICE,
    visible_scope: str = AuditVisibleScope.LIMITED,
    occurred_at=None,
) -> AuditRecord:
    if store is None and operation is not None:
        store = operation.store
    assert_no_secret_like_values(safe_message, field_name="audit safe_message")
    assert_no_secret_like_values(before_snapshot or {}, field_name="audit before_snapshot")
    assert_no_secret_like_values(after_snapshot or {}, field_name="audit after_snapshot")
    return AuditRecord.objects.create(
        occurred_at=occurred_at or timezone.now(),
        user=user,
        action_code=action_code,
        entity_type=entity_type,
        entity_id=str(entity_id or ""),
        store=store,
        operation=operation,
        safe_message=safe_message,
        before_snapshot=before_snapshot or {},
        after_snapshot=after_snapshot or {},
        source_context=source_context,
        visible_scope=visible_scope,
    )


def _active_allowed_store_ids(user) -> set[int]:
    rows = StoreAccess.objects.filter(user=user, is_active=True).values_list("store_id", "effect")
    allowed = {store_id for store_id, effect in rows if effect == AccessEffect.ALLOW}
    denied = {store_id for store_id, effect in rows if effect == AccessEffect.DENY}
    return allowed - denied


def _permission_allowed_store_ids(user, permission_code: str) -> set[int]:
    candidate_ids = _active_allowed_store_ids(user)
    if not candidate_ids:
        return set()
    stores = StoreAccount.objects.filter(pk__in=candidate_ids)
    return {
        store.pk
        for store in stores
        if has_permission(user, permission_code, store)
        and has_permission(user, "logs.scope.limited", store)
    }


def user_has_audit_full_scope(user) -> bool:
    return has_full_object_scope(user) or has_permission(user, "logs.scope.full")


def audit_records_visible_to(user, *, permission_code: str = "audit.list.view"):
    queryset = AuditRecord.objects.select_related("user", "store", "operation")
    if not user or not getattr(user, "is_authenticated", False) or not user.is_active:
        return queryset.none()

    if user_has_audit_full_scope(user) and has_permission(user, permission_code):
        return queryset

    store_ids = _permission_allowed_store_ids(user, permission_code)
    if not store_ids:
        return queryset.none()

    return queryset.filter(visible_scope=AuditVisibleScope.LIMITED).filter(
        Q(store_id__in=store_ids)
        | Q(operation__store_id__in=store_ids)
        | Q(user=user, store__isnull=True, operation__isnull=True)
    )


def can_view_audit_record(user, record: AuditRecord) -> bool:
    return audit_records_visible_to(user, permission_code="audit.card.view").filter(
        pk=record.pk,
    ).exists()


def cleanup_expired_audit_records(*, now=None) -> AuditCleanupResult:
    cutoff_at = now or timezone.now()
    expired = AuditRecord.objects.filter(retention_until__lte=cutoff_at)
    with allow_audit_retention_cleanup_delete():
        deleted_count, _ = expired.delete()
    logger.info(
        "audit_retention_cleanup_completed",
        extra={"deleted_count": deleted_count, "cutoff_at": cutoff_at.isoformat()},
    )
    return AuditCleanupResult(deleted_count=deleted_count, cutoff_at=cutoff_at)
