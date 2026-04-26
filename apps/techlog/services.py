"""Service helpers for technical log, notifications and retention."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.identity_access.models import AccessEffect, StoreAccess
from apps.identity_access.services import has_full_object_scope, has_permission
from apps.stores.models import StoreAccount

from .models import (
    SystemNotification,
    TECHLOG_EVENT_SEVERITY_BASELINE,
    TechLogHandledStatus,
    TechLogEventType,
    TechLogRecord,
    TechLogSeverity,
    allow_techlog_retention_cleanup_delete,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TechLogCleanupResult:
    deleted_count: int
    cutoff_at: object


_SEVERITY_RANK = {
    TechLogSeverity.INFO: 0,
    TechLogSeverity.WARNING: 1,
    TechLogSeverity.ERROR: 2,
    TechLogSeverity.CRITICAL: 3,
}


def _normalized_severity(*, event_type: str, severity: str) -> str:
    if event_type not in TechLogEventType.values:
        raise ValidationError("Unknown techlog event type.")
    if severity not in TechLogSeverity.values:
        raise ValidationError("Unknown techlog severity.")

    baseline = TECHLOG_EVENT_SEVERITY_BASELINE[event_type]
    if _SEVERITY_RANK[severity] < _SEVERITY_RANK[baseline]:
        return baseline
    return severity


@transaction.atomic
def create_techlog_record(
    *,
    severity: str,
    event_type: str,
    source_component: str,
    safe_message: str = "",
    sensitive_details_ref: str = "",
    operation=None,
    store=None,
    user=None,
    entity_type: str = "",
    entity_id: str = "",
    handled_status: str = TechLogHandledStatus.RECORDED,
    occurred_at=None,
    create_notification_for_critical: bool = True,
    notification_topic: str = "",
) -> TechLogRecord:
    if store is None and operation is not None:
        store = operation.store
    severity = _normalized_severity(event_type=event_type, severity=severity)
    if severity == TechLogSeverity.CRITICAL:
        handled_status = TechLogHandledStatus.NOTIFICATION_CREATED
    record = TechLogRecord.objects.create(
        occurred_at=occurred_at or timezone.now(),
        severity=severity,
        event_type=event_type,
        operation=operation,
        store=store,
        user=user,
        entity_type=entity_type,
        entity_id=str(entity_id or ""),
        safe_message=safe_message,
        sensitive_details_ref=sensitive_details_ref,
        source_component=source_component,
        handled_status=handled_status,
    )
    if severity == TechLogSeverity.CRITICAL:
        _create_notification_for_techlog(record, topic=notification_topic)
    return record


def _create_notification_for_techlog(record: TechLogRecord, *, topic: str = "") -> SystemNotification:
    return SystemNotification.objects.create(
        severity=record.severity,
        topic=topic or record.event_type,
        message=record.safe_message,
        related_operation=record.operation,
        related_store=record.store,
        related_user=record.user,
        related_techlog_record=record,
    )


@transaction.atomic
def create_system_notification(
    *,
    severity: str,
    topic: str,
    message: str,
    related_operation=None,
    related_store=None,
    related_user=None,
    related_techlog_record=None,
) -> SystemNotification:
    return SystemNotification.objects.create(
        severity=severity,
        topic=topic,
        message=message,
        related_operation=related_operation,
        related_store=related_store,
        related_user=related_user,
        related_techlog_record=related_techlog_record,
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


def user_has_techlog_full_scope(user) -> bool:
    return has_full_object_scope(user) or has_permission(user, "logs.scope.full")


def techlog_records_visible_to(user, *, permission_code: str = "techlog.list.view"):
    queryset = TechLogRecord.objects.select_related("user", "store", "operation")
    if not user or not getattr(user, "is_authenticated", False) or not user.is_active:
        return queryset.none()

    if user_has_techlog_full_scope(user) and has_permission(user, permission_code):
        return queryset

    store_ids = _permission_allowed_store_ids(user, permission_code)
    if not store_ids:
        return queryset.none()

    return queryset.filter(
        Q(store_id__in=store_ids)
        | Q(operation__store_id__in=store_ids)
        | Q(user=user, store__isnull=True, operation__isnull=True)
    )


def can_view_techlog_record(user, record: TechLogRecord) -> bool:
    return techlog_records_visible_to(user, permission_code="techlog.card.view").filter(
        pk=record.pk,
    ).exists()


def sensitive_details_for(user, record: TechLogRecord) -> str:
    if not can_view_techlog_record(user, record):
        return ""
    if not has_permission(user, "techlog.sensitive.view"):
        return ""
    return record.sensitive_details_ref


def cleanup_expired_techlog_records(*, now=None) -> TechLogCleanupResult:
    cutoff_at = now or timezone.now()
    expired = TechLogRecord.objects.filter(retention_until__lte=cutoff_at)
    with allow_techlog_retention_cleanup_delete():
        deleted_count, _ = expired.delete()
    logger.info(
        "techlog_retention_cleanup_completed",
        extra={"deleted_count": deleted_count, "cutoff_at": cutoff_at.isoformat()},
    )
    return TechLogCleanupResult(deleted_count=deleted_count, cutoff_at=cutoff_at)
