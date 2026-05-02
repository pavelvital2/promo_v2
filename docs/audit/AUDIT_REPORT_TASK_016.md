# AUDIT REPORT TASK-016

Task: `TASK-016 Stage 2.1 WB API UI`
Audit date: 2026-04-26
Auditor role: post-implementation UI auditor

## Verdict

PASS.

`TASK-016-D1` is closed. `TASK-017` may start from the TASK-016 UI audit perspective.

Product code was not changed by this audit. Only this audit report was created. No commit or push was performed. Real WB token files were not read or printed.

## Scope Audited

- `docs/tasks/implementation/stage-2/TASK-016-wb-api-ui-stage-2-1.md`
- `docs/tasks/implementation/stage-2/TASK-016-DESIGN-HANDOFF.md`
- `docs/audit/AUDIT_REPORT_TASK_016_DESIGN.md`
- `docs/testing/TEST_REPORT_TASK_016.md`
- `docs/testing/TEST_REPORT_TASK_016_RECHECK.md`
- Relevant Stage 2.1 sections of:
  - `docs/product/UI_SPEC.md`
  - `docs/product/OPERATIONS_SPEC.md`
  - `docs/product/PERMISSIONS_MATRIX.md`
  - `docs/architecture/API_CONNECTIONS_SPEC.md`
  - `docs/product/WB_DISCOUNTS_API_SPEC.md`
  - `docs/product/WB_API_PRICE_EXPORT_SPEC.md`
  - `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`
  - `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
  - `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
  - `docs/gaps/GAP_REGISTER.md`
  - `docs/adr/ADR_LOG.md`, ADR-0016..ADR-0020
- Changed TASK-016 UI/server dispatch files:
  - `apps/web/views.py`
  - `apps/web/urls.py`
  - `apps/web/tests.py`
  - `templates/web/marketplaces.html`
  - `templates/web/wb_api.html`
  - `templates/web/wb_api_upload_confirm.html`
  - `templates/web/operation_list.html`
  - `templates/web/_operation_table.html`
  - `templates/web/operation_card.html`
  - `apps/stores/views.py`
  - `templates/stores/store_card.html`
  - `apps/stores/templates/stores/store_card.html`

`docs/source/stage-inputs/tz_stage_2.1.txt` and the full final TZ were not bulk-read.

## Findings

No blocking findings.

No new UX/functionality GAP was identified. No question for the customer is required for TASK-016 acceptance.

## TASK-016-D1 Closure

Status: CLOSED.

Evidence:

- UI gate: `apps/web/views.py:823-829` includes `connection["connection_is_active"]` in Step 3 `can_run`; `templates/web/wb_api.html:81-96` disables the calculation submit button when `step.can_run` is false.
- Server-side dispatch gate: `apps/web/views.py:721-723` blocks crafted `action=calculate` POST before loading basis operations or calling `calculate_wb_api_discounts`.
- Recheck test: `apps/web/tests.py:483-551` covers both disabled UI state and crafted POST not calling the patched calculation service.
- Independent audit command passed:

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.web.tests.HomeSmokeTests.test_wb_api_master_requires_object_access_and_shows_active_connection apps.web.tests.HomeSmokeTests.test_wb_api_post_invokes_price_service_and_preserves_store_redirect apps.web.tests.HomeSmokeTests.test_wb_api_calculation_requires_active_connection_in_ui_and_dispatch apps.web.tests.HomeSmokeTests.test_operation_list_and_card_classify_wb_api_by_step_code apps.web.tests.HomeSmokeTests.test_wb_api_upload_confirmation_posts_exact_phrase_to_service
```

Result: PASS, 5 tests.

## Audit Checks

| Check | Result | Evidence |
| --- | --- | --- |
| WB API master route and confirmation route exist; no Ozon API route added. | PASS | `apps/web/urls.py:13-18` adds only WB API routes. `rg` found no Ozon API route/UI in changed product files. |
| Master route enforces object access and `wb.api.operation.view`. | PASS | `apps/web/views.py:628-635` selects only `_wb_api_stores()` and rejects selected stores without operation view. `_can_view_operation()` requires WB API operation view for API operation rows at `apps/web/views.py:401-407`. |
| All four Stage 2.1 actions require active WB API connection in UI/server path. | PASS | Step buttons require `connection_is_active` at `apps/web/views.py:797-845`. Price/promotions/upload services enforce active connection at `apps/discounts/wb_api/prices/services.py:64-78`, `apps/discounts/wb_api/promotions/services.py:71-85`, `apps/discounts/wb_api/upload/services.py:102-116`; calculation is now blocked in UI dispatch at `apps/web/views.py:721-723`. |
| Upload confirmation phrase flow is separate and exact. | PASS | Master opens confirmation by GET only at `templates/web/wb_api.html:99-108`; confirmation POST includes `confirmation_phrase` at `templates/web/wb_api_upload_confirm.html:25-33`; service validates exact phrase at `apps/discounts/wb_api/upload/services.py:184-186`. |
| Same-page output links are present and permission-gated. | PASS | Step cards render latest operation output links on the master at `templates/web/wb_api.html:64-75`; `_can_download_link()` uses scenario-specific download permissions via `apps/files/services.py:211-224`. |
| Operation list/card classify Stage 2.1 by `step_code`, not check/process type. | PASS | Classifier helpers are at `apps/web/views.py:382-391`; filters split Excel `type` and API `step_code` at `apps/web/views.py:1154-1157`; list/card templates show classifier and API `step_code` at `templates/web/_operation_table.html:1-13` and `templates/web/operation_card.html:12-20`. |
| Stage 1 Excel remains available and type-based. | PASS | Existing WB/Ozon Excel routes remain at `apps/web/urls.py:12,19`; marketplace page still shows WB/Ozon Excel at `templates/web/marketplaces.html:6-20`; operation `type` filtering is constrained to `mode=excel`. |
| No raw token/authorization/API key/bearer/secret display in changed UI. | PASS | WB API master renders only `[ref-set]`/`[empty]` at `templates/web/wb_api.html:29-32`; store cards also redact secret references. No real token file was accessed during audit. |

## Commands Run

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

## Residual Risk

The tester already ran the impacted suites and full suite in `docs/testing/TEST_REPORT_TASK_016_RECHECK.md` with PASS. This audit independently reran focused TASK-016 checks, `manage.py check`, and migration drift check, but did not rerun the full suite.

## TASK-017 Gate

TASK-017 may start.

Gate rationale:

- The original high-severity TASK-016-D1 defect is closed by code and recheck evidence.
- No blocking implementation defects were found in the audited TASK-016 UI scope.
- No open GAP blocks TASK-016 acceptance.
- Stage 1 Excel availability and Ozon API Stage 2.2 boundary are preserved.
