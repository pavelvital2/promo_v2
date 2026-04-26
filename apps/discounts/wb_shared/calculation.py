"""Shared WB discount formula used by Excel and API adapters."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING


@dataclass(frozen=True)
class WbDiscountDecision:
    final_discount: int
    reason_code: str
    final_discount_pre_threshold: int | None = None


def ceil_decimal_to_int(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_CEILING))


def decide_wb_discount(
    *,
    current_price: Decimal,
    min_discount: Decimal | None,
    max_plan_price: Decimal | None,
    threshold_percent: Decimal,
    fallback_no_promo_percent: Decimal,
    fallback_over_threshold_percent: Decimal,
) -> WbDiscountDecision:
    if min_discount is None or max_plan_price is None:
        return WbDiscountDecision(
            final_discount=ceil_decimal_to_int(fallback_no_promo_percent),
            reason_code="wb_no_promo_item",
        )

    calculated_discount = ceil_decimal_to_int(
        (Decimal("1") - max_plan_price / current_price) * Decimal("100")
    )
    final_discount_pre_threshold = min(
        ceil_decimal_to_int(min_discount),
        calculated_discount,
    )
    if Decimal(final_discount_pre_threshold) > threshold_percent:
        return WbDiscountDecision(
            final_discount=ceil_decimal_to_int(fallback_over_threshold_percent),
            reason_code="wb_over_threshold",
            final_discount_pre_threshold=final_discount_pre_threshold,
        )
    return WbDiscountDecision(
        final_discount=final_discount_pre_threshold,
        reason_code="wb_valid_calculated",
        final_discount_pre_threshold=final_discount_pre_threshold,
    )
