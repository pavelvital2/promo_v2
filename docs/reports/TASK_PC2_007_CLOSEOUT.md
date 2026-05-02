# TASK_PC2_007_CLOSEOUT

Date: 2026-05-02
Role: TASK-PC2-007 technical writer
Task: TASK-PC2-007 Product Core UI Integration
Status: DONE
Implementation Recheck: PASS

## Basis

- `docs/reports/TASK_PC2_007_DESIGN_HANDOFF.md`
- `docs/reports/TASK_PC2_007_DESIGN_AUDIT.md`
- `docs/reports/TASK_PC2_007_IMPLEMENTATION_AUDIT.md`
- `docs/reports/TASK_PC2_007_IMPLEMENTATION_RECHECK.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-007`

## Implemented

- Access-safe Product Core navigation additions for CORE-2 listing, review and export surfaces.
- Marketplace listing list/card UI for sync status, source warnings, cache age, latest values and related operation links.
- Listing list/card synchronization of linked internal data visibility with `product_core.view` and `product_variant.view` gates.
- Imported/draft and needs-review variant queue with separate lifecycle/review-state labels and permission-gated review actions.
- Operation detail row listing links based on nullable `OperationDetailRow.marketplace_listing`, with raw `product_ref` preserved.
- Export controls for approved PC2-006 listing, unmatched/review/conflict, latest-values, mapping-report and operation-link exports.
- Exact mapping UI additions for manual exact-basis review, invalid/non-unified article display and conflict/review queues.

## Intentionally Not Implemented

- Active external mapping-table upload, preview or apply workflow.
- `visual_external` table workflow.
- Future ERP working UI, including production, demand, suppliers and labels surfaces.
- Marketplace card-field write UI, including WB `vendorCode` and Ozon `offer_id` edits.
- Fuzzy, image, title, brand, category, partial-article or machine-vision matching.

## Verification

- `apps.web apps.product_core`: `111 tests`, `OK`.
- `manage.py check`: `OK`.
- `git diff --check`: `OK`.

## Residual Risks

- The positive visible-object path for imported/draft source context is covered by implementation inspection and broader visible-listing queue coverage; the new focused regression primarily covers the denial path for hidden IDs.
- Future changes to `ProductVariant.import_source_context` must keep object identifiers out of the safe summary whitelist unless each value is resolved and access-checked before rendering.
- Broader CORE-2 documentation still describes future mapping-table / `visual_external` behavior. For scoped TASK-PC2-007 this remains deferred under the audited handoff boundary.

## Closeout Verdict

TASK-PC2-007 Product Core UI Integration is closed as `DONE` after implementation recheck `PASS`. The implemented UI scope matches the audited handoff, exposes the approved CORE-2 review/listing/export/navigation behavior, and keeps deferred mapping-table, `visual_external`, future ERP/card-write and fuzzy/image matching workflows inactive.
