# CORE_2_READING_PACKAGES.md

Статус: исполнительная проектная документация CORE-2, обновлена после AUDIT PASS по решениям заказчика; готова к follow-up audit/recheck.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§13, §11.15.

## Общий принцип

Implementation agents read only task-scoped packages. They do not reread the full final TZ by default. If a needed rule is absent, ambiguous or blocked, the agent records/uses GAP instead of guessing.

Every CORE-2 package includes:

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_SCOPE.md`
- concrete task section from `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md`

`GAP-CORE2-001`..`GAP-CORE2-005` are retained in packages as resolved customer decisions with implementation constraints. Agents must follow the recorded decisions and must not treat the old open-gap wording from historical audit reports as current scope.

## TASK-PC2-001 Data Model And Migration

Read:

- `CORE_2_MODEL_AND_MIGRATION_PLAN.md`
- `CORE_2_OPERATION_LINKING_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md`
- `apps/operations/models.py`
- `apps/product_core/models.py`

GAP/ADR: ADR-0044, ADR-0045, GAP-CORE2-001 resolved decision, GAP-CORE2-003 resolved decision.

## TASK-PC2-002 Marketplace Listing Sync Integration

Read:

- `CORE_2_API_SYNC_SPEC.md`
- `CORE_2_DATA_FLOW.md`
- `CORE_2_SNAPSHOT_FILLING_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/product/WB_API_PRICE_EXPORT_SPEC.md`
- `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`
- `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`
- relevant Stage 2 API service files only.

GAP/ADR: ADR-0042, ADR-0046, GAP-CORE2-002 resolved decision and endpoint evidence gate, GAP-CORE2-004 resolved decision.

## TASK-PC2-003 Normalized Article Linkage And Auto-Create

Read:

- `CORE_2_MAPPING_RULES_SPEC.md`
- `CORE_2_UI_UX_SPEC.md`
- `docs/product/PRODUCT_CORE_SPEC.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `apps/product_core/services.py`

GAP/ADR: ADR-0043, ADR-0045, GAP-CORE2-001 resolved decision, GAP-CORE2-005 resolved decision with TASK-PC2-003 scope update, GAP-CORE2-006 resolved decision, GAP-CORE2-007 deferred/future task and non-blocking for the narrowed API linkage slice.

## TASK-PC2-004 Operation Row FK Enrichment

Read:

- `CORE_2_OPERATION_LINKING_SPEC.md`
- `CORE_2_MODEL_AND_MIGRATION_PLAN.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md`
- relevant `apps/discounts/**` operation detail writer files found by `rg "OperationDetailRow|product_ref" apps/discounts apps/operations`.

GAP/ADR: ADR-0044, GAP-CORE2-003 resolved decision.

## TASK-PC2-005 Snapshot Filling

Read:

- `CORE_2_SNAPSHOT_FILLING_SPEC.md`
- `CORE_2_API_SYNC_SPEC.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `apps/product_core/models.py`
- `apps/product_core/services.py`

GAP/ADR: ADR-0046, GAP-CORE2-002 resolved decision and endpoint evidence gate, GAP-CORE2-004 resolved decision.

## TASK-PC2-006 Product Core Exports And Excel Boundary

Read:

- `CORE_2_EXCEL_EXPORT_SPEC.md`
- `CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/architecture/FILE_CONTOUR.md`
- `apps/product_core/exports.py`
- relevant web export views only.

GAP/ADR: ADR-0042, ADR-0044, GAP-CORE2-005 resolved decision.

## TASK-PC2-007 Product Core UI Integration

Read:

- `CORE_2_UI_UX_SPEC.md`
- `CORE_2_MAPPING_RULES_SPEC.md`
- `CORE_2_OPERATION_LINKING_SPEC.md`
- `CORE_2_EXCEL_EXPORT_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- relevant web views/forms/templates only.

GAP/ADR: ADR-0042..ADR-0046, GAP-CORE2-001..005 as relevant.

## TASK-PC2-008 Permissions, Audit, Techlog, Redaction

Read:

- `CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- relevant identity/audit/techlog/redaction files only.

GAP/ADR: ADR-0042..ADR-0046.

## TASK-PC2-009 Regression And Acceptance

Read:

- `CORE_2_TEST_PLAN.md`
- `CORE_2_ACCEPTANCE_CHECKLIST.md`
- `docs/testing/TEST_PROTOCOL.md`
- Stage 1/2 and Product Core regression docs relevant to selected commands;
- implementation handoffs for TASK-PC2-001..008.

GAP/ADR: all open CORE-2 GAP and ADR list.

## TASK-PC2-010 Documentation And Rollout Closeout

Read:

- `CORE_2_ROLLOUT_RUNBOOK.md`
- `CORE_2_DESIGN_HANDOFF.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`
- implementation/test/audit reports;
- docs changed by CORE-2 implementation.

GAP/ADR: all CORE-2 records.

## Documentation Auditor Package

Read:

- input TZ: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md`
- all files in `docs/stages/stage-3-product-core/core-2/`
- updated shared docs:
  - `docs/DOCUMENTATION_MAP.md`
  - `docs/roles/READING_PACKAGES.md`
  - `docs/adr/ADR_LOG.md`
  - `docs/gaps/GAP_REGISTER.md`
  - `docs/project/CURRENT_STATUS.md`
- CORE-1 validation reports listed in CORE-2 scope.

Auditor may read relevant final TZ sections for critical verification. Full final TZ reread is not default for implementation agents.
