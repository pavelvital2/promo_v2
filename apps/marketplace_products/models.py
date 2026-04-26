"""Marketplace product list/card models for stage 1 UI."""

from __future__ import annotations

from django.db import models


class MarketplaceProduct(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        ARCHIVED = "archived", "Archived"

    marketplace = models.CharField(max_length=16, db_index=True)
    store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        related_name="products",
    )
    external_ids = models.JSONField(default=dict, blank=True)
    title = models.CharField(max_length=255, blank=True)
    sku = models.CharField(max_length=255, blank=True)
    barcode = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    last_values = models.JSONField(default=dict, blank=True)
    first_detected_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["marketplace", "store__name", "sku", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["marketplace", "store", "sku"],
                name="uniq_marketplace_product_store_sku",
            ),
        ]
        indexes = [
            models.Index(fields=["marketplace", "store", "status"]),
            models.Index(fields=["last_seen_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.marketplace}:{self.store_id}:{self.sku or self.pk}"


class MarketplaceProductHistory(models.Model):
    class ChangeType(models.TextChoices):
        DETECTED = "detected", "Detected"
        UPDATED = "updated", "Updated"

    product = models.ForeignKey(
        MarketplaceProduct,
        on_delete=models.PROTECT,
        related_name="history",
    )
    detected_at = models.DateTimeField(db_index=True)
    operation = models.ForeignKey(
        "operations.Operation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="product_history",
    )
    file_version = models.ForeignKey(
        "files.FileVersion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="product_history",
    )
    change_type = models.CharField(max_length=32, choices=ChangeType.choices)
    changed_fields = models.JSONField(default=list, blank=True)
    previous_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-detected_at", "-id"]
        indexes = [
            models.Index(fields=["product", "detected_at"]),
            models.Index(fields=["operation", "detected_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.product_id} {self.change_type} {self.detected_at:%Y-%m-%d %H:%M:%S}"
