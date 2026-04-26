"""Store-scoped parameter values needed by stage 1 Excel scenarios."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


WB_PARAMETER_CODES = {
    "wb_threshold_percent",
    "wb_fallback_no_promo_percent",
    "wb_fallback_over_threshold_percent",
}


class ParameterDefinition(models.Model):
    class ValueType(models.TextChoices):
        INTEGER = "integer", "Integer"
        DECIMAL = "decimal", "Decimal"
        STRING = "string", "String"

    code = models.CharField(max_length=128, primary_key=True)
    module = models.CharField(max_length=64)
    value_type = models.CharField(max_length=32, choices=ValueType.choices)
    is_user_managed = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def clean(self):
        super().clean()
        if self.code.startswith("wb_") and self.code not in WB_PARAMETER_CODES:
            raise ValidationError("Unsupported WB parameter code.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class SystemParameterValue(models.Model):
    parameter_code = models.CharField(max_length=128)
    value = models.JSONField()
    active_from = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["parameter_code", "-active_from", "-id"]
        indexes = [
            models.Index(fields=["parameter_code", "active_from"]),
        ]

    def clean(self):
        super().clean()
        if self.parameter_code.startswith("wb_") and self.parameter_code not in WB_PARAMETER_CODES:
            raise ValidationError("Unsupported WB parameter code.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class StoreParameterValue(models.Model):
    store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        related_name="parameter_values",
    )
    parameter_code = models.CharField(max_length=128)
    value = models.JSONField(null=True, blank=True)
    active_from = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="changed_store_parameters",
    )

    class Meta:
        ordering = ["store_id", "parameter_code", "-active_from", "-id"]
        indexes = [
            models.Index(fields=["store", "parameter_code", "active_from"]),
            models.Index(fields=["store", "parameter_code", "is_active"]),
        ]

    def clean(self):
        super().clean()
        if self.parameter_code.startswith("wb_") and self.parameter_code not in WB_PARAMETER_CODES:
            raise ValidationError("Unsupported WB parameter code.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class StoreParameterChangeHistory(models.Model):
    store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        related_name="parameter_history",
    )
    parameter_code = models.CharField(max_length=128)
    changed_at = models.DateTimeField(default=timezone.now, db_index=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="store_parameter_history_changes",
    )
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    old_source = models.CharField(max_length=16, blank=True)
    new_source = models.CharField(max_length=16, blank=True)
    audit_record = models.ForeignKey(
        "audit.AuditRecord",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="parameter_history_records",
    )

    class Meta:
        ordering = ["-changed_at", "-id"]
        indexes = [
            models.Index(fields=["store", "parameter_code", "changed_at"]),
        ]

    def clean(self):
        super().clean()
        if self.parameter_code.startswith("wb_") and self.parameter_code not in WB_PARAMETER_CODES:
            raise ValidationError("Unsupported WB parameter code.")

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Parameter history is immutable.")
        self.full_clean()
        return super().save(*args, **kwargs)
