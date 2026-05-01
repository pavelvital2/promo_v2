# TASK-PC-002-migration.md

ID: TASK-PC-002  
Тип задачи: реализация Stage 3.0 / migration  
Агент: разработчик Codex CLI  
Цель: migrate/backfill legacy `MarketplaceProduct` into `MarketplaceListing` without data loss.

## Источник Истины

- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`

## Входные Документы

- package TASK-PC-002 from `STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- `docs/architecture/DELETION_ARCHIVAL_POLICY.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`

## Разделы ТЗ Для Чтения

- task source §§5.1.5, §8.2, §13

## Связанные ADR/GAP

- ADR-0037
- ADR-0040

## Разрешённые Файлы / Области Изменения

- migration files for `MarketplaceListing` backfill and nullable FK enrichment
- `apps/marketplace_products/` compatibility services/tests
- focused references in `apps/operations/` only for nullable FK and read compatibility

## Запрещённые Файлы / Области Изменения

- deleting/truncating `MarketplaceProduct`
- rewriting historical operation rows, summaries or files
- creating internal products/variants from legacy products
- changing Stage 1/2 calculation logic

## Ожидаемый Результат

- Every legacy marketplace product is represented by a marketplace listing or a documented conflict row.
- Legacy `MarketplaceProduct` remains available.
- `OperationDetailRow.product_ref` remains raw and unchanged.

## Критерии Завершённости

- Migration is reversible where feasible and documents non-reversible copy limitations.
- Validation checks compare before/after counts.
- Stage 1/2 regression tests pass.
- Rollback plan is documented in task report.

## Обязательные Проверки

- migration tests on sanitized data
- Stage 1 WB/Ozon Excel focused regression
- Stage 2.1 WB API price/product regression
- Stage 2.2 Ozon API smoke/focused regression if touched

## Формат Отчёта

Include migration order, data validation output, rollback notes, changed files, tests, gaps and audit handoff.

## Получатель Результата

Оркестратор -> аудитор.

Нужен аудит: да.  
Нужны тесты: да.  
Нужен техрайтер: нет.

