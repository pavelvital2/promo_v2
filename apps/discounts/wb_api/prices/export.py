"""Excel writer for WB API price export."""

from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook


PRICE_EXPORT_COLUMNS = ("Артикул WB", "Текущая цена", "Новая скидка")


def build_price_export_workbook(rows) -> BytesIO:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Цены"
    sheet.append(PRICE_EXPORT_COLUMNS)
    for row in rows:
        sheet.append(
            [
                row.nm_id,
                str(row.derived_price) if row.derived_price is not None else "",
                "",
            ],
        )

    raw_sheet = workbook.create_sheet("_api_raw")
    raw_sheet.append(
        [
            "nmID",
            "vendorCode",
            "sizes_count",
            "derived_price",
            "discount",
            "currency",
            "size_conflict",
            "upload_ready",
            "row_status",
            "reason_code",
            "safe_message",
        ],
    )
    for row in rows:
        raw_sheet.append(
            [
                row.nm_id,
                row.vendor_code,
                row.sizes_count,
                str(row.derived_price) if row.derived_price is not None else "",
                row.discount,
                row.currency,
                row.size_conflict,
                row.upload_ready,
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
