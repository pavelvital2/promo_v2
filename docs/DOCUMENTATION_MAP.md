# DOCUMENTATION_MAP.md

Назначение: подробная карта исполнительной документации и правила навигации после реорганизации.

## Source

| Документ | Назначение | Когда читать |
| --- | --- | --- |
| `docs/source/README.md` | Объясняет, где лежат исходные TXT и как использовать ТЗ | При старте, аудите, споре |
| `itogovoe_tz_platforma_marketplace_codex.txt` | Источник истины | Только указанные разделы или аудит критичных требований |
| `promt_start_project.txt` | Исходные правила оркестрации | Оркестратор/аудитор при проверке процесса |

## Orchestration

| Документ | Назначение |
| --- | --- |
| `docs/orchestration/AGENTS.md` | Полные агентные правила проекта |
| `docs/orchestration/ORCHESTRATION.md` | Процесс управления документацией, реализацией, аудитом и gaps |
| `docs/orchestration/TASK_TEMPLATES.md` | Шаблоны постановки задач и GAP-записей |
| `docs/orchestration/HANDOFF_TEMPLATES.md` | Шаблоны передачи между агентами |
| `docs/orchestration/PARALLEL_WORK_RULES.md` | Правила параллельной работы |
| `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md` | Протокол обновления документации |

## Roles

| Документ | Назначение |
| --- | --- |
| `docs/roles/AGENT_ROLES_MATRIX.md` | Матрица ролей и ответственности |
| `docs/roles/READING_PACKAGES.md` | Пакеты чтения по ролям и типам задач |

## Architecture

| Документ | Назначение |
| --- | --- |
| `docs/architecture/ARCHITECTURE.md` | Архитектурный baseline и границы модулей |
| `docs/architecture/DATA_MODEL.md` | Сущности, связи, системные словари |
| `docs/architecture/PROJECT_STRUCTURE.md` | Структура будущего проекта |
| `docs/architecture/FILE_CONTOUR.md` | Файлы, версии, хранение, retention |
| `docs/architecture/DELETION_ARCHIVAL_POLICY.md` | Удаление, блокировка, деактивация, архивирование |
| `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md` | Audit actions, techlog events, поля и видимость |
| `docs/architecture/API_CONNECTIONS_SPEC.md` | API-подключения, secrets, rate limits, snapshots Stage 2.1 |

## Product

| Документ | Назначение |
| --- | --- |
| `docs/product/UI_SPEC.md` | Экранная спецификация веб-панели |
| `docs/product/PERMISSIONS_MATRIX.md` | Роли, права, object access, owner |
| `docs/product/OPERATIONS_SPEC.md` | Операции, run, check/process, статусы |
| `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md` | WB Excel сценарий скидок |
| `docs/product/WB_DISCOUNTS_API_SPEC.md` | WB API сценарий скидок Stage 2.1 |
| `docs/product/WB_API_PRICE_EXPORT_SPEC.md` | WB API скачивание цен Stage 2.1 |
| `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md` | WB API текущие акции Stage 2.1 |
| `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md` | Ozon Excel сценарий скидок |
| `docs/product/modules/README.md` | Модульная карта stage 1 |

## Stage 1

| Документ | Назначение |
| --- | --- |
| `docs/stages/stage-1/PROJECT_DOCUMENTATION_PLAN.md` | План исполнительной документации |
| `docs/stages/stage-1/ACCEPTANCE_TESTS.md` | Приёмочные тесты и контрольные файлы этапа 1 |
| `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md` | Индекс и правила задач реализации |
| `docs/tasks/implementation/stage-1/README.md` | Формат отчёта и правила handoff по implementation tasks |
| `docs/tasks/implementation/stage-1/` files `TASK-*` | Конкретные задачи реализации |

## Stage 2

| Документ | Назначение |
| --- | --- |
| `docs/stages/stage-2/STAGE_2_SCOPE.md` | Split Stage 2: 2.1 WB API, 2.2 Ozon API |
| `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md` | Scope 2.1.1-2.1.4 WB API |
| `docs/stages/stage-2/STAGE_2_1_WB_ACCEPTANCE_TESTS.md` | Приёмочные сценарии Stage 2.1 |
| `docs/tasks/implementation/stage-2/IMPLEMENTATION_TASKS.md` | Индекс TASK-011..TASK-017 |
| `docs/tasks/implementation/stage-2/TASK-011..TASK-017` | Task-scoped задачи Stage 2.1 |
| `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md` | Test protocol Stage 2.1 |
| `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md` | Acceptance checklists Stage 2.1 |
| `docs/traceability/STAGE_2_1_WB_TRACEABILITY_MATRIX.md` | Traceability matrix Stage 2.1 |

## Control Documents

| Каталог | Документы |
| --- | --- |
| `docs/gaps/` | `docs/gaps/GAP_REGISTER.md` |
| `docs/adr/` | `docs/adr/ADR_LOG.md` |
| `docs/audit/` | `docs/audit/AUDIT_PROTOCOL.md`, `docs/audit/AUDIT_REPORT.md`, `docs/audit/AUDIT_REPORT_ROUND_2.md` |
| `docs/testing/` | `docs/testing/TEST_PROTOCOL.md`, `docs/testing/ACCEPTANCE_CHECKLISTS.md` |
| `docs/operations/` | `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md` |
| `docs/traceability/` | `docs/traceability/TRACEABILITY_MATRIX.md` |
| `docs/reports/` | `docs/reports/DESIGNER_FIX_REPORT.md`, `docs/reports/DOCUMENT_REORGANIZATION_REPORT.md` |

## Navigation Rules

Все пути в документации указываются repo-root-relative, например `docs/product/UI_SPEC.md`. Это намеренно: документы читаются агентами из разных подпапок, а оркестратор выдаёт пакеты как набор путей от корня проекта.

Если при работе нужен документ вне пакета, агент запрашивает уточнение у оркестратора или фиксирует gap. Самостоятельное чтение всего ТЗ вместо запроса task-scoped разделов не допускается.
