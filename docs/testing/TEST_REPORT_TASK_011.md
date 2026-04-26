# TEST_REPORT_TASK_011.md

Task: `TASK-011 Stage 2.1 WB API connections`  
Tester: Codex CLI, tester role  
Date: 2026-04-26 12:56 MSK  
Verdict: PASS WITH REMARKS

## Scope

Checked against:

- `AGENTS.md`
- `docs/orchestration/AGENTS.md`
- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/tasks/implementation/stage-2/TASK-011-wb-api-connections.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/architecture/DATA_MODEL.md`

Product code was not changed. Only this test report was added.

## What Was Checked

| Area | Result |
| --- | --- |
| `manage.py check` | PASS |
| `makemigrations --check --dry-run` | PASS, no model changes detected |
| TASK-011 WB API client tests | PASS |
| TASK-011 connection/service tests | PASS |
| Audit/techlog safe-contour tests | PASS |
| `wb.api.connection.view/manage` and object access | PASS |
| Mock cases: success, 401/403, 429, timeout, invalid response | PASS |
| Secret guardrails: metadata, audit snapshots/messages, techlog safe fields, DB text checks | PASS |
| No real WB network calls in tests | PASS: tests use fake session/client; static scan found real `urlopen` only in the production client implementation |
| Stage 1 WB Excel regression | PASS |
| Stage 1 Ozon Excel regression | PASS |
| Ozon API / Ozon implementation touched | PASS: no Ozon files in current changed file list |
| Full Django suite smoke | REMARK: one pre-existing/out-of-scope deployment-readiness assertion fails |

## Commands And Results

```bash
python manage.py check
```

Result: BLOCKED by local shell because `python` command is unavailable.

```bash
python3 manage.py check
python3 manage.py makemigrations --check --dry-run
```

Result: BLOCKED for project checks without environment loading: `django` unavailable for system `python3`.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check
```

Result: PASS, `System check identified no issues (0 silenced).`

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
```

Result: PASS, `No changes detected`.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api apps.stores apps.audit apps.techlog apps.identity_access --verbosity 2
```

Result: PASS, 53 tests.

Covered notable TASK-011 cases:

- read-only check endpoint `/api/v2/list/goods/filter` with `limit=1`, `offset=0`;
- success status transition to `active`;
- auth failures 401/403;
- 429 retry/safe failure;
- timeout retry/safe failure;
- invalid JSON/schema/status safe failure;
- metadata rejection for secret-like keys and values;
- no raw token persisted in connection metadata, audit safe fields, or techlog safe fields;
- `wb.api.connection.manage` required for save/check;
- store object access enforced for connection UI.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_excel apps.discounts.ozon_excel --verbosity 2 --noinput
```

Result: PASS, 21 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test --verbosity 1 --noinput
```

Result: FAIL, 119 tests run, 1 failure:

- `apps.web.tests.DeploymentReadinessTests.test_acceptance_registry_keeps_customer_artifacts_gated`
- failure reason: the test still expects text `pending customer delivery` in `docs/testing/CONTROL_FILE_REGISTRY.md`, while the registry now states the real WB/Ozon artifacts are accepted as of 2026-04-26.
- no TASK-011 failure was observed in this full run.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.web.tests.DeploymentReadinessTests.test_acceptance_registry_keeps_customer_artifacts_gated --verbosity 2 --noinput
```

Result: FAIL, same isolated assertion as above.

```bash
rg -n "urlopen\(|requests\.|httpx\.|aiohttp|urllib\.request|wildberries|discounts-prices-api|api/v2/list/goods/filter" apps/discounts/wb_api apps/stores apps/audit apps/techlog apps/identity_access -g '*.py'
```

Result: PASS for test network isolation. The only real network primitive is in `apps/discounts/wb_api/client.py`; TASK-011 tests inject fake sessions/clients and do not perform real WB calls.

```bash
git diff --name-only && git status --short
```

Result: PASS for Ozon isolation. Current changed files do not include `apps/discounts/ozon_excel/` or future Ozon API paths.

## Test IDs

Test ID: TASK-011-CONNECTION-SUCCESS  
Scenario: Save WB API connection and successful read-only check.  
Expected: status moves to `configured` on save and `active` after check; audit records use WB API connection codes; token is only resolved at runtime and not persisted outside `protected_secret_ref`.  
Actual: matched by `StoreTask011WBApiConnectionTests.test_wb_api_connection_save_uses_protected_ref_status_and_audit` and `test_connection_check_success_sets_active_and_keeps_token_outside_db`.  
Status: pass.

Test ID: TASK-011-CONNECTION-FAILURES  
Scenario: WB check auth failure, rate limit, timeout, invalid response.  
Expected: safe failure, documented techlog event types, no secret leakage.  
Actual: matched by store-service and client tests for 401/403, 429, timeout, invalid response.  
Status: pass.

Test ID: TASK-011-SECRET-GUARDRAILS  
Scenario: Reject secret-like metadata and safe-contour values.  
Expected: no token/header/API key/bearer/secret-like values in metadata, audit safe fields, techlog `safe_message`/`sensitive_details_ref`, UI/test output.  
Actual: guardrail tests pass. Test command outputs did not print raw synthetic token values.  
Status: pass.

Test ID: TASK-011-PERMISSIONS  
Scenario: Enforce `wb.api.connection.view/manage` and object access.  
Expected: users without manage cannot edit/check; users without object access cannot access connection/store state; secret ref not displayed.  
Actual: covered by `test_connection_view_manage_and_object_access_are_enforced`.  
Status: pass.

Test ID: TASK-011-STAGE1-REGRESSION  
Scenario: WB/Ozon Excel Stage 1 remains passable.  
Expected: WB Excel and Ozon Excel tests pass; Ozon not affected.  
Actual: 21 Excel tests pass; no Ozon files changed.  
Status: pass.

## Findings / Defects

1. REMARK: full suite has one out-of-scope failure in deployment readiness documentation test.
   - Test: `apps.web.tests.DeploymentReadinessTests.test_acceptance_registry_keeps_customer_artifacts_gated`.
   - Expected by test: `pending customer delivery` remains in `docs/testing/CONTROL_FILE_REGISTRY.md`.
   - Actual document state: real WB/Ozon artifacts are accepted and future optional edge artifacts are marked separately.
   - Impact on TASK-011: no direct impact found. TASK-011, WB Excel, Ozon Excel, audit, techlog, stores and identity-access tests pass.
   - Recommended route: separate Stage 1 documentation/test alignment task or auditor decision.

## Remaining Risks

- `apps/discounts/wb_api/client.py` contains the real WB HTTP implementation. TASK-011 tests mock it correctly, but production check flow will call the real endpoint when wired to a real secret resolver.
- TASK-011 covers connection contour only. Later Stage 2.1 tasks must separately prove prices/promotions/calculation/upload snapshots, files, and upload-specific safety.
- Full-suite failure should be resolved before release readiness is claimed, even though it is not caused by TASK-011.

## Audit Readiness

TASK-011 can go to audit with remarks. The connection contour, permissions, secret guardrails, mock failure handling, migrations, and Stage 1 WB/Ozon Excel regression checks passed. The only observed failure is outside TASK-011 and should be tracked separately.

## Changed Files

- `docs/testing/TEST_REPORT_TASK_011.md`
