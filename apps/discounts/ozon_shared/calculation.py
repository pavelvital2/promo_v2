"""Shared Ozon Elastic Boosting 7-rule calculation engine."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


OZON_BUSINESS_REASON_CODES = {
    "missing_min_price",
    "no_stock",
    "no_boost_prices",
    "use_max_boost_price",
    "use_min_price",
    "below_min_price_threshold",
    "insufficient_ozon_input_data",
}


@dataclass(frozen=True)
class OzonRowDecision:
    row_no: int
    reason_code: str
    participates: bool
    final_price: Decimal | None
    min_price: Decimal | None
    min_boost_price: Decimal | None
    max_boost_price: Decimal | None
    stock: Decimal | None

    def final_value_payload(self) -> dict:
        payload = {
            "participates": self.participates,
            "final_price": decimal_to_json(self.final_price),
            "min_price": decimal_to_json(self.min_price),
            "min_boost_price": decimal_to_json(self.min_boost_price),
            "max_boost_price": decimal_to_json(self.max_boost_price),
            "stock": decimal_to_json(self.stock),
        }
        return {key: value for key, value in payload.items() if value is not None}


def decimal_to_json(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def parse_decimal(value) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value if value.is_finite() else None
    text = str(value).replace(" ", "").replace("\u00a0", "").replace(",", ".").strip()
    if not text:
        return None
    try:
        decimal = Decimal(text)
    except InvalidOperation:
        return None
    return decimal if decimal.is_finite() else None


def message_for_code(code: str) -> str:
    return {
        "missing_min_price": "Minimum allowed price is missing.",
        "no_stock": "Stock is missing or non-positive.",
        "no_boost_prices": "Both boost prices are missing.",
        "use_max_boost_price": "Max boost price is used as final promo price.",
        "use_min_price": "Minimum allowed price is used as final promo price.",
        "below_min_price_threshold": "Minimum boost price is below minimum allowed price.",
        "insufficient_ozon_input_data": "Input data is insufficient for Ozon decision rules.",
    }[code]


def problem_field_for_decision(decision: OzonRowDecision) -> str:
    return {
        "missing_min_price": "J",
        "no_stock": "R",
        "no_boost_prices": "O/P",
        "below_min_price_threshold": "O",
        "insufficient_ozon_input_data": "O/P",
    }.get(decision.reason_code, "")


def decide_ozon_row(
    *,
    row_no: int,
    min_price: Decimal | None,
    min_boost_price: Decimal | None,
    max_boost_price: Decimal | None,
    stock: Decimal | None,
) -> OzonRowDecision:
    if min_price is None:
        reason_code = "missing_min_price"
        final_price = None
    elif stock is None or stock <= 0:
        reason_code = "no_stock"
        final_price = None
    elif min_boost_price is None and max_boost_price is None:
        reason_code = "no_boost_prices"
        final_price = None
    elif max_boost_price is not None and max_boost_price >= min_price:
        reason_code = "use_max_boost_price"
        final_price = max_boost_price
    elif (
        max_boost_price is not None
        and min_boost_price is not None
        and max_boost_price < min_price
        and min_boost_price >= min_price
    ):
        reason_code = "use_min_price"
        final_price = min_price
    elif min_boost_price is not None and min_boost_price < min_price:
        reason_code = "below_min_price_threshold"
        final_price = None
    else:
        reason_code = "insufficient_ozon_input_data"
        final_price = None

    return OzonRowDecision(
        row_no=row_no,
        reason_code=reason_code,
        participates=final_price is not None,
        final_price=final_price,
        min_price=min_price,
        min_boost_price=min_boost_price,
        max_boost_price=max_boost_price,
        stock=stock,
    )
