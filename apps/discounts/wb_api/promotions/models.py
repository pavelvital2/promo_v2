"""Dedicated persistence for TASK-013 WB API promotion downloads."""

from __future__ import annotations

from django.db import models


class WBPromotion(models.Model):
    store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        related_name="wb_promotions",
    )
    wb_promotion_id = models.PositiveBigIntegerField()
    name = models.CharField(max_length=255, blank=True)
    type = models.CharField(max_length=64, blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_current_at_fetch = models.BooleanField(default=False)
    last_seen_at = models.DateTimeField()
    snapshot_ref = models.ForeignKey(
        "promotions.WBPromotionSnapshot",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="promotions",
    )

    class Meta:
        ordering = ["-last_seen_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["store", "wb_promotion_id"],
                name="uniq_wb_promotion_store_api_id",
            ),
        ]
        indexes = [
            models.Index(fields=["store", "wb_promotion_id"]),
            models.Index(fields=["store", "is_current_at_fetch"]),
            models.Index(fields=["start_datetime", "end_datetime"]),
        ]

    def __str__(self) -> str:
        return f"WB promotion {self.wb_promotion_id}"


class WBPromotionSnapshot(models.Model):
    operation = models.OneToOneField(
        "operations.Operation",
        on_delete=models.PROTECT,
        related_name="wb_promotion_snapshot",
    )
    store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        related_name="wb_promotion_snapshots",
    )
    fetched_at = models.DateTimeField()
    api_window_start = models.DateTimeField()
    api_window_end = models.DateTimeField()
    current_filter_timestamp = models.DateTimeField()
    raw_response_safe_snapshot = models.JSONField(default=dict, blank=True)
    promotions_count = models.PositiveIntegerField(default=0)
    current_promotions_count = models.PositiveIntegerField(default=0)
    regular_current_promotions_count = models.PositiveIntegerField(default=0)
    auto_current_promotions_count = models.PositiveIntegerField(default=0)
    promotion_products_count = models.PositiveIntegerField(default=0)
    invalid_product_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fetched_at", "-id"]
        indexes = [
            models.Index(fields=["store", "fetched_at"]),
            models.Index(fields=["operation"]),
        ]

    def __str__(self) -> str:
        return f"WB promotion snapshot {self.operation_id}"


class WBPromotionProduct(models.Model):
    promotion = models.ForeignKey(
        WBPromotion,
        on_delete=models.PROTECT,
        related_name="products",
    )
    nmID = models.CharField(max_length=64)
    inAction = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    currencyCode = models.CharField(max_length=16, blank=True)
    planPrice = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    discount = models.JSONField(null=True, blank=True)
    planDiscount = models.JSONField(null=True, blank=True)
    source_snapshot = models.ForeignKey(
        WBPromotionSnapshot,
        on_delete=models.PROTECT,
        related_name="products",
    )
    row_status = models.CharField(max_length=32)
    reason_code = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["promotion_id", "nmID", "inAction", "id"]
        indexes = [
            models.Index(fields=["promotion", "nmID"]),
            models.Index(fields=["source_snapshot", "row_status"]),
            models.Index(fields=["reason_code"]),
        ]

    def __str__(self) -> str:
        return f"WB promotion product {self.promotion_id}/{self.nmID}"


class WBPromotionExportFile(models.Model):
    promotion = models.ForeignKey(
        WBPromotion,
        on_delete=models.PROTECT,
        related_name="export_files",
    )
    operation = models.ForeignKey(
        "operations.Operation",
        on_delete=models.PROTECT,
        related_name="wb_promotion_export_files",
    )
    file_version = models.OneToOneField(
        "files.FileVersion",
        on_delete=models.PROTECT,
        related_name="wb_promotion_export_file",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["promotion", "operation", "file_version"],
                name="uniq_wb_promotion_export_file_link",
            ),
        ]
        indexes = [
            models.Index(fields=["promotion", "operation"]),
        ]

    def __str__(self) -> str:
        return f"WB promotion export {self.promotion_id}/{self.file_version_id}"
