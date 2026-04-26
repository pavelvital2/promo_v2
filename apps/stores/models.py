"""Stores, cabinets and connection blocks for TASK-003."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.deletion import ProtectedError


SENSITIVE_METADATA_KEY_MARKERS = ("secret", "token", "password", "api_key", "key")
_store_visible_id_service_update_allowed = ContextVar(
    "store_visible_id_service_update_allowed",
    default=False,
)


@contextmanager
def allow_store_visible_id_service_update():
    """Explicit service path for migrations/backfills that must repair visible IDs."""
    token = _store_visible_id_service_update_allowed.set(True)
    try:
        yield
    finally:
        _store_visible_id_service_update_allowed.reset(token)


def _is_store_visible_id_service_update_allowed() -> bool:
    return _store_visible_id_service_update_allowed.get()


def is_sensitive_metadata_key(key) -> bool:
    key_text = str(key).lower()
    compact_key = "".join(character for character in key_text if character.isalnum())
    return any(
        marker in key_text
        or "".join(character for character in marker if character.isalnum()) in compact_key
        for marker in SENSITIVE_METADATA_KEY_MARKERS
    )


def contains_sensitive_metadata_key(value) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if is_sensitive_metadata_key(key) or contains_sensitive_metadata_key(child):
                return True
        return False
    if isinstance(value, list):
        return any(contains_sensitive_metadata_key(child) for child in value)
    return False


class GuardedDeleteQuerySet(models.QuerySet):
    def delete(self):
        count = 0
        for obj in self:
            obj.delete()
            count += 1
        return count, {self.model._meta.label: count}


GuardedDeleteManager = models.Manager.from_queryset(GuardedDeleteQuerySet)


class StoreAccountQuerySet(GuardedDeleteQuerySet):
    def update(self, **kwargs):
        if (
            "visible_id" in kwargs
            and not _is_store_visible_id_service_update_allowed()
        ):
            raise ValidationError("StoreAccount.visible_id is immutable after creation.")
        return super().update(**kwargs)


StoreAccountManager = models.Manager.from_queryset(StoreAccountQuerySet)


class BusinessGroup(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        ARCHIVED = "archived", "Archived"

    visible_id = models.CharField(max_length=32, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = GuardedDeleteManager()

    class Meta:
        ordering = ["name", "id"]

    def __str__(self) -> str:
        return self.name

    def delete(self, using=None, keep_parents=False):
        if self.stores.exists():
            raise ProtectedError("Business groups with stores are archived, not deleted.", [self])
        return super().delete(using=using, keep_parents=keep_parents)


class StoreAccount(models.Model):
    class Marketplace(models.TextChoices):
        WB = "wb", "WB"
        OZON = "ozon", "Ozon"

    class CabinetType(models.TextChoices):
        STORE = "store", "Store"
        CABINET = "cabinet", "Cabinet"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        ARCHIVED = "archived", "Archived"

    visible_id = models.CharField(max_length=32, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    group = models.ForeignKey(
        BusinessGroup,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stores",
    )
    marketplace = models.CharField(max_length=16, choices=Marketplace.choices)
    cabinet_type = models.CharField(
        max_length=32,
        choices=CabinetType.choices,
        default=CabinetType.STORE,
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = StoreAccountManager()

    class Meta:
        ordering = ["name", "id"]

    def __str__(self) -> str:
        return f"{self.visible_id or 'STORE-new'} {self.name}"

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        visible_id_may_be_written = update_fields is None or "visible_id" in update_fields
        if (
            self.pk
            and not self._state.adding
            and visible_id_may_be_written
            and not _is_store_visible_id_service_update_allowed()
        ):
            current_visible_id = (
                type(self)
                .objects.filter(pk=self.pk)
                .values_list("visible_id", flat=True)
                .first()
            )
            if current_visible_id != self.visible_id:
                raise ValidationError("StoreAccount.visible_id is immutable after creation.")

        super().save(*args, **kwargs)
        if not self.visible_id:
            self.visible_id = f"STORE-{self.pk:06d}"
            with allow_store_visible_id_service_update():
                super().save(update_fields=["visible_id"])

    def has_physical_delete_usage(self) -> bool:
        if not self.pk:
            return False
        return any(
            (
                self.history.exists(),
                self.connection_blocks.exists(),
                self.user_access.exists(),
                self.permission_overrides.exists(),
                self.section_overrides.exists(),
            ),
        )

    def can_be_physically_deleted(self) -> bool:
        return not self.has_physical_delete_usage()

    def delete(self, using=None, keep_parents=False):
        if self.has_physical_delete_usage():
            raise ProtectedError(
                "Used stores/cabinets are deactivated or archived instead of physically deleted.",
                [self],
            )
        return super().delete(using=using, keep_parents=keep_parents)


class ConnectionBlock(models.Model):
    class Status(models.TextChoices):
        PREPARED = "prepared", "Prepared for stage 2"
        INACTIVE = "inactive", "Inactive"
        ARCHIVED = "archived", "Archived"

    store = models.ForeignKey(
        StoreAccount,
        on_delete=models.PROTECT,
        related_name="connection_blocks",
    )
    module = models.CharField(max_length=100)
    connection_type = models.CharField(max_length=100)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PREPARED,
    )
    protected_secret_ref = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_stage1_used = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = GuardedDeleteManager()

    class Meta:
        ordering = ["store__name", "module", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["store", "module", "connection_type"],
                name="uniq_store_connection_block",
            ),
            models.CheckConstraint(
                check=models.Q(is_stage1_used=False),
                name="connection_block_not_used_in_stage_1",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.store.visible_id} {self.module} {self.connection_type}"

    def clean(self):
        super().clean()
        if self.is_stage1_used:
            raise ValidationError("Connection blocks are stage 2 preparation and are not used in stage 1.")
        if contains_sensitive_metadata_key(self.metadata):
            raise ValidationError("Connection metadata must not contain secret-like values.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def has_physical_delete_usage(self) -> bool:
        if not self.pk:
            return False
        return bool(
            self.protected_secret_ref
            or self.store.history.filter(field_code__startswith="connection.").exists()
        )

    def delete(self, using=None, keep_parents=False):
        if self.has_physical_delete_usage():
            raise ProtectedError(
                "Used connection blocks are deactivated or archived, not deleted.",
                [self],
            )
        return super().delete(using=using, keep_parents=keep_parents)


class StoreAccountChangeHistory(models.Model):
    store = models.ForeignKey(
        StoreAccount,
        on_delete=models.PROTECT,
        related_name="history",
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="store_changes_made",
    )
    field_code = models.CharField(max_length=128)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    source = models.CharField(max_length=64, default="system")

    objects = GuardedDeleteManager()

    class Meta:
        ordering = ["-changed_at", "-id"]

    def __str__(self) -> str:
        return f"{self.store.visible_id} {self.field_code}"

    def delete(self, using=None, keep_parents=False):
        raise ProtectedError("Store/cabinet change history is immutable.", [self])
