# TEST_REPORT_TASK_012.md

Task: `TASK-012 Stage 2.1 WB API prices download`
Tester: Codex CLI, tester role
Date: 2026-04-26
Verdict: PASS

## Scope

Checked implementation against:

- `docs/tasks/implementation/stage-2/TASK-012-wb-api-prices-download.md`
- `docs/product/WB_API_PRICE_EXPORT_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/testing/TEST_REPORT_TASK_011_RECHECK.md`

Product code was not changed. Real WB calls and real secrets were not used.

## Results

| Area | Result |
| --- | --- |
| Prices pagination `GET /api/v2/list/goods/filter`, `limit=1000`, offsets until empty page | PASS |
| No WB write endpoints in TASK-012 flow | PASS |
| Operation classifier: `mode=api`, `marketplace=wb`, `step_code=wb_api_prices_download`, type not check/process | PASS |
| Excel schema: main sheet columns `Артикул WB`, `Текущая цена`, `Новая скидка`; diagnostics isolated on `_api_raw` | PASS |
| Equal price / missing sizes or price / different size prices | PASS |
| Size conflict visible and not upload-ready | PASS |
| Product directory and product history update for selected WB store | PASS |
| `FileObject/FileVersion` output scenario `wb_discounts_api_price_export` and operation output link | PASS |
| Permission, object access and active WB API connection prerequisite | PASS |
| Secret redaction in operation summary/snapshot, audit, techlog and test output | PASS |
| Stage 1 WB/Ozon Excel regression | PASS |
| Full Django suite | PASS |

## Commands And Results

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check
```

Result: PASS. `System check identified no issues (0 silenced).`

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
```

Result: PASS. `No changes detected`.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api apps.discounts.wb_api.prices apps.marketplace_products apps.operations apps.files apps.stores apps.audit apps.techlog apps.identity_access --verbosity 2 --noinput
```

Result: PASS. Ran 91 tests.

Focused TASK-012 coverage included:

- `test_download_paginates_to_empty_page_exports_excel_and_updates_products`
- `test_normalizer_size_rules_equal_conflict_and_invalid`
- `test_permission_and_object_access_required`
- `test_active_connection_required`
- `test_secret_redaction_in_operation_audit_techlog_and_snapshots`
- `test_api_failure_writes_safe_techlog_and_failed_operation`
- `test_operation_classifier_contract_rejects_check_process_for_api_step`

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_excel apps.discounts.ozon_excel --verbosity 2 --noinput
```

Result: PASS. Ran 21 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test --verbosity 1 --noinput
```

Result: PASS. Ran 132 tests.

```bash
rg -n "urlopen\(|requests\.|httpx\.|aiohttp|POST|upload|/api/v2/upload|list_goods_filter|Authorization" apps/discounts/wb_api apps/stores -g '*.py'
```

Result: PASS for TASK-012 no-write check. The prices flow uses read-only `list_goods_filter`; no WB upload/write endpoint was found in `apps/discounts/wb_api/prices/`.

## Test IDs

Test ID: TASK-012-PAGINATION  
Scenario: mocked prices pages with data page then empty page.  
Expected: `limit=1000`, offsets `0`, `1000`, stop on empty `listGoods`.  
Actual: focused test verified calls exactly.  
Status: pass.

Test ID: TASK-012-EXCEL-SCHEMA  
Scenario: generated price export from mocked API data.  
Expected: main sheet compatible with Stage 1 parser: `Артикул WB`, `Текущая цена`, `Новая скидка`; diagnostics must not break parser.  
Actual: main sheet has required columns; `_api_raw` carries diagnostics.  
Status: pass.

Test ID: TASK-012-SIZE-RULES  
Scenario: equal size prices, missing sizes, conflicting size prices.  
Expected: valid row for equal prices; `wb_api_price_row_invalid` for missing sizes/price; `wb_api_price_row_size_conflict` and not upload-ready for conflicts.  
Actual: focused normalizer and integration tests verified all cases.  
Status: pass.

Test ID: TASK-012-ACCESS-CONNECTION  
Scenario: user without object access, direct permission deny, inactive connection.  
Expected: download denied.  
Actual: `PermissionDenied` raised before API execution.  
Status: pass.

Test ID: TASK-012-SECRET-REDACTION  
Scenario: operation with runtime-resolved bearer token and safe snapshots/audit/techlog.  
Expected: no token/header/API key/bearer/secret-like values outside protected secret flow.  
Actual: focused test verified operation `execution_context`, summary, audit, techlog and test output are safe.  
Status: pass.

## Findings / Defects

No TASK-012 behavioral defects found.

No GAP/escalation was opened.

## Audit Readiness

Ready for audit. The required TASK-012 behavior is covered by passing focused tests, Stage 1 WB/Ozon regression and full suite. Token/header/API key/bearer/secret-like values were not printed or persisted in checked safe contours.

## Changed Files

- `docs/testing/TEST_REPORT_TASK_012.md`

Existing implementation changes were already present in the worktree before this tester report and were not modified by this check.
