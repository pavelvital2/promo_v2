# TEST_REPORT_TASK_014

Task: `TASK-014 Stage 2.1 WB API discount calculation Excel output`  
Tester: Codex CLI, tester role  
Date: 2026-04-26  
Verdict: PASS WITH REMARKS

## Scope

Checked TASK-014 behavior against:

- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/tasks/implementation/stage-2/TASK-014-wb-api-discount-calculation-excel-output.md`
- `docs/product/WB_DISCOUNTS_API_SPEC.md`
- `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`
- `docs/product/WB_API_PRICE_EXPORT_SPEC.md`
- `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`
- `docs/testing/TEST_REPORT_TASK_012.md`
- `docs/testing/TEST_REPORT_TASK_013_RECHECK.md`

Product code was not changed. Real WB calls and real secrets were not used. Tests were executed with the normal `.env.runtime` settings and PostgreSQL test database.

## Results

| Area | Result |
| --- | --- |
| Stage 1 WB Excel behavior unchanged through focused WB/Ozon regression | PASS |
| API calculation uses shared Stage 1 WB core for decimal + ceil and rule order | PASS |
| API result Excel is based on 2.1.1 price Excel and writes only `Новая скидка` | PASS |
| Rows/columns and extra workbook sheet are preserved in focused test | PASS |
| Basis stores selected price operation/file/checksum, selected promotion snapshot/files/checksums, `current_filter_timestamp`, WB parameter snapshot | PASS |
| Latest basis selection and explicit selected basis behavior | PASS |
| Recalculation creates a new operation and output file version | PASS |
| Uses selected/latest promotion export operation files/snapshot; no historical WBPromotionProduct scan was found | PASS |
| Operation classifier: `mode=api`, `marketplace=wb`, `step_code=wb_api_discount_calculation`, `type=not_applicable` | PASS |
| `wb_discount_out_of_range` blocks output and marks upload blocked | PASS |
| No WB API upload/write endpoint introduced in TASK-014 code paths | PASS |
| No token/header/API key/bearer/secret-like values in checked operation/audit/techlog/result file/test output | PASS |
| Test-only SQLite settings evaluation | PASS WITH REMARKS |

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
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api.calculation --verbosity 2 --noinput
```

Result: PASS. Ran 4 tests on PostgreSQL test DB.

Covered:

- `test_api_calculation_matches_stage1_logic_and_writes_result_excel_only_new_discount`
- `test_latest_basis_is_selected_and_recalculation_creates_new_operation_and_file_version`
- `test_errors_block_result_output_and_upload_basis`
- `test_secret_like_values_are_absent_from_operation_audit_techlog_and_result_file`

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api apps.operations apps.files apps.stores apps.audit apps.techlog apps.identity_access --verbosity 2 --noinput
```

Result: PASS. Ran 104 tests on PostgreSQL test DB.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_excel apps.discounts.ozon_excel --verbosity 2 --noinput
```

Result: PASS. Ran 21 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test --verbosity 1 --noinput
```

Result: PASS. Ran 145 tests.

```bash
rg -n "/api/v2/upload|upload/task|calendar/promotions/upload|promotions/upload|method=[\"']POST[\"']|\\.post\\(" apps/discounts/wb_api apps/discounts/wb_shared apps/discounts/wb_excel -g '*.py'
```

Result: PASS for TASK-014 no-write scan. No matches.

```bash
rg -n "calculation\\.test_settings|DJANGO_SETTINGS_MODULE|sqlite|sqlite3|TASK-014|TASK014" . -g '!**/__pycache__/**'
```

Result: `apps/discounts/wb_api/calculation/test_settings.py` is present as an isolated SQLite test settings module and is not referenced by default settings, `manage.py`, CI-like commands, or TASK-014 tests run above.

## Test IDs

Test ID: TASK-014-STAGE1-REGRESSION  
Scenario: Stage 1 WB/Ozon Excel regression after shared WB core extraction.  
Expected: existing WB/Ozon behavior remains green.  
Actual: `apps.discounts.wb_excel apps.discounts.ozon_excel` passed, 21 tests.  
Status: pass.

Test ID: TASK-014-SHARED-CORE  
Scenario: API calculation from 2.1.1 price Excel and 2.1.2 promo Excel with equivalent Stage 1 data.  
Expected: API result details equal Stage 1 calculation results, using decimal arithmetic, ceil and same fallback/threshold order.  
Actual: focused test compares API details to `stage1_calculate`; passed.  
Status: pass.

Test ID: TASK-014-RESULT-EXCEL  
Scenario: generated result workbook from price export with extra column/formula and `_api_raw` sheet.  
Expected: only `Новая скидка` changes; row order, other columns and workbook structure remain available.  
Actual: focused test verifies article/current price/extra column values, formula cell and `_api_raw` sheet; passed.  
Status: pass.

Test ID: TASK-014-BASIS-ACTUALITY  
Scenario: multiple price exports and repeated calculation.  
Expected: latest successful selected by default; basis stores operation/file/checksum/snapshot data; recalculation creates a new operation and file version.  
Actual: focused test verifies latest price operation, promotion operation, distinct operation IDs and distinct output file versions; basis includes promotion snapshot and file checksums.  
Status: pass.

Test ID: TASK-014-ERROR-BLOCKING  
Scenario: promo data produces `wb_discount_out_of_range`.  
Expected: calculation completes with error, no output file is produced, upload basis is blocked.  
Actual: `completed_with_error`, `error_count=1`, `upload_blocked=true`, no output file; passed.  
Status: pass.

Test ID: TASK-014-SECURITY  
Scenario: inspect operation summary/execution context, audit, techlog and generated result workbook bytes.  
Expected: no token/header/API key/bearer/secret-like values.  
Actual: focused test passed; command output did not print `.env.runtime` values or real secrets.  
Status: pass.

## Findings / Defects

No blocking TASK-014 behavioral defects found.

Remark: `apps/discounts/wb_api/calculation/test_settings.py` introduces a SQLite-only settings module for isolated local checks. It is not used by normal runtime or the executed acceptance checks, and PostgreSQL `.env.runtime` tests now pass. I do not classify it as a defect for TASK-014 behavior, but it should not be used as acceptance evidence in place of the standard `.env.runtime`/PostgreSQL suite. Keeping it is an audit/housekeeping decision.

No new GAP was opened.

## Audit Readiness

Ready for audit with the SQLite-settings remark above. TASK-014 evidence covers focused calculation behavior, Stage 1 regression, broader Stage 2.1 WB API regression, full suite, no-write scan and safe-contour checks.

## Changed Files

- `docs/testing/TEST_REPORT_TASK_014.md`

Existing implementation changes were present in the worktree before this tester report and were not modified by this check.
