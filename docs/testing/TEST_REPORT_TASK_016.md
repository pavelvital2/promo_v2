# TEST_REPORT_TASK_016

Task: `TASK-016 Stage 2.1 WB API UI`  
Tester: Codex CLI, tester role  
Date: 2026-04-26  
Verdict: FAIL

## Scope

Checked TASK-016 UI implementation against:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-2/TASK-016-wb-api-ui-stage-2-1.md`
- `docs/tasks/implementation/stage-2/TASK-016-DESIGN-HANDOFF.md`
- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/stages/stage-2/STAGE_2_1_WB_ACCEPTANCE_TESTS.md`

Product code was not changed. Real WB token files were not read or printed. WB API calls in checked UI tests were patch/mock based.

## Results

| Area | Result |
| --- | --- |
| `manage.py check` | PASS |
| `makemigrations --check --dry-run` | PASS |
| Focused TASK-016 web UI tests | PASS |
| Impacted suites: `apps.web`, `apps.stores`, `apps.operations`, `apps.discounts.wb_api`, `apps.files`, `apps.identity_access` | PASS |
| Full suite | PASS |
| WB API route and marketplace/store entry points | PASS |
| Object access and redacted connection display | PASS |
| Price/promotions actions wired to services and permission gates | PASS by focused mocked tests and impacted suites |
| Calculation action gate | FAIL: active connection is not required by UI/server dispatch |
| Upload confirmation phrase flow | PASS by focused mocked test |
| Same-page output download links after actions where applicable | PASS by static/template review and existing file permission helpers |
| Operation list/card Stage 2.1 classification by `step_code`; Stage 1 Excel by `type` | PASS |
| Buttons/disabled/in-progress template assertions | PARTIAL: disabled buttons covered indirectly/static; no dedicated in-progress behavior test |
| No Ozon API Stage 2.2 exposure | PASS |
| Secret safety in reports/test output | PASS |

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
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.web.tests.HomeSmokeTests.test_wb_api_master_requires_object_access_and_shows_active_connection apps.web.tests.HomeSmokeTests.test_wb_api_post_invokes_price_service_and_preserves_store_redirect apps.web.tests.HomeSmokeTests.test_operation_list_and_card_classify_wb_api_by_step_code apps.web.tests.HomeSmokeTests.test_wb_api_upload_confirmation_posts_exact_phrase_to_service
```

Result: PASS. Ran 4 tests.

Note: an earlier focused attempt used a wrong class name (`apps.web.tests.WebViewsTests...`) and failed with `AttributeError`; this was a tester command error, not a product failure. The corrected focused command above passed.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.web apps.stores apps.operations apps.discounts.wb_api apps.files apps.identity_access
```

Result: PASS. Ran 126 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test
```

Result: PASS. Ran 159 tests.

## Test IDs

Test ID: TASK-016-ROUTES-ENTRYPOINTS  
Scenario: WB API master route, upload confirmation route, marketplace and store card entry points.  
Expected: WB API is separate from WB Excel; Ozon API is absent.  
Actual: `apps/web/urls.py:13-18` adds WB API routes only; `templates/web/marketplaces.html:11-15` exposes WB API next to Excel; no Ozon API route/template entry was found in the TASK-016 UI surface.  
Status: pass.

Test ID: TASK-016-OBJECT-ACCESS-REDACTION  
Scenario: user with access to one WB store and no access to another opens the WB API master.  
Expected: only accessible store is shown; connection secret is redacted.  
Actual: focused test passed. Template renders `[ref-set]` / `[empty]` at `templates/web/wb_api.html:29-32`; raw `protected_secret_ref` is not rendered there.  
Status: pass.

Test ID: TASK-016-ACTIONS-PERMISSIONS  
Scenario: price, promotions, calculation and upload UI actions.  
Expected: actions are wired to existing services and blocked by documented permissions and active connection gates.  
Actual: price and promotions dispatch to services at `apps/web/views.py:711-719`; upload confirmation dispatches at `apps/web/views.py:666-674`; focused tests passed. Calculation dispatch exists at `apps/web/views.py:721-735`, but active connection is missing from the calculation gate.  
Status: fail. Defect TASK-016-D1.

Test ID: TASK-016-CONFIRMATION  
Scenario: upload confirmation screen posts the required phrase to the upload service.  
Expected: no direct upload from master; confirmation screen supplies exact phrase.  
Actual: focused test passed. Master opens confirmation with GET form at `templates/web/wb_api.html:99-108`; confirmation POST includes `confirmation_phrase` at `templates/web/wb_api_upload_confirm.html:25-33`.  
Status: pass.

Test ID: TASK-016-OPERATION-CLASSIFIER  
Scenario: Stage 2.1 API operations in list/card and Stage 1 Excel operations.  
Expected: API operations classified by `step_code`; Excel check/process remains classified by `operation_type`.  
Actual: focused test passed. Classifier logic is at `apps/web/views.py:382-391`; list filters API by `step_code` and Excel by `type` at `apps/web/views.py:1150-1153`; table/card render classifier/step code at `templates/web/_operation_table.html:7-12` and `templates/web/operation_card.html:13-20`.  
Status: pass.

Test ID: TASK-016-FILE-LINKS  
Scenario: same-page output download links after latest operations.  
Expected: file links are shown only when physically available and user has the Stage 2.1 file permission.  
Actual: master template gates links at `templates/web/wb_api.html:64-73`; permission helper uses file scenario permission at `apps/web/views.py:417-422`.  
Status: pass by static review and impacted suite.

Test ID: TASK-016-SECRET-SAFETY  
Scenario: test/report output and rendered connection snippets.  
Expected: no real token, API key, bearer value, authorization header or secret-like value is printed.  
Actual: real WB token files were not accessed; commands did not print environment values. Checked rendered UI path uses `[ref-set]`; test output contained no real secret contents.  
Status: pass.

## Findings / Defects

Defect TASK-016-D1 - calculation action is not blocked by inactive/missing WB API connection.  
Severity: High for TASK-016 acceptance; non-destructive to WB because calculation is read/local, but it violates the required shared Stage 2.1 UI gate.

Reproduction:

1. Create or use a WB store visible to a user with `wb.api.operation.view` and `wb.api.discounts.calculate`.
2. Make the store connection absent or set it to `configured`, `check_failed`, `disabled`, `archived` or `not_configured`.
3. Create successful 2.1.1 price export and 2.1.2 current promotions export basis operations for that store.
4. Open `GET /marketplaces/wb/discounts/api/?store=<store_id>`.
5. Expected: all four Stage 2.1 action controls are blocked because connection is not `active`.
6. Actual: Step 3 can be enabled when basis operations and calculation permission exist. A crafted POST with `action=calculate`, `price_operation_id` and `promotion_operation_id` reaches `calculate_wb_api_discounts`.

Evidence:

- Handoff requires for all four steps: connection not `active` blocks read/download/calculate/upload actions.
- Price gate includes active connection at `apps/web/views.py:794-798`; promotions gate includes active connection at `apps/web/views.py:807-811`; upload gate includes active connection at `apps/web/views.py:834-840`.
- Calculation gate at `apps/web/views.py:820-825` checks store, permission and basis operations, but not `connection["connection_is_active"]`.
- The calculation button disables only when `step.can_run` is false at `templates/web/wb_api.html:81-96`, so the missing gate reaches the rendered button state.
- Server-side POST dispatch at `apps/web/views.py:721-735` calls `calculate_wb_api_discounts` without an active-connection precondition.
- The calculation service checks permission and WB store at `apps/discounts/wb_api/calculation/services.py:291-294`, but does not require an active connection before creating the operation.

No new GAP was opened; this is an implementation defect against existing TASK-016 handoff rules.

## Coverage Notes

- Current focused tests cover the happy/negative path for object access redaction, price service dispatch, operation classifier and upload confirmation phrase.
- Missing focused tests should be added for calculation disabled state with non-active connection and crafted POST rejection.
- Template-level disabled assertions for every connection status (`configured`, `check_failed`, `disabled`, `archived`, `not_configured`) are not present in the current focused tests.

## Changed Files

- `docs/testing/TEST_REPORT_TASK_016.md`

