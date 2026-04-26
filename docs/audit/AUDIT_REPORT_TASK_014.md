# AUDIT_REPORT_TASK_014

Проверенная область: TASK-014 Stage 2.1 WB API discount calculation Excel output.

Дата: 2026-04-26.

Итог: PASS.

## Findings

1. Low / housekeeping: [apps/discounts/wb_api/calculation/test_settings.py](/home/pavel/projects/promo_v2/apps/discounts/wb_api/calculation/test_settings.py:1) добавляет SQLite-only settings module для isolated TASK-014 checks. Это не acceptance blocker: scan показал, что модуль не подключён `manage.py`, `config/asgi.py`, `config/wsgi.py` или TASK-014 acceptance commands; все выполненные проверки шли через `.env.runtime` и PostgreSQL test DB. Риск только организационный: файл может быть ошибочно использован как acceptance evidence вместо стандартного PostgreSQL контура. Required fix не требуется перед TASK-015; при ужесточении hygiene его можно удалить отдельной cleanup-задачей.

Блокирующих findings не обнаружено.

## Evidence

- Stage 1 WB Excel behavior сохраняется: Excel service теперь импортирует общий core [apps/discounts/wb_excel/services.py](/home/pavel/projects/promo_v2/apps/discounts/wb_excel/services.py:35), а расчётные ветки вызывают `decide_wb_discount` без отдельной формулы [apps/discounts/wb_excel/services.py](/home/pavel/projects/promo_v2/apps/discounts/wb_excel/services.py:607). Stage 1 WB/Ozon regression passed.
- Shared core содержит decimal `ROUND_CEILING`, fallback/no-promo order, threshold fallback and valid calculated decisions [apps/discounts/wb_shared/calculation.py](/home/pavel/projects/promo_v2/apps/discounts/wb_shared/calculation.py:16).
- API calculation не дублирует формулу: 2.1.3 вызывает `wb_excel_services.calculate(...)` [apps/discounts/wb_api/calculation/services.py](/home/pavel/projects/promo_v2/apps/discounts/wb_api/calculation/services.py:352) и использует тот же writer для workbook output [apps/discounts/wb_api/calculation/services.py](/home/pavel/projects/promo_v2/apps/discounts/wb_api/calculation/services.py:363).
- Latest/selected basis implemented: latest price/promo source selection filters successful WB API operations [apps/discounts/wb_api/calculation/services.py](/home/pavel/projects/promo_v2/apps/discounts/wb_api/calculation/services.py:55), explicit source validation checks store, step and status [apps/discounts/wb_api/calculation/services.py](/home/pavel/projects/promo_v2/apps/discounts/wb_api/calculation/services.py:255), and promo inputs come from selected operation export files, not historical `WBPromotionProduct` scans [apps/discounts/wb_api/calculation/services.py](/home/pavel/projects/promo_v2/apps/discounts/wb_api/calculation/services.py:101).
- Result Excel is based on TASK-012 price workbook and writes only `Новая скидка` via header lookup and targeted cell writes [apps/discounts/wb_excel/services.py](/home/pavel/projects/promo_v2/apps/discounts/wb_excel/services.py:800). TASK-014 tests verify row order, other columns, formulas and `_api_raw` sheet preservation [apps/discounts/wb_api/calculation/tests.py](/home/pavel/projects/promo_v2/apps/discounts/wb_api/calculation/tests.py:197).
- Operation classifier is correct: TASK-014 creates `mode=api`, `marketplace=wb`, `step_code=wb_api_discount_calculation` [apps/discounts/wb_api/calculation/services.py](/home/pavel/projects/promo_v2/apps/discounts/wb_api/calculation/services.py:317); `create_api_operation` stores `operation_type=not_applicable`, not check/process [apps/operations/services.py](/home/pavel/projects/promo_v2/apps/operations/services.py:517).
- Basis stores required operation/file/checksum/snapshot/filter timestamp/parameters/logic data [apps/discounts/wb_api/calculation/services.py](/home/pavel/projects/promo_v2/apps/discounts/wb_api/calculation/services.py:129).
- Errors block output/upload basis: summary sets `upload_blocked` from error count and creates output only when `result.error_count == 0` [apps/discounts/wb_api/calculation/services.py](/home/pavel/projects/promo_v2/apps/discounts/wb_api/calculation/services.py:354).
- Recalculation creates new operation and file version, covered by focused test [apps/discounts/wb_api/calculation/tests.py](/home/pavel/projects/promo_v2/apps/discounts/wb_api/calculation/tests.py:248).
- No WB upload/write endpoint was introduced in checked TASK-014 paths; grep for upload endpoints and `.post(` returned no matches.
- Secret checks are present for basis/summary [apps/discounts/wb_api/calculation/services.py](/home/pavel/projects/promo_v2/apps/discounts/wb_api/calculation/services.py:170) and covered by focused test [apps/discounts/wb_api/calculation/tests.py](/home/pavel/projects/promo_v2/apps/discounts/wb_api/calculation/tests.py:278).

## Required Fixes

None.

## Commands Run

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api.calculation apps.discounts.wb_excel apps.discounts.ozon_excel --verbosity 2 --noinput
```

Result: PASS, 25 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check && .venv/bin/python manage.py makemigrations --check --dry-run
```

Result: PASS, no system check issues, no migrations detected.

```bash
rg -n "/api/v2/upload|upload/task|calendar/promotions/upload|promotions/upload|method=[\"']POST[\"']|\\.post\\(" apps/discounts/wb_api apps/discounts/wb_shared apps/discounts/wb_excel -g '*.py'
```

Result: PASS, no matches.

```bash
rg -n "calculation\\.test_settings|DJANGO_SETTINGS_MODULE|sqlite|sqlite3|TASK-014|TASK014" . -g '!**/__pycache__/**'
```

Result: SQLite helper is present only at `apps/discounts/wb_api/calculation/test_settings.py`; no runtime/CI-style reference found.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test --verbosity 1 --noinput
```

Result: PASS, 145 tests.

## Open Gaps

None opened. Stage 2.1 GAP register remains without open Stage 2.1 gaps.

## Spec-Blocking Questions

None.

## TASK-015 Readiness

TASK-015 may start.

## Changed Files

- `docs/audit/AUDIT_REPORT_TASK_014.md`

