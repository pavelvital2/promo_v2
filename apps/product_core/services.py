"""Access checks, sync foundation and audited Product Core helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.audit.models import AuditActionCode, AuditSourceContext
from apps.audit.services import create_audit_record
from apps.discounts.wb_api.redaction import assert_no_secret_like_values
from apps.identity_access.services import has_permission, has_store_access
from apps.stores.models import StoreAccount
from apps.techlog.services import create_techlog_record

from .models import (
    ListingSource,
    ListingHistory,
    MarketplaceListing,
    MarketplaceSyncRun,
    PriceSnapshot,
    ProductIdentifier,
    ProductMappingHistory,
    ProductVariant,
    PromotionSnapshot,
    SalesPeriodSnapshot,
    StockSnapshot,
)


SNAPSHOT_VIEW_PERMISSION = "marketplace_snapshot.view"
SNAPSHOT_TECHNICAL_VIEW_PERMISSION = "marketplace_snapshot.technical_view"
ACTIVE_SYNC_STATUSES = (
    MarketplaceSyncRun.SyncStatus.CREATED,
    MarketplaceSyncRun.SyncStatus.RUNNING,
)


@dataclass(frozen=True)
class MappingCandidate:
    variant: ProductVariant
    match_type: str
    listing_value: str
    variant_value: str


class DuplicateActiveSyncRun(ValidationError):
    """Raised when the same store/marketplace/sync type already has an active run."""


def marketplace_listings_visible_to(user):
    queryset = MarketplaceListing.objects.select_related("store", "internal_variant")
    if not user or not getattr(user, "is_authenticated", False) or not user.is_active:
        return queryset.none()

    allowed_store_ids = [
        store.pk
        for store in StoreAccount.objects.filter(
            pk__in=queryset.values_list("store_id", flat=True).distinct(),
        )
        if has_permission(user, "marketplace_listing.view", store)
    ]
    if not allowed_store_ids:
        return queryset.none()
    return queryset.filter(store_id__in=allowed_store_ids)


def can_view_marketplace_listing(user, listing: MarketplaceListing) -> bool:
    return has_permission(user, "marketplace_listing.view", listing.store)


def can_export_marketplace_listing(user, listing: MarketplaceListing) -> bool:
    return has_permission(user, "marketplace_listing.export", listing.store)


def can_sync_marketplace_listing(user, store) -> bool:
    return has_permission(user, "marketplace_listing.sync", store)


def _snapshot_store(snapshot):
    listing = getattr(snapshot, "listing", None)
    return getattr(listing, "store", None)


def can_view_marketplace_snapshot(user, snapshot) -> bool:
    store = _snapshot_store(snapshot)
    return bool(store and has_permission(user, SNAPSHOT_VIEW_PERMISSION, store))


def can_view_marketplace_snapshot_technical_details(user, snapshot) -> bool:
    store = _snapshot_store(snapshot)
    return bool(
        store
        and has_permission(user, SNAPSHOT_VIEW_PERMISSION, store)
        and has_permission(user, SNAPSHOT_TECHNICAL_VIEW_PERMISSION, store)
    )


def _sync_techlog_event(status: str) -> str:
    if status == MarketplaceSyncRun.SyncStatus.COMPLETED_SUCCESS:
        return "marketplace_sync.completed"
    if status == MarketplaceSyncRun.SyncStatus.COMPLETED_WITH_WARNINGS:
        return "marketplace_sync.completed_with_warnings"
    return "marketplace_sync.failed"


def _sync_techlog_severity(status: str) -> str:
    if status == MarketplaceSyncRun.SyncStatus.COMPLETED_SUCCESS:
        return "info"
    if status == MarketplaceSyncRun.SyncStatus.COMPLETED_WITH_WARNINGS:
        return "warning"
    return "error"


def _listing_history_values(listing: MarketplaceListing) -> dict:
    return {
        "listing_status": listing.listing_status,
        "last_values": listing.last_values,
        "first_seen_at": listing.first_seen_at.isoformat() if listing.first_seen_at else "",
        "last_seen_at": listing.last_seen_at.isoformat() if listing.last_seen_at else "",
        "last_successful_sync_at": (
            listing.last_successful_sync_at.isoformat()
            if listing.last_successful_sync_at
            else ""
        ),
        "last_sync_run_id": listing.last_sync_run_id,
        "last_source": listing.last_source,
    }


def _latest_by_listing(queryset, timestamp_field: str) -> dict[int, object]:
    latest = {}
    for snapshot in queryset.order_by("listing_id", f"-{timestamp_field}", "-id"):
        latest.setdefault(snapshot.listing_id, snapshot)
    return latest


def _price_cache(snapshot: PriceSnapshot) -> dict:
    cache = {
        "price": str(snapshot.price),
        "currency": snapshot.currency,
        "price_snapshot_at": snapshot.snapshot_at.isoformat(),
    }
    if snapshot.price_with_discount is not None:
        cache["price_with_discount"] = str(snapshot.price_with_discount)
    if snapshot.discount_percent is not None:
        cache["discount_percent"] = str(snapshot.discount_percent)
    return cache


def _stock_cache(snapshot: StockSnapshot) -> dict:
    return {
        "total_stock": snapshot.total_stock,
        "stock_by_warehouse": snapshot.stock_by_warehouse,
        "in_way_to_client": snapshot.in_way_to_client,
        "in_way_from_client": snapshot.in_way_from_client,
        "stock_snapshot_at": snapshot.snapshot_at.isoformat(),
    }


def _sales_cache(snapshot: SalesPeriodSnapshot) -> dict:
    cache = {
        "sales_period_start": snapshot.period_start.isoformat(),
        "sales_period_end": snapshot.period_end.isoformat(),
        "orders_qty": snapshot.orders_qty,
        "sales_qty": snapshot.sales_qty,
        "buyout_qty": snapshot.buyout_qty,
        "returns_qty": snapshot.returns_qty,
        "currency": snapshot.currency,
    }
    if snapshot.sales_amount is not None:
        cache["sales_amount"] = str(snapshot.sales_amount)
    return cache


def _promotion_cache(snapshot: PromotionSnapshot) -> dict:
    cache = {
        "marketplace_promotion_id": snapshot.marketplace_promotion_id,
        "action_name": snapshot.action_name,
        "participation_status": snapshot.participation_status,
        "reason_code": snapshot.reason_code,
    }
    if snapshot.action_price is not None:
        cache["action_price"] = str(snapshot.action_price)
    return cache


def _apply_successful_sync_cache(sync_run: MarketplaceSyncRun) -> int:
    price_by_listing = _latest_by_listing(sync_run.price_snapshots.select_related("listing"), "snapshot_at")
    stock_by_listing = _latest_by_listing(sync_run.stock_snapshots.select_related("listing"), "snapshot_at")
    sales_by_listing = _latest_by_listing(
        sync_run.sales_period_snapshots.select_related("listing"),
        "period_start",
    )
    promotion_by_listing: dict[int, list[PromotionSnapshot]] = {}
    for snapshot in sync_run.promotion_snapshots.select_related("listing").order_by(
        "listing_id",
        "-created_at",
        "-id",
    ):
        promotion_by_listing.setdefault(snapshot.listing_id, []).append(snapshot)

    listing_ids = {
        *price_by_listing,
        *stock_by_listing,
        *sales_by_listing,
        *promotion_by_listing,
    }
    updated_count = 0
    for listing in MarketplaceListing.objects.select_for_update().filter(pk__in=listing_ids):
        before = _listing_history_values(listing)
        last_values = dict(listing.last_values or {})
        changed_fields = set()
        if listing.pk in price_by_listing:
            last_values.update(_price_cache(price_by_listing[listing.pk]))
        if listing.pk in stock_by_listing:
            last_values.update(_stock_cache(stock_by_listing[listing.pk]))
        if listing.pk in sales_by_listing:
            last_values.update(_sales_cache(sales_by_listing[listing.pk]))
        if listing.pk in promotion_by_listing:
            last_values["promotions"] = [
                _promotion_cache(snapshot) for snapshot in promotion_by_listing[listing.pk]
            ]
        if listing.last_values != last_values:
            listing.last_values = last_values
            changed_fields.add("last_values")
        if listing.listing_status != MarketplaceListing.ListingStatus.ACTIVE:
            listing.listing_status = MarketplaceListing.ListingStatus.ACTIVE
            changed_fields.add("listing_status")
        finished_at = sync_run.finished_at or timezone.now()
        if not listing.first_seen_at:
            listing.first_seen_at = finished_at
            changed_fields.add("first_seen_at")
        if listing.last_seen_at != finished_at:
            listing.last_seen_at = finished_at
            changed_fields.add("last_seen_at")
        if listing.last_successful_sync_at != finished_at:
            listing.last_successful_sync_at = finished_at
            changed_fields.add("last_successful_sync_at")
        if listing.last_sync_run_id != sync_run.pk:
            listing.last_sync_run = sync_run
            changed_fields.add("last_sync_run")
        if listing.last_source != sync_run.source:
            listing.last_source = sync_run.source
            changed_fields.add("last_source")
        if not changed_fields:
            continue
        listing.full_clean()
        listing.save(update_fields=[*sorted(changed_fields), "updated_at"])
        ListingHistory.objects.create(
            listing=listing,
            change_type=ListingHistory.ChangeType.UPDATED,
            changed_at=finished_at,
            changed_fields=sorted(changed_fields),
            previous_values=before,
            new_values=_listing_history_values(listing),
            sync_run=sync_run,
            operation=sync_run.operation,
            changed_by=sync_run.requested_by,
            source=sync_run.source,
        )
        create_audit_record(
            action_code=AuditActionCode.MARKETPLACE_LISTING_SYNCED,
            entity_type="MarketplaceListing",
            entity_id=str(listing.pk),
            user=sync_run.requested_by,
            store=listing.store,
            operation=sync_run.operation,
            safe_message="Marketplace listing updated by successful sync.",
            before_snapshot=before,
            after_snapshot=_listing_history_values(listing),
            source_context=AuditSourceContext.SERVICE,
        )
        updated_count += 1
    return updated_count


@transaction.atomic
def start_marketplace_sync_run(
    *,
    marketplace: str,
    store,
    sync_type: str,
    source: str,
    operation=None,
    requested_by=None,
    launch_method: str = "manual",
    summary: dict | None = None,
) -> MarketplaceSyncRun:
    if store.marketplace != marketplace:
        raise ValidationError("Sync run marketplace must match store/cabinet marketplace.")
    summary = summary or {}
    assert_no_secret_like_values(summary, field_name="sync run summary")
    duplicate = (
        MarketplaceSyncRun.objects.select_for_update()
        .filter(
            marketplace=marketplace,
            store=store,
            sync_type=sync_type,
            status__in=ACTIVE_SYNC_STATUSES,
        )
        .first()
    )
    if duplicate:
        raise DuplicateActiveSyncRun(
            f"Active sync run already exists for store={store.pk}, "
            f"marketplace={marketplace}, sync_type={sync_type}."
        )
    try:
        sync_run = MarketplaceSyncRun.objects.create(
            marketplace=marketplace,
            store=store,
            sync_type=sync_type,
            source=source,
            launch_method=launch_method,
            status=MarketplaceSyncRun.SyncStatus.RUNNING,
            started_at=timezone.now(),
            requested_by=requested_by,
            operation=operation,
            summary=summary,
        )
    except IntegrityError as exc:
        raise DuplicateActiveSyncRun("Active sync run already exists.") from exc
    create_techlog_record(
        severity="info",
        event_type="marketplace_sync.started",
        source_component="apps.product_core.sync",
        operation=operation,
        store=store,
        safe_message="Marketplace sync started.",
    )
    return sync_run


@transaction.atomic
def complete_marketplace_sync_run(
    sync_run: MarketplaceSyncRun,
    *,
    summary: dict | None = None,
    warning_count: int = 0,
) -> MarketplaceSyncRun:
    sync_run = MarketplaceSyncRun.objects.select_for_update().get(pk=sync_run.pk)
    if sync_run.status not in ACTIVE_SYNC_STATUSES:
        raise ValidationError("Only active sync runs can be completed.")
    summary = summary or {}
    assert_no_secret_like_values(summary, field_name="sync run summary")
    sync_run.status = (
        MarketplaceSyncRun.SyncStatus.COMPLETED_WITH_WARNINGS
        if warning_count
        else MarketplaceSyncRun.SyncStatus.COMPLETED_SUCCESS
    )
    sync_run.summary = summary
    sync_run.finished_at = timezone.now()
    sync_run.full_clean()
    sync_run.save(update_fields=["status", "summary", "finished_at"])
    updated_count = _apply_successful_sync_cache(sync_run)
    sync_run.summary = {**sync_run.summary, "updated_listing_cache_count": updated_count}
    sync_run.save(update_fields=["summary"])
    create_techlog_record(
        severity=_sync_techlog_severity(sync_run.status),
        event_type=_sync_techlog_event(sync_run.status),
        source_component="apps.product_core.sync",
        operation=sync_run.operation,
        store=sync_run.store,
        safe_message="Marketplace sync completed.",
    )
    return sync_run


@transaction.atomic
def fail_marketplace_sync_run(
    sync_run: MarketplaceSyncRun,
    *,
    error_summary: dict | None = None,
    status: str = MarketplaceSyncRun.SyncStatus.INTERRUPTED_FAILED,
) -> MarketplaceSyncRun:
    if status not in {
        MarketplaceSyncRun.SyncStatus.COMPLETED_WITH_ERROR,
        MarketplaceSyncRun.SyncStatus.INTERRUPTED_FAILED,
    }:
        raise ValidationError("Unsupported failed sync status.")
    sync_run = MarketplaceSyncRun.objects.select_for_update().get(pk=sync_run.pk)
    if sync_run.status not in ACTIVE_SYNC_STATUSES:
        raise ValidationError("Only active sync runs can fail.")
    error_summary = error_summary or {}
    assert_no_secret_like_values(error_summary, field_name="sync run error_summary")
    sync_run.status = status
    sync_run.error_summary = error_summary
    sync_run.finished_at = timezone.now()
    sync_run.full_clean()
    sync_run.save(update_fields=["status", "error_summary", "finished_at"])
    create_techlog_record(
        severity="error",
        event_type="marketplace_sync.failed",
        source_component="apps.product_core.sync",
        operation=sync_run.operation,
        store=sync_run.store,
        safe_message="Marketplace sync failed.",
    )
    return sync_run


def _snapshot_operation(sync_run: MarketplaceSyncRun, operation):
    return operation if operation is not None else sync_run.operation


def _assert_snapshot_can_attach(sync_run: MarketplaceSyncRun, listing: MarketplaceListing) -> None:
    if sync_run.status not in ACTIVE_SYNC_STATUSES:
        raise ValidationError("Snapshots can be attached only to active sync runs.")
    if listing.store_id != sync_run.store_id or listing.marketplace != sync_run.marketplace:
        raise ValidationError("Snapshot listing context must match sync run.")


def create_price_snapshot(
    *,
    sync_run: MarketplaceSyncRun,
    listing: MarketplaceListing,
    snapshot_at=None,
    price,
    currency: str,
    price_with_discount=None,
    discount_percent=None,
    raw_safe: dict | None = None,
    source_endpoint: str = "",
    operation=None,
) -> PriceSnapshot:
    _assert_snapshot_can_attach(sync_run, listing)
    raw_safe = raw_safe or {}
    assert_no_secret_like_values(raw_safe, field_name="price snapshot raw_safe")
    return PriceSnapshot.objects.create(
        listing=listing,
        sync_run=sync_run,
        operation=_snapshot_operation(sync_run, operation),
        snapshot_at=snapshot_at or timezone.now(),
        price=Decimal(str(price)),
        price_with_discount=(
            Decimal(str(price_with_discount)) if price_with_discount is not None else None
        ),
        discount_percent=Decimal(str(discount_percent)) if discount_percent is not None else None,
        currency=currency,
        raw_safe=raw_safe,
        source_endpoint=source_endpoint,
    )


def create_stock_snapshot(
    *,
    sync_run: MarketplaceSyncRun,
    listing: MarketplaceListing,
    snapshot_at=None,
    total_stock: int | None = None,
    stock_by_warehouse: dict | None = None,
    in_way_to_client: int | None = None,
    in_way_from_client: int | None = None,
    raw_safe: dict | None = None,
    source_endpoint: str = "",
    operation=None,
) -> StockSnapshot:
    _assert_snapshot_can_attach(sync_run, listing)
    raw_safe = raw_safe or {}
    stock_by_warehouse = stock_by_warehouse or {}
    assert_no_secret_like_values(raw_safe, field_name="stock snapshot raw_safe")
    assert_no_secret_like_values(stock_by_warehouse, field_name="stock snapshot warehouses")
    return StockSnapshot.objects.create(
        listing=listing,
        sync_run=sync_run,
        operation=_snapshot_operation(sync_run, operation),
        snapshot_at=snapshot_at or timezone.now(),
        total_stock=total_stock,
        stock_by_warehouse=stock_by_warehouse,
        in_way_to_client=in_way_to_client,
        in_way_from_client=in_way_from_client,
        raw_safe=raw_safe,
        source_endpoint=source_endpoint,
    )


def create_sales_period_snapshot(
    *,
    sync_run: MarketplaceSyncRun,
    listing: MarketplaceListing,
    period_start,
    period_end,
    orders_qty: int | None = None,
    sales_qty: int | None = None,
    buyout_qty: int | None = None,
    returns_qty: int | None = None,
    sales_amount=None,
    currency: str = "",
    raw_safe: dict | None = None,
    source_endpoint: str = "",
    operation=None,
) -> SalesPeriodSnapshot:
    _assert_snapshot_can_attach(sync_run, listing)
    raw_safe = raw_safe or {}
    assert_no_secret_like_values(raw_safe, field_name="sales period snapshot raw_safe")
    return SalesPeriodSnapshot.objects.create(
        listing=listing,
        sync_run=sync_run,
        operation=_snapshot_operation(sync_run, operation),
        period_start=period_start,
        period_end=period_end,
        orders_qty=orders_qty,
        sales_qty=sales_qty,
        buyout_qty=buyout_qty,
        returns_qty=returns_qty,
        sales_amount=Decimal(str(sales_amount)) if sales_amount is not None else None,
        currency=currency,
        raw_safe=raw_safe,
        source_endpoint=source_endpoint,
    )


def create_promotion_snapshot(
    *,
    sync_run: MarketplaceSyncRun,
    listing: MarketplaceListing,
    marketplace_promotion_id: str,
    participation_status: str,
    action_name: str = "",
    action_price=None,
    constraints: dict | None = None,
    reason_code: str = "",
    raw_safe: dict | None = None,
    source_endpoint: str = "",
    operation=None,
) -> PromotionSnapshot:
    _assert_snapshot_can_attach(sync_run, listing)
    raw_safe = raw_safe or {}
    constraints = constraints or {}
    assert_no_secret_like_values(raw_safe, field_name="promotion snapshot raw_safe")
    assert_no_secret_like_values(constraints, field_name="promotion snapshot constraints")
    return PromotionSnapshot.objects.create(
        listing=listing,
        sync_run=sync_run,
        operation=_snapshot_operation(sync_run, operation),
        marketplace_promotion_id=str(marketplace_promotion_id),
        action_name=action_name,
        participation_status=participation_status,
        action_price=Decimal(str(action_price)) if action_price is not None else None,
        constraints=constraints,
        reason_code=reason_code,
        raw_safe=raw_safe,
        source_endpoint=source_endpoint,
    )


def _assert_mapping_permission(actor, listing: MarketplaceListing, permission_code: str) -> None:
    if not has_store_access(actor, listing.store, allow_global=True):
        raise PermissionDenied("Actor has no access to listing store.")
    if not has_permission(actor, permission_code, listing.store):
        raise PermissionDenied("Actor has no marketplace listing mapping permission.")
    if not has_permission(actor, "product_core.view") or not has_permission(
        actor,
        "product_variant.view",
    ):
        raise PermissionDenied("Actor has no Product Core product/variant access.")


def _mapping_action_audit_code(action: str) -> str:
    if action == ProductMappingHistory.MappingAction.MAP:
        return AuditActionCode.MARKETPLACE_LISTING_MAPPED
    if action == ProductMappingHistory.MappingAction.UNMAP:
        return AuditActionCode.MARKETPLACE_LISTING_UNMAPPED
    if action == ProductMappingHistory.MappingAction.NEEDS_REVIEW_MARKER:
        return AuditActionCode.MARKETPLACE_LISTING_MAPPING_REVIEW_MARKED
    if action == ProductMappingHistory.MappingAction.CONFLICT_MARKER:
        return AuditActionCode.MARKETPLACE_LISTING_MAPPING_CONFLICT_MARKED
    raise ValidationError("Unsupported mapping action.")


def _scalar_tokens(value) -> set[str]:
    tokens: set[str] = set()
    if value is None:
        return tokens
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            tokens.add(stripped)
        return tokens
    if isinstance(value, (int, float)):
        tokens.add(str(value))
        return tokens
    if isinstance(value, list):
        for item in value:
            tokens.update(_scalar_tokens(item))
        return tokens
    if isinstance(value, dict):
        for item in value.values():
            tokens.update(_scalar_tokens(item))
    return tokens


def _candidate_sort_key(candidate: MappingCandidate):
    return (
        candidate.variant.product.internal_code,
        candidate.variant.internal_sku,
        candidate.variant.name,
        candidate.variant.pk,
        candidate.match_type,
        candidate.listing_value,
    )


def exact_mapping_candidates_for_listing(listing: MarketplaceListing) -> list[MappingCandidate]:
    """Return non-authoritative candidates from exact identifiers only.

    No title/fuzzy/partial matching is performed here, and callers must still
    require explicit user confirmation before creating a persisted mapping.
    """

    candidates: dict[tuple[int, str, str, str], MappingCandidate] = {}

    def add_candidate(variant: ProductVariant, match_type: str, listing_value: str, variant_value: str):
        key = (variant.pk, match_type, listing_value, variant_value)
        candidates[key] = MappingCandidate(
            variant=variant,
            match_type=match_type,
            listing_value=listing_value,
            variant_value=variant_value,
        )

    seller_article = (listing.seller_article or "").strip()
    if seller_article:
        variants = ProductVariant.objects.select_related("product").filter(
            internal_sku=seller_article,
        ).exclude(status="archived").exclude(product__status="archived")
        for variant in variants:
            add_candidate(variant, "exact_seller_article", seller_article, variant.internal_sku)
        identifiers = ProductIdentifier.objects.select_related("variant", "variant__product").filter(
            value=seller_article,
            identifier_type__in=[
                ProductIdentifier.IdentifierType.WB_VENDOR_CODE,
                ProductIdentifier.IdentifierType.OZON_OFFER_ID,
                ProductIdentifier.IdentifierType.LEGACY_ARTICLE,
            ],
        ).exclude(variant__status="archived").exclude(variant__product__status="archived")
        for identifier in identifiers:
            add_candidate(identifier.variant, "exact_seller_article", seller_article, identifier.value)

    barcode = (listing.barcode or "").strip()
    if barcode:
        variants = (
            ProductVariant.objects.select_related("product")
            .filter(barcode_internal=barcode)
            .exclude(status="archived")
            .exclude(product__status="archived")
        )
        for variant in variants:
            add_candidate(variant, "exact_barcode", barcode, variant.barcode_internal)
        identifiers = ProductIdentifier.objects.select_related("variant", "variant__product").filter(
            value=barcode,
            identifier_type=ProductIdentifier.IdentifierType.INTERNAL_BARCODE,
        ).exclude(variant__status="archived").exclude(variant__product__status="archived")
        for identifier in identifiers:
            add_candidate(identifier.variant, "exact_barcode", barcode, identifier.value)

    external_tokens = _scalar_tokens(listing.external_primary_id) | _scalar_tokens(listing.external_ids)
    if external_tokens:
        identifiers = ProductIdentifier.objects.select_related("variant", "variant__product").filter(
            value__in=external_tokens,
            identifier_type__in=[
                ProductIdentifier.IdentifierType.WB_VENDOR_CODE,
                ProductIdentifier.IdentifierType.OZON_OFFER_ID,
                ProductIdentifier.IdentifierType.LEGACY_ARTICLE,
            ],
        ).exclude(variant__status="archived").exclude(variant__product__status="archived")
        for identifier in identifiers:
            add_candidate(
                identifier.variant,
                "exact_external_identifier",
                identifier.value,
                identifier.value,
            )

    return sorted(candidates.values(), key=_candidate_sort_key)


def _candidate_variant_ids(candidates: list[MappingCandidate]) -> list[int]:
    return sorted({candidate.variant.pk for candidate in candidates})


def refresh_mapping_candidate_status(
    *,
    actor,
    listing: MarketplaceListing,
    candidates: list[MappingCandidate] | None = None,
) -> ProductMappingHistory | None:
    """Mark unmatched listings that have exact candidates as review/conflict.

    Suggestions remain non-authoritative: this helper never sets matched and
    never assigns an internal variant.
    """

    if listing.internal_variant_id or listing.mapping_status == MarketplaceListing.MappingStatus.ARCHIVED:
        return None
    candidates = candidates if candidates is not None else exact_mapping_candidates_for_listing(listing)
    variant_ids = _candidate_variant_ids(candidates)
    if not variant_ids:
        return None
    if len(variant_ids) > 1:
        if listing.mapping_status == MarketplaceListing.MappingStatus.CONFLICT:
            return None
        return record_product_mapping_change(
            actor=actor,
            listing=listing,
            action=ProductMappingHistory.MappingAction.CONFLICT_MARKER,
            source_context={
                "basis": "exact_candidate_suggestions",
                "candidate_variant_ids": variant_ids,
            },
            reason_comment="Multiple exact non-authoritative candidates require manual resolution.",
        )
    if listing.mapping_status in {
        MarketplaceListing.MappingStatus.NEEDS_REVIEW,
        MarketplaceListing.MappingStatus.CONFLICT,
    }:
        return None
    return record_product_mapping_change(
        actor=actor,
        listing=listing,
        action=ProductMappingHistory.MappingAction.NEEDS_REVIEW_MARKER,
        source_context={
            "basis": "exact_candidate_suggestions",
            "candidate_variant_ids": variant_ids,
        },
        reason_comment="Exact non-authoritative candidate requires manual confirmation.",
    )


@transaction.atomic
def record_product_mapping_change(
    *,
    actor,
    listing: MarketplaceListing,
    action: str,
    new_variant: ProductVariant | None = None,
    source: str = ListingSource.MANUAL_IMPORT,
    source_context: dict | None = None,
    reason_comment: str = "",
    sync_run=None,
    operation=None,
    mapping_status_after: str | None = None,
) -> ProductMappingHistory:
    permission_code = (
        "marketplace_listing.map"
        if action
        in {
            ProductMappingHistory.MappingAction.MAP,
            ProductMappingHistory.MappingAction.NEEDS_REVIEW_MARKER,
            ProductMappingHistory.MappingAction.CONFLICT_MARKER,
        }
        else "marketplace_listing.unmap"
    )
    _assert_mapping_permission(actor, listing, permission_code)
    source_context = source_context or {}
    assert_no_secret_like_values(source_context, field_name="product mapping source_context")
    assert_no_secret_like_values(reason_comment, field_name="product mapping reason_comment")

    previous_variant = listing.internal_variant
    previous_mapping_status = listing.mapping_status
    if action == ProductMappingHistory.MappingAction.MAP:
        if new_variant is None:
            raise ValidationError("Mapping requires a new variant.")
        listing.internal_variant = new_variant
        listing.mapping_status = MarketplaceListing.MappingStatus.MATCHED
    elif action == ProductMappingHistory.MappingAction.UNMAP:
        mapping_status_after = mapping_status_after or MarketplaceListing.MappingStatus.UNMATCHED
        if mapping_status_after not in {
            MarketplaceListing.MappingStatus.UNMATCHED,
            MarketplaceListing.MappingStatus.NEEDS_REVIEW,
            MarketplaceListing.MappingStatus.CONFLICT,
        }:
            raise ValidationError("Unsupported unmap target mapping status.")
        listing.internal_variant = None
        listing.mapping_status = mapping_status_after
    elif action == ProductMappingHistory.MappingAction.NEEDS_REVIEW_MARKER:
        listing.mapping_status = MarketplaceListing.MappingStatus.NEEDS_REVIEW
    elif action == ProductMappingHistory.MappingAction.CONFLICT_MARKER:
        listing.mapping_status = MarketplaceListing.MappingStatus.CONFLICT
    else:
        raise ValidationError("Unsupported mapping action.")

    listing.full_clean()
    listing.save(update_fields=["internal_variant", "mapping_status", "updated_at"])

    history = ProductMappingHistory.objects.create(
        listing=listing,
        action=action,
        mapping_status_after=listing.mapping_status,
        changed_at=timezone.now(),
        previous_variant=previous_variant,
        new_variant=new_variant,
        changed_by=actor,
        sync_run=sync_run,
        operation=operation,
        source=source,
        source_context=source_context,
        reason_comment=reason_comment,
    )
    create_audit_record(
        action_code=_mapping_action_audit_code(action),
        entity_type="ProductMappingHistory",
        entity_id=str(history.pk),
        user=actor,
        store=listing.store,
        operation=operation,
        safe_message=f"Marketplace listing mapping action recorded: {action}.",
        before_snapshot={
            "listing_id": listing.pk,
            "variant_id": previous_variant.pk if previous_variant else None,
            "mapping_status": previous_mapping_status,
        },
        after_snapshot={
            "listing_id": listing.pk,
            "variant_id": listing.internal_variant_id,
            "mapping_status": listing.mapping_status,
            "mapping_action": action,
            "mapping_source_context": source_context,
            "reason_comment": reason_comment,
        },
        source_context=AuditSourceContext.UI,
    )
    return history


def map_listing_to_variant(
    *,
    actor,
    listing: MarketplaceListing,
    variant: ProductVariant,
    source_context: dict | None = None,
    reason_comment: str = "",
) -> ProductMappingHistory:
    return record_product_mapping_change(
        actor=actor,
        listing=listing,
        action=ProductMappingHistory.MappingAction.MAP,
        new_variant=variant,
        source_context=source_context,
        reason_comment=reason_comment,
    )


def unmap_listing(
    *,
    actor,
    listing: MarketplaceListing,
    source_context: dict | None = None,
    reason_comment: str = "",
    mapping_status_after: str = MarketplaceListing.MappingStatus.UNMATCHED,
) -> ProductMappingHistory:
    return record_product_mapping_change(
        actor=actor,
        listing=listing,
        action=ProductMappingHistory.MappingAction.UNMAP,
        source_context=source_context,
        reason_comment=reason_comment,
        mapping_status_after=mapping_status_after,
    )


def mark_listing_needs_review(
    *,
    actor,
    listing: MarketplaceListing,
    source_context: dict | None = None,
    reason_comment: str = "",
) -> ProductMappingHistory:
    return record_product_mapping_change(
        actor=actor,
        listing=listing,
        action=ProductMappingHistory.MappingAction.NEEDS_REVIEW_MARKER,
        source_context=source_context,
        reason_comment=reason_comment,
    )


def mark_listing_conflict(
    *,
    actor,
    listing: MarketplaceListing,
    source_context: dict | None = None,
    reason_comment: str = "",
) -> ProductMappingHistory:
    return record_product_mapping_change(
        actor=actor,
        listing=listing,
        action=ProductMappingHistory.MappingAction.CONFLICT_MARKER,
        source_context=source_context,
        reason_comment=reason_comment,
    )
