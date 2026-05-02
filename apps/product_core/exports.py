"""CSV exports for Product Core boundary reports."""

from __future__ import annotations

import csv
import json

from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponse

from apps.discounts.wb_api.redaction import redact
from apps.identity_access.services import has_permission
from apps.operations.listing_enrichment import resolve_listing_for_detail_row

from .models import (
    InternalProduct,
    Marketplace,
    MarketplaceListing,
    ProductMappingHistory,
    ProductVariant,
)
from .services import marketplace_listings_visible_to


CSV_CONTENT_TYPE = "text/csv; charset=utf-8"
RAW_EXPORT_KEY_MARKERS = (
    "rawsafe",
    "rawsensitive",
    "rawrequest",
    "rawresponse",
    "requestheaders",
    "responseheaders",
    "stacktrace",
    "traceback",
)


def _csv_response(filename: str, headers: list[str], rows) -> HttpResponse:
    response = HttpResponse(content_type=CSV_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(["" if value is None else value for value in row])
    return response


def _is_raw_export_key(key) -> bool:
    normalized = "".join(character for character in str(key).lower() if character.isalnum())
    return any(marker in normalized for marker in RAW_EXPORT_KEY_MARKERS)


def _strip_raw_export_keys(value):
    if isinstance(value, dict):
        sanitized = {}
        redacted_index = 1
        for key, child in value.items():
            if _is_raw_export_key(key):
                sanitized[f"redacted_field_{redacted_index}"] = "[redacted]"
                redacted_index += 1
            else:
                sanitized[key] = _strip_raw_export_keys(child)
        return sanitized
    if isinstance(value, list):
        return [_strip_raw_export_keys(child) for child in value]
    return value


def _redact_export_json(value):
    return _strip_raw_export_keys(redact(value or {}))


def _json_safe(value) -> str:
    return json.dumps(_redact_export_json(value), ensure_ascii=False, sort_keys=True)


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


def _can_export_internal_product_identifiers(user) -> bool:
    return has_permission(user, "product_core.view") and has_permission(user, "product_variant.view")


def _can_export_internal_variant_identifiers(user) -> bool:
    return has_permission(user, "product_core.view") and has_permission(user, "product_variant.view")


def _latest_value(values: dict, *keys: str):
    for key in keys:
        if key in values:
            return values.get(key)
    return ""


def _listing_base_row(user, listing: MarketplaceListing, *, include_latest: bool) -> list:
    variant: ProductVariant | None = listing.internal_variant
    product: InternalProduct | None = variant.product if variant else None
    can_show_product = _can_export_internal_product_identifiers(user)
    can_show_variant = _can_export_internal_variant_identifiers(user)
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
        product.internal_code if product and can_show_product else "",
        product.name if product and can_show_product else "",
        variant.internal_sku if variant and can_show_variant else "",
        variant.name if variant and can_show_variant else "",
    ]
    if include_latest:
        values = listing.export_last_values
        row.extend(
            [
                _latest_value(values, "price", "latest_price"),
                _latest_value(values, "price_with_discount", "latest_price_with_discount"),
                _latest_value(values, "discount_percent", "latest_discount_percent"),
                _latest_value(values, "currency"),
                _latest_value(values, "total_stock", "stock_total", "latest_stock_total"),
                _latest_value(values, "promotion_action_id", "action_id", "latest_promotion_action_id"),
                _latest_value(values, "promotion_status", "action_status", "latest_promotion_status"),
                _latest_value(values, "price_snapshot_at", "latest_price_snapshot_at"),
                _latest_value(values, "stock_snapshot_at", "latest_stock_snapshot_at"),
                _latest_value(values, "promotion_snapshot_at", "latest_promotion_snapshot_at"),
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
        listing.export_last_values = _redact_export_json(listing.last_values or {})


def marketplace_listings_csv(user, queryset, *, filename: str, include_latest: bool = False) -> HttpResponse:
    listings = _prepare_listing_export(user, queryset)
    if include_latest:
        _attach_snapshot_access(user, listings)
        listings = [listing for listing in listings if listing.can_export_snapshot_values]
        if not listings:
            raise PermissionDenied("No snapshot view permission for latest-values export rows.")
    headers = [
        "marketplace",
        "store_visible_id",
        "store_name",
        "external_primary_id",
        "seller_article",
        "barcode",
        "title",
        "brand",
        "category",
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
                "currency",
                "latest_stock_total",
                "latest_promotion_action_id",
                "latest_promotion_status",
                "latest_price_snapshot_at",
                "latest_stock_snapshot_at",
                "latest_promotion_snapshot_at",
                "last_values_json_redacted",
            ]
        )
    headers.extend(["last_successful_sync_at", "last_source", "updated_at"])
    rows = (_listing_base_row(user, listing, include_latest=include_latest) for listing in listings)
    return _csv_response(filename, headers, rows)


def _latest_mapping_history(listing: MarketplaceListing) -> ProductMappingHistory | None:
    return listing.mapping_history.order_by("-changed_at", "-id").first()


def _mapping_conflict_class(history: ProductMappingHistory | None) -> str:
    if not history or history.action != ProductMappingHistory.MappingAction.CONFLICT_MARKER:
        return ""
    context = history.source_context if isinstance(history.source_context, dict) else {}
    return context.get("conflict_class", "") or context.get("basis", "")


def mapping_report_csv(user, queryset) -> HttpResponse:
    listings = _prepare_listing_export(user, queryset)
    can_show_product = _can_export_internal_product_identifiers(user)
    can_show_variant = _can_export_internal_variant_identifiers(user)
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
        "variant_review_state",
        "latest_mapping_action",
        "latest_mapping_changed_at",
        "latest_mapping_reason_comment",
        "conflict_class",
        "last_successful_sync_at",
        "last_source",
    ]
    rows = []
    for listing in listings:
        variant = listing.internal_variant
        product = variant.product if variant else None
        history = _latest_mapping_history(listing)
        rows.append(
            [
                listing.get_marketplace_display(),
                listing.store.visible_id,
                listing.store.name,
                listing.external_primary_id,
                listing.seller_article,
                listing.barcode,
                listing.title,
                listing.get_mapping_status_display(),
                product.internal_code if product and can_show_product else "",
                product.name if product and can_show_product else "",
                variant.internal_sku if variant and can_show_variant else "",
                variant.name if variant and can_show_variant else "",
                variant.get_review_state_display() if variant and can_show_variant else "",
                history.get_action_display() if history else "",
                _dt(history.changed_at) if history else "",
                history.reason_comment if history else "",
                _mapping_conflict_class(history),
                _dt(listing.last_successful_sync_at),
                listing.get_last_source_display(),
            ]
        )
    return _csv_response("product_core_mapping_report.csv", headers, rows)


def operation_link_report_csv(user, queryset) -> HttpResponse:
    rows = []
    can_show_variant = _can_export_internal_variant_identifiers(user)
    detail_rows = queryset.select_related(
        "operation",
        "operation__store",
        "marketplace_listing",
        "marketplace_listing__store",
        "marketplace_listing__internal_variant",
        "marketplace_listing__internal_variant__product",
    )
    for detail_row in detail_rows:
        operation = detail_row.operation
        if not has_permission(user, "marketplace_listing.view", operation.store):
            continue
        if not has_permission(user, "marketplace_listing.export", operation.store):
            continue
        listing = detail_row.marketplace_listing
        if listing is not None:
            if not has_permission(user, "marketplace_listing.view", listing.store):
                continue
            if not has_permission(user, "marketplace_listing.export", listing.store):
                continue
        result = resolve_listing_for_detail_row(detail_row)
        enrichment_status = "linked" if listing is not None else "not_linked"
        conflict_reason = result.conflict_class
        if conflict_reason:
            enrichment_status = "conflict"
        rows.append(
            [
                operation.visible_id,
                operation.get_marketplace_display(),
                operation.store.visible_id,
                operation.step_code or operation.operation_type,
                detail_row.row_no,
                detail_row.product_ref,
                detail_row.row_status,
                detail_row.reason_code,
                listing.external_primary_id if listing else "",
                listing.seller_article if listing else "",
                (
                    listing.internal_variant.internal_sku
                    if listing and listing.internal_variant_id and can_show_variant
                    else ""
                ),
                enrichment_status,
                conflict_reason,
            ]
        )
    headers = [
        "operation_visible_id",
        "marketplace",
        "store_visible_id",
        "step_code_or_type",
        "row_number",
        "raw_product_ref",
        "row_status",
        "reason_result_code",
        "linked_listing_external_primary_id",
        "linked_listing_seller_article",
        "linked_variant_internal_sku",
        "enrichment_status",
        "conflict_reason",
    ]
    return _csv_response("product_core_operation_link_report.csv", headers, rows)
