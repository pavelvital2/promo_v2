# AUDIT_REPORT_TASK_PC_008_EXCEL_EXPORT_BOUNDARY

Task: TASK-PC-008 Excel Export Boundary
Audit date: 2026-05-02
Auditor role: Stage 3 / Product Core audit only
Status: AUDIT PASS

## Scope

Audited requirements from:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- TASK-PC-008 package in `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-008-excel-export-boundary.md`
- `docs/product/PRODUCT_CORE_SPEC.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/FILE_CONTOUR.md`
- related `ADR-0041`

Audited implementation files:

- `apps/product_core/exports.py`
- `apps/web/views.py`
- `apps/web/urls.py`
- `templates/web/product_list.html`
- `templates/web/marketplace_listing_list.html`
- `templates/web/wb_excel.html`
- `templates/web/ozon_excel.html`
- `apps/web/tests.py`

## Result

AUDIT PASS. No blockers found for TASK-PC-008.

## Evidence

- Product Core export endpoints exist for internal products, marketplace listings, latest values, mapping report and unmatched listings in `apps/web/urls.py`.
- Internal product export requires `product_core.view` and `product_core.export`; exported columns are internal product fields and visible listing counts only. Linked listing/store details from hidden stores are not exported.
- Listing, unmatched, latest-values and mapping-report exports use visible listing querysets and row-level `marketplace_listing.export` permission filtering.
- Latest-values export gates snapshot values with `marketplace_snapshot.view`, redacts secret-like keys/values, and does not read snapshot `raw_safe` fields.
- WB/Ozon Excel upload/check/process handlers remain Stage 1 file/operation flows. They create/replace draft file versions or run existing discount services; Excel does not create `InternalProduct`/`ProductVariant`, confirmed mappings or `ProductMappingHistory` automatically. Legacy `MarketplaceProduct` compatibility sync may mirror operation `product_ref` into unmatched `MarketplaceListing` compatibility records, and that mirror is not explicit Excel import workflow.
- WB/Ozon Excel templates show explicit Product Core boundary messaging and do not imply automatic catalog/listing/mapping updates.

## Checks Considered

The audit considered the locally reported successful checks:

- `check` OK
- `makemigrations --check --dry-run` OK
- `git diff --check` OK
- `tests apps.web apps.product_core apps.marketplace_products apps.identity_access apps.operations apps.discounts.wb_excel apps.discounts.ozon_excel` OK, 126 tests

The audited tests include access/no-hidden-store export coverage, redaction/raw_safe coverage, unmatched/mapping report export coverage, and Excel boundary upload regression coverage in `apps/web/tests.py`.

## Gaps

No new gaps registered.
