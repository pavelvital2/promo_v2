"""Excel writer for WB API promotion exports."""

from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook


PROMOTION_EXPORT_COLUMNS = (
    "Артикул WB",
    "Плановая цена для акции",
    "Загружаемая скидка для участия в акции",
)


def build_promotion_export_workbook(products) -> BytesIO:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Акция"
    sheet.append(PROMOTION_EXPORT_COLUMNS)
    for row in products:
        sheet.append(
            [
                row.nm_id,
                str(row.plan_price) if row.plan_price is not None else "",
                row.plan_discount if row.plan_discount is not None else "",
            ],
        )

    raw_sheet = workbook.create_sheet("_api_raw")
    raw_sheet.append(
        [
            "promotionID",
            "nmID",
            "inAction",
            "price",
            "currencyCode",
            "planPrice",
            "discount",
            "planDiscount",
            "row_status",
            "reason_code",
            "safe_message",
        ],
    )
    for row in products:
        raw_sheet.append(
            [
                row.promotion_id,
                row.nm_id,
                row.in_action,
                str(row.price) if row.price is not None else "",
                row.currency_code,
                str(row.plan_price) if row.plan_price is not None else "",
                row.discount,
                row.plan_discount,
                row.row_status,
                row.reason_code,
                row.safe_message,
            ],
        )

    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()
    buffer.seek(0)
    return buffer
