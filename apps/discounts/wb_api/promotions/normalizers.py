"""Normalizers for WB Promotions Calendar API 2.1.2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from django.utils import timezone
from django.utils.dateparse import parse_datetime


ROW_STATUS_VALID = "valid"
ROW_STATUS_INVALID = "invalid"
ROW_STATUS_BLOCKED = "blocked"

REASON_CURRENT = "wb_api_promotion_current"
REASON_NOT_CURRENT = "wb_api_promotion_not_current_filtered"
REASON_REGULAR = "wb_api_promotion_regular"
REASON_AUTO = "wb_api_promotion_auto_no_nomenclatures"
REASON_PRODUCT_VALID = "wb_api_promotion_product_valid"
REASON_PRODUCT_INVALID = "wb_api_promotion_product_invalid"


@dataclass(frozen=True)
class NormalizedPromotion:
    wb_promotion_id: int
    name: str
    promotion_type: str
    start_datetime: datetime
    end_datetime: datetime
    is_current_at_fetch: bool
    raw_safe: dict

    @property
    def is_auto(self) -> bool:
        return "auto" in self.promotion_type.lower()


@dataclass(frozen=True)
class NormalizedPromotionProduct:
    row_no: int
    promotion_id: int
    nm_id: str
    in_action: bool
    price: Decimal | None
    currency_code: str
    plan_price: Decimal | None
    discount: object
    plan_discount: object
    row_status: str
    reason_code: str
    safe_message: str
    raw_safe: dict


def parse_wb_datetime(value) -> datetime:
    parsed = parse_datetime(str(value or ""))
    if parsed is None:
        raise ValueError("WB promotion datetime is invalid.")
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, UTC)
    return parsed.astimezone(UTC)


def _to_decimal(value) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def normalize_promotion(raw: dict, *, now_utc: datetime) -> NormalizedPromotion:
    promotion_id = int(raw.get("id"))
    start_datetime = parse_wb_datetime(raw.get("startDateTime"))
    end_datetime = parse_wb_datetime(raw.get("endDateTime"))
    is_current = start_datetime <= now_utc < end_datetime
    return NormalizedPromotion(
        wb_promotion_id=promotion_id,
        name="" if raw.get("name") is None else str(raw.get("name")),
        promotion_type="" if raw.get("type") is None else str(raw.get("type")),
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        is_current_at_fetch=is_current,
        raw_safe={
            "id": promotion_id,
            "name": raw.get("name"),
            "type": raw.get("type"),
            "startDateTime": raw.get("startDateTime"),
            "endDateTime": raw.get("endDateTime"),
        },
    )


def normalize_product(raw: dict, *, row_no: int, promotion_id: int, in_action: bool) -> NormalizedPromotionProduct:
    nm_id = "" if raw.get("id") is None else str(raw.get("id"))
    plan_price = _to_decimal(raw.get("planPrice"))
    plan_discount = raw.get("planDiscount")
    valid = bool(nm_id) and plan_price is not None and plan_discount not in (None, "")
    return NormalizedPromotionProduct(
        row_no=row_no,
        promotion_id=promotion_id,
        nm_id=nm_id,
        in_action=bool(raw.get("inAction", in_action)),
        price=_to_decimal(raw.get("price")),
        currency_code="" if raw.get("currencyCode") is None else str(raw.get("currencyCode")),
        plan_price=plan_price,
        discount=raw.get("discount"),
        plan_discount=plan_discount,
        row_status=ROW_STATUS_VALID if valid else ROW_STATUS_INVALID,
        reason_code=REASON_PRODUCT_VALID if valid else REASON_PRODUCT_INVALID,
        safe_message=(
            "WB API promotion product row is valid."
            if valid
            else "WB API promotion product row is invalid: planPrice or planDiscount is missing."
        ),
        raw_safe={
            "id": raw.get("id"),
            "inAction": raw.get("inAction", in_action),
            "price": raw.get("price"),
            "currencyCode": raw.get("currencyCode"),
            "planPrice": raw.get("planPrice"),
            "discount": raw.get("discount"),
            "planDiscount": raw.get("planDiscount"),
        },
    )
