# STAGE_3_PRODUCT_CORE_ACCEPTANCE_CHECKLISTS.md

Трассировка: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md` §14, §22.

## Documentation Gate

- [ ] Product Core documentation audit report exists.
- [ ] Audit result is `AUDIT PASS` or only explicit non-blocking remarks remain.
- [ ] No open spec-blocking GAP for implemented slice.
- [ ] Task-scoped reading packages are used for implementation.

## Data Model

- [ ] `InternalProduct`, `ProductVariant`, `ProductCategory`, `ProductIdentifier` exist.
- [ ] `MarketplaceListing` exists and belongs to marketplace + store/account.
- [ ] One variant can have multiple listings.
- [ ] One listing can remain unmatched.
- [ ] Status dictionaries are fixed and user cannot edit codes.
- [ ] Future stock/production/supplier/label hooks do not create working modules.

## Migration

- [ ] Each legacy `MarketplaceProduct` is represented by a listing or documented conflict.
- [ ] Backfilled listings have `internal_variant_id = null`.
- [ ] Backfilled listings have `mapping_status = unmatched`.
- [ ] `MarketplaceProduct` remains available as compatibility data.
- [ ] `OperationDetailRow.product_ref` remains unchanged.
- [ ] Backup/rollback/validation evidence exists.

## Mapping

- [ ] Link listing to existing variant.
- [ ] Create product+variant and link.
- [ ] Create variant under existing product and link.
- [ ] Remove wrong link.
- [ ] Manual map/unmap writes audit and history.
- [ ] Candidate suggestions, if present, are non-authoritative exact `seller_article` / `barcode` / external identifier matches only.
- [ ] Candidate suggestions never create a confirmed link without explicit user confirmation, audit and history.
- [ ] Multiple candidates or conflicting exact matches result in `needs_review` or `conflict` until user resolution.
- [ ] No confirmed link is created by title/barcode/article similarity without user action.

## UI

- [ ] Internal product list has required columns, filters, search and pagination.
- [ ] Internal product card has main data, variants, identifiers, linked listings and history.
- [ ] Listing list has required columns, filters, search and pagination.
- [ ] Listing card has identifiers, mapping, snapshots, operations, files and errors.
- [ ] Unmatched listings workflow is usable.
- [ ] Future sections are hidden/disabled/planned, not empty working screens.

## Permissions

- [ ] Listing access follows `StoreAccount` object access.
- [ ] Product core view/create/update/archive/export rights are enforced.
- [ ] Mapping requires separate map/unmap rights.
- [ ] Snapshot technical view requires separate permission.
- [ ] Exports do not reveal inaccessible stores.
- [ ] Owner/global/local/admin/manager/observer seeds match matrix.

## Operations, Audit, Techlog

- [ ] Sync and import/export operations use approved `step_code` values.
- [ ] Completed operations remain immutable.
- [ ] Manual product/variant/listing/mapping changes emit audit.
- [ ] Sync/migration failures emit safe techlog.
- [ ] `raw_safe` snapshots are redacted.

## Excel And Regression

- [ ] Stage 1 WB Excel still passes.
- [ ] Stage 1 Ozon Excel still passes.
- [ ] Stage 2.1 WB API still passes.
- [ ] Stage 2.2 Ozon Elastic still passes.
- [ ] Existing Excel uploads do not automatically create internal products or confirmed mappings.
- [ ] Explicit Excel import, if implemented, has diff/confirmation/audit.

## Secret Safety

- [ ] No WB token/API key/authorization header in UI/logs/audit/techlog/snapshots/files/reports.
- [ ] No Ozon Client-Id/Api-Key in UI/logs/audit/techlog/snapshots/files/reports.
- [ ] `sensitive_details_ref` does not store secret-like values.
