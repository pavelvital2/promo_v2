# WB_DISCOUNTS_API_SPEC.md

Трассировка: `docs/source/stage-inputs/tz_stage_2.1.txt` §3, §8-§9, §11, §13-§16; ADR-0017, ADR-0019, ADR-0020.

## Назначение

Документ описывает WB API-режим скидок Stage 2.1: связку 2.1.1-2.1.4, расчёт по API-источникам, итоговый Excel для ручной загрузки и безопасную API-загрузку.

## Связанные документы

- Цены: `docs/product/WB_API_PRICE_EXPORT_SPEC.md`
- Акции: `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`
- Stage 1 WB logic: `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`
- API connections: `docs/architecture/API_CONNECTIONS_SPEC.md`
- File contour: `docs/architecture/FILE_CONTOUR.md`

## Flow

```text
2.1.1 price export
  -> price Excel + price snapshot + product directory
2.1.2 current promotions export
  -> promo Excel files + promotion snapshots
2.1.3 discount calculation
  -> result Excel for manual WB cabinet upload
2.1.4 API upload
  -> optional write to WB after confirmation and drift check
```

2.1.1, 2.1.2 и 2.1.3 не меняют данные в WB. 2.1.4 - единственный write step.

## 2.1.3 Calculation

Input selection:

- последний или явно выбранный successful price export 2.1.1;
- последний или явно выбранный successful current promotions export 2.1.2;
- store/account должен совпадать;
- file versions и snapshots должны быть доступны в metadata, даже если физический файл истёк по retention.

Расчёт использует общее WB calculation core Stage 1:

```text
calculated_discount = ceil((1 - max_plan_price / current_price) * 100)
final_discount_pre_threshold = MIN(min_discount, calculated_discount)

1. no promo item -> wb_fallback_no_promo_percent
2. over threshold -> wb_fallback_over_threshold_percent
3. otherwise -> final_discount_pre_threshold
```

Обязательные инварианты:

- decimal arithmetic;
- float запрещён;
- порядок правил не меняется;
- `wb_discount_out_of_range` остаётся error;
- частичная обработка workbook при range error запрещена;
- Stage 1 Excel behaviour не меняется.

## API-generated adapters

Реализация должна иметь единое ядро:

```text
WB calculation core
  <- Excel input adapter
  <- API-generated Excel / API snapshot adapter
  -> WB output writer
```

Нельзя дублировать формулу отдельно для API mode.

## Result Excel

Итоговый Excel 2.1.3:

- основан на price Excel 2.1.1;
- имеет основной лист с `Артикул WB`, `Текущая цена`, `Новая скидка`;
- записывает только `Новая скидка`;
- сохраняет порядок строк;
- не разрушает формулы и workbook structure;
- имеет checksum;
- хранится как `FileObject/FileVersion` scenario `wb_discounts_api_result_excel`;
- пригоден для ручной загрузки в ЛК WB в рамках формальной Stage 2.1 схемы price workbook.

Если заказчик позднее потребует официальный WB cabinet template шире этой схемы, это отдельное documentation change/GAP до реализации изменения.

## Data actuality

Calculation basis включает:

- store/account;
- price export operation/file version/snapshot checksum;
- promotion export operation/file versions/snapshots checksums;
- applied WB parameters;
- calculation logic version;
- current promotion filter timestamp;
- API safe snapshot checksums.

Если пользователь перескачал цены или акции, старый расчёт не становится автоматически актуальным для upload. UI должен показывать выбранную basis явно.

## 2.1.4 API upload preconditions

- Есть successful calculation 2.1.3 без errors.
- Есть upload-ready rows; size-conflict и invalid rows исключены и блокируют upload для соответствующих nmID.
- Пользователь имеет `wb.api.discounts.upload` и `wb.api.discounts.upload.confirm`.
- Пользователь имеет object access к store.
- WB API connection active.
- Пользователь прошёл explicit confirmation screen.

## Explicit confirmation

Перед upload UI показывает:

- store;
- operation расчёта;
- result file;
- дата расчёта;
- количество товаров к отправке;
- количество исключённых товаров;
- предупреждение, что скидки будут отправлены в WB по API.

Пользователь обязан явно подтвердить фразу:

```text
Я понимаю, что скидки будут отправлены в WB по API.
```

Без подтверждения API upload запрещён. Подтверждение фиксируется в audit.

## Pre-upload drift check

Перед upload система повторно получает по API текущие товары:

- endpoint: `POST /api/v2/list/goods/filter`;
- request: `nmList`, batches 1..1000 nmID;
- цель: проверить existence, price, size conflict, upload eligibility.

Проверки:

- товар существует;
- текущая price равна price snapshot расчёта;
- товар не стал size-conflict;
- товар не исключён из расчёта;
- текущая скидка может быть обновлена.

Если есть drift:

- upload запрещён;
- operation получает `completed_with_error`;
- detail rows получают `wb_api_upload_blocked_by_drift`;
- UI показывает список расхождений;
- пользователь повторяет 2.1.1-2.1.3.

## Upload payload

Endpoint: `POST /api/v2/upload/task`.

WB docs: `data` содержит максимум 1000 products; `price` и `discount` не могут быть одновременно пустыми.

Stage 2.1 отправляет discount-only payload:

```json
{
  "data": [
    {
      "nmID": 123,
      "discount": 30
    }
  ]
}
```

Normal upload payload содержит только `nmID` and `discount` for each product. Поле `price` запрещено добавлять из расчётного Excel, старого price snapshot or stale internal value.

Это решение принято для защиты от перезаписи price. Если WB API в конкретной среде отвергнет discount-only payload, реализация не должна молча отправлять старую price; нужно остановить upload, зафиксировать безопасную ошибку and escalation note for orchestrator. Автоматический fallback к payload с `price` запрещён без отдельного documentation change/audit.

## Batching

- batch size <= 1000 products;
- каждый batch имеет payload checksum;
- каждый batch получает и хранит `uploadID`;
- operation summary агрегирует batch statuses;
- partial error одного batch не скрывает status остальных batches.

## Status polling

Первый HTTP 200 не означает успех.

Contract:

1. После POST сохранить `uploadID`.
2. Проверять `GET /api/v2/history/tasks?uploadID=...`.
3. Если upload ещё processing/unprocessed, проверять `GET /api/v2/buffer/tasks?uploadID=...`.
4. При ошибках товаров получать:
   - `GET /api/v2/history/goods/task`;
   - `GET /api/v2/buffer/goods/task`.
5. Сохранять WB status, `errorText` и details в safe snapshot.

## Status mapping

| WB response/status | Operation.status | Result code |
| --- | --- | --- |
| status 3 | `completed_success` | `wb_api_upload_success` |
| status 5 | `completed_with_warnings` | `wb_api_upload_partial_error` |
| status 6 | `completed_with_error` | `wb_api_upload_all_error` |
| status 4 | `completed_with_error` | `wb_api_upload_canceled` |
| quarantine detected | status follows batch outcome | `wb_api_upload_quarantine` |
| status not resolved by polling policy | `completed_with_error` or `interrupted_failed` by uploadID presence | `wb_api_upload_status_unknown` |
| HTTP/API failure before uploadID | `interrupted_failed` | safe techlog |
| HTTP/API failure after uploadID | `completed_with_error` until status resolved | safe techlog |
| 208 already exists | do not resend blindly | use existing status if available; otherwise safe error |

## Quarantine

WB may place a product in price quarantine when the new discounted price is at least 3 times lower than the previous one. Stage 2.1 must:

- detect quarantine from upload state/details and, if needed, `GET /api/v2/quarantine/goods`;
- show quarantine rows separately in UI;
- use `wb_api_upload_quarantine`;
- not hide applied rows behind quarantine rows;
- not auto-release products from quarantine.

## Reason/result code catalog Stage 2.1

Closed catalog for WB API mode:

- `wb_api_price_download_success`
- `wb_api_price_download_failed`
- `wb_api_price_row_valid`
- `wb_api_price_row_size_conflict`
- `wb_api_price_row_invalid`
- `wb_api_promotion_current`
- `wb_api_promotion_not_current_filtered`
- `wb_api_promotion_regular`
- `wb_api_promotion_auto_no_nomenclatures`
- `wb_api_promotion_product_valid`
- `wb_api_promotion_product_invalid`
- `wb_api_calculated_from_api_sources`
- `wb_api_upload_ready`
- `wb_api_upload_blocked_by_drift`
- `wb_api_upload_sent`
- `wb_api_upload_success`
- `wb_api_upload_partial_error`
- `wb_api_upload_all_error`
- `wb_api_upload_canceled`
- `wb_api_upload_quarantine`
- `wb_api_upload_status_unknown`

Adding/renaming codes requires documentation update and ADR.

## Запреты

- Нельзя считать API upload успешным по HTTP 200.
- Нельзя выполнять upload без confirmation и drift check.
- Нельзя отправлять stale price.
- Нельзя добавлять `price` в normal upload payload; Stage 2.1 sends only `nmID` + `discount`.
- Нельзя использовать size upload or WB Club discount endpoints in Stage 2.1.
- Нельзя раскрывать token, authorization header, API key, bearer value or secret-like values in metadata/UI/audit/techlog/sensitive_details_ref/snapshots/files/reports.
