# AUDIT_REPORT_CORE_2_DESIGN_DOCUMENTATION

Date: 2026-05-02
Role: documentation auditor
Scope: Stage 3 / CORE-2 - Product Core Integration with WB/Ozon Operations
Input TZ: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md`
Verdict: AUDIT PASS

Product code was not changed during this audit. This report audits only the CORE-2 design documentation package and updated shared documentation.

## Scope Reviewed

- Root/project rules: `AGENTS.md`, `docs/README.md`, `docs/orchestration/AGENTS.md`.
- Navigation/status: `docs/PROJECT_NAVIGATOR.md`, `docs/DOCUMENTATION_MAP.md`, `docs/project/CURRENT_STATUS.md`.
- CORE-2 input TZ and all files under `docs/stages/stage-3-product-core/core-2/`.
- CORE-1 release validation reports.
- Stage 3 CORE-1 scope and migration plan.
- `docs/adr/ADR_LOG.md`, `docs/gaps/GAP_REGISTER.md`, `docs/roles/READING_PACKAGES.md`.
- Endpoint/source cross-check against relevant Stage 2 docs and current adapter constants.

## Coverage Result

All mandatory documents from TZ §3.2/§11 are present:

- `CORE_2_SCOPE.md`
- `CORE_2_ARCHITECTURE.md`
- `CORE_2_DATA_FLOW.md`
- `CORE_2_MODEL_AND_MIGRATION_PLAN.md`
- `CORE_2_API_SYNC_SPEC.md`
- `CORE_2_OPERATION_LINKING_SPEC.md`
- `CORE_2_MAPPING_RULES_SPEC.md`
- `CORE_2_SNAPSHOT_FILLING_SPEC.md`
- `CORE_2_EXCEL_EXPORT_SPEC.md`
- `CORE_2_UI_UX_SPEC.md`
- `CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md`
- `CORE_2_TEST_PLAN.md`
- `CORE_2_ACCEPTANCE_CHECKLIST.md`
- `CORE_2_AGENT_TASKS.md`
- `CORE_2_READING_PACKAGES.md`
- `CORE_2_ROLLOUT_RUNBOOK.md`

Shared documents required by TZ §3.3 were updated in the working tree: `docs/DOCUMENTATION_MAP.md`, `docs/roles/READING_PACKAGES.md`, `docs/adr/ADR_LOG.md`, `docs/gaps/GAP_REGISTER.md`, `docs/project/CURRENT_STATUS.md`.

## Documentation Audit Gate

| Gate | Result | Evidence |
| --- | --- | --- |
| Scope is complete and non-contradictory | PASS | `CORE_2_SCOPE.md:34-47`, `CORE_2_ARCHITECTURE.md:134-185` |
| Non-scope protected | PASS | `CORE_2_SCOPE.md:48-69`, `CORE_2_UI_UX_SPEC.md:154-168` |
| Stage 1/2 regression protected | PASS | `CORE_2_SCOPE.md:71-80`, `CORE_2_TEST_PLAN.md:361-373` |
| Legacy `MarketplaceProduct` protected | PASS | `CORE_2_SCOPE.md:29`, `CORE_2_MODEL_AND_MIGRATION_PLAN.md:145-154`, `CORE_2_ROLLOUT_RUNBOOK.md:241-249` |
| `product_ref` immutability protected | PASS WITH NOTE | `CORE_2_OPERATION_LINKING_SPEC.md:282-305`; see MINOR-002 |
| Product Core source-of-truth described | PASS | `CORE_2_ARCHITECTURE.md:187-199`, `CORE_2_MAPPING_RULES_SPEC.md:11-22` |
| API endpoints not invented | PASS | `CORE_2_API_SYNC_SPEC.md:166-178`; full Ozon catalog remains blocked by `GAP-CORE2-002` |
| GAPs recorded | PASS | `docs/gaps/GAP_REGISTER.md:214-290` |
| Permissions/audit/techlog described | PASS | `CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md:180-240` |
| Secret redaction described | PASS | `CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md:242-276`, `CORE_2_API_SYNC_SPEC.md:240-245` |
| Task-scoped packages exist | PASS | `CORE_2_AGENT_TASKS.md`, `CORE_2_READING_PACKAGES.md` |
| Acceptance checklist exists | PASS | `CORE_2_ACCEPTANCE_CHECKLIST.md` |
| Rollout/backup/rollback exists | PASS | `CORE_2_ROLLOUT_RUNBOOK.md:186-287` |

## Findings By Severity

### BLOCKER

None.

### MAJOR

None.

### MINOR

#### MINOR-001: `GAP-CORE2-001` wording can be read as blocking all normalized article linkage

- File: `docs/gaps/GAP_REGISTER.md:220-223`
- Problem: the gap correctly blocks ProductVariant auto-create/imported-draft behavior, but the wording says it blocks `TASK-PC2-003`. `CORE_2_AGENT_TASKS.md:201-206` allows exact comparison and `needs_review`/`conflict` behavior without auto-create. This is not a documentation-audit blocker because other docs preserve the safe slice, but task assignment could become ambiguous.
- Recommendation: clarify that `GAP-CORE2-001` blocks only auto-create/imported-draft lifecycle and related UI/model/export behavior, while exact match candidate marking may proceed after audit if the task explicitly excludes auto-create.

#### MINOR-002: Product-ref immutability validation needs stronger release evidence

- File: `docs/stages/stage-3-product-core/core-2/CORE_2_MODEL_AND_MIGRATION_PLAN.md:122-143`, `docs/stages/stage-3-product-core/core-2/CORE_2_ROLLOUT_RUNBOOK.md:241-249`
- Problem: the invariant is stated correctly, but the example SQL checks only `product_ref is null`; current `OperationDetailRow.product_ref` is a blank-compatible string, and null checks alone do not prove existing values were not rewritten. The rollout runbook says `product_ref` must be unchanged, but does not require a concrete before/after checksum or id/value sample.
- Recommendation: before implementation release, require a pre/post validation artifact for existing detail rows, such as row count plus checksum over `(id, product_ref)` and targeted checks for legitimate blank summary rows. This is a validation-strengthening note, not a blocker to design approval.

## GAP Classification

Open CORE-2 gaps are correctly represented as non-blocking for documentation audit and blocking only for affected implementation slices:

- `GAP-CORE2-001`: blocks auto-created/imported-draft ProductVariant behavior and related UI/model/export slices until customer decision.
- `GAP-CORE2-002`: blocks full listing sync endpoints not already approved in docs/code, especially full Ozon catalog/listing sync.
- `GAP-CORE2-003`: blocks broad operation FK enrichment/backfill scope until final operation families are approved.
- `GAP-CORE2-004`: blocks snapshot filling beyond the documented safe minimum and any unapproved source/semantic.
- `GAP-CORE2-005`: blocks external normalization mapping import/report workflow.

Implementation may proceed only for slices that either have the relevant GAP resolved or explicitly exclude the blocked behavior.

## ADR Check

ADR-0042..ADR-0046 are present in `docs/adr/ADR_LOG.md:427-470`.

- ADR-0042 protects the CORE-2 boundary and prohibited future ERP scope.
- ADR-0043 keeps `ProductVariant.internal_sku` as business key and marketplace ids as technical source keys.
- ADR-0044 preserves `OperationDetailRow.product_ref` and makes `marketplace_listing_id` nullable enrichment.
- ADR-0045 is correctly `proposed/pending_customer_decision` and blocks auto-create implementation.
- ADR-0046 is accepted with a scope gate and keeps unsupported snapshots foundation-only.

No contradiction with CORE-1 release validation, CORE-1 migration constraints, or the CORE-2 TZ was found.

## Endpoint Check

No unsupported marketplace endpoint is authorized by the CORE-2 design docs.

- WB price/listing source `GET /api/v2/list/goods/filter` is already documented in `docs/product/WB_API_PRICE_EXPORT_SPEC.md`.
- WB promotions sources are already documented in `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`.
- Ozon sources are limited to existing Stage 2.2 Elastic-scoped endpoints and product-data joins documented in `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`; full Ozon catalog/listing sync remains blocked by `GAP-CORE2-002`.
- Marketplace write endpoints are not introduced for CORE-2 sync.

## Customer Decisions Required Before Implementation

Customer/orchestrator decisions are required before implementing the affected slices:

- `GAP-CORE2-001`: auto-create mode for `ProductVariant`, imported/draft lifecycle, and parent `InternalProduct` shell policy.
- `GAP-CORE2-002`: any full WB/Ozon listing source not already approved, especially full Ozon catalog/listing sync.
- `GAP-CORE2-003`: final operation families/step codes eligible for FK enrichment/backfill.
- `GAP-CORE2-004`: snapshot filling beyond the documented safe minimum.
- `GAP-CORE2-005`: external normalization mapping import/report workflow.

No customer decision is required to start implementation slices that explicitly exclude the blocked behavior and stay within approved sources/safe minimums.

## Implementation Start Decision

Implementation may start: yes, after this audit report is accepted by the orchestrator, but only through task-scoped implementation assignments and only for slices whose GAP blockers are resolved or explicitly excluded from scope.

## Checks

- `git diff --check`: PASS, no whitespace/errors reported.
- Product code changes: none observed. `git status --short` shows modified shared docs and untracked CORE-2/audit documentation only; no `apps/`, scripts, migrations, templates, product tests or other product-code files are changed by this audit.

## Changed Files

- `docs/audit/AUDIT_REPORT_CORE_2_DESIGN_DOCUMENTATION.md`
