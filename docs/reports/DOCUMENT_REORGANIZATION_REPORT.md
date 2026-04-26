# DOCUMENT_REORGANIZATION_REPORT.md

Дата: 2026-04-25

## Что сделано

Документация реорганизована из плоской структуры корня в каталог `docs/` по назначению документов. Итоговое ТЗ не удалено и не заменено исполнительной документацией.

Созданы:

- `docs/README.md` - точка входа и краткая карта документации;
- `docs/DOCUMENTATION_MAP.md` - подробная карта документов;
- `docs/source/README.md` - правила использования исходных TXT;
- `docs/orchestration/AGENTS.md` - полные агентные правила после реорганизации;
- `docs/roles/READING_PACKAGES.md` - пакеты чтения по ролям;
- `docs/reports/DOCUMENT_REORGANIZATION_REPORT.md` - этот отчёт.

## Что перемещено

| Было | Стало |
| --- | --- |
| `ORCHESTRATION.md`, `TASK_TEMPLATES.md`, `HANDOFF_TEMPLATES.md`, `PARALLEL_WORK_RULES.md`, `DOCUMENTATION_UPDATE_PROTOCOL.md` | `docs/orchestration/` |
| `AGENT_ROLES_MATRIX.md` | `docs/roles/` |
| `ARCHITECTURE.md`, `DATA_MODEL.md`, `FILE_CONTOUR.md`, `DELETION_ARCHIVAL_POLICY.md`, `AUDIT_AND_TECHLOG_SPEC.md`, `PROJECT_STRUCTURE.md` | `docs/architecture/` |
| `UI_SPEC.md`, `PERMISSIONS_MATRIX.md`, `OPERATIONS_SPEC.md`, `WB_DISCOUNTS_EXCEL_SPEC.md`, `OZON_DISCOUNTS_EXCEL_SPEC.md` | `docs/product/` |
| `MODULE_SPECIFICATIONS/README.md` | `docs/product/modules/README.md` |
| `PROJECT_DOCUMENTATION_PLAN.md`, `ACCEPTANCE_TESTS.md` | `docs/stages/stage-1/` |
| `IMPLEMENTATION_TASKS.md`, `IMPLEMENTATION_TASKS/*.md` | `docs/tasks/implementation/stage-1/` |
| `GAP_REGISTER.md` | `docs/gaps/` |
| `ADR_LOG.md` | `docs/adr/` |
| `AUDIT_PROTOCOL.md`, `AUDIT_REPORT.md`, `AUDIT_REPORT_ROUND_2.md` | `docs/audit/` |
| `DESIGNER_FIX_REPORT.md` | `docs/reports/` |
| `TEST_PROTOCOL.md`, `ACCEPTANCE_CHECKLISTS.md` | `docs/testing/` |
| `RELEASE_AND_UPDATE_RUNBOOK.md` | `docs/operations/` |
| `TRACEABILITY_MATRIX.md` | `docs/traceability/` |

## Что осталось в корне

| Файл | Почему оставлен |
| --- | --- |
| `AGENTS.md` | Короткий root entrypoint для Codex CLI; указывает на `docs/README.md` и `docs/orchestration/AGENTS.md` |
| `itogovoe_tz_platforma_marketplace_codex.txt` | Источник истины для аудита и спорных требований; не удаляется и не заменяется |
| `promt_start_project.txt` | Исходный стартовый prompt; оставлен для истории входного контекста и ссылок |

## Где карта документации

- Краткая карта и правила чтения: `docs/README.md`.
- Подробная карта: `docs/DOCUMENTATION_MAP.md`.
- Ссылки на исходники: `docs/source/README.md`.

## Где reading packages

Пакеты чтения по ролям: `docs/roles/READING_PACKAGES.md`.

Пакеты созданы для:

- оркестратора;
- проектировщика документации;
- аудитора документации;
- разработчика платформенного каркаса;
- разработчика WB Excel;
- разработчика Ozon Excel;
- frontend/UI агента;
- тестировщика;
- техрайтера.

Каждый пакет запрещает полное чтение итогового ТЗ по умолчанию и требует чтения только task-scoped разделов ТЗ, выданных оркестратором.

## Какие ссылки обновлены

Внутренние ссылки и упоминания старых путей обновлены на repo-root-relative формат:

- `docs/architecture/...`;
- `docs/product/...`;
- `docs/tasks/implementation/stage-1/...`;
- `docs/gaps/GAP_REGISTER.md`;
- `docs/adr/ADR_LOG.md`;
- `docs/audit/...`;
- `docs/testing/...`;
- `docs/operations/...`;
- `docs/traceability/...`.

`docs/DOCUMENTATION_MAP.md` фиксирует правило: все пути в документации указываются относительно корня репозитория.

## Обновлённые правила эскалации

Зафиксировано в `AGENTS.md`, `docs/orchestration/AGENTS.md`, `docs/orchestration/ORCHESTRATION.md`, `docs/README.md`, `docs/roles/READING_PACKAGES.md` и `docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md`:

- UX/functionality gaps веб-панели передаются по маршруту: агент -> оркестратор -> заказчик;
- spec-blocking gaps передаются по маршруту: агент -> оркестратор -> заказчик;
- аудитор сверяет проектную документацию с исходным ТЗ;
- исполнители работают по утверждённой исполнительной документации и task-scoped пакетам.

## Риски и что проверить аудитору

- Проверить, что в task-scoped списках задач нет ссылок на старые root-документы.
- Проверить, что `docs/roles/READING_PACKAGES.md` покрывает все роли из задачи заказчика.
- Проверить, что перенос не изменил бизнес-логику WB/Ozon, модель прав, check/process, файловый контур, audit/techlog separation и открытые gaps.
- Проверить, что `GAP-0002`, `GAP-0003`, `GAP-0004`, `GAP-0007`, `GAP-0008`, `GAP-0009` остались открытыми/не закрытыми предположениями.
- Проверить, что исходное ТЗ осталось доступным как источник истины.
