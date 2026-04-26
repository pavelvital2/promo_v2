"""Audit records for significant user/admin actions."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone


AUDIT_RETENTION_DAYS = 90
_audit_retention_cleanup_allowed = ContextVar(
    "audit_retention_cleanup_allowed",
    default=False,
)


@contextmanager
def allow_audit_retention_cleanup_delete():
    token = _audit_retention_cleanup_allowed.set(True)
    try:
        yield
    finally:
        _audit_retention_cleanup_allowed.reset(token)


def _is_audit_retention_cleanup_allowed() -> bool:
    return _audit_retention_cleanup_allowed.get()


class AuditActionCode(models.TextChoices):
    OPERATION_CHECK_STARTED = "operation.check_started", "Operation check started"
    OPERATION_PROCESS_STARTED = "operation.process_started", "Operation process started"
    OPERATION_WARNING_CONFIRMED = (
        "operation.warning_confirmed",
        "Operation warning confirmed",
    )
    FILE_INPUT_UPLOADED = "file.input_uploaded", "Input file uploaded"
    FILE_INPUT_REPLACED = "file.input_replaced", "Input file replaced"
    FILE_OUTPUT_DOWNLOADED = "file.output_downloaded", "Output file downloaded"
    SETTINGS_WB_PARAMETER_CHANGED = (
        "settings.wb_parameter_changed",
        "WB parameter changed",
    )
    STORE_CREATED = "store.created", "Store created"
    STORE_CHANGED = "store.changed", "Store changed"
    STORE_ARCHIVED_OR_DEACTIVATED = (
        "store.archived_or_deactivated",
        "Store archived or deactivated",
    )
    STORE_CONNECTION_CHANGED = "store.connection_changed", "Store connection changed"
    STORE_CONNECTION_SECRET_CHANGED = (
        "store.connection_secret_changed",
        "Store connection secret changed",
    )
    STORE_ACCESS_CHANGED = "store.access_changed", "Store access changed"
    USER_CREATED = "user.created", "User created"
    USER_CHANGED = "user.changed", "User changed"
    USER_BLOCKED_OR_UNBLOCKED = "user.blocked_or_unblocked", "User blocked/unblocked"
    USER_ARCHIVED = "user.archived", "User archived"
    ROLE_CREATED = "role.created", "Role created"
    ROLE_CHANGED = "role.changed", "Role changed"
    ROLE_ARCHIVED_OR_DEACTIVATED = (
        "role.archived_or_deactivated",
        "Role archived or deactivated",
    )
    PERMISSION_OVERRIDE_CHANGED = (
        "permission.override_changed",
        "Permission override changed",
    )
    SYSTEM_DICTIONARY_CHANGED_BY_MIGRATION = (
        "system.dictionary_changed_by_migration",
        "System dictionary changed by migration",
    )
    WB_API_CONNECTION_CREATED = "wb_api_connection_created", "WB API connection created"
    WB_API_CONNECTION_UPDATED = "wb_api_connection_updated", "WB API connection updated"
    WB_API_CONNECTION_CHECKED = "wb_api_connection_checked", "WB API connection checked"
    WB_API_PRICES_DOWNLOAD_STARTED = (
        "wb_api_prices_download_started",
        "WB API prices download started",
    )
    WB_API_PRICES_DOWNLOAD_COMPLETED = (
        "wb_api_prices_download_completed",
        "WB API prices download completed",
    )
    WB_API_PRICES_FILE_DOWNLOADED = (
        "wb_api_prices_file_downloaded",
        "WB API prices file downloaded",
    )
    WB_API_PROMOTIONS_DOWNLOAD_STARTED = (
        "wb_api_promotions_download_started",
        "WB API promotions download started",
    )
    WB_API_PROMOTIONS_DOWNLOAD_COMPLETED = (
        "wb_api_promotions_download_completed",
        "WB API promotions download completed",
    )
    WB_API_PROMOTIONS_FILE_DOWNLOADED = (
        "wb_api_promotions_file_downloaded",
        "WB API promotions file downloaded",
    )
    WB_API_DISCOUNT_CALCULATION_STARTED = (
        "wb_api_discount_calculation_started",
        "WB API discount calculation started",
    )
    WB_API_DISCOUNT_CALCULATION_COMPLETED = (
        "wb_api_discount_calculation_completed",
        "WB API discount calculation completed",
    )
    WB_API_DISCOUNT_RESULT_DOWNLOADED = (
        "wb_api_discount_result_downloaded",
        "WB API discount result downloaded",
    )
    WB_API_DISCOUNT_UPLOAD_CONFIRMED = (
        "wb_api_discount_upload_confirmed",
        "WB API discount upload confirmed",
    )
    WB_API_DISCOUNT_UPLOAD_STARTED = (
        "wb_api_discount_upload_started",
        "WB API discount upload started",
    )
    WB_API_DISCOUNT_UPLOAD_COMPLETED = (
        "wb_api_discount_upload_completed",
        "WB API discount upload completed",
    )
    WB_API_DISCOUNT_UPLOAD_FAILED = (
        "wb_api_discount_upload_failed",
        "WB API discount upload failed",
    )


class AuditSourceContext(models.TextChoices):
    UI = "ui", "UI"
    API = "api", "API"
    SERVICE = "service", "Service"
    AUTOMATIC = "automatic", "Automatic"
    MIGRATION = "migration", "Migration"


class AuditVisibleScope(models.TextChoices):
    LIMITED = "limited", "Limited"
    FULL = "full", "Full"


class ImmutableAuditQuerySet(models.QuerySet):
    def update(self, **kwargs):
        if self.exists():
            raise ValidationError("Audit records are immutable.")
        return super().update(**kwargs)

    def delete(self):
        if not _is_audit_retention_cleanup_allowed():
            raise ProtectedError(
                "Audit records are deleted only by regulated retention cleanup.",
                list(self[:1]),
            )
        count = 0
        with transaction.atomic():
            for obj in self:
                obj.delete()
                count += 1
        return count, {self.model._meta.label: count}


AuditRecordManager = models.Manager.from_queryset(ImmutableAuditQuerySet)


class AuditRecord(models.Model):
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    retention_until = models.DateTimeField(db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_records",
    )
    action_code = models.CharField(
        max_length=128,
        choices=AuditActionCode.choices,
        db_index=True,
    )
    entity_type = models.CharField(max_length=128)
    entity_id = models.CharField(max_length=128, blank=True)
    store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_records",
    )
    operation = models.ForeignKey(
        "operations.Operation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_records",
    )
    safe_message = models.TextField(blank=True)
    before_snapshot = models.JSONField(default=dict, blank=True)
    after_snapshot = models.JSONField(default=dict, blank=True)
    source_context = models.CharField(
        max_length=32,
        choices=AuditSourceContext.choices,
        default=AuditSourceContext.SERVICE,
    )
    visible_scope = models.CharField(
        max_length=16,
        choices=AuditVisibleScope.choices,
        default=AuditVisibleScope.LIMITED,
    )

    objects = AuditRecordManager()

    class Meta:
        ordering = ["-occurred_at", "-id"]
        indexes = [
            models.Index(fields=["action_code", "occurred_at"]),
            models.Index(fields=["store", "occurred_at"]),
            models.Index(fields=["operation", "occurred_at"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.occurred_at:%Y-%m-%d %H:%M:%S} {self.action_code}"

    def _default_retention_until(self):
        return self.occurred_at + timedelta(days=AUDIT_RETENTION_DAYS)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Audit records are immutable.")
        if not self.retention_until:
            self.retention_until = self._default_retention_until()
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if not _is_audit_retention_cleanup_allowed():
            raise ProtectedError(
                "Audit records are deleted only by regulated retention cleanup.",
                [self],
            )
        return super().delete(using=using, keep_parents=keep_parents)
