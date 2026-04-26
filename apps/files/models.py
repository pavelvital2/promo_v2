"""Files/storage domain models for TASK-004."""

from __future__ import annotations

import re
from contextlib import contextmanager
from contextvars import ContextVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Max
from django.db.models.deletion import ProtectedError
from django.utils import timezone


_file_visible_id_service_update_allowed = ContextVar(
    "file_visible_id_service_update_allowed",
    default=False,
)
_file_pre_operation_metadata_delete_allowed = ContextVar(
    "file_pre_operation_metadata_delete_allowed",
    default=False,
)


@contextmanager
def allow_file_visible_id_service_update():
    token = _file_visible_id_service_update_allowed.set(True)
    try:
        yield
    finally:
        _file_visible_id_service_update_allowed.reset(token)


def _is_file_visible_id_service_update_allowed() -> bool:
    return _file_visible_id_service_update_allowed.get()


@contextmanager
def allow_file_pre_operation_metadata_delete():
    token = _file_pre_operation_metadata_delete_allowed.set(True)
    try:
        yield
    finally:
        _file_pre_operation_metadata_delete_allowed.reset(token)


def _is_file_pre_operation_metadata_delete_allowed() -> bool:
    return _file_pre_operation_metadata_delete_allowed.get()


class GuardedDeleteQuerySet(models.QuerySet):
    def delete(self):
        count = 0
        with transaction.atomic():
            for obj in self:
                obj.delete()
                count += 1
        return count, {self.model._meta.label: count}


GuardedDeleteManager = models.Manager.from_queryset(GuardedDeleteQuerySet)


class FileObjectQuerySet(GuardedDeleteQuerySet):
    def update(self, **kwargs):
        if "visible_id" in kwargs and not _is_file_visible_id_service_update_allowed():
            raise ValidationError("FileObject.visible_id is immutable after creation.")
        return super().update(**kwargs)


FileObjectManager = models.Manager.from_queryset(FileObjectQuerySet)


class FileObject(models.Model):
    class Kind(models.TextChoices):
        INPUT = "input", "Input"
        OUTPUT = "output", "Output"
        DETAIL_REPORT = "detail_report", "Detail report"

    class Scenario(models.TextChoices):
        WB_DISCOUNTS_EXCEL = "wb_discounts_excel", "WB discounts Excel"
        OZON_DISCOUNTS_EXCEL = "ozon_discounts_excel", "Ozon discounts Excel"
        WB_DISCOUNTS_API_PRICE_EXPORT = (
            "wb_discounts_api_price_export",
            "WB discounts API price export",
        )
        WB_DISCOUNTS_API_PROMOTION_EXPORT = (
            "wb_discounts_api_promotion_export",
            "WB discounts API promotion export",
        )
        WB_DISCOUNTS_API_RESULT_EXCEL = (
            "wb_discounts_api_result_excel",
            "WB discounts API result Excel",
        )
        WB_DISCOUNTS_API_DETAIL_REPORT = (
            "wb_discounts_api_detail_report",
            "WB discounts API detail report",
        )
        WB_DISCOUNTS_API_UPLOAD_REPORT = (
            "wb_discounts_api_upload_report",
            "WB discounts API upload report",
        )

    class Marketplace(models.TextChoices):
        WB = "wb", "WB"
        OZON = "ozon", "Ozon"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    visible_id = models.CharField(max_length=32, unique=True, null=True, blank=True)
    store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        related_name="files",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    scenario = models.CharField(max_length=64, choices=Scenario.choices)
    marketplace = models.CharField(max_length=16, choices=Marketplace.choices)
    module = models.CharField(max_length=64, default="discounts_excel")
    logical_name = models.CharField(max_length=255, blank=True)
    original_name = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_file_objects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = FileObjectManager()

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(scenario="wb_discounts_excel", marketplace="wb")
                    | models.Q(scenario__startswith="wb_discounts_api_", marketplace="wb")
                    | models.Q(scenario="ozon_discounts_excel", marketplace="ozon")
                ),
                name="file_object_scenario_marketplace_match",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.visible_id or 'FILE-new'} {self.original_name}"

    def clean(self):
        super().clean()
        expected_marketplace = {
            self.Scenario.WB_DISCOUNTS_EXCEL: self.Marketplace.WB,
            self.Scenario.WB_DISCOUNTS_API_PRICE_EXPORT: self.Marketplace.WB,
            self.Scenario.WB_DISCOUNTS_API_PROMOTION_EXPORT: self.Marketplace.WB,
            self.Scenario.WB_DISCOUNTS_API_RESULT_EXCEL: self.Marketplace.WB,
            self.Scenario.WB_DISCOUNTS_API_DETAIL_REPORT: self.Marketplace.WB,
            self.Scenario.WB_DISCOUNTS_API_UPLOAD_REPORT: self.Marketplace.WB,
            self.Scenario.OZON_DISCOUNTS_EXCEL: self.Marketplace.OZON,
        }.get(self.scenario)
        if expected_marketplace and self.marketplace != expected_marketplace:
            raise ValidationError("File scenario and marketplace must match.")

    def _next_visible_id(self) -> str:
        year = timezone.localtime(self.created_at or timezone.now()).year
        prefix = f"FILE-{year}-"
        max_visible_id = (
            type(self)
            .objects.filter(visible_id__startswith=prefix)
            .aggregate(max_visible_id=Max("visible_id"))["max_visible_id"]
        )
        next_no = 1
        if max_visible_id:
            match = re.match(rf"^{re.escape(prefix)}(\d{{6}})$", max_visible_id)
            if match:
                next_no = int(match.group(1)) + 1
        return f"{prefix}{next_no:06d}"

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        visible_id_may_be_written = update_fields is None or "visible_id" in update_fields
        if (
            self.pk
            and not self._state.adding
            and visible_id_may_be_written
            and not _is_file_visible_id_service_update_allowed()
        ):
            current_visible_id = (
                type(self)
                .objects.filter(pk=self.pk)
                .values_list("visible_id", flat=True)
                .first()
            )
            if current_visible_id != self.visible_id:
                raise ValidationError("FileObject.visible_id is immutable after creation.")

        self.full_clean()
        super().save(*args, **kwargs)
        if not self.visible_id:
            self.visible_id = self._next_visible_id()
            with allow_file_visible_id_service_update():
                super().save(update_fields=["visible_id"])

    def has_operation_links(self) -> bool:
        if not self.pk:
            return False
        return self.versions.filter(
            models.Q(operation_ref__gt="") | models.Q(run_ref__gt=""),
        ).exists()

    def delete(self, using=None, keep_parents=False):
        if self.versions.exists() and not _is_file_pre_operation_metadata_delete_allowed():
            raise ProtectedError(
                "File metadata with versions is preserved; archive instead of delete.",
                [self],
            )
        return super().delete(using=using, keep_parents=keep_parents)


class FileVersion(models.Model):
    class PhysicalStatus(models.TextChoices):
        AVAILABLE = "available", "Available"
        RETENTION_DELETED = "retention_deleted", "Deleted by retention"
        MISSING = "missing", "Missing from storage"

    file = models.ForeignKey(FileObject, on_delete=models.PROTECT, related_name="versions")
    version_no = models.PositiveIntegerField()
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, blank=True)
    storage_backend = models.CharField(max_length=64, default="default")
    storage_path = models.CharField(max_length=1024)
    size = models.PositiveBigIntegerField(default=0)
    checksum_sha256 = models.CharField(max_length=64)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_file_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    retention_until = models.DateTimeField()
    physical_status = models.CharField(
        max_length=32,
        choices=PhysicalStatus.choices,
        default=PhysicalStatus.AVAILABLE,
    )
    physical_deleted_at = models.DateTimeField(null=True, blank=True)
    operation_ref = models.CharField(max_length=64, blank=True)
    run_ref = models.CharField(max_length=64, blank=True)

    objects = GuardedDeleteManager()

    class Meta:
        ordering = ["file_id", "-version_no"]
        constraints = [
            models.UniqueConstraint(fields=["file", "version_no"], name="uniq_file_version_no"),
        ]

    def __str__(self) -> str:
        return f"{self.file.visible_id or self.file_id} v{self.version_no}"

    @property
    def is_retention_expired(self) -> bool:
        return self.retention_until <= timezone.now()

    @property
    def is_physically_available(self) -> bool:
        return (
            self.physical_status == self.PhysicalStatus.AVAILABLE
            and not self.is_retention_expired
        )

    def delete(self, using=None, keep_parents=False):
        if not _is_file_pre_operation_metadata_delete_allowed():
            raise ProtectedError("File version metadata is historical and is not deleted.", [self])
        return super().delete(using=using, keep_parents=keep_parents)
