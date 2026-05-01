# Audit report: Stage 3 Product Core documentation

Дата аудита: 2026-05-01.  
Аудитор: Codex CLI.  
Область: Stage 3.0 / CORE-1 Product Core Foundation documentation. Код продукта не изменялся.

## Проверенная область

Проверена исполнительная проектная документация CORE-1 для внутреннего товарного ядра, внешнего слоя WB/Ozon листингов, миграции `MarketplaceProduct`, sync/snapshot foundation, UI, прав, audit/techlog, Excel boundary, task-scoped пакетов, implementation tasks, testing/acceptance/traceability и audit gate.

Дополнительно выполнен read-only sanity-check текущих зависимостей `MarketplaceProduct` / `OperationDetailRow.product_ref` через `rg`; найденные зависимости соответствуют рискам и inventory в migration/design docs.

## Проверенные файлы

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md`
- `docs/audit/HANDOFF_STAGE_3_PRODUCT_CORE_DOCUMENTATION_TO_AUDITOR.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_SCOPE.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_DESIGN_PLAN.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_ACCEPTANCE_TESTS.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/PRODUCT_CORE_SPEC.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/adr/ADR_LOG.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-3-product-core/IMPLEMENTATION_TASKS.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-001-data-model.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-002-migration.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-003-listings-sync-foundation.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-004-ui-internal-products.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-005-ui-marketplace-listings.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-006-mapping-workflow.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-007-permissions-audit-techlog.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-008-excel-export-boundary.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-009-tests-and-acceptance.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-010-docs-and-runbook.md`
- `docs/testing/STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md`
- `docs/testing/STAGE_3_PRODUCT_CORE_ACCEPTANCE_CHECKLISTS.md`
- `docs/traceability/STAGE_3_PRODUCT_CORE_TRACEABILITY_MATRIX.md`

## Источник требований

- Итоговое ТЗ `itogovoe_tz_platforma_marketplace_codex.txt`, редакция 25.04.2026: §1, §2.4-§2.5, §7.2, §9-§13, §18, §20-§23, §25-§27.
- Task source: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md` §§1-23.
- Handoff: `docs/audit/HANDOFF_STAGE_3_PRODUCT_CORE_DOCUMENTATION_TO_AUDITOR.md`.
- ADR: ADR-0036..ADR-0041.
- GAP: `GAP-0023` resolved/customer_decision от 2026-05-01.

## Итог

`AUDIT PASS`

## Проверка по требованиям

| Требование | Документ/раздел | Статус | Замечание |
| --- | --- | --- | --- |
| Соответствие source TZ | Stage scope, architecture/product specs, DATA_MODEL, permissions, operations, audit/techlog, tests, traceability | PASS | Документация отражает релевантные требования итогового ТЗ и task source. |
| `InternalProduct`/`ProductVariant` = ядро | `PRODUCT_CORE_ARCHITECTURE.md` lines 11-16; `PRODUCT_CORE_SPEC.md` lines 7, 127-136; `DATA_MODEL.md` lines 407-418; ADR-0036 | PASS | WB/Ozon identifiers не становятся внутренней идентичностью. |
| `MarketplaceListing` = внешний WB/Ozon слой | `MARKETPLACE_LISTINGS_SPEC.md` lines 7-34; `DATA_MODEL.md` lines 420-426; ADR-0037 | PASS | Listing привязан к marketplace + store/account и nullable internal variant. |
| Нет автоматического подтверждённого склеивания WB/Ozon | `MARKETPLACE_LISTINGS_SPEC.md` lines 80-104; `PRODUCT_CORE_UI_SPEC.md` lines 177-199; ADR-0038; GAP-0023 | PASS | Candidate suggestions только non-authoritative exact matches, confirmed mapping только ручной. |
| `GAP-0023` закрыт решением заказчика 2026-05-01 | `GAP_REGISTER.md` lines 190-212; ADR-0038 lines 391-398; traceability lines 28-30 | PASS | Статус `resolved/customer_decision`, Option B. |
| `MarketplaceProduct` защищён от удаления/очистки | `STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md` lines 36-48, 88-134; `DATA_MODEL.md` lines 491-500; ADR-0037 | PASS | Выбран option B: backfill + legacy compatibility. |
| `PromotionSnapshot` только foundation/contract | `MARKETPLACE_LISTINGS_SPEC.md` lines 177-194; `DATA_MODEL.md` line 442; TASK-PC-003 prohibitions | PASS | Полное покрытие всех promotion/action API не включено в CORE-1. |
| Sales/buyout nullable, без формул потребности | `MARKETPLACE_LISTINGS_SPEC.md` lines 157-175; `DATA_MODEL.md` line 441; ADR-0039 | PASS | Operational use для demand/production analytics требует отдельной спецификации. |
| Excel не раздувает ядро автоматически | `PRODUCT_CORE_SPEC.md` lines 119-125; `PRODUCT_CORE_UI_SPEC.md` lines 209-219; `OPERATIONS_SPEC.md` lines 266-271; ADR-0041 | PASS | Existing Excel check/process не создают internal products/mappings. |
| CORE-1 не превращён в ERP/склад/производство | `STAGE_3_PRODUCT_CORE_SCOPE.md` lines 35-49; `PRODUCT_CORE_ARCHITECTURE.md` lines 105-116; `PRODUCT_CORE_UI_SPEC.md` lines 85-95 | PASS | Future hooks есть, operational modules исключены. |
| UI не вводит в заблуждение future-блоками | `PRODUCT_CORE_UI_SPEC.md` lines 41, 85-95; acceptance checklist lines 42-50 | PASS | Future entry points disabled/planned/hidden, без пустых рабочих таблиц. |
| Object access, audit/techlog, secret safety, Client-Id | `PERMISSIONS_MATRIX.md` lines 210-250; `AUDIT_AND_TECHLOG_SPEC.md` lines 228-268; `PRODUCT_CORE_ARCHITECTURE.md` lines 131-141 | PASS | Store-scoped access и запрет Client-Id/API secrets в unsafe surfaces зафиксированы. |
| Stage 1 Excel, Stage 2.1 WB API, Stage 2.2 Ozon compatibility | `STAGE_3_PRODUCT_CORE_SCOPE.md` lines 62-72; `MIGRATION_PLAN.md` lines 116-133; `OPERATIONS_SPEC.md` lines 266-271; test protocol lines 22-24 | PASS | Регрессии обязательны, `product_ref` сохраняется raw. |
| Task-scoped reading packages | `STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md` lines 5-18, 19-176; `READING_PACKAGES.md` lines 227-241, 282-303 | PASS | Реализация не требует всем агентам читать весь проект или всё итоговое ТЗ. |
| TASK-PC-001..010 имеют границы, запреты, проверки, аудит/тесты | `IMPLEMENTATION_TASKS.md` lines 9-40; TASK-PC files | PASS | Все задачи содержат source docs, allowed/forbidden areas, checks, report route, audit/test flags. |
| Testing/acceptance/traceability покрывают требования | `STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md`; `STAGE_3_PRODUCT_CORE_ACCEPTANCE_CHECKLISTS.md`; `STAGE_3_PRODUCT_CORE_TRACEABILITY_MATRIX.md` | PASS | Покрыты model, migration, permissions, UI, mapping, sync, Excel, Stage 1/2 regression, audit/secret safety. |
| `DOCUMENTATION_MAP.md` / `docs/README.md` обновлены | `DOCUMENTATION_MAP.md` Stage 3 section; `docs/README.md` Stage 3 catalog/rules | PASS | Новые Stage 3 paths включены. |
| Нет открытых spec-blocking gaps | `GAP_REGISTER.md` lines 190-212 and statuses check | PASS | Открытых Stage 3 spec-blocking GAP не найдено. |

## Нарушения

Не выявлены.

## Риски

- Текущий код имеет широкие зависимости от `MarketplaceProduct` и `OperationDetailRow.product_ref`; migration option B снижает риск, но implementation TASK-PC-002 должен подтвердить count checks, rollback/re-run safety и Stage 1/2 regression на фактической БД/fixtures.
- Candidate suggestions даже exact-match могут быть неверными при грязных barcode/article данных; документация правильно делает их non-authoritative, но UI/tests должны явно показывать пользователю, что это только подсказки.
- `PromotionSnapshot`, sales/orders/buyout snapshots являются foundation: любая будущая аналитика потребности/производства должна пройти отдельное проектирование формул и источников.
- Internal product visibility шире store access может раскрывать агрегированные listing counts; документация требует store-filtered counts, но реализация должна тестировать отсутствие side-channel leakage.
- Secret-safety зависит от практической redaction implementation; Client-Id ограничен как unsafe surface, но нужны негативные тесты по UI, logs, snapshots, files and reports.

## Spec-blocking вопросы

Нет.

## Обязательные исправления

Нет.

## Non-blocking рекомендации

- В TASK-PC-002 приложить к отчёту фактический список найденных code dependencies по `MarketplaceProduct` / `product_ref`, чтобы migration inventory не устарел между аудитом документации и реализацией.
- В TASK-PC-006 добавить отдельный UI/test assertion, что candidate suggestion визуально отличается от confirmed mapping и требует явного действия пользователя.
- В TASK-PC-003/TASK-PC-007 отдельно проверить negative fixtures для `Client-Id`, `Api-Key`, authorization headers and secret-like values во всех safe surfaces.
- В TASK-PC-009 сделать Stage 1/2 regression evidence обязательным приложением к acceptance report, а не только отметкой в checklist.

## Решение

Реализация разрешена после этого documentation audit pass, строго по task order and preconditions in `docs/tasks/implementation/stage-3-product-core/IMPLEMENTATION_TASKS.md`. Любое отклонение, влияющее на business logic, права, операции, миграцию, Excel boundary, candidate mapping or Stage 1/2 compatibility, должно идти через ADR/GAP и повторный аудит затронутой области.
