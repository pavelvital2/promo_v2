# STAGE_3_PRODUCT_CORE_DESIGN_PLAN.md

Трассировка: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md` §15-§22; итоговое ТЗ §25-§26.

## Назначение

План фиксирует, как подготовленный комплект документации должен использоваться перед реализацией Stage 3.0 / CORE-1 Product Core Foundation.

## Документы Комплекта

| Группа | Документы |
| --- | --- |
| Stage scope | `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_SCOPE.md`, `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_DESIGN_PLAN.md`, `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_ACCEPTANCE_TESTS.md`, `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md`, `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md` |
| Architecture/product | `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md`, `docs/product/PRODUCT_CORE_SPEC.md`, `docs/product/MARKETPLACE_LISTINGS_SPEC.md`, `docs/product/PRODUCT_CORE_UI_SPEC.md` |
| Shared updates | `docs/architecture/DATA_MODEL.md`, `docs/product/PERMISSIONS_MATRIX.md`, `docs/product/OPERATIONS_SPEC.md`, `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`, `docs/adr/ADR_LOG.md`, `docs/gaps/GAP_REGISTER.md` |
| Implementation tasks | `docs/tasks/implementation/stage-3-product-core/IMPLEMENTATION_TASKS.md`, `TASK-PC-001..TASK-PC-010` |
| Testing/traceability/audit | `docs/testing/STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md`, `docs/testing/STAGE_3_PRODUCT_CORE_ACCEPTANCE_CHECKLISTS.md`, `docs/traceability/STAGE_3_PRODUCT_CORE_TRACEABILITY_MATRIX.md`, `docs/audit/HANDOFF_STAGE_3_PRODUCT_CORE_DOCUMENTATION_TO_AUDITOR.md` |

## Execution Order After Audit Pass

1. Run documentation audit using `docs/audit/HANDOFF_STAGE_3_PRODUCT_CORE_DOCUMENTATION_TO_AUDITOR.md`.
2. Block implementation until auditor creates `docs/audit/AUDIT_REPORT_STAGE_3_PRODUCT_CORE_DOCUMENTATION.md` with `AUDIT PASS`.
3. Start implementation with `TASK-PC-001-data-model.md`.
4. Implement `TASK-PC-002-migration.md` only after data model audit pass.
5. Implement sync/snapshot foundation after model and migration contracts are fixed.
6. UI tasks can start after backend model contracts are stable; mapping UI depends on listings UI.
7. Permissions/audit/techlog must be audited before exposing write actions.
8. Test/acceptance task closes the stage only after Stage 1/2 regression and Product Core acceptance pass.
9. Tech writer/runbook task runs last and must not change product behavior.

## Parallel Work Rules

Allowed after audit pass:

- UI internal products and UI listings can be implemented in parallel after shared view/query contracts are agreed by orchestrator.
- Tests can be prepared in parallel with implementation as long as they do not change production code outside the assigned task.

Not allowed in parallel without orchestration lock:

- migrations and data model tasks;
- permission catalog and seed changes;
- mapping workflow writes;
- operation/sync run status contracts;
- shared templates/routes for the same screen;
- changes to Stage 1/2 business flows.

## Design Notes

What already exists:

- Django/PostgreSQL modular monolith with server-rendered UI.
- `StoreAccount`, `Operation`, `Run`, `FileObject/FileVersion`, audit, techlog, permissions and object access.
- `MarketplaceProduct` and `MarketplaceProductHistory` created from Stage 1 Excel detail rows and WB API prices.
- `OperationDetailRow.product_ref` as raw product reference in Stage 1/2 flows.
- Stage 2.1 WB API and Stage 2.2 Ozon Elastic API use `Operation.step_code`.

High-risk dependencies:

- `apps/marketplace_products/services.py` writes `MarketplaceProduct` from operation detail rows.
- `apps/discounts/wb_api/prices/services.py` updates `MarketplaceProduct` from WB price API.
- `apps/web/views.py` exposes current product list/card on `MarketplaceProduct`.
- tests under `apps/web`, `apps/discounts/wb_api`, `apps/discounts/wb_excel`, `apps/discounts/ozon_excel`, `apps/operations` assert current `product_ref`/`MarketplaceProduct` behavior.

Chosen migration design:

- Option B from the design TZ: create new `MarketplaceListing`, backfill from `MarketplaceProduct`, keep legacy `MarketplaceProduct` as deprecated/compatibility layer until an audited removal/rename task exists.

## Audit Gate

No developer, tester or tech writer implementation task may start before documentation audit result:

```text
AUDIT PASS
```

`AUDIT PASS WITH REMARKS` allows implementation only if the auditor explicitly marks all remarks non-blocking. Any spec-blocking remark returns to design/gap handling.

## Implementation Status

Status as of 2026-05-02: Stage 3.0 / CORE-1 Product Core Foundation implementation tasks TASK-PC-001..009 are accepted by audit/test reports, and TASK-PC-010 performed the documentation/runbook closeout.

Accepted boundaries:

- `MarketplaceProduct` remains as the legacy compatibility layer. Existing `/references/products/` routes keep legacy list/card behavior and do not route to `InternalProduct` by primary-key collision.
- Product Core UI is exposed through explicit routes under `/references/product-core/products/` and `/references/marketplace-listings/`.
- Mapping is manual. Candidate suggestions are exact and non-authoritative; they may mark `needs_review`/`conflict` but do not confirm a mapping without explicit user action.
- CSV exports exist for internal products, marketplace listings, latest listing values, mapping report and unmatched listings. Exports respect object access and snapshot visibility.
- WB/Ozon Excel workflows remain Stage 1 file/operation flows and do not create `InternalProduct`/`ProductVariant` records or automatically create confirmed mappings/`ProductMappingHistory`. Existing legacy `MarketplaceProduct` compatibility sync may still mirror operation product refs into unmatched `MarketplaceListing` compatibility records.
- Stage 1 WB/Ozon Excel, Stage 2.1 WB API and Stage 2.2 Ozon Elastic regression groups passed in the Stage 3 acceptance run.
- Runtime rollout requires applying Stage 3 migrations before Product Core validation and acceptance checks.
