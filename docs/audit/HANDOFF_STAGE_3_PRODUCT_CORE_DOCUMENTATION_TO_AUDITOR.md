# HANDOFF_STAGE_3_PRODUCT_CORE_DOCUMENTATION_TO_AUDITOR.md

Исходная задача: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md`  
Исполнитель: проектировщик Codex CLI  
Получатель: аудитор Codex CLI  
Статус: needs_audit

## Область Аудита

Stage 3.0 / CORE-1 Product Core Foundation documentation. No product code was changed by the designer task.

## Проверяемые Файлы

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
- `docs/DOCUMENTATION_MAP.md`
- `docs/README.md`

## Требования Для Сверки

- task source §§1-23
- final TZ relevant sections §1, §2.4-§2.5, §7.2, §9-§13, §18, §20-§23, §25-§27

## Что Проверить

- InternalProduct/ProductVariant are the core.
- MarketplaceListing is external and store-specific.
- WB/Ozon are not auto-merged.
- Candidate suggestions are non-authoritative exact `seller_article` / `barcode` / external identifier matches only and cannot create confirmed mappings automatically.
- `MarketplaceProduct` is protected by migration/backfill/compatibility plan.
- Stage 1 Excel and Stage 2 API flows remain compatible.
- Operation immutability and `product_ref` raw compatibility are preserved.
- Permissions and object access do not leak hidden store/listing data.
- Audit/techlog and secret redaction are complete.
- Excel boundary is explicit.
- Implementation tasks are task-scoped and blocked by audit gate.
- Documentation map includes new paths.

## Known Risks

- Current code has broad `MarketplaceProduct` dependencies; direct rename is intentionally not selected.
- `GAP-0023` is resolved by customer decision 2026-05-01, Option B; candidate suggestions still require careful audit because they are UX/functionality behavior.
- Future stock/production/supplier/label hooks must stay non-operational in CORE-1 UI.

## Known Gaps / Questions

- No open spec-blocking Stage 3.0 / CORE-1 GAP is recorded after the `GAP-0023` decision update.

## Required Auditor Output

Create:

```text
docs/audit/AUDIT_REPORT_STAGE_3_PRODUCT_CORE_DOCUMENTATION.md
```

Use result:

```text
AUDIT PASS
AUDIT FAIL
AUDIT PASS WITH NON-BLOCKING REMARKS
```

Implementation remains prohibited unless result is `AUDIT PASS` or auditor explicitly marks all remarks non-blocking.
