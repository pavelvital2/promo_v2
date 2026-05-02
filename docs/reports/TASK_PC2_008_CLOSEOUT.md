# TASK_PC2_008_CLOSEOUT

Date: 2026-05-02
Role: TASK-PC2-008 technical writer
Task: TASK-PC2-008 Permissions, Audit, Techlog, Redaction
Status: DONE
Implementation Audit: PASS

## Basis

- `docs/reports/TASK_PC2_008_DESIGN_HANDOFF.md`
- `docs/reports/TASK_PC2_008_DESIGN_AUDIT.md`
- `docs/reports/TASK_PC2_008_IMPLEMENTATION_AUDIT.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-008`

## Implemented

- CORE-2 audit action codes and migration for:
  - `product_variant.auto_created_draft`;
  - `operation_detail_row.listing_fk_enriched`;
  - `marketplace_sync.failed`;
  - `marketplace_snapshot.write_failed`.
- CORE-2 techlog event types and migration for:
  - `marketplace_sync.api_error`;
  - `marketplace_snapshot.write_error`;
  - `marketplace_mapping.conflict`;
  - `operation_detail_row.enrichment_error`;
  - `product_variant.auto_create_error`.
- Safe audit/techlog hooks for failed marketplace sync, snapshot write failure, Product Variant auto-create failure, automatic mapping conflict and operation-row listing FK enrichment.
- FK enrichment audit/techlog context hardening with safe summaries and hashed/redacted source references instead of raw `product_ref`.
- Redaction and no-leakage tests for audit/techlog safe fields, snapshot/latest JSON, imported source context, hidden object identifiers, UI/export/audit/techlog visibility and operation row links.
- Product Core permission matrix hardening tests for role defaults, direct deny precedence, imported/draft review through explicit `product_variant.update`, object access and hidden-store denial.

## Intentionally Not Implemented

- Permission seed or identity migration changes.
- Deferred external mapping-table workflow and `visual_external` behavior.
- `marketplace_mapping.import_table` / `marketplace_mapping.apply_table` permissions or role defaults.
- `marketplace_mapping.table_previewed` / `marketplace_mapping.table_applied` audit calls.
- New UI route, template, parser, upload/preview/apply workflow, export or feature slice outside the audited hardening scope.

## Verification

Implementation audit records these passing checks:

- `git diff --check`: PASS.
- `manage.py check`: PASS, no system check issues.
- `manage.py makemigrations --check --dry-run`: PASS, no changes detected.
- Targeted suites `apps.identity_access apps.audit apps.techlog apps.product_core apps.operations apps.web`: PASS, `173 tests OK`.
- Regression suite `apps.discounts`: PASS, `103 tests OK`.

The audit notes that an initial parallel run hit a shared PostgreSQL test database creation conflict for `test_promo_v2`; the affected targeted suite was rerun sequentially and passed.

## Residual Risks

- No separate pre-audit implementation/test closeout report was found with the previously expected `147` and `114` test counts. The implementation audit therefore relies on its local rerun evidence: `173` targeted tests and `103` discounts tests.
- `GAP-CORE2-007` remains deferred for the future external mapping table / `visual_external` workflow. Any future implementation must reopen permission seed policy, audit actions, techlog events, row/file contract and UI scope through a separate task.
- New failure hooks intentionally store safe classes and redacted references instead of raw exception text. This protects redaction boundaries, but operational diagnosis may require correlation with server logs that must also preserve the no-secret rule.

## Closeout Verdict

TASK-PC2-008 Permissions, Audit, Techlog, Redaction is closed as `DONE` after implementation audit `PASS`.

The implementation matches the audited hardening scope: audit/techlog catalogs and safe service calls are present, redaction/no-leakage and permission matrix coverage are strengthened, and deferred mapping-table, `visual_external`, permission seed and new UI/feature-slice work remain out of scope.
