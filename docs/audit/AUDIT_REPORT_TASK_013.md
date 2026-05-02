# AUDIT_REPORT_TASK_013.md

Task: `TASK-013 Stage 2.1 WB API current promotions download`
Auditor: Codex CLI
Date: 2026-04-26
Verdict: PASS

## Проверенная область

Реализация 2.1.2 WB API current promotions download: read-only скачивание текущих акций WB, strict current filter, Promotions Calendar API pagination/details/nomenclatures, dedicated promotion persistence, promo Excel exports, operation/run/file/audit/techlog integration, permissions/object access/active connection prerequisite, secret redaction and closure of `DEF-TASK-013-001`.

Реальные WB token files не читались, реальные WB вызовы не выполнялись. Automated audit/tests оставлены mock-based.

## Проверенные файлы

- `docs/tasks/implementation/stage-2/TASK-013-wb-api-current-promotions-download.md`
- `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/testing/TEST_REPORT_TASK_013.md`
- `docs/testing/TEST_REPORT_TASK_013_RECHECK.md`
- `docs/source/stage-inputs/tz_stage_2.1.txt` scoped sections `5.5`, `6.6`, `7`, `10.1`, `11`, `15.2`, `16`
- `apps/discounts/wb_api/client.py`
- `apps/discounts/wb_api/promotions/`
- `apps/operations/models.py`
- `apps/operations/services.py`
- `apps/operations/migrations/0004_allow_multiple_operation_outputs_per_kind.py`
- `apps/files/models.py`
- `apps/files/services.py`
- `apps/identity_access/seeds.py`
- `apps/stores/services.py`
- `config/settings.py`

## Метод проверки

- Сверка task expected result and mandatory checks: `docs/tasks/implementation/stage-2/TASK-013-wb-api-current-promotions-download.md`.
- Сверка product/data/file/operation/permission contracts for 2.1.2.
- Code review of client, service, normalizers, Excel writer, models, migrations and tests.
- Mock-based Django test runs and static scan for WB write/upload endpoints.
- Runtime model discovery for `WBPromotion`, `WBPromotionSnapshot`, `WBPromotionProduct`, `WBPromotionExportFile`.

## Findings

No blocking or non-blocking TASK-013 defects found. `DEF-TASK-013-001` is closed.

Evidence:

- Current filter is exactly `start_datetime <= now_utc < end_datetime`: `apps/discounts/wb_api/promotions/normalizers.py:75`.
- API window is `now_utc - 24h` / `now_utc + 24h`; list request sends `allPromo=true`, `limit=1000`, offset pagination: `apps/discounts/wb_api/promotions/services.py:545`, `apps/discounts/wb_api/promotions/services.py:110`.
- `current_filter_timestamp`, API window and safe snapshot are persisted in `WBPromotionSnapshot`: `apps/discounts/wb_api/promotions/services.py:314`.
- Details batching deduplicates IDs and limits batches to 100: `apps/discounts/wb_api/promotions/services.py:147`, `apps/discounts/wb_api/promotions/services.py:157`.
- Nomenclatures are fetched for `inAction=true` and `inAction=false` with `limit=1000`, offset until an empty page: `apps/discounts/wb_api/promotions/services.py:178`, `apps/discounts/wb_api/promotions/services.py:611`.
- Auto promotions skip nomenclatures and create no product/export rows; they are recorded with `wb_api_promotion_auto_no_nomenclatures`: `apps/discounts/wb_api/promotions/services.py:377`.
- Dedicated persistence entities exist and are migrated: `apps/discounts/wb_api/promotions/models.py:8`, `apps/discounts/wb_api/promotions/models.py:47`, `apps/discounts/wb_api/promotions/models.py:82`, `apps/discounts/wb_api/promotions/models.py:116`, `apps/discounts/wb_api/promotions/migrations/0001_initial.py:18`.
- Regular promotions persist products and export links tied to store/operation/file version: `apps/discounts/wb_api/promotions/services.py:467`, `apps/discounts/wb_api/promotions/services.py:419`.
- Promo Excel required columns are present and output links support multiple `promotion_export` files: `apps/discounts/wb_api/promotions/export.py:10`, `apps/operations/models.py:149`, `apps/operations/models.py:675`.
- Operation classifier uses `mode=api`, `step_code=wb_api_promotions_download`, and `operation_type=not_applicable`; model validation rejects check/process for WB API steps: `apps/discounts/wb_api/promotions/services.py:551`, `apps/operations/models.py:527`.
- Permission, object access, WB store guard and active Stage 2.1 connection are checked before API execution: `apps/discounts/wb_api/promotions/services.py:540`, `apps/discounts/wb_api/promotions/services.py:71`.
- Safe contours assert no secret-like values in request params, safe snapshots, operation summary and connection metadata: `apps/discounts/wb_api/client.py:151`, `apps/discounts/wb_api/promotions/services.py:123`, `apps/discounts/wb_api/promotions/services.py:313`, `apps/discounts/wb_api/promotions/services.py:499`, `apps/discounts/wb_api/promotions/services.py:584`.
- WB Promotions Calendar client contains only read GET endpoints for TASK-013; static scan found no `calendar/promotions/upload`: `apps/discounts/wb_api/client.py:18`.
- Ozon API and Stage 1 WB Excel behavior were not changed by TASK-013 implementation scope; Stage 1 WB/Ozon regression tests passed.

## Риски

Residual risk is limited to future TASK-014 consumption conventions: promotion products are versioned through `source_snapshot`, so consumers must use the selected/latest `WBPromotionSnapshot` rather than all historical `promotion.products`. This is compatible with the implemented model and does not block TASK-014.

## Обязательные исправления

None.

## Рекомендации

- In TASK-014, consume `WBPromotionProduct` through the selected `WBPromotionSnapshot` / operation basis to avoid mixing historical promotion rows.
- Keep real WB credentials outside tests and reports; continue using protected secret refs and mock fixtures.

## Открытые gaps

No new GAP opened. `DEF-TASK-013-001` was an implementation defect and is verified closed, not a documentation gap.

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
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api.promotions --verbosity 2 --noinput
```

Result: PASS. Ran 9 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api apps.operations apps.files apps.stores apps.audit apps.techlog apps.identity_access --verbosity 2 --noinput
```

Result: PASS. Ran 100 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_excel apps.discounts.ozon_excel --verbosity 2 --noinput
```

Result: PASS. Ran 21 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test --verbosity 1 --noinput
```

Result: PASS. Ran 141 tests.

```bash
rg -n "calendar/promotions/upload|promotions/upload|api/v1/calendar/promotions/upload|method=\"POST\"|method='POST'|\.post\(" apps/discounts/wb_api apps -g '*.py'
```

Result: PASS for TASK-013 no-write scan. No `calendar/promotions/upload` / WB promotions upload reference was found; `.post(` matches are unrelated Django view tests outside WB API promotions client/use case code.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py shell -c "from django.apps import apps; print([apps.get_model('promotions', name).__name__ for name in ['WBPromotion','WBPromotionSnapshot','WBPromotionProduct','WBPromotionExportFile']])"
```

Result: PASS. Output: `['WBPromotion', 'WBPromotionSnapshot', 'WBPromotionProduct', 'WBPromotionExportFile']`.

## TASK-014 readiness

TASK-014 may start.

## Changed files from this audit

- `docs/audit/AUDIT_REPORT_TASK_013.md`

## Итог

pass
