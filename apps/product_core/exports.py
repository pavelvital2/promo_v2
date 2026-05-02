"""CSV exports for Product Core boundary reports."""

from __future__ import annotations

import csv
import json

from django.db.models import Count
from django.http import HttpResponse

from apps.discounts.wb_api.redaction import redact
from apps.identity_access.services import has_permission

from .models import InternalProduct, Marketplace, MarketplaceListing, ProductVariant
from .services import marketplace_listings_visible_to


CSV_CONTENT_TYPE = "text/csv; charset=utf-8"


def _csv_response(filename: str, headers: list[str], rows) -> HttpResponse:
    response = HttpResponse(content_type=CSV_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(["" if value is None else value for value in row])
    return response


def _json_safe(value) -> str:
    return json.dumps(redact(value or {}), ensure_ascii=False, sort_keys=True)


def _dt(value) -> str:
    return value.isoformat() if value else ""


def _attach_visible_listing_counts(user, products) -> None:
    product_ids = [product.pk for product in products]
    counts = {product_id: {Marketplace.WB: 0, Marketplace.OZON: 0} for product_id in product_ids}
    if product_ids:
        rows = (
            marketplace_listings_visible_to(user)
            .filter(internal_variant__product_id__in=product_ids)
            .values("internal_variant__product_id", "marketplace")
            .annotate(total=Count("id"))
        )
        for row in rows:
            counts[row["internal_variant__product_id"]][row["marketplace"]] = row["total"]
    for product in products:
        product.visible_wb_listing_count = counts.get(product.pk, {}).get(Marketplace.WB, 0)
        product.visible_ozon_listing_count = counts.get(product.pk, {}).get(Marketplace.OZON, 0)


def internal_products_csv(user, queryset) -> HttpResponse:
    products = list(
        queryset.select_related("category").annotate(
            export_variant_count=Count("variants", distinct=True),
        )
    )
    _attach_visible_listing_counts(user, products)
    headers = [
        "internal_code",
        "name",
        "product_type",
        "category",
        "status",
        "variant_count",
        "visible_wb_listing_count",
        "visible_ozon_listing_count",
        "updated_at",
    ]
    rows = (
        [
            product.internal_code,
            product.name,
            product.get_product_type_display(),
            product.category.name if product.category_id else "",
            product.get_status_display(),
            product.export_variant_count,
            product.visible_wb_listing_count,
            product.visible_ozon_listing_count,
            _dt(product.updated_at),
        ]
        for product in products
    )
    return _csv_response("product_core_internal_products.csv", headers, rows)


def _listing_base_row(listing: MarketplaceListing, *, include_latest: bool) -> list:
    variant: ProductVariant | None = listing.internal_variant
    product: InternalProduct | None = variant.product if variant else None
    row = [
        listing.get_marketplace_display(),
        listing.store.visible_id,
        listing.store.name,
        listing.external_primary_id,
        listing.seller_article,
        listing.barcode,
        listing.title,
        listing.brand,
        listing.category_name,
        listing.get_listing_status_display(),
        listing.get_mapping_status_display(),
        product.internal_code if product else "",
        product.name if product else "",
        variant.internal_sku if variant else "",
        variant.name if variant else "",
    ]
    if include_latest:
        values = listing.export_last_values if getattr(listing, "can_export_snapshot_values", False) else {}
        row.extend(
            [
                values.get("price", ""),
                values.get("price_with_discount", ""),
                values.get("discount_percent", ""),
                values.get("currency", ""),
                values.get("total_stock", ""),
                values.get("price_snapshot_at", ""),
                values.get("stock_snapshot_at", ""),
                _json_safe(values),
            ]
        )
    row.extend([_dt(listing.last_successful_sync_at), listing.get_last_source_display(), _dt(listing.updated_at)])
    return row


def _prepare_listing_export(user, queryset):
    listings = list(
        queryset.select_related("store", "internal_variant", "internal_variant__product")
    )
    return [
        listing
        for listing in listings
        if has_permission(user, "marketplace_listing.export", listing.store)
    ]


def _attach_snapshot_access(user, listings) -> None:
    for listing in listings:
        listing.can_export_snapshot_values = has_permission(
            user,
            "marketplace_snapshot.view",
            listing.store,
        )
        listing.export_last_values = redact(listing.last_values or {})


def marketplace_listings_csv(user, queryset, *, filename: str, include_latest: bool = False) -> HttpResponse:
    listings = _prepare_listing_export(user, queryset)
    if include_latest:
        _attach_snapshot_access(user, listings)
    headers = [
        "marketplace",
        "store_visible_id",
        "store_name",
        "external_primary_id",
        "seller_article",
        "barcode",
        "title",
        "brand",
        "category_name",
        "listing_status",
        "mapping_status",
        "internal_product_code",
        "internal_product_name",
        "internal_variant_sku",
        "internal_variant_name",
    ]
    if include_latest:
        headers.extend(
            [
                "latest_price",
                "latest_price_with_discount",
                "latest_discount_percent",
                "latest_currency",
                "latest_total_stock",
                "price_snapshot_at",
                "stock_snapshot_at",
                "last_values_json_redacted",
            ]
        )
    headers.extend(["last_successful_sync_at", "last_source", "updated_at"])
    rows = (_listing_base_row(listing, include_latest=include_latest) for listing in listings)
    return _csv_response(filename, headers, rows)


def mapping_report_csv(user, queryset) -> HttpResponse:
    listings = _prepare_listing_export(user, queryset)
    headers = [
        "marketplace",
        "store_visible_id",
        "store_name",
        "external_primary_id",
        "seller_article",
        "barcode",
        "title",
        "mapping_status",
        "internal_product_code",
        "internal_product_name",
        "internal_variant_sku",
        "internal_variant_name",
        "last_successful_sync_at",
        "last_source",
    ]
    rows = (
        [
            listing.get_marketplace_display(),
            listing.store.visible_id,
            listing.store.name,
            listing.external_primary_id,
            listing.seller_article,
            listing.barcode,
            listing.title,
            listing.get_mapping_status_display(),
            listing.internal_variant.product.internal_code if listing.internal_variant_id else "",
            listing.internal_variant.product.name if listing.internal_variant_id else "",
            listing.internal_variant.internal_sku if listing.internal_variant_id else "",
            listing.internal_variant.name if listing.internal_variant_id else "",
            _dt(listing.last_successful_sync_at),
            listing.get_last_source_display(),
        ]
        for listing in listings
    )
    return _csv_response("product_core_mapping_report.csv", headers, rows)
