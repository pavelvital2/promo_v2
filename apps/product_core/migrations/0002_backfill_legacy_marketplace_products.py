# Generated for TASK-PC-002 on 2026-05-01

from django.db import migrations
from django.utils import timezone


def _listing_status_from_product_status(status):
    if status == "inactive":
        return "inactive"
    if status == "archived":
        return "archived"
    return "active"


def _seller_article_from_external_ids(external_ids):
    if not isinstance(external_ids, dict):
        return ""
    for key in ("vendorCode", "vendor_code", "offer_id", "offerId"):
        value = external_ids.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def _listing_history_values(listing):
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


def _forward_backfill(apps, schema_editor):
    MarketplaceProduct = apps.get_model("marketplace_products", "MarketplaceProduct")
    MarketplaceListing = apps.get_model("product_core", "MarketplaceListing")
    ListingHistory = apps.get_model("product_core", "ListingHistory")

    for product in MarketplaceProduct.objects.select_related("store").order_by("id"):
        external_primary_id = (product.sku or "").strip()
        values = {
            "external_ids": product.external_ids,
            "seller_article": _seller_article_from_external_ids(product.external_ids),
            "barcode": product.barcode,
            "title": product.title,
            "listing_status": _listing_status_from_product_status(product.status),
            "last_values": product.last_values,
            "first_seen_at": product.first_detected_at,
            "last_seen_at": product.last_seen_at,
            "last_source": "migration",
        }
        listing, created = MarketplaceListing.objects.get_or_create(
            marketplace=product.marketplace,
            store=product.store,
            external_primary_id=external_primary_id,
            defaults={
                **values,
                "mapping_status": "unmatched",
            },
        )

        previous = _listing_history_values(listing)
        changed_fields = []
        if not created:
            for field, value in values.items():
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
                change_type="appeared" if created else "updated",
                changed_at=changed_at,
                changed_fields=changed_fields,
                previous_values={} if created else previous,
                new_values=_listing_history_values(listing),
                source="migration",
            )


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace_products", "0001_initial"),
        ("product_core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(_forward_backfill, migrations.RunPython.noop),
    ]
