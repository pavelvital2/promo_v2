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

## Stage 0

| Документ | Назначение |
| --- | --- |
| `docs/tasks/design/stage-0/STAGE_0_OZON_ELASTIC_UI_TZ.md` | Проектное ТЗ Stage 0 для приведения Ozon Elastic UI в порядок |
| `docs/tasks/implementation/stage-0/OZON_ELASTIC_UI_READING_PACKAGE.md` | Task-scoped пакет чтения для будущей реализации Stage 0 UI Ozon Elastic |
| `docs/testing/STAGE_0_OZON_ELASTIC_UI_ACCEPTANCE_CHECKLIST.md` | UI acceptance checklist for future Stage 0 Ozon Elastic implementation |

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
| `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md` | Архитектура InternalProduct/ProductVariant, MarketplaceListing and sync/snapshot layer Stage 3.0 CORE-1 |

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
| `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md` | Ozon API акция `Эластичный бустинг` Stage 2.2 |
| `docs/product/OZON_API_ELASTIC_UI_SPEC.md` | Stage 0 target UI spec and workflow Ozon API `Эластичный бустинг` Stage 2.2 |
| `docs/product/PRODUCT_CORE_SPEC.md` | InternalProduct/ProductVariant спецификация Stage 3.0 CORE-1 |
| `docs/product/MARKETPLACE_LISTINGS_SPEC.md` | MarketplaceListing, sync/snapshot and mapping spec Stage 3.0 CORE-1 |
| `docs/product/PRODUCT_CORE_UI_SPEC.md` | UI внутреннего каталога, листингов and mapping workflow Stage 3.0 CORE-1 |
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
| `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md` | Scope Ozon API `Эластичный бустинг` Stage 2.2 |
| `docs/stages/stage-2/STAGE_2_1_WB_ACCEPTANCE_TESTS.md` | Приёмочные сценарии Stage 2.1 |
| `docs/tasks/implementation/stage-2/IMPLEMENTATION_TASKS.md` | Индекс TASK-011..TASK-017 and TASK-019..TASK-026 |
| `docs/tasks/implementation/stage-2/TASK-011..TASK-017` | Task-scoped задачи Stage 2.1 |
| `docs/tasks/implementation/stage-2/TASK-018-DESIGN-STAGE-2-2-OZON-API.md` | Design task Stage 2.2 |
| `docs/tasks/implementation/stage-2/TASK-019..TASK-026` | Task-scoped задачи Stage 2.2 Ozon API |
| `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md` | Test protocol Stage 2.1 |
| `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md` | Acceptance checklists Stage 2.1 |
| `docs/traceability/STAGE_2_1_WB_TRACEABILITY_MATRIX.md` | Traceability matrix Stage 2.1 |
| `docs/testing/STAGE_2_2_OZON_TEST_PROTOCOL.md` | Test protocol Stage 2.2 |
| `docs/testing/STAGE_2_2_OZON_ACCEPTANCE_CHECKLISTS.md` | Acceptance checklists Stage 2.2 |
| `docs/traceability/STAGE_2_2_OZON_TRACEABILITY_MATRIX.md` | Traceability matrix Stage 2.2 |

## Stage 3.0 Product Core

| Документ | Назначение |
| --- | --- |
| `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_SCOPE.md` | Scope CORE-1 Product Core Foundation |
| `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_DESIGN_PLAN.md` | Design plan, order, audit gate |
| `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_ACCEPTANCE_TESTS.md` | Acceptance scenarios Stage 3.0 |
| `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md` | `MarketplaceProduct -> MarketplaceListing` migration plan |
| `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md` | Task-scoped reading packages Stage 3.0 |
| `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md` | Product Core architecture |
| `docs/tasks/implementation/stage-3-product-core/IMPLEMENTATION_TASKS.md` | TASK-PC-001..TASK-PC-010 index |
| `docs/tasks/implementation/stage-3-product-core/TASK-PC-001..TASK-PC-010` | Task-scoped implementation tasks CORE-1 |
| `docs/testing/STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md` | Test protocol Stage 3.0 |
| `docs/testing/STAGE_3_PRODUCT_CORE_ACCEPTANCE_CHECKLISTS.md` | Acceptance checklists Stage 3.0 |
| `docs/testing/TEST_REPORT_TASK_PC_009_STAGE_3_ACCEPTANCE.md` | Accepted TASK-PC-009 test and regression evidence for implemented Stage 3.0 |
| `docs/traceability/STAGE_3_PRODUCT_CORE_TRACEABILITY_MATRIX.md` | Traceability matrix Stage 3.0 |
| `docs/audit/HANDOFF_STAGE_3_PRODUCT_CORE_DOCUMENTATION_TO_AUDITOR.md` | Handoff package for documentation audit |
| `docs/audit/AUDIT_REPORT_TASK_PC_001_DATA_MODEL.md` .. `docs/audit/AUDIT_REPORT_TASK_PC_009_TESTS_ACCEPTANCE.md` | Implementation/test audit reports for TASK-PC-001..009 |
| `docs/reports/STAGE_3_PRODUCT_CORE_IMPLEMENTATION_REPORT.md` | TASK-PC-010 documentation/runbook closeout report |

## Control Documents

| Каталог | Документы |
| --- | --- |
| `docs/gaps/` | `docs/gaps/GAP_REGISTER.md` |
| `docs/adr/` | `docs/adr/ADR_LOG.md` |
| `docs/audit/` | `docs/audit/AUDIT_PROTOCOL.md`, `docs/audit/AUDIT_REPORT.md`, `docs/audit/AUDIT_REPORT_ROUND_2.md`, `docs/audit/AUDIT_FIX_REPORT_STAGE_2_2_OZON_DOCUMENTATION.md`, `docs/audit/HANDOFF_STAGE_3_PRODUCT_CORE_DOCUMENTATION_TO_AUDITOR.md` |
| `docs/testing/` | `docs/testing/TEST_PROTOCOL.md`, `docs/testing/ACCEPTANCE_CHECKLISTS.md`, `docs/testing/STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md`, `docs/testing/STAGE_3_PRODUCT_CORE_ACCEPTANCE_CHECKLISTS.md` |
| `docs/operations/` | `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md` |
| `docs/traceability/` | `docs/traceability/TRACEABILITY_MATRIX.md`, `docs/traceability/STAGE_3_PRODUCT_CORE_TRACEABILITY_MATRIX.md` |
| `docs/reports/` | `docs/reports/DESIGNER_FIX_REPORT.md`, `docs/reports/DOCUMENT_REORGANIZATION_REPORT.md`, `docs/reports/STAGE_3_PRODUCT_CORE_IMPLEMENTATION_REPORT.md` |

## Navigation Rules

Все пути в документации указываются repo-root-relative, например `docs/product/UI_SPEC.md`. Это намеренно: документы читаются агентами из разных подпапок, а оркестратор выдаёт пакеты как набор путей от корня проекта.

Если при работе нужен документ вне пакета, агент запрашивает уточнение у оркестратора или фиксирует gap. Самостоятельное чтение всего ТЗ вместо запроса task-scoped разделов не допускается.
