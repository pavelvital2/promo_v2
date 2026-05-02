# CORE-2 Design Handoff

Статус: handoff от проектировщика к аудитору документации.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §16.

## Created / Updated Docs

Created:

- `docs/stages/stage-3-product-core/core-2/CORE_2_SCOPE.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_ARCHITECTURE.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_DATA_FLOW.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_MODEL_AND_MIGRATION_PLAN.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_API_SYNC_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_OPERATION_LINKING_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_MAPPING_RULES_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_SNAPSHOT_FILLING_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_EXCEL_EXPORT_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_UI_UX_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_TEST_PLAN.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_ACCEPTANCE_CHECKLIST.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_ROLLOUT_RUNBOOK.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_DESIGN_HANDOFF.md`

Updated:

- `docs/DOCUMENTATION_MAP.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/adr/ADR_LOG.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/project/CURRENT_STATUS.md`

## Scope Summary

CORE-2 connects Product Core to approved WB/Ozon operations through `MarketplaceListing`, exact normalized article linkage, nullable operation row FK enrichment, snapshots and exports. It keeps Stage 1/2 workflows operational and does not make Excel a Product Core import source.

## Non-Scope Protected

- warehouse;
- production;
- suppliers;
- purchases;
- BOM;
- packaging;
- labels;
- demand planning;
- machine vision;
- external normalization program implementation;
- WB/Ozon vendorCode/offer_id mutation;
- fuzzy/title/image matching;
- legacy `MarketplaceProduct` removal;
- historical operation result rewrite.

## ADR

- ADR-0042: CORE-2 Product Core Integration Boundary
- ADR-0043: Normalized Article As Business Key
- ADR-0044: OperationDetailRow MarketplaceListing FK Enrichment
- ADR-0045: Auto-created ProductVariant Policy
- ADR-0046: CORE-2 Snapshot Semantics

## GAP

- GAP-CORE2-001: ProductVariant auto-create mode, open, requires customer decision via orchestrator.
- GAP-CORE2-002: Approved WB/Ozon listing sources, open, requires source/customer decision via orchestrator for unapproved endpoints.
- GAP-CORE2-003: OperationDetailRow enrichment scope, open, requires customer/orchestrator decision before implementation scope.
- GAP-CORE2-004: Snapshot filling scope, open, requires customer/orchestrator decision for fillable types beyond safe minimum.
- GAP-CORE2-005: External normalization mapping import, open, requires customer decision via orchestrator.

## Implementation Task Index

- TASK-PC2-001 Data Model And Migration
- TASK-PC2-002 Marketplace Listing Sync Integration
- TASK-PC2-003 Normalized Article Linkage And Auto-Create
- TASK-PC2-004 Operation Row FK Enrichment
- TASK-PC2-005 Snapshot Filling
- TASK-PC2-006 Product Core Exports And Excel Boundary
- TASK-PC2-007 Product Core UI Integration
- TASK-PC2-008 Permissions, Audit, Techlog, Redaction
- TASK-PC2-009 Regression And Acceptance
- TASK-PC2-010 Documentation And Rollout Closeout

## Reading Packages

Task-scoped packages are defined in `CORE_2_READING_PACKAGES.md`. Each package includes common project rules, CORE-2 scope, concrete task section, relevant specs, code context and ADR/GAP references. Agents must not read the full final TZ by default.

## Acceptance Checklist

Acceptance checklist is defined in `CORE_2_ACCEPTANCE_CHECKLIST.md`. It covers documentation audit, implementation acceptance, Stage 1/2 regression, Product Core regression, permissions, redaction, rollback and blocked-feature checks.

## Known Risks

- Ozon full catalog/listing endpoint is not approved in current docs; full Ozon listing sync remains blocked by `GAP-CORE2-002`.
- ProductVariant auto-create requires customer decision, including how to represent imported/draft lifecycle and parent `InternalProduct` shell.
- Snapshot filling is intentionally limited to approved source semantics; sales/buyout/return formulas remain out of scope.
- Operation row enrichment scope affects UI/report behavior and must be approved before implementation.

## Ready For Audit

Yes.
