# STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md

Трассировка: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md` §17-§18; итоговое ТЗ §25-§26.

## Общий Принцип

Implementation agents read only task-scoped packages. They do not reread the full project TZ or broad designer context by default. If a needed rule is absent, the agent asks the orchestrator or registers a GAP instead of guessing.

Every package includes:

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`
- the concrete task file

## TASK-PC-001 Data Model Foundation

Read:

- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_SCOPE.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md`
- `docs/product/PRODUCT_CORE_SPEC.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-001-data-model.md`
- `apps/marketplace_products/models.py`
- `apps/stores/models.py`
- `apps/operations/models.py`

TZ sections: only task source §§5.1.1-5.1.4, §7, §10 and final TZ §9 if orchestrator requires direct audit.

## TASK-PC-002 MarketplaceProduct Migration

Read:

- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/DELETION_ARCHIVAL_POLICY.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-002-migration.md`
- `apps/marketplace_products/**`
- `apps/operations/models.py`
- relevant `apps/discounts/**/services.py` files that read/write `MarketplaceProduct` or `OperationDetailRow.product_ref`
- relevant tests found by `rg MarketplaceProduct product_ref apps`

TZ sections: task source §§5.1.5, §8.2, §13.

## TASK-PC-003 Sync Run And Snapshot Foundation

Read:

- `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-003-listings-sync-foundation.md`
- relevant Stage 2 API service files only

TZ sections: task source §§5.1.4, §7.7-§7.12, §8.

## TASK-PC-004 Internal Products UI

Read:

- `docs/product/PRODUCT_CORE_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-004-ui-internal-products.md`
- relevant web views/forms/templates only

TZ sections: task source §§5.1.6, §9.1-§9.3.

## TASK-PC-005 Marketplace Listings UI

Read:

- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-005-ui-marketplace-listings.md`
- relevant marketplace product/listing web files only

TZ sections: task source §§5.1.6, §9.4-§9.5.

## TASK-PC-006 Mapping Workflow

Read:

- `docs/product/PRODUCT_CORE_SPEC.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-006-mapping-workflow.md`
- resolved `docs/gaps/GAP_REGISTER.md` entry `GAP-0023`

TZ sections: task source §§5.1.3, §6.2, §9.6, §19.3.

## TASK-PC-007 Permissions, Audit, Techlog

Read:

- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-007-permissions-audit-techlog.md`
- relevant identity/access, audit and techlog files only

TZ sections: task source §§5.1.7-5.1.8, §10-§11.

## TASK-PC-008 Excel Export Boundary

Read:

- `docs/product/PRODUCT_CORE_SPEC.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-008-excel-export-boundary.md`
- relevant export and file modules only

TZ sections: task source §§5.1.9, §12.

## TASK-PC-009 Tests And Acceptance

Read:

- `docs/testing/STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md`
- `docs/testing/STAGE_3_PRODUCT_CORE_ACCEPTANCE_CHECKLISTS.md`
- `docs/traceability/STAGE_3_PRODUCT_CORE_TRACEABILITY_MATRIX.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_ACCEPTANCE_TESTS.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-009-tests-and-acceptance.md`
- Stage 1/2 testing docs relevant to regression only

TZ sections: task source §14, §22.

## TASK-PC-010 Docs And Runbook

Read:

- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_DESIGN_PLAN.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-010-docs-and-runbook.md`
- docs changed by TASK-PC-001..TASK-PC-009
- audit/test reports for Stage 3 implementation

TZ sections: task source §15-§18, §22.

## Documentation Auditor Package

Read:

- `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md`
- `docs/DOCUMENTATION_MAP.md`
- all files in `docs/stages/stage-3-product-core/`
- `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md`
- `docs/product/PRODUCT_CORE_SPEC.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- updated shared docs listed in `docs/audit/HANDOFF_STAGE_3_PRODUCT_CORE_DOCUMENTATION_TO_AUDITOR.md`
- all files in `docs/tasks/implementation/stage-3-product-core/`
- Stage 3 testing and traceability docs

The auditor may read relevant final TZ sections for critical verification; full final TZ reread is not the default for implementation agents.
