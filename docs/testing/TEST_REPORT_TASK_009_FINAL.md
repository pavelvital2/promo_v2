# TEST_REPORT_TASK_009_FINAL

Дата проверки: 2026-04-25.

Роль проверки: тестировщик Codex CLI TASK-009 после audit round 4 PASS и закрытия дефекта `T009-UI-001`. Архитектурный аудит и разработка не выполнялись. Продуктовый код не изменялся.

## status

PASS

Полный повторный task-wide regression для TASK-009 в разрешённом контуре прошёл. Дефект `T009-UI-001` не воспроизводится: UI и прямой download route разделяют права `download_output` и `download_detail_report`.

## scenario matrix

| # | Scenario | Status | Evidence / notes |
| --- | --- | --- | --- |
| 1 | Product list/card: store-aware visibility, card data, related operations scope | PASS | `apps.web` tests cover product list/card rendering and related operations filtered by store and marketplace. |
| 2 | WB store parameter write/history/audit | PASS | `apps.web` covers POST write through settings UI, active store value, history row and audit record. WB template shows effective parameter block; Ozon template has no WB parameters. |
| 3 | Draft run context upload/replace/delete/version list/check/process controls | PASS | `apps.web` covers WB replace preserving file version chain and audit; launch denial before file creation when action permission is insufficient. WB/Ozon templates expose draft context, delete controls, version list and "Проверить" / "Обработать" controls. `apps.files` covers pre-operation delete behavior. |
| 4 | Admin users/roles/store access write-flow | PASS | `apps.web` covers user creation and distinct edit/status/archive permissions. Templates/views expose role, permission and store access assignment flows; `apps.identity_access` and `apps.stores` cover owner/system protections, direct denies, object scope and access history. |
| 5 | Access-aware visibility and object access | PASS | `apps.web` covers reference index for store-scoped local admin and hidden inaccessible store. `apps.stores`, `apps.audit`, `apps.techlog`, `apps.files` cover object-scoped visibility and direct deny behavior. |
| 6 | Output vs detail download permissions, including `T009-UI-001` | PASS | `apps.web` regression covers detail-only user seeing/using detail report link without output link, and output-only user seeing output link without detail report link. `apps.files` covers direct route permission checks and observer default no-download behavior. |
| 7 | Operation list/card/result/action visibility | PASS | Owner smoke covers operation screens; operation card template separates detail/output links and hides row details/downloads by rights. Confirmation entry remains gated by `confirm_warnings` plus `run_process`. |
| 8 | WB/Ozon Excel behavior under existing synthetic fixtures | PASS | `apps.discounts.wb_excel` and `apps.discounts.ozon_excel` passed; they cover check/process rules, process gates, output constraints, parameter snapshots for WB and absence of Ozon parameters. |
| 9 | Audit/techlog/system notifications visibility | PASS | `apps.web` smoke covers audit/techlog/notification routes for owner. `apps.audit` and `apps.techlog` cover limited/full scopes, sensitive detail gating, immutability and notifications. |

## commands run/results

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check
```

Result: PASS.

```text
System check identified no issues (0 silenced).
```

Initial full test command without `--noinput` hit an existing test database and stopped before running tests:

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.web apps.marketplace_products apps.platform_settings apps.identity_access apps.files apps.operations apps.discounts.wb_excel apps.discounts.ozon_excel apps.audit apps.techlog apps.stores
```

Result: infrastructure retry required.

```text
Got an error creating the test database: database "test_promo_v2" already exists
EOFError: EOF when reading a line
```

The same task-wide test scope was then rerun non-interactively:

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test --noinput apps.web apps.marketplace_products apps.platform_settings apps.identity_access apps.files apps.operations apps.discounts.wb_excel apps.discounts.ozon_excel apps.audit apps.techlog apps.stores
```

Result: PASS.

```text
Found 100 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
....................................................................................................
----------------------------------------------------------------------
Ran 100 tests in 80.458s

OK
Destroying test database for alias 'default'...
```

## defects found

None.

## residual risks

- Проверка выполнена через Django checks, Django test client, существующие synthetic/internal fixtures and static inspection of relevant templates/views. Ручной браузерный sanity check не выполнялся.
- Post-acceptance update 2026-04-26: customer WB/Ozon control Excel comparison artifacts are registered and accepted as `WB-REAL-001` / `OZ-REAL-001`; no fabricated customer files were created.
- The first test command encountered stale/occupied PostgreSQL `test_promo_v2`; final rerun with `--noinput` completed successfully.

## decision

TASK-009 final tester retest: PASS.
