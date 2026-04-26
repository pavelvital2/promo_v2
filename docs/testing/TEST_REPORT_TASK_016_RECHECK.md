# TEST_REPORT_TASK_016_RECHECK

Task: `TASK-016 Stage 2.1 WB API UI`  
Recheck target: `TASK-016-D1` after executor fix  
Tester: Codex CLI, tester role  
Date: 2026-04-26  
Verdict: PASS

## Scope

Rechecked the previously failed `TASK-016-D1` from `docs/testing/TEST_REPORT_TASK_016.md`:

- Step 3 `calculate` requires active WB API connection in UI button state.
- Crafted server-side POST with `action=calculate` is blocked before dispatch when connection is not `active`.
- Other TASK-016 UI functions remain covered by focused and impacted regression tests.

Product code was not changed during recheck. Real WB token files were not read or printed. WB API service calls in focused UI tests were patch/mock based.

## Results

| Area | Result |
| --- | --- |
| `manage.py check` | PASS |
| `makemigrations --check --dry-run` | PASS |
| Focused TASK-016 UI tests | PASS |
| Impacted suites: `apps.web`, `apps.stores`, `apps.operations`, `apps.discounts.wb_api`, `apps.files`, `apps.identity_access` | PASS |
| Full suite | PASS |
| `TASK-016-D1` active connection gate | PASS |
| Other TASK-016 UI functions | PASS by focused and impacted suites |
| Secret safety during recheck | PASS |

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
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.web.tests.HomeSmokeTests.test_wb_api_master_requires_object_access_and_shows_active_connection apps.web.tests.HomeSmokeTests.test_wb_api_post_invokes_price_service_and_preserves_store_redirect apps.web.tests.HomeSmokeTests.test_wb_api_calculation_requires_active_connection_in_ui_and_dispatch apps.web.tests.HomeSmokeTests.test_operation_list_and_card_classify_wb_api_by_step_code apps.web.tests.HomeSmokeTests.test_wb_api_upload_confirmation_posts_exact_phrase_to_service
```

Result: PASS. Ran 5 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.web apps.stores apps.operations apps.discounts.wb_api apps.files apps.identity_access
```

Result: PASS. Ran 127 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test
```

Result: PASS. Ran 160 tests.

## Recheck Evidence

Test ID: TASK-016-D1-RECHECK-UI-GATE  
Scenario: WB API master has successful price and current promotion basis operations, but selected store connection is `configured`, not `active`.  
Expected: Step 3 calculation action is disabled and the page explains that Stage 2.1 actions require active connection.  
Actual: focused test `test_wb_api_calculation_requires_active_connection_in_ui_and_dispatch` passed. `apps/web/views.py` includes `connection["connection_is_active"]` in Step 3 `can_run`; `templates/web/wb_api.html` disables the calculation button when `step.can_run` is false.  
Status: pass.

Test ID: TASK-016-D1-RECHECK-SERVER-GATE  
Scenario: crafted POST sends `action=calculate` with valid successful basis operation IDs while connection is not `active`.  
Expected: calculation service is not called; response stays on master with a safe active-connection error.  
Actual: focused test passed. `apps/web/views.py` checks `connection_is_active` before loading basis operations and before calling `calculate_wb_api_discounts`; patched calculation service was not called.  
Status: pass.

Test ID: TASK-016-RECHECK-OTHER-UI  
Scenario: object access/redaction, price action dispatch, operation classifier by `step_code`, upload confirmation phrase and related TASK-016 UI paths.  
Expected: behavior from the original passing TASK-016 areas remains green.  
Actual: focused TASK-016 tests passed; impacted suites and full suite passed.  
Status: pass.

Test ID: TASK-016-RECHECK-SECRET-SAFETY  
Scenario: recheck commands and report generation.  
Expected: no token/header/API key/bearer/secret-like value is printed; real WB token file is not read.  
Actual: `.env.runtime` was sourced only for Django commands, environment values were not printed, real WB token files were not accessed, and WB API service calls in focused UI tests were mocked.  
Status: pass.

## Defects

No open defects found in this recheck.

`TASK-016-D1` status: closed by recheck.

## Changed Files

- `docs/testing/TEST_REPORT_TASK_016_RECHECK.md`
