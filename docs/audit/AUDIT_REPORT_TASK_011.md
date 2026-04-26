# AUDIT_REPORT_TASK_011.md

Task: `TASK-011 Stage 2.1 WB API connections`
Auditor: Codex CLI, audit role
Date: 2026-04-26
Verdict: FAIL

## Проверенная область

- TASK-011 WB API connection contour: model/migration, permissions, UI routes, service check flow, audit/techlog codes, WB API client and tests.
- Separate maintenance fix in `apps/web/tests.py` for stale Stage 1 readiness assertion.
- Stage 1 WB/Ozon Excel regression boundary and Ozon isolation.

## Проверенные файлы

- `apps/stores/models.py`
- `apps/stores/services.py`
- `apps/stores/forms.py`
- `apps/stores/views.py`
- `apps/stores/urls.py`
- `templates/stores/store_card.html`
- `apps/stores/templates/stores/store_card.html`
- `apps/stores/tests.py`
- `apps/discounts/wb_api/client.py`
- `apps/discounts/wb_api/redaction.py`
- `apps/discounts/wb_api/tests.py`
- `apps/audit/models.py`
- `apps/audit/services.py`
- `apps/audit/tests.py`
- `apps/techlog/models.py`
- `apps/techlog/services.py`
- `apps/techlog/tests.py`
- `apps/identity_access/seeds.py`
- `apps/*/migrations/*TASK-011*` new migrations
- `apps/web/tests.py`
- `docs/testing/TEST_REPORT_TASK_011.md`

## Метод проверки

- Read required task/spec/testing documents listed by orchestrator.
- Inspected current diff and untracked TASK-011 files.
- Checked secret paths, permission gates, object access, connection status transitions, WB/Ozon boundaries, audit/techlog catalogs, and mockability.
- Ran focused and full Django test commands listed below.

## Нарушения

### HIGH: UI connection check cannot succeed in the production path

`apps/stores/views.py:176` calls `check_wb_api_connection(request.user, connection)` without passing a resolver. The service default is `default_secret_resolver`, and `apps/stores/services.py:279-280` always raises `WBApiInvalidResponseError("Protected secret resolver is not configured.")`. As a result, the shipped UI check path can never resolve a saved `protected_secret_ref` and can never perform the documented read-only WB check successfully.

This violates TASK-011 expected result "WB API connection can be configured, checked" and `API_CONNECTIONS_SPEC.md` connection check flow. Existing tests only prove the path with an injected fake resolver.

### HIGH: `active` status can be set without a successful check

`apps/stores/forms.py:19-24` exposes `status` in `ConnectionBlockForm`; `apps/stores/views.py:151-153` forwards all form fields to `save_connection_block`; `apps/stores/services.py:220-228` writes those fields and does not reject `active` unless produced by `check_wb_api_connection`.

A user with `wb.api.connection.manage` can therefore mark a connection `active` directly from the edit form, bypassing the documented read-only check. This breaks the `configured` vs `active` contract in `API_CONNECTIONS_SPEC.md`: only a successful last check may make the connection usable for Stage 2.1 operations.

### HIGH: WB API connection UI is not restricted to WB stores

The create route builds a WB API connection for any store visible_id at `apps/stores/views.py:134-142`; the service marks any `module=wb_api` connection as Stage 2.1 at `apps/stores/services.py:223-227`. The marketplace guard exists only later in the check flow (`apps/stores/services.py:292-295`), after an Ozon store can already receive a WB API connection block.

This violates the Stage 2.1 boundary: TASK-011 and `API_CONNECTIONS_SPEC.md` are WB-only, and WB/Ozon Stage 2.1/2.2 contours must not be mixed.

### HIGH: saved protected secret reference is rendered back in the edit form

`protected_secret_ref` is part of `ConnectionBlockForm` (`apps/stores/forms.py:19-24`), and both connection form templates render `{{ form.as_p }}` (`templates/stores/connection_form.html:7-10`, `apps/stores/templates/stores/connection_form.html:14-17`). If this field contains a token/API key/bearer value or any secret-like value, the edit UI displays it back to users with manage rights.

The store card masks the field as `[ref-set]`, but the edit form is still a UI leak path. TASK-011 and `API_CONNECTIONS_SPEC.md` require no token/header/API key/bearer/secret-like value in UI and prohibit showing a saved token after input. The field should be write-only or masked with replacement semantics.

## Риски

- Later TASK-012 operations may trust `ConnectionBlock.status=active`; with the current implementation, that status is not reliable.
- The real connection check flow is less covered than the test report implies because tests inject fake dependencies not wired into the UI route.
- Untracked `apps/discounts/wb_api/__pycache__/` files are present under the new untracked package and must not be committed.

## Положительные проверки

- New audit action codes and techlog event types match the documented Stage 2.1 catalogs.
- Metadata validation rejects documented secret-like keys and tested bearer/key-value patterns.
- Store card redacts protected refs and metadata display.
- `wb.api.connection.view/manage` and object access are used in the store card/edit/check paths.
- WB API client is mockable through injected session/client factory; tests do not call the real WB endpoint.
- No changes were made under `apps/discounts/wb_excel/` or `apps/discounts/ozon_excel/`.
- The maintenance fix in `apps/web/tests.py` is narrow and updates only the stale accepted-artifacts assertion.

## Обязательные исправления

1. Wire a real protected-secret resolver into the UI/service check path, or otherwise make the production path able to resolve `protected_secret_ref` without exposing the token.
2. Remove direct user control over `active`; only `check_wb_api_connection` may set `active` after a successful read-only check. Manual statuses should be limited to allowed administrative states such as disabled/archived where documented.
3. Restrict WB API connection creation/edit/check UI and service paths to WB stores only.
4. Make the protected secret input write-only/masked on edit; never render saved token/API key/bearer/secret-like content back into UI. Add tests for the edit form, not only the store card.
5. Remove generated `__pycache__` artifacts before handoff/commit.

## Открытые gaps

No new GAP was opened by the auditor. The findings are implementation defects against existing approved docs, not missing requirements.

## Spec-blocking вопросы

None.

## Требуется эскалация заказчику через оркестратора

No. Fixes can be made under existing TASK-011 documentation.

## TASK-012 readiness

TASK-012 must not start until the required fixes above are implemented and re-audited. The active-connection invariant is a prerequisite for prices download.

## Commands/tests run

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api apps.stores apps.audit apps.techlog apps.identity_access --verbosity 2 --noinput
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_excel apps.discounts.ozon_excel --verbosity 2 --noinput
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.web.tests.DeploymentReadinessTests.test_acceptance_registry_keeps_customer_artifacts_gated --verbosity 2 --noinput
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test --verbosity 1 --noinput
```

Results:

- `manage.py check`: PASS.
- `makemigrations --check --dry-run`: PASS, no changes detected.
- TASK-011 focused suite: PASS, 53 tests.
- WB/Ozon Excel regression: PASS, 21 tests.
- Maintenance readiness assertion: PASS.
- Full Django suite: PASS, 119 tests.

One first attempt to run WB/Ozon Excel regression in parallel was blocked by the same PostgreSQL test database being used by another running test process; it was rerun sequentially and passed.

## Changed files from this audit

- `docs/audit/AUDIT_REPORT_TASK_011.md`

## Итог

FAIL. TASK-011 is not ready for TASK-012 because the production check flow cannot succeed, `active` can be user-forced without check, WB API connections can be created on Ozon stores, and the edit form can render saved secret material.
