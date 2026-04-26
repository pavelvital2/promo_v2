# AUDIT_REPORT_TASK_012.md

Task: `TASK-012 Stage 2.1 WB API prices download`
Auditor: Codex CLI
Date: 2026-04-26
Verdict: PASS

## Проверенная область

Реализация 2.1.1 WB API prices download: read-only скачивание цен WB, нормализация size prices, Excel export, обновление `MarketplaceProduct`, operation/run/file/audit/techlog интеграция, права/object access/active connection prerequisite и тестовый отчёт `docs/testing/TEST_REPORT_TASK_012.md`.

Реальный WB token file не читался, его содержимое не выводилось. Automated tests оставлены mock-based.

## Проверенные файлы

- `docs/tasks/implementation/stage-2/TASK-012-wb-api-prices-download.md`
- `docs/product/WB_API_PRICE_EXPORT_SPEC.md`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/testing/TEST_REPORT_TASK_012.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`
- `apps/discounts/wb_api/client.py`
- `apps/discounts/wb_api/prices/`
- `apps/files/models.py`
- `apps/files/services.py`
- `apps/files/migrations/0002_remove_fileobject_file_object_scenario_marketplace_match_and_more.py`
- `apps/operations/models.py`
- `apps/operations/services.py`
- `apps/operations/migrations/0003_remove_operation_operation_status_matches_type_and_more.py`
- `apps/marketplace_products/models.py`
- `apps/marketplace_products/services.py`
- relevant tests in `apps/discounts/wb_api/`, `apps/operations/`, `apps/files/`, `apps/stores/`, `apps/audit/`, `apps/techlog/`, `apps/identity_access/`, `apps/discounts/wb_excel/`, `apps/discounts/ozon_excel/`

## Метод проверки

- Сверка implementation task expected results and checks: `docs/tasks/implementation/stage-2/TASK-012-wb-api-prices-download.md:61`.
- Сверка price export contract: pagination/API endpoint/preconditions/Excel columns/size rules/product mapping/prohibitions in `docs/product/WB_API_PRICE_EXPORT_SPEC.md:13`, `docs/product/WB_API_PRICE_EXPORT_SPEC.md:21`, `docs/product/WB_API_PRICE_EXPORT_SPEC.md:41`, `docs/product/WB_API_PRICE_EXPORT_SPEC.md:55`, `docs/product/WB_API_PRICE_EXPORT_SPEC.md:65`, `docs/product/WB_API_PRICE_EXPORT_SPEC.md:115`.
- Сверка Stage 2.1 read-only boundary and 2.1.1 flow: `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md:25`, `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md:27`.
- Code review of client/service/model/migration/test changes.
- Mock-based Django test runs and static endpoint/secret contour checks.
- Maintenance check for `apps/` and `config/` `__pycache__` / `*.pyc`.

## Findings

No blocking or non-blocking TASK-012 defects found.

Evidence:

- Pagination uses read-only `GET /api/v2/list/goods/filter`, `limit=1000`, offset increment by 1000, and stops only on empty `listGoods`: `apps/discounts/wb_api/client.py:93`, `apps/discounts/wb_api/prices/services.py:98`.
- TASK-012 prices flow does not introduce WB write/upload endpoint behavior. The client path in scope is GET-only: `apps/discounts/wb_api/client.py:100`, `apps/discounts/wb_api/client.py:156`.
- Operation classifier contract is implemented with `mode=api`, WB `step_code`, and `operation_type=not_applicable`; DB/model validation rejects check/process for WB API steps: `apps/operations/services.py:492`, `apps/operations/models.py:526`, `apps/operations/migrations/0003_remove_operation_operation_status_matches_type_and_more.py:44`.
- Main Excel sheet contains only Stage 1-compatible required columns; diagnostics are isolated to `_api_raw`: `apps/discounts/wb_api/prices/export.py:10`, `apps/discounts/wb_api/prices/export.py:27`.
- Size rules are explicit: equal prices are upload-ready, missing price/sizes are invalid, and conflicts are not upload-ready: `apps/discounts/wb_api/prices/normalizers.py:78`, `apps/discounts/wb_api/prices/normalizers.py:84`, `apps/discounts/wb_api/prices/normalizers.py:90`.
- Product sync is store-scoped and does not invent titles; history links operation and file version: `apps/discounts/wb_api/prices/services.py:132`, `apps/discounts/wb_api/prices/services.py:171`.
- Output file scenario/linking uses `wb_discounts_api_price_export` and immutable operation output links: `apps/discounts/wb_api/prices/services.py:231`, `apps/operations/services.py:632`, `apps/operations/models.py:658`.
- Permission, object access, WB-store guard and active connection prerequisite are enforced before API execution: `apps/discounts/wb_api/prices/services.py:341`, `apps/discounts/wb_api/prices/services.py:343`, `apps/discounts/wb_api/prices/services.py:64`.
- Safe contours reject secret-like values in operation summary, audit, techlog and connection metadata: `apps/discounts/wb_api/prices/services.py:303`, `apps/audit/services.py:52`, `apps/techlog/services.py:78`, `apps/stores/models.py:274`.
- Test report evidence matches the rerun results: `docs/testing/TEST_REPORT_TASK_012.md:27`, `docs/testing/TEST_REPORT_TASK_012.md:42`, `docs/testing/TEST_REPORT_TASK_012.md:90`.

## Риски

Residual risk is limited to future integration with real protected secret storage and real WB credentials. That must remain a protected ref / environment secret flow and must not be converted into source-controlled files, reports, snapshots, audit or techlog values.

## Обязательные исправления

None.

## Рекомендации

- Keep TASK-013 tests mock-based and continue using protected secret refs only.
- Do not reuse TASK-012 price snapshots as a shortcut for future upload logic; 2.1.4 still requires separate confirmation, drift check and upload status polling.

## Открытые gaps

No new GAP opened. Existing Stage 2.1 GAP evaluation reports no open Stage 2.1 GAP.

## Spec-blocking вопросы

None.

## Требуется эскалация заказчику через оркестратора

No.

## Commands/tests run

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

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_excel apps.discounts.ozon_excel --verbosity 2 --noinput
```

Result: PASS. Ran 21 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test --verbosity 1 --noinput
```

Result: PASS. Ran 132 tests.

```bash
rg -n "urlopen\(|requests\.|httpx\.|aiohttp|POST|upload|/api/v2/upload|Authorization|Bearer|api[_-]?key|token" apps/discounts/wb_api apps/stores -g '*.py'
```

Result: PASS for TASK-012 no-write check. Matches are limited to GET client code, protected secret resolution, UI POST forms for connection management, upload-ready metadata, and mock/test redaction sentinels; no WB write/upload endpoint exists in the TASK-012 prices flow.

```bash
find apps config -type d -name __pycache__ -o -name '*.pyc'
find apps config -type d -name __pycache__ -prune -exec rm -rf {} +
find apps config -type d -name __pycache__ -o -name '*.pyc'
```

Result: tests regenerated cache files; generated `__pycache__` / `*.pyc` artifacts were removed. Final check returned no entries.

## TASK-013 readiness

TASK-013 may start.

## Итог

pass
