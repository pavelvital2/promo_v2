# TASK_PC2_006_IMPLEMENTATION_RECHECK

Date: 2026-05-02
Role: TASK-PC2-006 implementation recheck auditor
Task: TASK-PC2-006 Product Core Exports And Excel Boundary
Original audit: `docs/reports/TASK_PC2_006_IMPLEMENTATION_AUDIT.md`
Verdict: PASS

## Documents And Evidence Read

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/reports/TASK_PC2_006_IMPLEMENTATION_AUDIT.md`
- `docs/reports/TASK_PC2_006_DESIGN_HANDOFF.md`
- `docs/reports/TASK_PC2_006_DESIGN_RECHECK.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-006`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md` section `TASK-PC2-006`
- `docs/stages/stage-3-product-core/core-2/CORE_2_EXCEL_EXPORT_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/gaps/GAP_REGISTER.md` and `docs/adr/ADR_LOG.md` scoped checks
- Current `git status`, `git diff --stat`, targeted diffs and implementation files

## Recheck Findings

### B1. Internal identifier gate

Status: CLOSED.

`apps/product_core/exports.py` now gates linked internal product and variant identifiers with both `product_core.view` and `product_variant.view`:

- `_can_export_internal_product_identifiers()` and `_can_export_internal_variant_identifiers()` both require the two permissions.
- Listing and latest exports blank `internal_product_code`, `internal_product_name`, `internal_variant_sku` and `internal_variant_name` through `_listing_base_row()`.
- Mapping report blanks `internal_product_code`, `internal_product_name`, `internal_variant_sku`, `internal_variant_name` and `variant_review_state` unless the same combined gate passes.
- Operation-link report blanks `linked_variant_internal_sku` unless the combined gate passes. No internal product code/name columns are present in this report.

This satisfies the original blocker: a user with only one of the two internal view permissions does not receive linked internal product/variant identifiers in listing, latest, mapping or operation-link exports.

### Regression tests

Status: PASS.

Focused tests were added in `apps/web/tests.py`:

- listing export blanks internal identifiers without Product Core/variant view access;
- listing/latest/mapping/operation-link exports blank internal product code/name, variant SKU/name for `product_core.view=allow` and `product_variant.view=deny`;
- operation-link export keeps visible listing data while blanking linked variant SKU and preserving read-only FK behavior.

The tests exercise the blocker path and are meaningful for the fixed permission contract.

### Audit action migration packaging

Status: PASS WITH PACKAGING NOTE.

`AuditActionCode.PRODUCT_CORE_EXPORT_GENERATED = "product_core.export_generated"` is present in `apps/audit/models.py`, and `apps/audit/migrations/0011_product_core_export_generated_action.py` exists.

Current status shows the migration is untracked:

```text
?? apps/audit/migrations/0011_product_core_export_generated_action.py
```

This is acceptable for recheck only because the untracked status is explicitly acknowledged here. The migration must be included in the implementation package/commit together with the model/test changes.

### Scope creep

Status: PASS.

Changed implementation files remain in Product Core exports, web views/urls/template/tests and audit catalog/migration/tests. No implementation diff was found in:

- `apps/discounts/wb_excel/**`
- `apps/discounts/ozon_excel/**`
- `apps/files/**`
- file-contour persisted Product Core export scenarios
- Stage 1/2 Excel calculation/upload/reason-result behavior
- external mapping-table / `visual_external` workflow

No new scope creep was found in this recheck.

## Verification Commands

- `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres POSTGRES_DB=promo_v2 POSTGRES_HOST=127.0.0.1 .venv/bin/python manage.py test apps.web apps.product_core apps.audit --verbosity 1 --noinput` - PASS: 111 tests, OK.
- `git diff --check` - PASS, no output.

## Residual Risks

- The migration file remains untracked until staged/committed by the implementation owner.
- Regression coverage directly tests the `product_core.view=allow` / `product_variant.view=deny` one-permission case across all four scoped exports; the reverse one-permission case is covered by the shared `and` gate in code rather than a separate cross-export test.

## Final Verdict

PASS. The blocker from `TASK_PC2_006_IMPLEMENTATION_AUDIT.md` is closed, regression tests pass, the audit migration is present with untracked packaging status acknowledged, and no new scope creep was found.
