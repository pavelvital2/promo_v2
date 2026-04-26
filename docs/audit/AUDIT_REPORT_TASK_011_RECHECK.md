# AUDIT_REPORT_TASK_011_RECHECK.md

Task: `TASK-011 Stage 2.1 WB API connections` recheck after audit FAIL
Auditor: Codex CLI, audit recheck role
Date: 2026-04-26
Verdict: PASS

## Проверенная область

- Recheck of HIGH findings from `docs/audit/AUDIT_REPORT_TASK_011.md`.
- WB API connection default protected secret resolver, service/UI check flow, active status ownership, WB-only store boundary, write-only secret edit form.
- Stage 1 WB/Ozon Excel regression boundary.
- Maintenance update in `apps/web/tests.py`.

## Проверенные файлы

- `docs/audit/AUDIT_REPORT_TASK_011.md`
- `docs/testing/TEST_REPORT_TASK_011.md`
- `docs/testing/TEST_REPORT_TASK_011_RECHECK.md`
- `docs/tasks/implementation/stage-2/TASK-011-wb-api-connections.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/product/UI_SPEC.md`
- `apps/stores/forms.py`
- `apps/stores/models.py`
- `apps/stores/services.py`
- `apps/stores/views.py`
- `apps/stores/tests.py`
- `templates/stores/connection_form.html`
- `apps/stores/templates/stores/connection_form.html`
- `templates/stores/store_card.html`
- `apps/stores/templates/stores/store_card.html`
- `apps/discounts/wb_api/client.py`
- `apps/discounts/wb_api/redaction.py`
- `apps/web/tests.py`

## Метод проверки

- Read task, audit, test and profile specification documents.
- Inspected TASK-011 code changes, forms/templates, service paths, permissions, default resolver, redaction/client code and focused tests.
- Ran Django checks and test suites listed below.
- Checked `__pycache__` outside `.venv` before tests, after tests, and after cleanup.

## Findings

No TASK-011 recheck defects found.

## Status of Previous Findings

1. Production UI/service check can succeed via default resolver: CLOSED.
   - `apps/stores/services.py:299-309` implements deterministic `env://ENV_VAR_NAME` resolution.
   - `apps/stores/views.py:180-189` calls `check_wb_api_connection(...)` without an injected test resolver, using the service default.
   - `apps/stores/services.py:451-464` records only safe check metadata; the token is not written into audit/techlog snapshots.
   - Covered by `apps/stores/tests.py:530-556`.

2. `active` cannot be set manually: CLOSED.
   - `apps/stores/forms.py:26-31` excludes `status` from the edit form.
   - `apps/stores/services.py:213-214` rejects direct `status=active`.
   - `apps/stores/services.py:436-449` is the only checked path that sets `active`.
   - Covered by `apps/stores/tests.py:684-711`.

3. WB API connection create/edit/check is WB-only: CLOSED.
   - `apps/stores/services.py:211-212` blocks service save for non-WB stores when `module=wb_api`.
   - `apps/stores/views.py:137-140` and `apps/stores/views.py:181-187` guard edit/check routes with the WB store requirement.
   - Store card connection controls are gated by `is_wb_store` in `apps/stores/views.py:92-94` and templates.
   - Covered by `apps/stores/tests.py:713-759`.

4. Edit form no longer renders saved protected ref/secret: CLOSED.
   - `apps/stores/forms.py:16-24` uses `PasswordInput(render_value=False)`.
   - `apps/stores/forms.py:33-37` clears initial protected ref for existing instances.
   - `apps/stores/views.py:150-163` preserves old ref on blank input and replaces only on non-blank input.
   - Covered by `apps/stores/tests.py:625-682`.

5. `__pycache__` outside `.venv`: CLOSED.
   - Before test execution: `find . -path './.venv' -prune -o -type d -name __pycache__ -print` returned no output.
   - Test execution regenerated runtime caches outside `.venv`; they were removed before final report.
   - Final checks for `__pycache__` directories and non-`.venv` `*.pyc` files returned no output.

## Additional Checks

- No Stage 1 WB Excel or Ozon Excel product paths were changed in the inspected diff.
- Stage 1 WB/Ozon Excel regression tests passed.
- Maintenance change in `apps/web/tests.py:92-107` remains narrow: it updates the stale customer artifact gate assertion to the accepted registry/plan state and does not touch product behavior.

## Risks

- The local default resolver intentionally supports only `env://ENV_VAR_NAME`. Unsupported protected secret backends fail safely as `check_failed`; adding a real vault/backend resolver later must preserve the no-readback/no-leak contract.

## Open Gaps

None.

## Spec-blocking Questions

None.

## Requires Customer Escalation Through Orchestrator

No.

## TASK-012 Readiness

TASK-012 may start. TASK-011 connection preconditions for Stage 2.1 are satisfied by this recheck.

## Commands/tests Run

```bash
find . -path './.venv' -prune -o -type d -name __pycache__ -print
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api apps.stores apps.audit apps.techlog apps.identity_access --verbosity 2 --noinput
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_excel apps.discounts.ozon_excel --verbosity 2 --noinput
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.web.tests.DeploymentReadinessTests.test_acceptance_registry_keeps_customer_artifacts_gated --verbosity 2 --noinput
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test --verbosity 1 --noinput
find . -path './.venv' -prune -o -type d -name __pycache__ -exec rm -rf {} +
find . -path './.venv' -prune -o -type d -name __pycache__ -print
find . -path './.venv' -prune -o -type f -name '*.pyc' -print
```

Results:

- Pre-test `__pycache__` check: PASS, no output.
- `manage.py check`: PASS.
- `makemigrations --check --dry-run`: PASS, no changes detected.
- TASK-011 focused suite: PASS, 59 tests.
- Stage 1 WB/Ozon Excel regression: PASS, 21 tests.
- Maintenance readiness assertion: PASS, 1 test.
- Full Django suite: PASS, 125 tests.
- Post-cleanup `__pycache__` and `*.pyc` checks: PASS, no output.

## Changed Files From This Audit

- `docs/audit/AUDIT_REPORT_TASK_011_RECHECK.md`

## Итог

PASS. Previous audit FAIL findings are closed, no new TASK-011 defects were found, and TASK-012 may start.
