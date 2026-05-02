"""Product Core and Marketplace Listing foundation models for Stage 3.0."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.discounts.wb_api.redaction import assert_no_secret_like_values


class ProductStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class Marketplace(models.TextChoices):
    WB = "wb", "WB"
    OZON = "ozon", "Ozon"


class ProductIdentifierSource(models.TextChoices):
    MANUAL = "manual", "Manual"
    MIGRATION = "migration", "Migration"
    IMPORT = "import", "Import"
    API = "api", "API"
    FUTURE = "future", "Future"


class ListingSource(models.TextChoices):
    EXCEL = "excel", "Excel"
    WB_API_PRICES = "wb_api_prices", "WB API prices"
    OZON_API_ACTIONS = "ozon_api_actions", "Ozon API actions"
    MANUAL_IMPORT = "manual_import", "Manual import"
    MIGRATION = "migration", "Migration"
    FUTURE = "future", "Future"


class SyncLaunchMethod(models.TextChoices):
    MANUAL = "manual", "Manual"
    AUTOMATIC = "automatic", "Automatic"
    SERVICE = "service", "Service"
    API = "api", "API"


class InternalProduct(models.Model):
    class ProductType(models.TextChoices):
        FINISHED_GOOD = "finished_good", "Finished good"
        MATERIAL = "material", "Material"
        PACKAGING = "packaging", "Packaging"
        SEMI_FINISHED = "semi_finished", "Semi-finished"
        KIT = "kit", "Kit"
        SERVICE_OR_DESIGN_ARTIFACT = (
            "service_or_design_artifact",
            "Service or design artifact",
        )
        UNKNOWN = "unknown", "Unknown"

    internal_code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    product_type = models.CharField(
        max_length=64,
        choices=ProductType.choices,
        default=ProductType.UNKNOWN,
    )
    category = models.ForeignKey(
        "ProductCategory",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="products",
    )
    status = models.CharField(
        max_length=32,
        choices=ProductStatus.choices,
        default=ProductStatus.ACTIVE,
    )
    attributes = models.JSONField(default=dict, blank=True)
    comments = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="created_internal_products",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="updated_internal_products",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["internal_code", "id"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["product_type", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.internal_code} {self.name}"


class ProductCategory(models.Model):
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=32,
        choices=ProductStatus.choices,
        default=ProductStatus.ACTIVE,
    )
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name", "id"]
        indexes = [
            models.Index(fields=["parent", "status", "sort_order"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "name"],
                name="uniq_product_category_parent_name",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self):
        super().clean()
        if self.pk and self.parent_id == self.pk:
            raise ValidationError("Product category cannot be its own parent.")


class ProductVariant(models.Model):
    product = models.ForeignKey(
        InternalProduct,
        on_delete=models.PROTECT,
        related_name="variants",
    )
    internal_sku = models.CharField(max_length=128, blank=True)
    name = models.CharField(max_length=255)
    barcode_internal = models.CharField(max_length=128, blank=True)
    variant_attributes = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=32,
        choices=ProductStatus.choices,
        default=ProductStatus.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["product__internal_code", "internal_sku", "name", "id"]
        indexes = [
            models.Index(fields=["product", "status"]),
            models.Index(fields=["barcode_internal"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["internal_sku"],
                condition=~models.Q(internal_sku=""),
                name="uniq_product_variant_internal_sku_when_present",
            ),
        ]

    def __str__(self) -> str:
        return self.internal_sku or f"{self.product_id}:{self.name}"


class ProductIdentifier(models.Model):
    class IdentifierType(models.TextChoices):
        INTERNAL_SKU = "internal_sku", "Internal SKU"
        INTERNAL_BARCODE = "internal_barcode", "Internal barcode"
        SUPPLIER_SKU = "supplier_sku", "Supplier SKU"
        WB_VENDOR_CODE = "wb_vendor_code", "WB vendor code"
        OZON_OFFER_ID = "ozon_offer_id", "Ozon offer ID"
        LEGACY_ARTICLE = "legacy_article", "Legacy article"

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="identifiers",
    )
    identifier_type = models.CharField(max_length=64, choices=IdentifierType.choices)
    value = models.CharField(max_length=255)
    source = models.CharField(
        max_length=32,
        choices=ProductIdentifierSource.choices,
        default=ProductIdentifierSource.MANUAL,
    )
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["variant_id", "identifier_type", "source", "value", "id"]
        indexes = [
            models.Index(fields=["identifier_type", "value"]),
            models.Index(fields=["source"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["variant", "identifier_type", "source", "value"],
                name="uniq_product_identifier_variant_type_source_value",
            ),
            models.UniqueConstraint(
                fields=["variant", "identifier_type", "source"],
                condition=models.Q(is_primary=True),
                name="uniq_primary_product_identifier_per_variant_type_source",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.identifier_type}:{self.value}"

    def clean(self):
        super().clean()
        self.value = self.value.strip()
        if not self.value:
            raise ValidationError("Product identifier value is required.")


class MarketplaceSyncRun(models.Model):
    class SyncType(models.TextChoices):
        LISTINGS = "listings", "Listings"
        PRICES = "prices", "Prices"
        STOCKS = "stocks", "Stocks"
        SALES = "sales", "Sales"
        ORDERS = "orders", "Orders"
        PROMOTIONS = "promotions", "Promotions"
        FULL_CATALOG_REFRESH = "full_catalog_refresh", "Full catalog refresh"
        MAPPING_IMPORT = "mapping_import", "Mapping import"

    class SyncStatus(models.TextChoices):
        CREATED = "created", "Created"
        RUNNING = "running", "Running"
        COMPLETED_SUCCESS = "completed_success", "Completed successfully"
        COMPLETED_WITH_WARNINGS = "completed_with_warnings", "Completed with warnings"
        COMPLETED_WITH_ERROR = "completed_with_error", "Completed with error"
        INTERRUPTED_FAILED = "interrupted_failed", "Interrupted / failed"

    operation = models.ForeignKey(
        "operations.Operation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="marketplace_sync_runs",
    )
    marketplace = models.CharField(max_length=16, choices=Marketplace.choices)
    store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        related_name="marketplace_sync_runs",
    )
    sync_type = models.CharField(max_length=64, choices=SyncType.choices)
    source = models.CharField(max_length=64, choices=ListingSource.choices)
    launch_method = models.CharField(
        max_length=16,
        choices=SyncLaunchMethod.choices,
        default=SyncLaunchMethod.MANUAL,
    )
    status = models.CharField(
        max_length=32,
        choices=SyncStatus.choices,
        default=SyncStatus.CREATED,
    )
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="requested_marketplace_sync_runs",
    )
    summary = models.JSONField(default=dict, blank=True)
    error_summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-started_at", "-id"]
        indexes = [
            models.Index(fields=["marketplace", "store", "sync_type", "status"]),
            models.Index(fields=["source", "started_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["marketplace", "store", "sync_type"],
                condition=models.Q(status__in=["created", "running"]),
                name="uniq_active_marketplace_sync_run",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.marketplace}:{self.store_id}:{self.sync_type}:{self.status}"

    def clean(self):
        super().clean()
        assert_no_secret_like_values(self.summary, field_name="sync run summary")
        assert_no_secret_like_values(self.error_summary, field_name="sync run error_summary")
        if self.store_id and self.marketplace != self.store.marketplace:
            raise ValidationError("Sync run marketplace must match store/cabinet marketplace.")
        if self.operation_id:
            if self.operation.store_id != self.store_id:
                raise ValidationError("Sync run operation store/cabinet must match sync run.")
            if self.operation.marketplace != self.marketplace:
                raise ValidationError("Sync run operation marketplace must match sync run.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class MarketplaceListing(models.Model):
    class ListingStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        NOT_SEEN_LAST_SYNC = "not_seen_last_sync", "Not seen in last sync"
        INACTIVE = "inactive", "Inactive"
        ARCHIVED = "archived", "Archived"
        SYNC_ERROR = "sync_error", "Sync error"

    class MappingStatus(models.TextChoices):
        UNMATCHED = "unmatched", "Unmatched"
        MATCHED = "matched", "Matched"
        NEEDS_REVIEW = "needs_review", "Needs review"
        CONFLICT = "conflict", "Conflict"
        ARCHIVED = "archived", "Archived"

    marketplace = models.CharField(max_length=16, choices=Marketplace.choices)
    store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        related_name="marketplace_listings",
    )
    internal_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="marketplace_listings",
    )
    external_primary_id = models.CharField(max_length=255)
    external_ids = models.JSONField(default=dict, blank=True)
    seller_article = models.CharField(max_length=255, blank=True)
    barcode = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255, blank=True)
    brand = models.CharField(max_length=255, blank=True)
    category_name = models.CharField(max_length=255, blank=True)
    category_external_id = models.CharField(max_length=255, blank=True)
    listing_status = models.CharField(
        max_length=32,
        choices=ListingStatus.choices,
        default=ListingStatus.ACTIVE,
    )
    mapping_status = models.CharField(
        max_length=32,
        choices=MappingStatus.choices,
        default=MappingStatus.UNMATCHED,
    )
    last_values = models.JSONField(default=dict, blank=True)
    first_seen_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_successful_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_run = models.ForeignKey(
        MarketplaceSyncRun,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="latest_listings",
    )
    last_source = models.CharField(max_length=64, choices=ListingSource.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["marketplace", "store__name", "external_primary_id", "id"]
        indexes = [
            models.Index(fields=["marketplace", "store", "listing_status"]),
            models.Index(fields=["marketplace", "store", "mapping_status"]),
            models.Index(fields=["seller_article"]),
            models.Index(fields=["barcode"]),
            models.Index(fields=["last_seen_at"]),
            models.Index(fields=["last_successful_sync_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["marketplace", "store", "external_primary_id"],
                name="uniq_marketplace_listing_store_external_primary",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(mapping_status="matched", internal_variant__isnull=False)
                    | ~models.Q(mapping_status="matched")
                ),
                name="matched_listing_requires_internal_variant",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.marketplace}:{self.store_id}:{self.external_primary_id}"

    def clean(self):
        super().clean()
        if self.store_id and self.marketplace != self.store.marketplace:
            raise ValidationError("Listing marketplace must match store/cabinet marketplace.")
        if self.mapping_status == self.MappingStatus.MATCHED and not self.internal_variant_id:
            raise ValidationError("Matched listing requires an internal variant.")
        if self.last_sync_run_id:
            if self.last_sync_run.store_id != self.store_id:
                raise ValidationError("Listing last sync run store/cabinet must match listing.")
            if self.last_sync_run.marketplace != self.marketplace:
                raise ValidationError("Listing last sync run marketplace must match listing.")


def _validate_snapshot_context(listing, sync_run, operation=None):
    if listing.store_id != sync_run.store_id:
        raise ValidationError("Snapshot listing store/cabinet must match sync run.")
    if listing.marketplace != sync_run.marketplace:
        raise ValidationError("Snapshot listing marketplace must match sync run.")
    if operation:
        if operation.store_id != listing.store_id:
            raise ValidationError("Snapshot operation store/cabinet must match listing.")
        if operation.marketplace != listing.marketplace:
            raise ValidationError("Snapshot operation marketplace must match listing.")


def _validate_raw_safe(raw_safe, field_name: str) -> None:
    assert_no_secret_like_values(raw_safe, field_name=field_name)


class RawSafeSnapshotMixin:
    raw_safe_field_name = "snapshot raw_safe"

    def clean(self):
        super().clean()
        _validate_raw_safe(self.raw_safe, self.raw_safe_field_name)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ListingHistory(models.Model):
    class ChangeType(models.TextChoices):
        APPEARED = "appeared", "Appeared"
        UPDATED = "updated", "Updated"
        STATUS_CHANGED = "status_changed", "Status changed"

    listing = models.ForeignKey(
        MarketplaceListing,
        on_delete=models.PROTECT,
        related_name="history",
    )
    change_type = models.CharField(max_length=32, choices=ChangeType.choices)
    changed_at = models.DateTimeField()
    changed_fields = models.JSONField(default=list, blank=True)
    previous_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    sync_run = models.ForeignKey(
        MarketplaceSyncRun,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="listing_history",
    )
    operation = models.ForeignKey(
        "operations.Operation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="listing_history",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="listing_history_changes",
    )
    source = models.CharField(max_length=64, choices=ListingSource.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at", "-id"]
        indexes = [
            models.Index(fields=["listing", "changed_at"]),
            models.Index(fields=["sync_run", "changed_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.listing_id} {self.change_type} {self.changed_at:%Y-%m-%d %H:%M:%S}"


class ProductMappingHistory(models.Model):
    class MappingAction(models.TextChoices):
        MAP = "map", "Map"
        UNMAP = "unmap", "Unmap"
        CONFLICT_MARKER = "conflict_marker", "Conflict marker"
        NEEDS_REVIEW_MARKER = "needs_review_marker", "Needs review marker"

    listing = models.ForeignKey(
        MarketplaceListing,
        on_delete=models.PROTECT,
        related_name="mapping_history",
    )
    action = models.CharField(max_length=32, choices=MappingAction.choices)
    mapping_status_after = models.CharField(
        max_length=32,
        choices=MarketplaceListing.MappingStatus.choices,
    )
    changed_at = models.DateTimeField()
    previous_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="previous_mapping_history",
    )
    new_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="new_mapping_history",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="product_mapping_history",
    )
    sync_run = models.ForeignKey(
        MarketplaceSyncRun,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="mapping_history",
    )
    operation = models.ForeignKey(
        "operations.Operation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="product_mapping_history",
    )
    source = models.CharField(max_length=64, choices=ListingSource.choices)
    source_context = models.JSONField(default=dict, blank=True)
    reason_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at", "-id"]
        indexes = [
            models.Index(fields=["listing", "changed_at"]),
            models.Index(fields=["action", "changed_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.listing_id} {self.action} {self.changed_at:%Y-%m-%d %H:%M:%S}"


class PriceSnapshot(RawSafeSnapshotMixin, models.Model):
    raw_safe_field_name = "price snapshot raw_safe"
    listing = models.ForeignKey(
        MarketplaceListing,
        on_delete=models.PROTECT,
        related_name="price_snapshots",
    )
    sync_run = models.ForeignKey(
        MarketplaceSyncRun,
        on_delete=models.PROTECT,
        related_name="price_snapshots",
    )
    operation = models.ForeignKey(
        "operations.Operation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="price_snapshots",
    )
    snapshot_at = models.DateTimeField()
    price = models.DecimalField(max_digits=14, decimal_places=2)
    price_with_discount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    currency = models.CharField(max_length=16)
    raw_safe = models.JSONField(default=dict, blank=True)
    source_endpoint = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-snapshot_at", "-id"]
        indexes = [
            models.Index(fields=["listing", "snapshot_at"]),
            models.Index(fields=["sync_run", "snapshot_at"]),
        ]

    def clean(self):
        super().clean()
        if self.listing_id and self.sync_run_id:
            _validate_snapshot_context(self.listing, self.sync_run, self.operation)


class StockSnapshot(RawSafeSnapshotMixin, models.Model):
    raw_safe_field_name = "stock snapshot raw_safe"
    listing = models.ForeignKey(
        MarketplaceListing,
        on_delete=models.PROTECT,
        related_name="stock_snapshots",
    )
    sync_run = models.ForeignKey(
        MarketplaceSyncRun,
        on_delete=models.PROTECT,
        related_name="stock_snapshots",
    )
    operation = models.ForeignKey(
        "operations.Operation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stock_snapshots",
    )
    snapshot_at = models.DateTimeField()
    total_stock = models.IntegerField(null=True, blank=True)
    stock_by_warehouse = models.JSONField(default=dict, blank=True)
    in_way_to_client = models.IntegerField(null=True, blank=True)
    in_way_from_client = models.IntegerField(null=True, blank=True)
    raw_safe = models.JSONField(default=dict, blank=True)
    source_endpoint = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-snapshot_at", "-id"]
        indexes = [
            models.Index(fields=["listing", "snapshot_at"]),
            models.Index(fields=["sync_run", "snapshot_at"]),
        ]

    def clean(self):
        super().clean()
        if self.listing_id and self.sync_run_id:
            _validate_snapshot_context(self.listing, self.sync_run, self.operation)


class SalesPeriodSnapshot(RawSafeSnapshotMixin, models.Model):
    raw_safe_field_name = "sales period snapshot raw_safe"
    listing = models.ForeignKey(
        MarketplaceListing,
        on_delete=models.PROTECT,
        related_name="sales_period_snapshots",
    )
    sync_run = models.ForeignKey(
        MarketplaceSyncRun,
        on_delete=models.PROTECT,
        related_name="sales_period_snapshots",
    )
    operation = models.ForeignKey(
        "operations.Operation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sales_period_snapshots",
    )
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    orders_qty = models.IntegerField(null=True, blank=True)
    sales_qty = models.IntegerField(null=True, blank=True)
    buyout_qty = models.IntegerField(null=True, blank=True)
    returns_qty = models.IntegerField(null=True, blank=True)
    sales_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )
    currency = models.CharField(max_length=16, blank=True)
    raw_safe = models.JSONField(default=dict, blank=True)
    source_endpoint = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-period_start", "-id"]
        indexes = [
            models.Index(fields=["listing", "period_start", "period_end"]),
            models.Index(fields=["sync_run", "period_start"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(period_end__gte=models.F("period_start")),
                name="sales_period_snapshot_end_gte_start",
            ),
        ]

    def clean(self):
        super().clean()
        if self.listing_id and self.sync_run_id:
            _validate_snapshot_context(self.listing, self.sync_run, self.operation)
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValidationError("Sales period end must be greater than or equal to start.")


class PromotionSnapshot(RawSafeSnapshotMixin, models.Model):
    raw_safe_field_name = "promotion snapshot raw_safe"
    listing = models.ForeignKey(
        MarketplaceListing,
        on_delete=models.PROTECT,
        related_name="promotion_snapshots",
    )
    sync_run = models.ForeignKey(
        MarketplaceSyncRun,
        on_delete=models.PROTECT,
        related_name="promotion_snapshots",
    )
    operation = models.ForeignKey(
        "operations.Operation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="promotion_snapshots",
    )
    marketplace_promotion_id = models.CharField(max_length=255)
    action_name = models.CharField(max_length=255, blank=True)
    participation_status = models.CharField(max_length=64)
    action_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    constraints = models.JSONField(default=dict, blank=True)
    reason_code = models.CharField(max_length=128, blank=True)
    raw_safe = models.JSONField(default=dict, blank=True)
    source_endpoint = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["listing", "marketplace_promotion_id"]),
            models.Index(fields=["sync_run", "created_at"]),
        ]

    def clean(self):
        super().clean()
        if self.listing_id and self.sync_run_id:
            _validate_snapshot_context(self.listing, self.sync_run, self.operation)
