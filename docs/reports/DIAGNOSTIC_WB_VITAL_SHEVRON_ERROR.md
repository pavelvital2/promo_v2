# Diagnostic: WB Vital Shevron Check Error

Date: 2026-04-26

Scope: read-only diagnostics for WB store `Vital Shevron`; no product code or DB data changed.

## Runtime and Logs

- Gunicorn is running on port `8080`: master PID `421762`, workers `421764`, `421765`, `421766`.
- `logs/gunicorn-8080-error.log` has only startup lines at `2026-04-26 07:55:19 +0300`; no traceback or runtime error around the user action.
- `logs/gunicorn-8080-access.log` shows the relevant flow:
  - `08:26:40` `POST /stores/create/` -> created `STORE-000001`.
  - `08:27:29` `POST /stores/create/` -> created `STORE-000002`.
  - `08:28:41` `POST /marketplaces/wb/discounts/excel/` -> price file upload, redirect.
  - `08:29:01` `POST /marketplaces/wb/discounts/excel/?store=1` -> promo files upload, redirect.
  - `08:29:24` `POST /marketplaces/wb/discounts/excel/?store=1` -> check started, redirect.
  - `08:29:25` `GET /operations/OP-2026-000001/result/` -> result page rendered with HTTP 200.

## Store Records

There are two stores with the same name:

| DB id | visible_id | marketplace | status | created_at |
| --- | --- | --- | --- | --- |
| 1 | `STORE-000001` | `wb` | `active` | `2026-04-26T08:26:40+03:00` |
| 2 | `STORE-000002` | `ozon` | `active` | `2026-04-26T08:27:29+03:00` |

The failing operation belongs to WB store `STORE-000001`.

## Operation / Run

Run:

- DB id: `1`
- visible_id: `RUN-2026-000001`
- marketplace/module/mode: `wb` / `discounts_excel` / `excel`
- status: `completed`
- created_at: `2026-04-26T08:29:24+03:00`

Operation:

- DB id: `1`
- visible_id: `OP-2026-000001`
- type: `check`
- status: `completed_with_errors`
- error_count: `8`
- warning_count: `0`
- logic_version: `wb_discounts_excel_v1`
- started_at: `2026-04-26T08:29:24+03:00`
- finished_at: `2026-04-26T08:29:24+03:00`
- output files: none, as expected for `check`.
- process operation: none.

Applied WB parameters were system defaults:

- `wb_threshold_percent`: `70`, source `system:1`
- `wb_fallback_over_threshold_percent`: `55`, source `system:2`
- `wb_fallback_no_promo_percent`: `55`, source `system:3`

Summary:

- `price_rows`: `0`
- `promo_files`: `6`
- `valid_promo_files`: `0`
- `invalid_promo_rows`: `0`
- `calculated_rows`: `0`
- `error_count`: `8`
- `warning_count`: `0`

## Input Files

| role | ordinal | file_visible_id | version id | original_name | size | status |
| --- | ---: | --- | ---: | --- | ---: | --- |
| price | 1 | `FILE-2026-000001` | 1 | `1.xlsx` | 82112 | `available` |
| promo | 1 | `FILE-2026-000002` | 2 | `2.xlsx` | 47794 | `available` |
| promo | 2 | `FILE-2026-000003` | 3 | `3.xlsx` | 31340 | `available` |
| promo | 3 | `FILE-2026-000004` | 4 | `4.xlsx` | 25541 | `available` |
| promo | 4 | `FILE-2026-000005` | 5 | `5.xlsx` | 45506 | `available` |
| promo | 5 | `FILE-2026-000006` | 6 | `6.xlsx` | 7277 | `available` |
| promo | 6 | `FILE-2026-000007` | 7 | `7.xlsx` | 46075 | `available` |

All versions are linked to `OP-2026-000001` and `RUN-2026-000001`.

## Exact Errors

Detail rows for `OP-2026-000001`:

| reason_code | problem_field | message |
| --- | --- | --- |
| `wb_missing_required_column` | `required_columns` | Missing required price columns: `Артикул WB`, `Текущая цена`, `Новая скидка` |
| `wb_missing_required_column` | `promo_1:required_columns` | Missing required promo columns: `Артикул WB`, `Плановая цена для акции`, `Загружаемая скидка для участия в акции` |
| `wb_missing_required_column` | `promo_2:required_columns` | Missing required promo columns: `Артикул WB`, `Плановая цена для акции`, `Загружаемая скидка для участия в акции` |
| `wb_missing_required_column` | `promo_3:required_columns` | Missing required promo columns: `Артикул WB`, `Плановая цена для акции`, `Загружаемая скидка для участия в акции` |
| `wb_missing_required_column` | `promo_4:required_columns` | Missing required promo columns: `Артикул WB`, `Плановая цена для акции`, `Загружаемая скидка для участия в акции` |
| `wb_missing_required_column` | `promo_5:required_columns` | Missing required promo columns: `Артикул WB`, `Плановая цена для акции`, `Загружаемая скидка для участия в акции` |
| `wb_missing_required_column` | `promo_6:required_columns` | Missing required promo columns: `Артикул WB`, `Плановая цена для акции`, `Загружаемая скидка для участия в акции` |
| `wb_invalid_workbook` | `promo_files` | All promo files are invalid. |

No row-level product data is needed to explain this failure.

## Workbook Header Inspection

The WB parser uses the first worksheet and reads required headers from row 1.

| file | sheetnames | first sheet dimensions | row 1 non-empty values | required headers found in rows 1-20 |
| --- | --- | --- | --- | --- |
| `1.xlsx` | `Sheet1` | `max_row=1`, `max_column=1` | column 1: `Бренд` | none of price required headers |
| `2.xlsx` | `Отчёт по скидкам` | `max_row=1`, `max_column=1` | column 1: `Товар уже участвует в акции` | none of promo required headers |
| `3.xlsx` | `Отчёт по скидкам` | `max_row=1`, `max_column=1` | column 1: `Товар уже участвует в акции` | none of promo required headers |
| `4.xlsx` | `Отчёт по скидкам` | `max_row=1`, `max_column=1` | column 1: `Товар уже участвует в акции` | none of promo required headers |
| `5.xlsx` | `Отчёт по скидкам` | `max_row=1`, `max_column=1` | column 1: `Товар уже участвует в акции` | none of promo required headers |
| `6.xlsx` | `Отчёт по скидкам` | `max_row=1`, `max_column=1` | column 1: `Товар уже участвует в акции` | none of promo required headers |
| `7.xlsx` | `Отчёт по скидкам` | `max_row=1`, `max_column=1` | column 1: `Товар уже участвует в акции` | none of promo required headers |

## Cause Classification

Most likely cause: wrong workbook structure / wrong exported files for the implemented WB Excel scenario.

The failure occurs during check operation workbook validation, specifically required-column detection:

- Not upload transport validation: files were accepted, stored, and linked.
- Not file storage: all input versions have `physical_status=available`.
- Not permissions/object access: operation was created and result page rendered.
- Not WB discount calculation: no rows reached calculation because required headers were missing.
- Not output writing: this was a check operation and no output workbook is expected.
- Not server crash: no gunicorn error log entries and no techlog records for this store/operation.

## Recommended Next Step

Ask the user to upload WB price and promo workbooks matching the approved stage-1 column contract:

- Price file row 1 must contain exact headers: `Артикул WB`, `Текущая цена`, `Новая скидка`.
- Each promo file row 1 must contain exact headers: `Артикул WB`, `Плановая цена для акции`, `Загружаемая скидка для участия в акции`.

If the user confirms these files are the real WB exports that must be supported, route a question to the orchestrator/customer: should the WB Excel spec be extended to support this alternative WB report format where row 1 contains values like `Бренд` / `Товар уже участвует в акции` and the required stage-1 headers are absent?
