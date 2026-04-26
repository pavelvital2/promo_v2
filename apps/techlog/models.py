"""Technical log records and system notifications."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone


TECHLOG_RETENTION_DAYS = 90
_techlog_retention_cleanup_allowed = ContextVar(
    "techlog_retention_cleanup_allowed",
    default=False,
)


@contextmanager
def allow_techlog_retention_cleanup_delete():
    token = _techlog_retention_cleanup_allowed.set(True)
    try:
        yield
    finally:
        _techlog_retention_cleanup_allowed.reset(token)


def _is_techlog_retention_cleanup_allowed() -> bool:
    return _techlog_retention_cleanup_allowed.get()


class TechLogSeverity(models.TextChoices):
    INFO = "info", "Info"
    WARNING = "warning", "Warning"
    ERROR = "error", "Error"
    CRITICAL = "critical", "Critical"


class TechLogEventType(models.TextChoices):
    EXCEL_READ_ERROR = "excel.read_error", "Excel read error"
    EXCEL_TEMPLATE_MISSING_SHEET = (
        "excel.template_missing_sheet",
        "Excel template missing sheet",
    )
    EXCEL_TEMPLATE_MISSING_COLUMNS = (
        "excel.template_missing_columns",
        "Excel template missing columns",
    )
    EXCEL_SAFE_WRITE_ERROR = "excel.safe_write_error", "Excel safe write error"
    FILE_STORAGE_SAVE_ERROR = "file.storage_save_error", "File storage save error"
    FILE_STORAGE_READ_ERROR = "file.storage_read_error", "File storage read error"
    OPERATION_EXECUTION_FAILED = (
        "operation.execution_failed",
        "Operation execution failed",
    )
    OPERATION_INTERRUPTED_MARKED = (
        "operation.interrupted_marked",
        "Operation interrupted marked",
    )
    DATABASE_ERROR = "database.error", "Database error"
    APPLICATION_EXCEPTION = "application.exception", "Application exception"
    CONNECTION_FUTURE_API_ERROR = (
        "connection.future_api_error",
        "Future API connection error",
    )
    NOTIFICATION_CRITICAL_CREATED = (
        "notification.critical_created",
        "Critical notification created",
    )
    BACKUP_RESTORE_CHECK_FAILED = (
        "backup.restore_check_failed",
        "Backup restore check failed",
    )
    WB_API_AUTH_FAILED = "wb_api_auth_failed", "WB API auth failed"
    WB_API_RATE_LIMITED = "wb_api_rate_limited", "WB API rate limited"
    WB_API_TIMEOUT = "wb_api_timeout", "WB API timeout"
    WB_API_RESPONSE_INVALID = "wb_api_response_invalid", "WB API response invalid"
    WB_API_PRICES_DOWNLOAD_FAILED = (
        "wb_api_prices_download_failed",
        "WB API prices download failed",
    )
    WB_API_PROMOTIONS_DOWNLOAD_FAILED = (
        "wb_api_promotions_download_failed",
        "WB API promotions download failed",
    )
    WB_API_UPLOAD_FAILED = "wb_api_upload_failed", "WB API upload failed"
    WB_API_UPLOAD_STATUS_POLL_FAILED = (
        "wb_api_upload_status_poll_failed",
        "WB API upload status poll failed",
    )
    WB_API_UPLOAD_PARTIAL_ERRORS = (
        "wb_api_upload_partial_errors",
        "WB API upload partial errors",
    )
    WB_API_QUARANTINE_DETECTED = (
        "wb_api_quarantine_detected",
        "WB API quarantine detected",
    )
    WB_API_SECRET_REDACTION_VIOLATION = (
        "wb_api_secret_redaction_violation",
        "WB API secret redaction violation",
    )


TECHLOG_EVENT_SEVERITY_BASELINE = {
    TechLogEventType.EXCEL_READ_ERROR: TechLogSeverity.ERROR,
    TechLogEventType.EXCEL_TEMPLATE_MISSING_SHEET: TechLogSeverity.ERROR,
    TechLogEventType.EXCEL_TEMPLATE_MISSING_COLUMNS: TechLogSeverity.ERROR,
    TechLogEventType.EXCEL_SAFE_WRITE_ERROR: TechLogSeverity.ERROR,
    TechLogEventType.FILE_STORAGE_SAVE_ERROR: TechLogSeverity.CRITICAL,
    TechLogEventType.FILE_STORAGE_READ_ERROR: TechLogSeverity.ERROR,
    TechLogEventType.OPERATION_EXECUTION_FAILED: TechLogSeverity.CRITICAL,
    TechLogEventType.OPERATION_INTERRUPTED_MARKED: TechLogSeverity.WARNING,
    TechLogEventType.DATABASE_ERROR: TechLogSeverity.CRITICAL,
    TechLogEventType.APPLICATION_EXCEPTION: TechLogSeverity.ERROR,
    TechLogEventType.CONNECTION_FUTURE_API_ERROR: TechLogSeverity.ERROR,
    TechLogEventType.NOTIFICATION_CRITICAL_CREATED: TechLogSeverity.WARNING,
    TechLogEventType.BACKUP_RESTORE_CHECK_FAILED: TechLogSeverity.CRITICAL,
    TechLogEventType.WB_API_AUTH_FAILED: TechLogSeverity.ERROR,
    TechLogEventType.WB_API_RATE_LIMITED: TechLogSeverity.WARNING,
    TechLogEventType.WB_API_TIMEOUT: TechLogSeverity.WARNING,
    TechLogEventType.WB_API_RESPONSE_INVALID: TechLogSeverity.ERROR,
    TechLogEventType.WB_API_PRICES_DOWNLOAD_FAILED: TechLogSeverity.ERROR,
    TechLogEventType.WB_API_PROMOTIONS_DOWNLOAD_FAILED: TechLogSeverity.ERROR,
    TechLogEventType.WB_API_UPLOAD_FAILED: TechLogSeverity.ERROR,
    TechLogEventType.WB_API_UPLOAD_STATUS_POLL_FAILED: TechLogSeverity.ERROR,
    TechLogEventType.WB_API_UPLOAD_PARTIAL_ERRORS: TechLogSeverity.WARNING,
    TechLogEventType.WB_API_QUARANTINE_DETECTED: TechLogSeverity.WARNING,
    TechLogEventType.WB_API_SECRET_REDACTION_VIOLATION: TechLogSeverity.CRITICAL,
}


class TechLogHandledStatus(models.TextChoices):
    RECORDED = "recorded", "Recorded"
    NOTIFICATION_CREATED = "notification_created", "Notification created"
    RESOLVED_BY_OPERATOR = "resolved_by_operator", "Resolved by operator"


class NotificationStatus(models.TextChoices):
    OPEN = "open", "Open"
    ACKNOWLEDGED = "acknowledged", "Acknowledged"
    RESOLVED = "resolved", "Resolved"
    ARCHIVED = "archived", "Archived"


class ImmutableTechLogQuerySet(models.QuerySet):
    def update(self, **kwargs):
        if self.exists():
            raise ValidationError("Techlog records are immutable.")
        return super().update(**kwargs)

    def delete(self):
        if not _is_techlog_retention_cleanup_allowed():
            raise ProtectedError(
                "Techlog records are deleted only by regulated retention cleanup.",
                list(self[:1]),
            )
        count = 0
        with transaction.atomic():
            for obj in self:
                obj.delete()
                count += 1
        return count, {self.model._meta.label: count}


TechLogRecordManager = models.Manager.from_queryset(ImmutableTechLogQuerySet)


class TechLogRecord(models.Model):
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    retention_until = models.DateTimeField(db_index=True)
    severity = models.CharField(
        max_length=16,
        choices=TechLogSeverity.choices,
        db_index=True,
    )
    event_type = models.CharField(
        max_length=128,
        choices=TechLogEventType.choices,
        db_index=True,
    )
    operation = models.ForeignKey(
        "operations.Operation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="techlog_records",
    )
    store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="techlog_records",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="techlog_records",
    )
    entity_type = models.CharField(max_length=128, blank=True)
    entity_id = models.CharField(max_length=128, blank=True)
    safe_message = models.TextField(blank=True)
    sensitive_details_ref = models.TextField(blank=True)
    source_component = models.CharField(max_length=128)
    handled_status = models.CharField(
        max_length=64,
        choices=TechLogHandledStatus.choices,
        default=TechLogHandledStatus.RECORDED,
        db_index=True,
    )

    objects = TechLogRecordManager()

    class Meta:
        ordering = ["-occurred_at", "-id"]
        indexes = [
            models.Index(fields=["event_type", "occurred_at"]),
            models.Index(fields=["severity", "occurred_at"]),
            models.Index(fields=["store", "occurred_at"]),
            models.Index(fields=["operation", "occurred_at"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.occurred_at:%Y-%m-%d %H:%M:%S} {self.severity} {self.event_type}"

    def _default_retention_until(self):
        return self.occurred_at + timedelta(days=TECHLOG_RETENTION_DAYS)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Techlog records are immutable.")
        if not self.retention_until:
            self.retention_until = self._default_retention_until()
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if not _is_techlog_retention_cleanup_allowed():
            raise ProtectedError(
                "Techlog records are deleted only by regulated retention cleanup.",
                [self],
            )
        return super().delete(using=using, keep_parents=keep_parents)


class SystemNotification(models.Model):
    severity = models.CharField(
        max_length=16,
        choices=TechLogSeverity.choices,
        default=TechLogSeverity.CRITICAL,
        db_index=True,
    )
    topic = models.CharField(max_length=128)
    message = models.TextField()
    status = models.CharField(
        max_length=32,
        choices=NotificationStatus.choices,
        default=NotificationStatus.OPEN,
        db_index=True,
    )
    related_operation = models.ForeignKey(
        "operations.Operation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="system_notifications",
    )
    related_store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="system_notifications",
    )
    related_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="system_notifications",
    )
    related_techlog_record = models.OneToOneField(
        TechLogRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="system_notification",
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status", "severity", "created_at"]),
            models.Index(fields=["related_operation", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.severity} {self.topic}"

    def clean(self):
        super().clean()
        if self.related_operation_id and self.related_store_id:
            if self.related_operation.store_id != self.related_store_id:
                raise ValidationError("Notification store must match related operation.")

    def save(self, *args, **kwargs):
        if self.related_store is None and self.related_operation is not None:
            self.related_store = self.related_operation.store
        self.full_clean()
        return super().save(*args, **kwargs)
