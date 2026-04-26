"""Service helpers for stage 1 marketplace product history."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.identity_access.services import has_section_access, has_store_access

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
    return product


def sync_products_for_operation(operation) -> None:
    for detail in operation.detail_rows.all().order_by("row_no", "id"):
        record_product_from_operation_detail(operation, detail)
