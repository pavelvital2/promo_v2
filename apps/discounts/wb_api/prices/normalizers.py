"""Normalizers for WB Prices and Discounts API 2.1.1."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


ROW_STATUS_VALID = "valid"
ROW_STATUS_WARNING = "warning"
ROW_STATUS_ERROR = "error"

REASON_VALID = "wb_api_price_row_valid"
REASON_SIZE_CONFLICT = "wb_api_price_row_size_conflict"
REASON_INVALID = "wb_api_price_row_invalid"


@dataclass(frozen=True)
class NormalizedPriceRow:
    row_no: int
    nm_id: str
    vendor_code: str
    sizes_count: int
    derived_price: Decimal | None
    currency: str
    discount: object
    club_discount: object
    discounted_price: Decimal | None
    club_discounted_price: Decimal | None
    size_conflict: bool
    row_status: str
    reason_code: str
    upload_ready: bool
    safe_message: str
    external_ids: dict
    last_values: dict
    sizes_safe: list[dict]


def _to_decimal(value) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _clean_size(size: dict) -> dict:
    return {
        "sizeID": size.get("sizeID"),
        "price": size.get("price"),
        "discountedPrice": size.get("discountedPrice"),
        "clubDiscountedPrice": size.get("clubDiscountedPrice"),
        "techSizeName": size.get("techSizeName"),
    }


def _first_decimal(values) -> Decimal | None:
    for value in values:
        decimal_value = _to_decimal(value)
        if decimal_value is not None:
            return decimal_value
    return None


def normalize_price_good(good: dict, *, row_no: int) -> NormalizedPriceRow:
    nm_id_value = good.get("nmID")
    nm_id = "" if nm_id_value is None else str(nm_id_value)
    vendor_code = "" if good.get("vendorCode") is None else str(good.get("vendorCode"))
    sizes = good.get("sizes") if isinstance(good.get("sizes"), list) else []
    sizes_safe = [_clean_size(size) for size in sizes if isinstance(size, dict)]
    prices = [_to_decimal(size.get("price")) for size in sizes if isinstance(size, dict)]
    present_prices = [price for price in prices if price is not None]
    unique_prices = set(present_prices)
    derived_price = present_prices[0] if len(unique_prices) == 1 else None

    if not nm_id or not sizes or len(present_prices) != len(sizes):
        row_status = ROW_STATUS_ERROR
        reason_code = REASON_INVALID
        upload_ready = False
        size_conflict = False
        safe_message = "WB API price row is invalid: nmID, sizes or size price is missing."
    elif len(unique_prices) > 1:
        row_status = ROW_STATUS_WARNING
        reason_code = REASON_SIZE_CONFLICT
        upload_ready = False
        size_conflict = True
        safe_message = "WB API price row has different size prices and is blocked for upload."
    else:
        row_status = ROW_STATUS_VALID
        reason_code = REASON_VALID
        upload_ready = True
        size_conflict = False
        safe_message = "WB API price row is valid."

    discounted_price = _first_decimal(size.get("discountedPrice") for size in sizes_safe)
    club_discounted_price = _first_decimal(size.get("clubDiscountedPrice") for size in sizes_safe)
    currency = "" if good.get("currencyIsoCode4217") is None else str(good.get("currencyIsoCode4217"))
    size_ids = [size.get("sizeID") for size in sizes_safe if size.get("sizeID") is not None]
    tech_size_names = [
        size.get("techSizeName")
        for size in sizes_safe
        if size.get("techSizeName") not in (None, "")
    ]

    external_ids = {
        "nmID": nm_id_value,
        "vendorCode": vendor_code,
        "sizeIDs": size_ids,
        "techSizeNames": tech_size_names,
        "source": "wb_prices_api",
    }
    last_values = {
        "price": str(derived_price) if derived_price is not None else None,
        "discount": good.get("discount"),
        "discountedPrice": str(discounted_price) if discounted_price is not None else None,
        "clubDiscount": good.get("clubDiscount"),
        "clubDiscountedPrice": str(club_discounted_price) if club_discounted_price is not None else None,
        "currencyIsoCode4217": currency,
        "editableSizePrice": good.get("editableSizePrice"),
        "isBadTurnover": good.get("isBadTurnover"),
        "upload_ready": upload_ready,
        "reason_code": reason_code,
    }
    return NormalizedPriceRow(
        row_no=row_no,
        nm_id=nm_id,
        vendor_code=vendor_code,
        sizes_count=len(sizes),
        derived_price=derived_price,
        currency=currency,
        discount=good.get("discount"),
        club_discount=good.get("clubDiscount"),
        discounted_price=discounted_price,
        club_discounted_price=club_discounted_price,
        size_conflict=size_conflict,
        row_status=row_status,
        reason_code=reason_code,
        upload_ready=upload_ready,
        safe_message=safe_message,
        external_ids=external_ids,
        last_values=last_values,
        sizes_safe=sizes_safe,
    )
