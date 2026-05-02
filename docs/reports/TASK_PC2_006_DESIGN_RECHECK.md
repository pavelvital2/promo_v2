# TASK_PC2_006_DESIGN_RECHECK

Date: 2026-05-02
Role: TASK-PC2-006 design recheck auditor
Rechecked handoff: `docs/reports/TASK_PC2_006_DESIGN_HANDOFF.md`
Original audit: `docs/reports/TASK_PC2_006_DESIGN_AUDIT.md`
Verdict: PASS

## Documents Read

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/reports/TASK_PC2_006_DESIGN_AUDIT.md`
- `docs/reports/TASK_PC2_006_DESIGN_HANDOFF.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-006`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md` section `TASK-PC2-006`
- `docs/stages/stage-3-product-core/core-2/CORE_2_EXCEL_EXPORT_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md`
- `docs/gaps/GAP_REGISTER.md` via scoped search for new blocking/customer questions

## Recheck Result

### B1. Operation-link export internal identifier leakage

Status: CLOSED.

The revised handoff now explicitly protects `linked_variant_internal_sku` in the operation-link report with both `product_core.view` and `product_variant.view`. It also extends the same gate to any future internal product/variant identifier columns, including product code/name and variant name, and requires blank output when listing access is present but Product Core/variant view is absent.

The required regression test is present: an actor with operation visibility plus listing export/access but without `product_core.view` or `product_variant.view` must receive blank `linked_variant_internal_sku` and blank internal product/variant identifiers.

### B2. Export audit action contract

Status: CLOSED.

The revised handoff closes the audit action rule on `product_core.export_generated` for all scoped PC2-006 export generation events: marketplace listings, unmatched/conflict listings, latest values, mapping report and operation-link report. It also says not to substitute `marketplace_listing.exported`.

If the action is absent from code, the handoff allows the required audit catalog alignment files: `apps/audit/models.py`, `apps/audit/migrations/*`, and `apps/audit/tests.py` or existing audit-related tests. This is sufficient for implementation to add the action, migration and focused tests without a separate ambiguity.

## Additional Checks

- No new UX/functionality/business/customer question was introduced by the blocker fixes.
- Deferred external mapping-table preview/apply/export, product variant review export and persisted Product Core file exports remain explicit future/separate-task boundaries, not new blockers for PC2-006.
- The handoff is sufficient for a developer: scoped exports, headers, filters, permission gates, Excel boundary, file/audit behavior, allowed/prohibited files, required tests and audit criteria are all stated.

## Blockers

None.

## Final Verdict

PASS. The corrected `TASK_PC2_006_DESIGN_HANDOFF.md` resolves the blockers from `TASK_PC2_006_DESIGN_AUDIT.md` and is ready for implementation under the scoped PC2-006 task package.
