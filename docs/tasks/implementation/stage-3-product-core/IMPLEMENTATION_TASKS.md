# IMPLEMENTATION_TASKS.md

Трассировка: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md` §16-§18.

## Назначение

Index of Stage 3.0 / CORE-1 Product Core Foundation implementation tasks. These tasks are not ready for execution until documentation audit result is `AUDIT PASS`.

## Preconditions

- `docs/audit/AUDIT_REPORT_STAGE_3_PRODUCT_CORE_DOCUMENTATION.md` exists.
- Audit result is `AUDIT PASS`, or all remarks are explicitly non-blocking.
- No open spec-blocking GAP for the affected slice.
- Stage 1/2 regression baselines are preserved.
- No implementation task may change product code outside its allowed files.

## Task Order

| Order | Task | Purpose | Dependencies |
| --- | --- | --- | --- |
| 1 | `TASK-PC-001-data-model.md` | Internal product/listing/snapshot models and dictionaries | audit pass |
| 2 | `TASK-PC-002-migration.md` | Backfill `MarketplaceProduct` into `MarketplaceListing` compatibility layer | TASK-PC-001 |
| 3 | `TASK-PC-003-listings-sync-foundation.md` | Sync run/snapshot foundation and safe current cache | TASK-PC-001, selected parts after TASK-PC-002 |
| 4 | `TASK-PC-004-ui-internal-products.md` | Internal products/variants UI | TASK-PC-001 |
| 5 | `TASK-PC-005-ui-marketplace-listings.md` | Marketplace listings UI | TASK-PC-001, TASK-PC-002 |
| 6 | `TASK-PC-006-mapping-workflow.md` | Map/unmap workflow with exact non-authoritative candidates | TASK-PC-004, TASK-PC-005, TASK-PC-007 permissions ready or paired |
| 7 | `TASK-PC-007-permissions-audit-techlog.md` | Permissions, audit, techlog, histories | TASK-PC-001 |
| 8 | `TASK-PC-008-excel-export-boundary.md` | Exports and Excel no-auto-import boundary | TASK-PC-004, TASK-PC-005, TASK-PC-007 |
| 9 | `TASK-PC-009-tests-and-acceptance.md` | Tests, regression and acceptance execution | TASK-PC-001..TASK-PC-008 |
| 10 | `TASK-PC-010-docs-and-runbook.md` | Post-implementation docs/runbook sync | TASK-PC-009 reports |

## Global Prohibitions

- Do not auto-create internal products from Excel/API rows.
- Do not auto-merge WB and Ozon listings.
- Do not delete/truncate/replace `MarketplaceProduct`.
- Do not change Stage 1 WB/Ozon Excel business logic.
- Do not change Stage 2.1 WB API or Stage 2.2 Ozon Elastic behavior outside explicit compatibility fixes.
- Do not expose API secrets in UI, files, audit, techlog, snapshots or reports.
- Do not treat future stock/production/supplier/label hooks as implemented modules.
