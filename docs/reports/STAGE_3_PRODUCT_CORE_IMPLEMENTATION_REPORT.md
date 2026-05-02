# STAGE_3_PRODUCT_CORE_IMPLEMENTATION_REPORT.md

Дата: 2026-05-02
Роль: техрайтер Stage 3 / TASK-PC-010 Docs And Runbook
Статус: documentation closeout completed

## Что обновлено

Обновлены финальные пользовательские и эксплуатационные документы после принятого Stage 3.0 / CORE-1 Product Core Foundation.

## Почему обновлено

TASK-PC-009 зафиксировал `PASS` по Stage 3 acceptance, регрессии Stage 1/2 и миграционной валидации. TASK-PC-010 требует синхронизировать README, карту документации, runbook и stage status с фактически реализованным поведением.

## Связанные требования ТЗ

Task-scoped source sections from TASK-PC-010: §15-§18, §22. Полное итоговое ТЗ не перечитывалось.

## Использованные входные документы

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-010-docs-and-runbook.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_DESIGN_PLAN.md`
- `docs/audit/AUDIT_REPORT_TASK_PC_001_DATA_MODEL.md` .. `docs/audit/AUDIT_REPORT_TASK_PC_009_TESTS_ACCEPTANCE.md`
- `docs/testing/TEST_REPORT_TASK_PC_009_STAGE_3_ACCEPTANCE.md`
- `README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md`

## Изменённые документы

- `README.md` - current state now reflects accepted Stage 3 Product Core, compatibility boundaries, Excel boundary and migration validation command.
- `docs/DOCUMENTATION_MAP.md` - Stage 3 report/audit/test links added.
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_DESIGN_PLAN.md` - implementation status and accepted boundaries added.
- `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md` - Stage 3 migration/release notes, validation gate, routes, CSV exports and post-update checks added.
- `docs/reports/STAGE_3_PRODUCT_CORE_IMPLEMENTATION_REPORT.md` - this TASK-PC-010 closeout report.

## Реализованные границы, отражённые в документации

- Legacy `MarketplaceProduct` remains supported through `/references/products/` list/card routes.
- Product Core routes are explicit and separate: `/references/product-core/products/`, `/references/marketplace-listings/`, unmatched listing view and mapping workflow route.
- `MarketplaceProduct -> MarketplaceListing` backfill is required through migrations; release validation must report no missing listings and no mismatched mappings.
- Mapping suggestions are exact and non-authoritative. Confirmed mapping requires explicit user action.
- Product Core CSV exports are implemented for internal products, listings, latest values, mapping report and unmatched listings; export access remains object-scoped.
- WB/Ozon Excel flows do not create `InternalProduct`/`ProductVariant` records or automatically create confirmed mappings/`ProductMappingHistory`. Existing legacy `MarketplaceProduct` compatibility sync may still mirror operation product refs into unmatched `MarketplaceListing` compatibility records.
- Stage 1 WB/Ozon Excel, Stage 2.1 WB API and Stage 2.2 Ozon Elastic regression groups passed in TASK-PC-009.

## Связанные ADR/GAP

- ADR-0036..ADR-0041 remain the Stage 3 decision set.
- `GAP-0023` is resolved/customer_decision as of 2026-05-01.
- No new GAP was opened by TASK-PC-010.

## Проверки

- Compared README/runbook/map updates against TASK-PC-001..009 audit/test reports.
- Checked Product Core route names and paths in `apps/web/urls.py` by `rg`/read-only inspection.
- Ran path/link consistency checks with `rg`.
- No product code, migrations or tests were modified.

## Оставшиеся ограничения

- Product Core sync remains foundation/snapshot/cache infrastructure; the docs do not describe future marketplace API modules as fully implemented.
- Excel import into Product Core remains out of Stage 3 scope unless a future explicit audited workflow is added.
- Release acceptance requires `manage.py migrate` before Product Core validation.
