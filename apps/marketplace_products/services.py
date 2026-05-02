"""Service helpers for stage 1 marketplace product history."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.identity_access.services import has_section_access, has_store_access
from apps.product_core.models import ListingHistory, ListingSource, MarketplaceListing

from .models import MarketplaceProduct, MarketplaceProductHistory


def products_visible_to(user):
    queryset = MarketplaceProduct.objects.select_related("store", "store__group")
    if not has_section_access(user, "products.view"):
        return queryset.none()
    visible_ids = [
        product.pk
        for product in queryset
        if has_store_access(user, product.store, allow_global=True)
    ]
    return queryset.filter(pk__in=visible_ids)


def _listing_status_from_product_status(status: str) -> str:
    if status == MarketplaceProduct.Status.INACTIVE:
        return MarketplaceListing.ListingStatus.INACTIVE
    if status == MarketplaceProduct.Status.ARCHIVED:
        return MarketplaceListing.ListingStatus.ARCHIVED
    return MarketplaceListing.ListingStatus.ACTIVE


def _seller_article_from_external_ids(external_ids) -> str:
    if not isinstance(external_ids, dict):
        return ""
    for key in ("vendorCode", "vendor_code", "offer_id", "offerId"):
        value = external_ids.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def _listing_snapshot(product: MarketplaceProduct) -> dict:
    return {
        "external_ids": product.external_ids,
        "seller_article": _seller_article_from_external_ids(product.external_ids),
        "barcode": product.barcode,
        "title": product.title,
        "listing_status": _listing_status_from_product_status(product.status),
        "last_values": product.last_values,
        "first_seen_at": product.first_detected_at,
        "last_seen_at": product.last_seen_at,
        "last_source": ListingSource.MIGRATION,
    }


def _listing_history_values(listing: MarketplaceListing) -> dict:
    return {
        "external_ids": listing.external_ids,
        "seller_article": listing.seller_article,
        "barcode": listing.barcode,
        "title": listing.title,
        "listing_status": listing.listing_status,
        "mapping_status": listing.mapping_status,
        "last_values": listing.last_values,
        "first_seen_at": listing.first_seen_at.isoformat() if listing.first_seen_at else "",
        "last_seen_at": listing.last_seen_at.isoformat() if listing.last_seen_at else "",
        "last_source": listing.last_source,
    }


@transaction.atomic
def sync_listing_from_legacy_product(product: MarketplaceProduct) -> MarketplaceListing:
    external_primary_id = (product.sku or "").strip()
    defaults = _listing_snapshot(product)
    listing, created = MarketplaceListing.objects.select_for_update().get_or_create(
        marketplace=product.marketplace,
        store=product.store,
        external_primary_id=external_primary_id,
        defaults={
            **defaults,
            "mapping_status": MarketplaceListing.MappingStatus.UNMATCHED,
        },
    )

    previous = _listing_history_values(listing)
    changed_fields: list[str] = []
    if not created:
        for field, value in defaults.items():
            if field == "last_source" and listing.last_source != "":
                continue
            if getattr(listing, field) != value:
                setattr(listing, field, value)
                changed_fields.append(field)
        if changed_fields:
            listing.save(update_fields=[*changed_fields, "updated_at"])
    else:
        changed_fields = [
            "external_ids",
            "seller_article",
            "barcode",
            "title",
            "listing_status",
            "mapping_status",
            "last_values",
            "first_seen_at",
            "last_seen_at",
            "last_source",
        ]

    if created or changed_fields:
        changed_at = product.last_seen_at or product.first_detected_at or timezone.now()
        ListingHistory.objects.create(
            listing=listing,
            change_type=(
                ListingHistory.ChangeType.APPEARED
                if created
                else ListingHistory.ChangeType.UPDATED
            ),
            changed_at=changed_at,
            changed_fields=changed_fields,
            previous_values={} if created else previous,
            new_values=_listing_history_values(listing),
            source=ListingSource.MIGRATION,
        )
    return listing


def backfill_marketplace_listings_from_legacy_products() -> dict:
    created = 0
    existing = 0
    for product in MarketplaceProduct.objects.select_related("store").order_by("id"):
        before_exists = MarketplaceListing.objects.filter(
            marketplace=product.marketplace,
            store=product.store,
            external_primary_id=(product.sku or "").strip(),
        ).exists()
        sync_listing_from_legacy_product(product)
        if before_exists:
            existing += 1
        else:
            created += 1
    return {
        "legacy_products": MarketplaceProduct.objects.count(),
        "created_listings": created,
        "existing_listings": existing,
        "unmatched_backfilled_listings": MarketplaceListing.objects.filter(
            internal_variant__isnull=True,
            mapping_status=MarketplaceListing.MappingStatus.UNMATCHED,
        ).count(),
    }


def validate_legacy_product_listing_backfill() -> dict:
    missing_product_ids: list[int] = []
    mismatched_mapping_product_ids: list[int] = []
    for product in MarketplaceProduct.objects.order_by("id"):
        listing = MarketplaceListing.objects.filter(
            marketplace=product.marketplace,
            store=product.store,
            external_primary_id=(product.sku or "").strip(),
        ).first()
        if not listing:
            missing_product_ids.append(product.pk)
            continue
        if listing.internal_variant_id or listing.mapping_status != MarketplaceListing.MappingStatus.UNMATCHED:
            mismatched_mapping_product_ids.append(product.pk)
    return {
        "legacy_products": MarketplaceProduct.objects.count(),
        "missing_listing_product_ids": missing_product_ids,
        "mismatched_mapping_product_ids": mismatched_mapping_product_ids,
    }


@transaction.atomic
def record_product_from_operation_detail(operation, detail_row) -> MarketplaceProduct | None:
    product_ref = (detail_row.product_ref or "").strip()
    if not product_ref:
        return None

    input_link = operation.input_files.select_related("file_version").order_by("ordinal_no", "id").first()
    file_version = input_link.file_version if input_link else None
    now = operation.finished_at or operation.updated_at or timezone.now()
    external_ids = {operation.marketplace: product_ref}
    last_values = {
        "last_reason_code": detail_row.reason_code,
        "last_row_status": detail_row.row_status,
        "last_message_level": detail_row.message_level,
        "last_problem_field": detail_row.problem_field,
        "last_final_value": detail_row.final_value,
    }
    defaults = {
        "external_ids": external_ids,
        "sku": product_ref,
        "last_values": last_values,
        "first_detected_at": now,
        "last_seen_at": now,
    }
    product, created = MarketplaceProduct.objects.select_for_update().get_or_create(
        marketplace=operation.marketplace,
        store=operation.store,
        sku=product_ref,
        defaults=defaults,
    )
    previous = {
        "external_ids": product.external_ids,
        "title": product.title,
        "sku": product.sku,
        "barcode": product.barcode,
        "status": product.status,
        "last_values": product.last_values,
    }
    changed_fields: list[str] = []
    if not created:
        if product.external_ids != external_ids:
            product.external_ids = external_ids
            changed_fields.append("external_ids")
        if product.last_values != last_values:
            product.last_values = last_values
            changed_fields.append("last_values")
        if product.status != MarketplaceProduct.Status.ACTIVE:
            product.status = MarketplaceProduct.Status.ACTIVE
            changed_fields.append("status")
        product.last_seen_at = now
        changed_fields.append("last_seen_at")
        product.save()
    else:
        changed_fields = list(defaults)

    if created or changed_fields:
        MarketplaceProductHistory.objects.create(
            product=product,
            detected_at=now,
            operation=operation,
            file_version=file_version,
            change_type=(
                MarketplaceProductHistory.ChangeType.DETECTED
                if created
                else MarketplaceProductHistory.ChangeType.UPDATED
            ),
            changed_fields=changed_fields,
            previous_values={} if created else previous,
            new_values={
                "external_ids": product.external_ids,
                "title": product.title,
                "sku": product.sku,
                "barcode": product.barcode,
                "status": product.status,
                "last_values": product.last_values,
                "last_seen_at": product.last_seen_at.isoformat() if product.last_seen_at else "",
            },
        )
    sync_listing_from_legacy_product(product)
    return product


def sync_products_for_operation(operation) -> None:
    for detail in operation.detail_rows.all().order_by("row_no", "id"):
        record_product_from_operation_detail(operation, detail)
