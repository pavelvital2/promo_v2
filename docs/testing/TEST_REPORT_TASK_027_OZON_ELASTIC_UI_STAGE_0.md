# TEST_REPORT_TASK_027_OZON_ELASTIC_UI_STAGE_0

Дата: 2026-05-01  
Задача: TASK-027 Ozon Elastic UI Stage 0 implementation

## Scope

Реализован UI слой страницы `Маркетплейсы / Ozon / Акции / API / Эластичный бустинг` без изменения бизнес-логики расчёта, Ozon API client/write behavior, permission codes, operation step codes, file contour, audit/techlog.

## Что изменено

- Страница Ozon Elastic разделена на вкладки `Рабочий процесс`, `Результат`, `Диагностика`.
- Workflow приведён к 7 операторским шагам; три read-only download operations объединены только на уровне UI.
- Permission surface после audit fixes: opening workflow/page requires `ozon.api.actions.view`; `ozon.api.operation.view` alone does not open the page. Diagnostics additionally require owner/global admin/local admin persona plus existing operation/audit/techlog/log-scope permissions.
- Header, workflow badges, substeps and operation card status now use human-readable labels instead of raw `review_state` / `operation.status`.
- Audit blocker fix: Ozon connection status in operator-facing header now renders Russian labels (`Активно`, `Не настроено`, `Проверка не пройдена`), and workflow blocking text no longer says raw English `active Ozon API connection`.
- Raw `basis`, checksum/source/API metadata и JSON-like summaries убраны из workflow и доступны в diagnostics/operation card по существующим правам.
- Результат сгруппирован человеко-читаемо, группы показывают до 10 строк и компактный `0` для пустых групп.
- Result filters cover source, action, reason/status, upload readiness, upload status and product search.
- `Excel для ручной загрузки - Stage 1-compatible template` показан в workflow step 6 и в files block результата; `Excel результата` убран из main workflow.
- Files block now shows `ozon_api_elastic_upload_report` when present. Successful/finished upload shows final block `Загрузка завершена` with sent/accepted/rejected counts, operation card link and manual Excel link.
- Diagnostics are grouped into operation evidence, calculation basis, snapshots/checksums/source operations, API metadata, audit/techlog links and technical codes.
- Deactivate group confirmation в UI сохранён как отдельный safety control.
- Operation card keeps raw structures such as `groups_count`, `basis`, source/API details and `result_code` out of `Краткий результат`; they remain in collapsed technical blocks with scrollable/preformatted values.
- Marketplace page приведена к hierarchy `marketplace -> section -> mode -> scenario`, future sections marked `Планируется`.
- Mobile tables/technical values wrapped in local scroll containers.

## Проверки

| Check | Result |
| --- | --- |
| `.venv/bin/python manage.py test apps.web --verbosity 2 --noinput` without `.env.runtime` | BLOCKED by local PostgreSQL credentials: password authentication failed for user `promo_v2`. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.web --verbosity 1 --noinput` | PASS, 37 tests after audit blocker fix. |
| Focused Ozon Elastic / operation-card tests after audit fixes | PASS: permission gate, human-readable statuses, filters/upload report/final block, diagnostics grouping/persona gate, operation card raw summary separation. |
| Focused audit blocker regression: `apps.web.tests.HomeSmokeTests.test_ozon_elastic_connection_status_is_human_readable_in_header_and_workflow` | PASS: header badge uses Russian connection labels; raw `not_configured` / `check_failed` and `active Ozon API connection` are absent from operator-facing page. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` | PASS, no issues. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run` | PASS, no changes detected. |
| Playwright desktop screenshot | PASS: `tmp/task027_screens/ozon-elastic-desktop.png`. |
| Playwright mobile screenshot/result tab at `390x844` | PASS: `tmp/task027_screens/ozon-elastic-mobile-result.png`. |
| Mobile page-level horizontal overflow check after audit fixes | PASS: Playwright `390x844`, rendered result tab with long values, `scrollWidth=390`, `clientWidth=390`, overflow `False`. |

Playwright required installing the Chromium browser cache with `.venv/bin/python -m playwright install chromium`; the first download attempt timed out twice for headless shell and then completed on retry.

## Acceptance Checklist Notes

- Stage 0 UI documentation audit pass is referenced by TASK-027; no new product-code scope outside TASK-027 was used.
- Diagnostics tab requires existing operation/audit/techlog/log scope permissions; `ozon.api.operation.view` alone is not enough.
- Diagnostics tab also requires owner/global admin/local admin persona; marketplace manager with individually granted log permissions still does not see diagnostics.
- Ozon Elastic workflow/page opening requires `ozon.api.actions.view`.
- Select-action UI context is not broader than spec: it requires `ozon.api.actions.view`; the existing service-side action execution permission remains unchanged.
- Secrets and direct Client-Id/Api-Key/auth-like keys are redacted in technical render helpers.
- Future inactive marketplace entries expose no forms/buttons/routes.
- `Отклонено Ozon` group is always present with counter; it remains empty until upload rejections exist.

## Gaps / Questions

No new UX/functionality gap found during implementation. No changes were made to `docs/gaps/GAP_REGISTER.md`.

## Blockers

No product blocker remains. Local test command without `.env.runtime` is blocked by environment credentials only; `.env.runtime` test path passes.

## Ready State

Ready for tester/auditor review.
