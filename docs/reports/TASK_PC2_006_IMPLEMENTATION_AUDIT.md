# TASK_PC2_006_IMPLEMENTATION_AUDIT

Date: 2026-05-02
Role: TASK-PC2-006 implementation auditor
Task: TASK-PC2-006 Product Core Exports And Excel Boundary
Verdict: BLOCKED

## Documents Read

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/reports/TASK_PC2_006_DESIGN_HANDOFF.md`
- `docs/reports/TASK_PC2_006_DESIGN_RECHECK.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_EXCEL_EXPORT_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md`
- current `git status`, `git diff --stat`, targeted diffs and implementation files

## Blocking Findings

### B1. Internal product identifiers are not consistently gated by `product_core.view` + `product_variant.view`

Owner: TASK-PC2-006 developer.

Severity: blocking access-control defect.

The implementation blanks variant identifiers only when either `product_core.view` or `product_variant.view` is absent, but it allows linked internal product code/name with `product_core.view` alone:

- `apps/product_core/exports.py:135` defines `_can_export_internal_product_identifiers()` as only `has_permission(user, "product_core.view")`.
- `apps/product_core/exports.py:153` and `apps/product_core/exports.py:167`-`168` use that weaker gate for listing/latest export product code/name.
- `apps/product_core/exports.py:272` and `apps/product_core/exports.py:310`-`311` use the same weaker gate for mapping report product code/name.

The task audit requirement says internal product/variant identifiers are gated by `product_core.view` + `product_variant.view`. The handoff also requires linked internal product/variant columns to be blank when Product Core/variant view access is absent. A user with `product_core.view` allowed and `product_variant.view` denied can still receive linked internal product code/name in listing/latest/mapping exports.

Required fix:

- Gate all linked internal product and variant identifier columns in marketplace listing, latest values and mapping report exports on both `product_core.view` and `product_variant.view`, or obtain an explicit design/customer decision that product code/name may be exposed with `product_core.view` alone.
- Add a focused regression test for `product_core.view=allow` and `product_variant.view=deny` proving `internal_product_code`, `internal_product_name`, `internal_variant_sku`, `internal_variant_name` and `variant_review_state` are blank across listing/latest/mapping exports.

## Checks

| Area | Result | Evidence |
| --- | --- | --- |
| Scope boundary | PASS | Changed files stay in Product Core exports, web endpoints/template/tests and audit catalog. No `apps/discounts/wb_excel/**`, `apps/discounts/ozon_excel/**`, `apps/files/**`, persisted `FileObject`/`FileVersion`, XLSX, Product Core import or Stage 1/2 Excel workflow change was found in the implementation diff. |
| Export types | PASS | Implemented/extended streamed CSV exports for marketplace listings, unmatched/needs-review/conflict listing export, latest values, mapping report and operation-link report. |
| Store/object access | PASS WITH BLOCKER ABOVE | Listing exports start from visible listings and re-check `marketplace_listing.export` per row. Latest export filters rows by `marketplace_snapshot.view`. Operation-link rows start from visible operations and require listing export scope. The blocker is limited to the Product Core/variant identifier gate. |
| Latest redaction | PASS | Latest JSON runs through redaction plus raw-key stripping for raw-safe/raw-sensitive/request/response/header/stack-trace markers. Tests assert secret-like and raw-safe markers are absent. |
| Operation-link report read-only | PASS | `operation_link_report_csv()` calls the resolver but does not call FK enrichment/write code. Test refreshes linked and unresolved rows and confirms `OperationDetailRow.marketplace_listing_id` is unchanged. |
| Audit action | PASS WITH PACKAGING NOTE | `AuditActionCode.PRODUCT_CORE_EXPORT_GENERATED` exists in `apps/audit/models.py:193`; migration `apps/audit/migrations/0011_product_core_export_generated_action.py` exists but is untracked and must be included in the implementation package/commit. Scoped exports call `_audit_product_core_export()` with `product_core.export_generated`. |
| Tests | PASS | Runtime-env verification passed: `check`, `makemigrations --check --dry-run`, `apps.web apps.product_core` 104 tests OK, `apps.audit` 6 tests OK, `git diff --check` OK. |

## Verification Commands

- `git diff --check` - PASS, no output.
- `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` - PASS: `System check identified no issues (0 silenced).`
- `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run` - PASS: `No changes detected`.
- `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.web apps.product_core --verbosity 1 --noinput` - PASS: 104 tests, OK.
- `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.audit --verbosity 1 --noinput` - PASS: 6 tests, OK.

Note: running `python` directly is not valid in this workspace because only `.venv/bin/python` has Django installed.

## Packaging Notes

Current implementation package includes untracked files that must not be lost:

- `apps/audit/migrations/0011_product_core_export_generated_action.py`
- `docs/reports/TASK_PC2_006_DESIGN_AUDIT.md`
- `docs/reports/TASK_PC2_006_DESIGN_HANDOFF.md`
- `docs/reports/TASK_PC2_006_DESIGN_RECHECK.md`
- `docs/reports/TASK_PC2_006_IMPLEMENTATION_AUDIT.md`

## Final Verdict

BLOCKED. The implementation is close and the verification suite is green, but the identifier access-control gate does not satisfy the task requirement for `product_core.view` + `product_variant.view`. Recheck after the gate and focused regression test are fixed.
