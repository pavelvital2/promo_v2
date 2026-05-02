"""Access checks, sync foundation and audited Product Core helpers."""

from __future__ import annotations

from dataclasses import dataclass, is_dataclass, asdict
from decimal import Decimal
import hashlib
import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from apps.audit.models import AuditActionCode, AuditSourceContext
from apps.audit.services import create_audit_record
from apps.discounts.wb_api.redaction import assert_no_secret_like_values
from apps.identity_access.services import has_permission, has_store_access
from apps.stores.models import StoreAccount
from apps.techlog.models import TechLogEventType
from apps.techlog.services import create_techlog_record

from .models import (
    InternalProduct,
    ListingSource,
    ListingHistory,
    Marketplace,
    MarketplaceListing,
    MarketplaceSyncRun,
    PriceSnapshot,
    ProductIdentifier,
    ProductMappingHistory,
    ProductStatus,
    ProductVariant,
    PromotionSnapshot,
    SalesPeriodSnapshot,
    StockSnapshot,
    validate_core2_internal_sku,
)


SNAPSHOT_VIEW_PERMISSION = "marketplace_snapshot.view"
SNAPSHOT_TECHNICAL_VIEW_PERMISSION = "marketplace_snapshot.technical_view"
ACTIVE_SYNC_STATUSES = (
    MarketplaceSyncRun.SyncStatus.CREATED,
    MarketplaceSyncRun.SyncStatus.RUNNING,
)
WB_PRICES_ENDPOINT_CODE = "wb_prices_list_goods_filter"
WB_PROMOTIONS_ENDPOINT_CODE = "wb_promotions_nomenclatures"
OZON_ACTION_PRODUCTS_ENDPOINT_CODE = "ozon_actions_products"
OZON_ACTION_CANDIDATES_ENDPOINT_CODE = "ozon_actions_candidates"
OZON_PRODUCT_INFO_STOCKS_ENDPOINT_CODE = "ozon_product_info_stocks"


@dataclass(frozen=True)
class MappingCandidate:
    variant: ProductVariant
    match_type: str
    listing_value: str
    variant_value: str


class DuplicateActiveSyncRun(ValidationError):
    """Raised when the same store/marketplace/sync type already has an active run."""


class MarketplaceSyncAdapterError(ValidationError):
    """Raised when Product Core approved-source sync adapter input is invalid."""


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


def _decimal_cache_value(snapshot, field_name: str, raw_key: str) -> str:
    value = getattr(snapshot, field_name)
    raw_value = (snapshot.raw_safe or {}).get(raw_key)
    if raw_value not in (None, "") and _decimal_or_none(raw_value) == value:
        return str(raw_value)
    return str(value)


def _price_cache(snapshot: PriceSnapshot) -> dict:
    cache = {
        "price": _decimal_cache_value(snapshot, "price", "price"),
        "currency": snapshot.currency,
        "price_snapshot_at": snapshot.snapshot_at.isoformat(),
    }
    if snapshot.price_with_discount is not None:
        cache["price_with_discount"] = _decimal_cache_value(
            snapshot,
            "price_with_discount",
            "price_with_discount",
        )
    if snapshot.discount_percent is not None:
        cache["discount_percent"] = _decimal_cache_value(
            snapshot,
            "discount_percent",
            "discount_percent",
        )
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
    create_audit_record(
        action_code=AuditActionCode.MARKETPLACE_SYNC_FAILED,
        entity_type="MarketplaceSyncRun",
        entity_id=str(sync_run.pk),
        user=sync_run.requested_by,
        store=sync_run.store,
        operation=sync_run.operation,
        safe_message="Marketplace sync failed.",
        after_snapshot={
            "sync_run_id": sync_run.pk,
            "operation_id": sync_run.operation_id,
            "source": sync_run.source,
            "status": sync_run.status,
            "sync_type": sync_run.sync_type,
            "marketplace": sync_run.marketplace,
            "error_summary": error_summary,
        },
        source_context=AuditSourceContext.SERVICE,
    )
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


def _record_snapshot_write_failure(
    *,
    sync_run: MarketplaceSyncRun,
    listing: MarketplaceListing,
    snapshot_kind: str,
    source_endpoint: str,
    failure: Exception,
    operation=None,
) -> None:
    snapshot_operation = _snapshot_operation(sync_run, operation)
    safe_context = {
        "snapshot_kind": snapshot_kind,
        "listing_id": listing.pk,
        "sync_run_id": sync_run.pk,
        "operation_id": getattr(snapshot_operation, "pk", None),
        "source_endpoint": source_endpoint,
        "failure_class": failure.__class__.__name__,
    }
    create_audit_record(
        action_code=AuditActionCode.MARKETPLACE_SNAPSHOT_WRITE_FAILED,
        entity_type="MarketplaceListing",
        entity_id=str(listing.pk),
        user=sync_run.requested_by,
        store=listing.store,
        operation=snapshot_operation,
        safe_message="Marketplace snapshot write failed.",
        after_snapshot=safe_context,
        source_context=AuditSourceContext.SERVICE,
    )
    create_techlog_record(
        severity="error",
        event_type=TechLogEventType.MARKETPLACE_SNAPSHOT_WRITE_ERROR,
        source_component="apps.product_core.snapshots",
        operation=snapshot_operation,
        store=listing.store,
        entity_type="MarketplaceListing",
        entity_id=str(listing.pk),
        safe_message="Marketplace snapshot write failed.",
        sensitive_details_ref="redacted:marketplace-snapshot-write-failure",
    )


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
    try:
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
    except Exception as exc:
        _record_snapshot_write_failure(
            sync_run=sync_run,
            listing=listing,
            snapshot_kind="price",
            source_endpoint=source_endpoint,
            failure=exc,
            operation=operation,
        )
        raise


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
    try:
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
    except Exception as exc:
        _record_snapshot_write_failure(
            sync_run=sync_run,
            listing=listing,
            snapshot_kind="stock",
            source_endpoint=source_endpoint,
            failure=exc,
            operation=operation,
        )
        raise


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
    try:
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
    except Exception as exc:
        _record_snapshot_write_failure(
            sync_run=sync_run,
            listing=listing,
            snapshot_kind="sales_period",
            source_endpoint=source_endpoint,
            failure=exc,
            operation=operation,
        )
        raise


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
    try:
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
    except Exception as exc:
        _record_snapshot_write_failure(
            sync_run=sync_run,
            listing=listing,
            snapshot_kind="promotion",
            source_endpoint=source_endpoint,
            failure=exc,
            operation=operation,
        )
        raise


def _row_dict(row) -> dict:
    if isinstance(row, dict):
        return dict(row)
    if is_dataclass(row):
        return asdict(row)
    return {
        name: getattr(row, name)
        for name in dir(row)
        if not name.startswith("_") and not callable(getattr(row, name))
    }


def _first_present(row: dict, *names: str):
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return value
    return None


def _string_value(value) -> str:
    return "" if value in (None, "") else str(value).strip()


def _valid_api_internal_sku(value: str) -> str:
    internal_sku = (value or "").strip()
    if not internal_sku:
        return ""
    try:
        validate_core2_internal_sku(internal_sku)
    except ValidationError:
        return ""
    return internal_sku


def _article_traits(internal_sku: str) -> dict:
    tokens = internal_sku.split("_")
    final_token = tokens[-1]
    content_type = "text" if final_token.startswith("text") else "pict"
    suffix = final_token.removeprefix(content_type)
    traits = {
        "source": "core2_internal_sku",
        "internal_sku": internal_sku,
        "product_type_token": tokens[0],
        "content_type": content_type,
        "numeric_suffix": suffix,
    }
    optional_tokens = tokens[1:-1]
    purposes = {"pz", "back"}
    structures = {"mvd", "fsin", "rg", "fso", "fsb", "fssp"}
    for token in optional_tokens:
        if token in purposes:
            traits["purpose"] = token
        elif token.startswith("kit"):
            traits["kit"] = token
        elif token in structures:
            traits["structure"] = token
    return traits


def _api_linkage_source_context(
    *,
    sync_run: MarketplaceSyncRun,
    listing: MarketplaceListing,
    internal_sku: str,
    outcome: str,
    variant: ProductVariant | None = None,
    product: InternalProduct | None = None,
    extra: dict | None = None,
) -> dict:
    context = {
        "basis": "api_exact_valid_internal_sku",
        "outcome": outcome,
        "source": sync_run.source,
        "sync_run_id": sync_run.pk,
        "operation_id": sync_run.operation_id,
        "marketplace": sync_run.marketplace,
        "store_id": sync_run.store_id,
        "listing_id": listing.pk,
        "listing_external_primary_id": listing.external_primary_id,
        "seller_article": listing.seller_article,
        "trimmed_article": internal_sku,
        "variant_id": variant.pk if variant else None,
        "product_id": product.pk if product else None,
    }
    if extra:
        context.update(extra)
    assert_no_secret_like_values(context, field_name="api product mapping source_context")
    return context


def _create_api_mapping_history(
    *,
    sync_run: MarketplaceSyncRun,
    listing: MarketplaceListing,
    action: str,
    previous_variant: ProductVariant | None,
    new_variant: ProductVariant | None,
    previous_mapping_status: str,
    source_context: dict,
    reason_comment: str,
) -> ProductMappingHistory:
    assert_no_secret_like_values(source_context, field_name="api product mapping source_context")
    assert_no_secret_like_values(reason_comment, field_name="api product mapping reason_comment")
    history = ProductMappingHistory.objects.create(
        listing=listing,
        action=action,
        mapping_status_after=listing.mapping_status,
        changed_at=timezone.now(),
        previous_variant=previous_variant,
        new_variant=new_variant,
        changed_by=sync_run.requested_by,
        sync_run=sync_run,
        operation=sync_run.operation,
        source=sync_run.source,
        source_context=source_context,
        reason_comment=reason_comment,
    )
    create_audit_record(
        action_code=_mapping_action_audit_code(action),
        entity_type="ProductMappingHistory",
        entity_id=str(history.pk),
        user=sync_run.requested_by,
        store=listing.store,
        operation=sync_run.operation,
        safe_message=f"Marketplace listing API mapping action recorded: {action}.",
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
        source_context=AuditSourceContext.API,
    )
    return history


def _mark_api_listing_conflict(
    *,
    sync_run: MarketplaceSyncRun,
    listing: MarketplaceListing,
    internal_sku: str,
    outcome: str,
    extra: dict | None = None,
) -> ProductMappingHistory | None:
    if listing.mapping_status == MarketplaceListing.MappingStatus.CONFLICT:
        return None
    previous_variant = listing.internal_variant
    previous_mapping_status = listing.mapping_status
    listing.mapping_status = MarketplaceListing.MappingStatus.CONFLICT
    listing.full_clean()
    listing.save(update_fields=["mapping_status", "updated_at"])
    context = _api_linkage_source_context(
        sync_run=sync_run,
        listing=listing,
        internal_sku=internal_sku,
        outcome=outcome,
        variant=previous_variant,
        product=previous_variant.product if previous_variant else None,
        extra=extra,
    )
    create_techlog_record(
        severity="warning",
        event_type=TechLogEventType.MARKETPLACE_MAPPING_CONFLICT,
        source_component="apps.product_core.mapping",
        operation=sync_run.operation,
        store=listing.store,
        entity_type="MarketplaceListing",
        entity_id=str(listing.pk),
        safe_message="Automatic marketplace listing mapping conflict detected.",
        sensitive_details_ref="redacted:marketplace-mapping-conflict",
    )
    return _create_api_mapping_history(
        sync_run=sync_run,
        listing=listing,
        action=ProductMappingHistory.MappingAction.CONFLICT_MARKER,
        previous_variant=previous_variant,
        new_variant=previous_variant,
        previous_mapping_status=previous_mapping_status,
        source_context=context,
        reason_comment="API exact internal SKU resolution is unsafe; automatic mapping was not applied.",
    )


def _safe_existing_api_variant(internal_sku: str) -> tuple[str, ProductVariant | None, dict]:
    variants = list(
        ProductVariant.objects.select_for_update()
        .select_related("product")
        .filter(internal_sku=internal_sku)
    )
    safe_variants = [
        variant
        for variant in variants
        if variant.status == ProductStatus.ACTIVE
        and variant.product.status == ProductStatus.ACTIVE
    ]
    unsafe_variant_ids = [
        variant.pk
        for variant in variants
        if variant.status != ProductStatus.ACTIVE
        or variant.product.status != ProductStatus.ACTIVE
    ]
    if len(safe_variants) == 1 and not unsafe_variant_ids:
        return "unique", safe_variants[0], {}
    if len(safe_variants) == 0 and not unsafe_variant_ids:
        return "missing", None, {}
    return (
        "conflict",
        None,
        {
            "safe_variant_ids": [variant.pk for variant in safe_variants],
            "unsafe_variant_ids": unsafe_variant_ids,
        },
    )


def _safe_parent_for_api_auto_create(
    *,
    internal_sku: str,
    title: str,
    sync_run: MarketplaceSyncRun,
) -> tuple[str, InternalProduct | None, bool, dict]:
    products = list(InternalProduct.objects.select_for_update().filter(internal_code=internal_sku))
    safe_products = [product for product in products if product.status == ProductStatus.ACTIVE]
    unsafe_product_ids = [product.pk for product in products if product.status != ProductStatus.ACTIVE]
    if len(safe_products) == 1 and not unsafe_product_ids:
        return "unique", safe_products[0], False, {}
    if len(safe_products) > 1 or unsafe_product_ids:
        return (
            "conflict",
            None,
            False,
            {
                "safe_product_ids": [product.pk for product in safe_products],
                "unsafe_product_ids": unsafe_product_ids,
            },
        )
    product_name = title or internal_sku
    product = InternalProduct(
        internal_code=internal_sku,
        name=product_name,
        product_type=InternalProduct.ProductType.FINISHED_GOOD,
        category=None,
        status=ProductStatus.ACTIVE,
        attributes=_article_traits(internal_sku),
        comments="",
        created_by=sync_run.requested_by,
        updated_by=sync_run.requested_by,
    )
    product.full_clean()
    product.save()
    create_audit_record(
        action_code=AuditActionCode.PRODUCT_CORE_CREATED,
        entity_type="InternalProduct",
        entity_id=str(product.pk),
        user=sync_run.requested_by,
        store=sync_run.store,
        operation=sync_run.operation,
        safe_message="Internal product auto-created from valid API article.",
        after_snapshot={
            "product_id": product.pk,
            "internal_code": internal_sku,
            "source": sync_run.source,
            "sync_run_id": sync_run.pk,
        },
        source_context=AuditSourceContext.API,
    )
    return "created", product, True, {}


def _create_api_imported_draft_variant(
    *,
    product: InternalProduct,
    internal_sku: str,
    title: str,
    sync_run: MarketplaceSyncRun,
    listing: MarketplaceListing,
    parent_created: bool,
) -> ProductVariant:
    variant_name = title or internal_sku
    source_context = _api_linkage_source_context(
        sync_run=sync_run,
        listing=listing,
        internal_sku=internal_sku,
        outcome="auto_created",
        product=product,
        extra={
            "parent_created": parent_created,
            "review_state": ProductVariant.ReviewState.IMPORTED_DRAFT,
        },
    )
    variant = ProductVariant(
        product=product,
        internal_sku=internal_sku,
        name=variant_name,
        status=ProductStatus.ACTIVE,
        review_state=ProductVariant.ReviewState.IMPORTED_DRAFT,
        import_source_context=source_context,
    )
    variant.full_clean()
    variant.save()
    create_audit_record(
        action_code=AuditActionCode.PRODUCT_VARIANT_AUTO_CREATED_DRAFT,
        entity_type="ProductVariant",
        entity_id=str(variant.pk),
        user=sync_run.requested_by,
        store=sync_run.store,
        operation=sync_run.operation,
        safe_message="Product variant imported draft auto-created from valid API article.",
        after_snapshot={
            "variant_id": variant.pk,
            "product_id": product.pk,
            "internal_sku": internal_sku,
            "review_state": variant.review_state,
            "source": sync_run.source,
            "sync_run_id": sync_run.pk,
        },
        source_context=AuditSourceContext.API,
    )
    return variant


def _record_product_variant_auto_create_error(
    *,
    sync_run: MarketplaceSyncRun,
    listing: MarketplaceListing,
    internal_sku: str,
    failure: Exception,
) -> None:
    create_techlog_record(
        severity="error",
        event_type=TechLogEventType.PRODUCT_VARIANT_AUTO_CREATE_ERROR,
        source_component="apps.product_core.api_linkage",
        operation=sync_run.operation,
        store=sync_run.store,
        entity_type="MarketplaceListing",
        entity_id=str(listing.pk),
        safe_message="Product variant auto-create from approved API article failed.",
        sensitive_details_ref="redacted:product-variant-auto-create-failure",
    )


def _record_deferred_auto_create_error_if_present(exc: Exception) -> None:
    context = getattr(exc, "product_variant_auto_create_context", None)
    if not context:
        return
    _record_product_variant_auto_create_error(**context)


def _api_title_mismatch_requires_review(variant: ProductVariant, title: str) -> bool:
    incoming_title = (title or "").strip()
    if not incoming_title:
        return False
    return incoming_title not in {variant.name, variant.product.name}


def _mark_variant_title_mismatch_review(
    *,
    variant: ProductVariant,
    sync_run: MarketplaceSyncRun,
    listing: MarketplaceListing,
    internal_sku: str,
) -> None:
    if variant.review_state == ProductVariant.ReviewState.NEEDS_REVIEW:
        return
    before_state = variant.review_state
    variant.review_state = ProductVariant.ReviewState.NEEDS_REVIEW
    context = _api_linkage_source_context(
        sync_run=sync_run,
        listing=listing,
        internal_sku=internal_sku,
        outcome="title_mismatch_needs_review",
        variant=variant,
        product=variant.product,
        extra={
            "previous_review_state": before_state,
            "marketplace_title": listing.title,
            "variant_name_preserved": variant.name,
            "product_name_preserved": variant.product.name,
        },
    )
    variant.import_source_context = {
        **(variant.import_source_context or {}),
        "latest_title_mismatch_review": context,
    }
    variant.full_clean()
    variant.save(update_fields=["review_state", "import_source_context", "updated_at"])
    create_audit_record(
        action_code=AuditActionCode.MARKETPLACE_LISTING_MAPPING_REVIEW_MARKED,
        entity_type="ProductVariant",
        entity_id=str(variant.pk),
        user=sync_run.requested_by,
        store=listing.store,
        operation=sync_run.operation,
        safe_message="Product variant marked needs review due to API title mismatch.",
        before_snapshot={
            "variant_id": variant.pk,
            "review_state": before_state,
        },
        after_snapshot={
            "variant_id": variant.pk,
            "review_state": variant.review_state,
            "source_context": context,
        },
        source_context=AuditSourceContext.API,
    )


@transaction.atomic
def api_link_listing_by_valid_article(
    *,
    sync_run: MarketplaceSyncRun,
    listing: MarketplaceListing,
) -> ProductMappingHistory | None:
    internal_sku = _valid_api_internal_sku(listing.seller_article)
    if not internal_sku:
        return None

    if listing.internal_variant_id and listing.internal_variant.internal_sku != internal_sku:
        return _mark_api_listing_conflict(
            sync_run=sync_run,
            listing=listing,
            internal_sku=internal_sku,
            outcome="existing_listing_variant_conflict",
            extra={"existing_variant_id": listing.internal_variant_id},
        )

    resolution, variant, conflict_context = _safe_existing_api_variant(internal_sku)
    parent_created = False
    parent = variant.product if variant else None
    created_variant = False
    if resolution == "conflict":
        return _mark_api_listing_conflict(
            sync_run=sync_run,
            listing=listing,
            internal_sku=internal_sku,
            outcome="variant_resolution_conflict",
            extra=conflict_context,
        )
    if resolution == "missing":
        try:
            parent_resolution, parent, parent_created, parent_context = _safe_parent_for_api_auto_create(
                internal_sku=internal_sku,
                title=listing.title.strip(),
                sync_run=sync_run,
            )
            if parent_resolution == "conflict" or parent is None:
                return _mark_api_listing_conflict(
                    sync_run=sync_run,
                    listing=listing,
                    internal_sku=internal_sku,
                    outcome="parent_resolution_conflict",
                    extra=parent_context,
                )
            variant = _create_api_imported_draft_variant(
                product=parent,
                internal_sku=internal_sku,
                title=listing.title.strip(),
                sync_run=sync_run,
                listing=listing,
                parent_created=parent_created,
            )
        except Exception as exc:
            exc.product_variant_auto_create_context = {
                "sync_run": sync_run,
                "listing": listing,
                "internal_sku": internal_sku,
                "failure": exc,
            }
            raise
        created_variant = True

    if variant is None:
        return None

    previous_variant = listing.internal_variant
    previous_mapping_status = listing.mapping_status
    if previous_variant_id := listing.internal_variant_id:
        if previous_variant_id != variant.pk:
            return _mark_api_listing_conflict(
                sync_run=sync_run,
                listing=listing,
                internal_sku=internal_sku,
                outcome="existing_listing_variant_conflict",
                extra={
                    "existing_variant_id": previous_variant_id,
                    "candidate_variant_id": variant.pk,
                },
            )

    listing.internal_variant = variant
    listing.mapping_status = MarketplaceListing.MappingStatus.MATCHED
    listing.full_clean()
    listing.save(update_fields=["internal_variant", "mapping_status", "updated_at"])
    if _api_title_mismatch_requires_review(variant, listing.title):
        _mark_variant_title_mismatch_review(
            variant=variant,
            sync_run=sync_run,
            listing=listing,
            internal_sku=internal_sku,
        )
        variant.refresh_from_db()
    context = _api_linkage_source_context(
        sync_run=sync_run,
        listing=listing,
        internal_sku=internal_sku,
        outcome="auto_created" if created_variant else "existing_variant_linked",
        variant=variant,
        product=parent or variant.product,
        extra={
            "parent_created": parent_created,
            "variant_created": created_variant,
            "review_state": variant.review_state,
        },
    )
    return _create_api_mapping_history(
        sync_run=sync_run,
        listing=listing,
        action=ProductMappingHistory.MappingAction.MAP,
        previous_variant=previous_variant,
        new_variant=variant,
        previous_mapping_status=previous_mapping_status,
        source_context=context,
        reason_comment="API exact valid internal SKU matched listing to variant.",
    )


def _decimal_or_none(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _integer_or_none(value):
    decimal_value = _decimal_or_none(value)
    if decimal_value is None:
        return None
    integral = decimal_value.to_integral_value()
    if decimal_value != integral:
        return None
    return int(integral)


def _safe_summary_value(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _safe_summary_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe_summary_value(item) for item in value]
    return value


def _safe_checksum(value: object) -> str:
    raw = json.dumps(_safe_summary_value(value), sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _detect_duplicate_articles(normalized_rows: list[dict]) -> set[str]:
    article_counts: dict[str, int] = {}
    for row in normalized_rows:
        article = _string_value(row.get("seller_article"))
        if article:
            article_counts[article] = article_counts.get(article, 0) + 1
    return {article for article, count in article_counts.items() if count > 1}


def _source_data_integrity_warning_summary(
    *,
    duplicate_articles: set[str],
    affected_count: int,
) -> dict:
    return {
        "duplicate_external_article_count": len(duplicate_articles),
        "affected_rows_count": affected_count,
    }


def _record_source_data_integrity_warning(
    *,
    sync_run: MarketplaceSyncRun,
    duplicate_articles: set[str],
    affected_count: int,
) -> None:
    create_techlog_record(
        severity="error",
        event_type=TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR,
        source_component="apps.product_core.sync",
        operation=sync_run.operation,
        store=sync_run.store,
        safe_message=(
            "Marketplace sync source contains duplicate external article values; "
            "affected rows were skipped."
        ),
        entity_type="MarketplaceSyncRun",
        entity_id=str(sync_run.pk),
        sensitive_details_ref="redacted:marketplace-sync-source-data-integrity",
    )
    sync_run.summary = {
        **(sync_run.summary or {}),
        "source_data_integrity_warning": {
            "duplicate_external_article_count": len(duplicate_articles),
            "affected_rows_count": affected_count,
        },
    }
    sync_run.full_clean()
    sync_run.save(update_fields=["summary"])


def _upsert_listing_from_source(
    *,
    sync_run: MarketplaceSyncRun,
    external_primary_id: str,
    external_ids: dict,
    seller_article: str = "",
    title: str = "",
    barcode: str = "",
    brand: str = "",
    category_name: str = "",
    category_external_id: str = "",
) -> tuple[MarketplaceListing, bool]:
    if not external_primary_id:
        raise MarketplaceSyncAdapterError("Marketplace listing external primary id is required.")
    external_ids = _safe_summary_value(external_ids or {})
    assert_no_secret_like_values(external_ids, field_name="marketplace listing external_ids")
    defaults = {
        "external_ids": external_ids,
        "seller_article": seller_article,
        "title": title,
        "barcode": barcode,
        "brand": brand,
        "category_name": category_name,
        "category_external_id": category_external_id,
        "listing_status": MarketplaceListing.ListingStatus.ACTIVE,
        "last_source": sync_run.source,
    }
    listing, created = MarketplaceListing.objects.select_for_update().get_or_create(
        marketplace=sync_run.marketplace,
        store=sync_run.store,
        external_primary_id=external_primary_id,
        defaults=defaults,
    )
    changed_fields: list[str] = []
    if not created:
        for field, value in defaults.items():
            if getattr(listing, field) != value:
                setattr(listing, field, value)
                changed_fields.append(field)
        if changed_fields:
            listing.full_clean()
            listing.save(update_fields=[*changed_fields, "updated_at"])
    return listing, created


def _find_existing_listing_for_wb_promotion_row(
    *,
    sync_run: MarketplaceSyncRun,
    external_primary_id: str,
    seller_article: str = "",
) -> MarketplaceListing | None:
    lookup = Q()
    if external_primary_id:
        lookup |= Q(external_primary_id=external_primary_id)
        lookup |= Q(external_ids__nmID=external_primary_id)
    if seller_article:
        lookup |= Q(seller_article=seller_article)
        lookup |= Q(external_ids__vendorCode=seller_article)
    if not lookup:
        return None

    matches = list(
        MarketplaceListing.objects.select_for_update()
        .filter(
            marketplace=sync_run.marketplace,
            store=sync_run.store,
        )
        .filter(lookup)[:2]
    )
    if len(matches) != 1:
        return None
    return matches[0]


def _normalize_wb_price_row(row) -> dict:
    data = _row_dict(row)
    nm_id = _string_value(_first_present(data, "nm_id", "nmID", "external_primary_id"))
    vendor_code = _string_value(_first_present(data, "vendor_code", "vendorCode", "seller_article"))
    external_ids = dict(data.get("external_ids") or {})
    if nm_id and "nmID" not in external_ids:
        external_ids["nmID"] = nm_id
    if vendor_code and "vendorCode" not in external_ids:
        external_ids["vendorCode"] = vendor_code
    external_ids.setdefault("source", "wb_prices_api")
    price = _decimal_or_none(_first_present(data, "derived_price", "price"))
    price_with_discount = _decimal_or_none(
        _first_present(data, "discounted_price", "discountedPrice", "price_with_discount")
    )
    discount_percent = _decimal_or_none(_first_present(data, "discount", "discount_percent"))
    return {
        "external_primary_id": nm_id,
        "seller_article": vendor_code,
        "external_ids": external_ids,
        "price": price,
        "price_with_discount": price_with_discount,
        "discount_percent": discount_percent,
        "currency": _string_value(_first_present(data, "currency", "currencyIsoCode4217")),
        "raw_safe": {
            "nmID": nm_id,
            "vendorCode": vendor_code,
            "price": str(price) if price is not None else None,
            "price_with_discount": str(price_with_discount) if price_with_discount is not None else None,
            "discount_percent": str(discount_percent) if discount_percent is not None else None,
            "currency": _string_value(_first_present(data, "currency", "currencyIsoCode4217")),
            "reason_code": data.get("reason_code"),
            "upload_ready": data.get("upload_ready"),
        },
    }


def sync_wb_price_rows_to_product_core(
    *,
    store,
    rows,
    operation=None,
    requested_by=None,
    launch_method: str = "service",
) -> MarketplaceSyncRun:
    """Upsert Product Core WB listings from already-approved Stage 2.1 price rows."""

    sync_run = start_marketplace_sync_run(
        marketplace=Marketplace.WB,
        store=store,
        sync_type=MarketplaceSyncRun.SyncType.PRICES,
        source=ListingSource.WB_API_PRICES,
        operation=operation,
        requested_by=requested_by,
        launch_method=launch_method,
        summary={"source": "wb_prices", "approved_source": WB_PRICES_ENDPOINT_CODE},
    )
    try:
        normalized_rows = [_normalize_wb_price_row(row) for row in rows]
        duplicate_articles = _detect_duplicate_articles(normalized_rows)
        skipped_count = 0
        listing_count = 0
        mapping_count = 0
        snapshot_count = 0
        warning_count = 0
        for row in normalized_rows:
            if not row["external_primary_id"]:
                warning_count += 1
                skipped_count += 1
                continue
            if row["seller_article"] in duplicate_articles:
                warning_count += 1
                skipped_count += 1
                continue
            listing, _created = _upsert_listing_from_source(
                sync_run=sync_run,
                external_primary_id=row["external_primary_id"],
                external_ids=row["external_ids"],
                seller_article=row["seller_article"],
            )
            listing_count += 1
            if api_link_listing_by_valid_article(sync_run=sync_run, listing=listing):
                mapping_count += 1
            if row["price"] is not None and row["currency"]:
                create_price_snapshot(
                    sync_run=sync_run,
                    listing=listing,
                    price=row["price"],
                    price_with_discount=row["price_with_discount"],
                    discount_percent=row["discount_percent"],
                    currency=row["currency"],
                    raw_safe={key: value for key, value in row["raw_safe"].items() if value is not None},
                    source_endpoint=WB_PRICES_ENDPOINT_CODE,
                )
                snapshot_count += 1
            else:
                warning_count += 1
        if duplicate_articles:
            duplicate_affected_count = sum(
                1 for row in normalized_rows if row["seller_article"] in duplicate_articles
            )
            _record_source_data_integrity_warning(
                sync_run=sync_run,
                duplicate_articles=duplicate_articles,
                affected_count=duplicate_affected_count,
            )
        else:
            duplicate_affected_count = 0
        return complete_marketplace_sync_run(
            sync_run,
            summary={
                "source": "wb_prices",
                "approved_source": WB_PRICES_ENDPOINT_CODE,
                "rows_count": len(normalized_rows),
                "listings_upserted_count": listing_count,
                "api_article_mapping_count": mapping_count,
                "price_snapshots_count": snapshot_count,
                "skipped_rows_count": skipped_count,
                "duplicate_external_article_count": len(duplicate_articles),
                "source_data_integrity_warning": _source_data_integrity_warning_summary(
                    duplicate_articles=duplicate_articles,
                    affected_count=duplicate_affected_count,
                ) if duplicate_articles else None,
            },
            warning_count=warning_count,
        )
    except Exception as exc:
        fail_marketplace_sync_run(
            sync_run,
            error_summary={
                "source": "wb_prices",
                "approved_source": WB_PRICES_ENDPOINT_CODE,
                "failure_class": exc.__class__.__name__,
            },
        )
        _record_deferred_auto_create_error_if_present(exc)
        raise


def _normalize_wb_promotion_row(row, *, promotion_id=None, action_name: str = "") -> dict:
    data = _row_dict(row)
    nm_id = _string_value(_first_present(data, "nm_id", "nmID", "external_primary_id"))
    action_price = _decimal_or_none(_first_present(data, "plan_price", "planPrice", "action_price"))
    return {
        "external_primary_id": nm_id,
        "seller_article": _string_value(_first_present(data, "vendor_code", "vendorCode", "seller_article")),
        "external_ids": {
            "nmID": nm_id,
            "source": "wb_promotions_api",
        },
        "marketplace_promotion_id": _string_value(
            _first_present(data, "promotion_id", "wb_promotion_id", "marketplace_promotion_id")
            or promotion_id
        ),
        "action_name": _string_value(_first_present(data, "action_name", "name") or action_name),
        "participation_status": "in_action" if bool(_first_present(data, "in_action", "inAction")) else "candidate",
        "action_price": action_price,
        "constraints": {
            "planDiscount": _first_present(data, "plan_discount", "planDiscount"),
            "discount": data.get("discount"),
            "currencyCode": _first_present(data, "currency_code", "currencyCode"),
        },
        "reason_code": _string_value(data.get("reason_code")),
    }


def sync_wb_regular_promotion_rows_to_product_core(
    *,
    store,
    rows,
    promotion_id=None,
    action_name: str = "",
    operation=None,
    requested_by=None,
    is_auto_promotion: bool = False,
    launch_method: str = "service",
) -> MarketplaceSyncRun:
    """Create WB promotion snapshots only from real regular-promotion product rows."""

    sync_run = start_marketplace_sync_run(
        marketplace=Marketplace.WB,
        store=store,
        sync_type=MarketplaceSyncRun.SyncType.PROMOTIONS,
        source=ListingSource.WB_API_PRICES,
        operation=operation,
        requested_by=requested_by,
        launch_method=launch_method,
        summary={"source": "wb_promotions", "approved_source": WB_PROMOTIONS_ENDPOINT_CODE},
    )
    try:
        if is_auto_promotion:
            return complete_marketplace_sync_run(
                sync_run,
                summary={
                    "source": "wb_promotions",
                    "approved_source": WB_PROMOTIONS_ENDPOINT_CODE,
                    "auto_promotion_without_product_rows": True,
                    "rows_count": 0,
                    "listings_upserted_count": 0,
                    "promotion_snapshots_count": 0,
                },
                warning_count=1,
            )
        normalized_rows = [
            _normalize_wb_promotion_row(row, promotion_id=promotion_id, action_name=action_name)
            for row in rows
        ]
        duplicate_articles = _detect_duplicate_articles(normalized_rows)
        skipped_count = 0
        matched_listing_count = 0
        mapping_count = 0
        snapshot_count = 0
        warning_count = 0
        missing_listing_match_count = 0
        for row in normalized_rows:
            if not row["external_primary_id"] or not row["marketplace_promotion_id"]:
                skipped_count += 1
                warning_count += 1
                continue
            if row["seller_article"] in duplicate_articles:
                skipped_count += 1
                warning_count += 1
                continue
            listing = _find_existing_listing_for_wb_promotion_row(
                sync_run=sync_run,
                external_primary_id=row["external_primary_id"],
                seller_article=row["seller_article"],
            )
            if listing is None:
                skipped_count += 1
                missing_listing_match_count += 1
                warning_count += 1
                continue
            matched_listing_count += 1
            if api_link_listing_by_valid_article(sync_run=sync_run, listing=listing):
                mapping_count += 1
            create_promotion_snapshot(
                sync_run=sync_run,
                listing=listing,
                marketplace_promotion_id=row["marketplace_promotion_id"],
                action_name=row["action_name"],
                participation_status=row["participation_status"],
                action_price=row["action_price"],
                constraints={key: value for key, value in row["constraints"].items() if value not in (None, "")},
                reason_code=row["reason_code"],
                raw_safe={
                    "nmID": row["external_primary_id"],
                    "promotion_id": row["marketplace_promotion_id"],
                    "participation_status": row["participation_status"],
                },
                source_endpoint=WB_PROMOTIONS_ENDPOINT_CODE,
            )
            snapshot_count += 1
        duplicate_affected_count = sum(
            1 for row in normalized_rows if row["seller_article"] in duplicate_articles
        )
        if duplicate_articles:
            _record_source_data_integrity_warning(
                sync_run=sync_run,
                duplicate_articles=duplicate_articles,
                affected_count=duplicate_affected_count,
            )
        return complete_marketplace_sync_run(
            sync_run,
            summary={
                "source": "wb_promotions",
                "approved_source": WB_PROMOTIONS_ENDPOINT_CODE,
                "rows_count": len(normalized_rows),
                "listings_upserted_count": 0,
                "listings_matched_count": matched_listing_count,
                "api_article_mapping_count": mapping_count,
                "promotion_snapshots_count": snapshot_count,
                "skipped_rows_count": skipped_count,
                "missing_listing_match_count": missing_listing_match_count,
                "duplicate_external_article_count": len(duplicate_articles),
                "source_data_integrity_warning": _source_data_integrity_warning_summary(
                    duplicate_articles=duplicate_articles,
                    affected_count=duplicate_affected_count,
                ) if duplicate_articles else None,
            },
            warning_count=warning_count,
        )
    except Exception as exc:
        fail_marketplace_sync_run(
            sync_run,
            error_summary={
                "source": "wb_promotions",
                "approved_source": WB_PROMOTIONS_ENDPOINT_CODE,
                "failure_class": exc.__class__.__name__,
            },
        )
        _record_deferred_auto_create_error_if_present(exc)
        raise


def _normalize_ozon_elastic_row(row, *, action_id: str, source_group: str) -> dict:
    data = _row_dict(row)
    product_id = _string_value(_first_present(data, "product_id", "id", "external_primary_id"))
    offer_id = _string_value(_first_present(data, "offer_id", "offer", "seller_article"))
    name = _string_value(_first_present(data, "name", "title"))
    action_price = _decimal_or_none(
        _first_present(data, "action_price", "current_action_price", "calculated_action_price")
    )
    external_ids = {
        "product_id": product_id,
        "offer_id": offer_id,
        "sku": _first_present(data, "sku", "fbo_sku", "fbs_sku"),
        "action_id": str(action_id),
        "source_group": source_group,
        "source": "ozon_elastic_actions_api",
    }
    return {
        "external_primary_id": product_id,
        "seller_article": offer_id,
        "title": name,
        "external_ids": {key: value for key, value in external_ids.items() if value not in (None, "")},
        "marketplace_promotion_id": str(action_id),
        "participation_status": source_group,
        "action_name": _string_value(_first_present(data, "action_name")),
        "action_price": action_price,
        "constraints": {
            "price_min_elastic": _first_present(data, "price_min_elastic", "O_price_min_elastic"),
            "price_max_elastic": _first_present(data, "price_max_elastic", "P_price_max_elastic"),
        },
        "raw_safe": {
            "action_id": str(action_id),
            "product_id": product_id,
            "offer_id": offer_id,
            "source_group": source_group,
        },
    }


def _normalize_ozon_stock_row(row, *, action_id: str) -> dict:
    data = _row_dict(row)
    product_id = _string_value(_first_present(data, "product_id", "id", "external_primary_id"))
    offer_id = _string_value(_first_present(data, "offer_id", "offer", "seller_article"))
    name = _string_value(_first_present(data, "name", "title"))
    source_group = _string_value(data.get("source_group"))
    stock_info = data.get("stock_info") if isinstance(data.get("stock_info"), dict) else {}
    stock_rows = stock_info.get("stocks") if isinstance(stock_info.get("stocks"), list) else []
    safe_stock_rows = []
    total_stock = 0
    parseable_present_count = 0
    for stock_row in stock_rows:
        if not isinstance(stock_row, dict):
            continue
        safe_row = {
            key: stock_row.get(key)
            for key in ("type", "present", "reserved")
            if stock_row.get(key) not in (None, "")
        }
        safe_stock_rows.append(_safe_summary_value(safe_row))
        present = _integer_or_none(stock_row.get("present"))
        if present is None:
            continue
        total_stock += present
        parseable_present_count += 1
    external_ids = {
        "product_id": product_id,
        "offer_id": offer_id,
        "action_id": str(action_id),
        "source_group": source_group,
        "source": "ozon_elastic_product_data_api",
    }
    return {
        "external_primary_id": product_id,
        "seller_article": offer_id,
        "title": name,
        "source_group": source_group,
        "external_ids": {key: value for key, value in external_ids.items() if value not in (None, "")},
        "stock_rows": safe_stock_rows,
        "total_stock": total_stock if parseable_present_count else None,
        "parseable_present_count": parseable_present_count,
        "raw_safe": {
            "action_id": str(action_id),
            "product_id": product_id,
            "offer_id": offer_id,
            "source_group": source_group,
            "stock_rows_count": len(safe_stock_rows),
            "stock_rows_checksum": _safe_checksum(safe_stock_rows),
        },
    }


def sync_ozon_elastic_action_rows_to_product_core(
    *,
    store,
    rows,
    action_id: str,
    source_group: str,
    operation=None,
    requested_by=None,
    launch_method: str = "service",
) -> MarketplaceSyncRun:
    """Upsert Ozon listings only for the selected Elastic action product set."""

    if source_group not in {"active", "candidate", "candidate_and_active"}:
        raise MarketplaceSyncAdapterError("Unsupported Ozon Elastic source group.")
    endpoint_code = (
        OZON_ACTION_CANDIDATES_ENDPOINT_CODE
        if source_group == "candidate"
        else OZON_ACTION_PRODUCTS_ENDPOINT_CODE
    )
    sync_run = start_marketplace_sync_run(
        marketplace=Marketplace.OZON,
        store=store,
        sync_type=MarketplaceSyncRun.SyncType.PROMOTIONS,
        source=ListingSource.OZON_API_ACTIONS,
        operation=operation,
        requested_by=requested_by,
        launch_method=launch_method,
        summary={
            "source": "ozon_elastic_actions",
            "approved_source": endpoint_code,
            "action_id": str(action_id),
            "source_group": source_group,
            "not_full_catalog": True,
        },
    )
    try:
        normalized_rows = [
            _normalize_ozon_elastic_row(row, action_id=str(action_id), source_group=source_group)
            for row in rows
        ]
        duplicate_articles = _detect_duplicate_articles(normalized_rows)
        skipped_count = 0
        listing_count = 0
        mapping_count = 0
        snapshot_count = 0
        warning_count = 0
        for row in normalized_rows:
            if not row["external_primary_id"]:
                skipped_count += 1
                warning_count += 1
                continue
            if row["seller_article"] in duplicate_articles:
                skipped_count += 1
                warning_count += 1
                continue
            listing, _created = _upsert_listing_from_source(
                sync_run=sync_run,
                external_primary_id=row["external_primary_id"],
                external_ids=row["external_ids"],
                seller_article=row["seller_article"],
                title=row["title"],
            )
            listing_count += 1
            if api_link_listing_by_valid_article(sync_run=sync_run, listing=listing):
                mapping_count += 1
            create_promotion_snapshot(
                sync_run=sync_run,
                listing=listing,
                marketplace_promotion_id=row["marketplace_promotion_id"],
                action_name=row["action_name"],
                participation_status=row["participation_status"],
                action_price=row["action_price"],
                constraints={key: value for key, value in row["constraints"].items() if value not in (None, "")},
                raw_safe=row["raw_safe"],
                source_endpoint=endpoint_code,
            )
            snapshot_count += 1
        if duplicate_articles:
            duplicate_affected_count = sum(
                1 for row in normalized_rows if row["seller_article"] in duplicate_articles
            )
            _record_source_data_integrity_warning(
                sync_run=sync_run,
                duplicate_articles=duplicate_articles,
                affected_count=duplicate_affected_count,
            )
        else:
            duplicate_affected_count = 0
        return complete_marketplace_sync_run(
            sync_run,
            summary={
                "source": "ozon_elastic_actions",
                "approved_source": endpoint_code,
                "action_id": str(action_id),
                "source_group": source_group,
                "not_full_catalog": True,
                "rows_count": len(normalized_rows),
                "listings_upserted_count": listing_count,
                "api_article_mapping_count": mapping_count,
                "promotion_snapshots_count": snapshot_count,
                "skipped_rows_count": skipped_count,
                "duplicate_external_article_count": len(duplicate_articles),
                "source_data_integrity_warning": _source_data_integrity_warning_summary(
                    duplicate_articles=duplicate_articles,
                    affected_count=duplicate_affected_count,
                ) if duplicate_articles else None,
            },
            warning_count=warning_count,
        )
    except Exception as exc:
        fail_marketplace_sync_run(
            sync_run,
            error_summary={
                "source": "ozon_elastic_actions",
                "approved_source": endpoint_code,
                "action_id": str(action_id),
                "source_group": source_group,
                "failure_class": exc.__class__.__name__,
            },
        )
        _record_deferred_auto_create_error_if_present(exc)
        raise


def sync_ozon_elastic_stock_rows_to_product_core(
    *,
    store,
    rows,
    action_id: str,
    operation=None,
    requested_by=None,
    launch_method: str = "service",
) -> MarketplaceSyncRun:
    """Write Ozon stock snapshots only for the selected Elastic product set."""

    sync_run = start_marketplace_sync_run(
        marketplace=Marketplace.OZON,
        store=store,
        sync_type=MarketplaceSyncRun.SyncType.STOCKS,
        source=ListingSource.OZON_API_ACTIONS,
        operation=operation,
        requested_by=requested_by,
        launch_method=launch_method,
        summary={
            "source": "ozon_elastic_product_data",
            "approved_source": OZON_PRODUCT_INFO_STOCKS_ENDPOINT_CODE,
            "action_id": str(action_id),
            "not_full_catalog": True,
        },
    )
    try:
        normalized_rows = [_normalize_ozon_stock_row(row, action_id=str(action_id)) for row in rows]
        duplicate_articles = _detect_duplicate_articles(normalized_rows)
        skipped_count = 0
        listing_count = 0
        mapping_count = 0
        snapshot_count = 0
        warning_count = 0
        no_parseable_present_count = 0
        for row in normalized_rows:
            if not row["external_primary_id"]:
                skipped_count += 1
                warning_count += 1
                continue
            if row["seller_article"] in duplicate_articles:
                skipped_count += 1
                warning_count += 1
                continue
            if row["total_stock"] is None:
                skipped_count += 1
                no_parseable_present_count += 1
                warning_count += 1
                continue
            listing, _created = _upsert_listing_from_source(
                sync_run=sync_run,
                external_primary_id=row["external_primary_id"],
                external_ids=row["external_ids"],
                seller_article=row["seller_article"],
                title=row["title"],
            )
            listing_count += 1
            if api_link_listing_by_valid_article(sync_run=sync_run, listing=listing):
                mapping_count += 1
            create_stock_snapshot(
                sync_run=sync_run,
                listing=listing,
                total_stock=row["total_stock"],
                stock_by_warehouse={"rows": row["stock_rows"]},
                in_way_to_client=None,
                in_way_from_client=None,
                raw_safe={key: value for key, value in row["raw_safe"].items() if value not in (None, "")},
                source_endpoint=OZON_PRODUCT_INFO_STOCKS_ENDPOINT_CODE,
            )
            snapshot_count += 1
        if duplicate_articles:
            duplicate_affected_count = sum(
                1 for row in normalized_rows if row["seller_article"] in duplicate_articles
            )
            _record_source_data_integrity_warning(
                sync_run=sync_run,
                duplicate_articles=duplicate_articles,
                affected_count=duplicate_affected_count,
            )
        else:
            duplicate_affected_count = 0
        return complete_marketplace_sync_run(
            sync_run,
            summary={
                "source": "ozon_elastic_product_data",
                "approved_source": OZON_PRODUCT_INFO_STOCKS_ENDPOINT_CODE,
                "action_id": str(action_id),
                "not_full_catalog": True,
                "rows_count": len(normalized_rows),
                "listings_upserted_count": listing_count,
                "api_article_mapping_count": mapping_count,
                "stock_snapshots_count": snapshot_count,
                "skipped_rows_count": skipped_count,
                "no_parseable_present_count": no_parseable_present_count,
                "duplicate_external_article_count": len(duplicate_articles),
                "source_data_integrity_warning": _source_data_integrity_warning_summary(
                    duplicate_articles=duplicate_articles,
                    affected_count=duplicate_affected_count,
                ) if duplicate_articles else None,
            },
            warning_count=warning_count,
        )
    except Exception as exc:
        fail_marketplace_sync_run(
            sync_run,
            error_summary={
                "source": "ozon_elastic_product_data",
                "approved_source": OZON_PRODUCT_INFO_STOCKS_ENDPOINT_CODE,
                "action_id": str(action_id),
                "failure_class": exc.__class__.__name__,
            },
        )
        _record_deferred_auto_create_error_if_present(exc)
        raise


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
