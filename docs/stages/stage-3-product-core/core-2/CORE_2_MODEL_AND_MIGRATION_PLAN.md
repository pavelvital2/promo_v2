# CORE_2_MODEL_AND_MIGRATION_PLAN.md

Статус: исполнительная проектная документация CORE-2, обновлена после AUDIT PASS по решениям заказчика; готова к follow-up audit/recheck.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§7.2-7.5, §11.4, §14-§15.

## Назначение

Define non-destructive model and migration work for CORE-2. This is a plan only; no migration is created by this documentation task.

## Required Model Changes

### OperationDetailRow Nullable FK

Add nullable enrichment:

```text
OperationDetailRow.marketplace_listing_id nullable -> MarketplaceListing.id
```

Rules:

- `on_delete=PROTECT`;
- nullable and blank-compatible;
- indexed for operation card/listing card queries;
- no uniqueness constraint;
- no change to `product_ref`;
- safe to clear during rollback/backfill correction;
- not required for old rows or rows that do not represent a product/listing identifier.

### ProductVariant Imported/Draft Lifecycle

Customer decision 2026-05-02 approves imported/draft auto-create under strict CORE-2 rules. Model design must add an explicit lifecycle that does not overload `ProductVariant.status=active/inactive/archived`.

Required implementation shape:

- add a field such as `ProductVariant.review_state` or equivalent fixed dictionary;
- allowed minimum states: `manual_confirmed`, `imported_draft`, `needs_review`;
- keep existing `status` for active/inactive/archive lifecycle;
- add safe source context for API auto-create basis;
- create/select the required parent `InternalProduct` shell when a valid API article or explicitly confirmed mapping-table row has no existing variant;
- write `ProductMappingHistory` and audit for auto-created imported/draft variants and links.

Auto-created variants are not manually confirmed business products until review, even when their listing mapping status is `matched`.

### Internal SKU Dictionary

CORE-2 must validate `ProductVariant.internal_sku` against the fixed structured patch/chevron dictionary from `CORE_2_MAPPING_RULES_SPEC.md`. The dictionary is fixed in docs/code for CORE-2. User-editable SKU dictionaries and UI management of these dictionaries are future scope.

### Normalized Article Comparison

No required DB field is mandated for CORE-2 v1. The deterministic comparison value is:

```text
trim(value)
```

Forbidden transformations:

- case folding;
- transliteration;
- removing punctuation/hyphens/spaces inside the value;
- partial matching;
- title/image/barcode fuzzy matching.

Automatic API matching is allowed only after the source article passes the internal SKU format validator. If implementation adds a persisted normalized cache later, it must use the same exact rule and include migration validation.

## Data Migration / Backfill

### FK Backfill

Backfill may set `OperationDetailRow.marketplace_listing_id` only when all are true:

1. row operation has marketplace and store;
2. row `product_ref` is non-empty and belongs to a product/listing row, not a promotion/action summary row;
3. exactly one `MarketplaceListing` in the same marketplace/store matches by documented deterministic key;
4. no conflicting listing or duplicate candidate exists;
5. enrichment does not alter operation status, summary, result files, warning confirmations, reason/result code, message or `product_ref`.

Conflict rows remain unmodified and are counted in safe summary.

### Listing Upsert From API Sources

Listing upsert is idempotent by:

```text
marketplace + store + external_primary_id
```

For rows without a stable external primary id, implementation must not create a listing unless an approved source-specific fallback is documented in `CORE_2_API_SYNC_SPEC.md` with official endpoint evidence and tests.

If the API returns duplicate external article values within the same marketplace/store, the affected source rows are data-integrity errors. Listing upsert may still persist non-conflicting listing identity, but auto-link and auto-create are skipped for the duplicate group and a techlog/safe summary entry is required.

## Backup

Before schema/data migration implementation:

- run PostgreSQL backup;
- run media/file storage backup if exports/files are touched;
- record row counts for:
  - `MarketplaceProduct`;
  - `MarketplaceListing`;
  - `ProductVariant`;
  - `Operation`;
  - `OperationDetailRow`;
  - snapshot tables;
- record pre-migration `OperationDetailRow.product_ref` immutability evidence: row count plus checksum/hash over `(id, product_ref)` for all existing detail rows;
- record duplicate candidate counts by marketplace/store/key;
- verify no pending migrations.

## Rollback

Rollback expectations:

- schema rollback can remove nullable FK only after FK values are no longer required by accepted release state;
- data rollback can clear `OperationDetailRow.marketplace_listing_id` without touching `product_ref`;
- legacy `MarketplaceProduct` remains authoritative for old Stage 1/2 compatibility;
- snapshots may be deleted only if created by the failed migration/sync and not referenced by accepted operations/files;
- audit/techlog records are not manually deleted outside retention policy.

## Re-run Safety

All backfills and sync adapters must be idempotent:

- re-running listing sync updates existing listing by unique key;
- re-running FK enrichment leaves already valid FK unchanged;
- conflicts are counted once per run context and do not create duplicate user-visible mappings;
- failed sync does not overwrite last successful cache.

## Validation Queries

Future implementation must provide checks equivalent to:

```sql
-- OperationDetailRow.product_ref immutability evidence before and after
-- migration/enrichment/release validation; row count and checksum must match
-- for rows that existed before the change.
select
  count(*) as row_count,
  md5(string_agg(id::text || ':' || coalesce(product_ref, '<NULL>'), '|' order by id)) as product_ref_checksum
from operations_operationdetailrow;

-- FK points to same store/marketplace as operation
select count(*)
from operations_operationdetailrow r
join operations_operation o on o.id = r.operation_id
join product_core_marketplacelisting l on l.id = r.marketplace_listing_id
where r.marketplace_listing_id is not null
  and (o.store_id <> l.store_id or o.marketplace <> l.marketplace);

-- legacy rows remain present
select count(*) from marketplace_products_marketplaceproduct;
```

Null/blank checks alone are not sufficient evidence for `product_ref` immutability. Release validation must preserve the pre/post artifact with the row count and checksum/hash over `(id, product_ref)` before and after migration, FK enrichment and final release validation.

Implementation must adapt table names to actual Django migrations and include ORM-level validation where preferred.

## Non-Destructive Constraints

Prohibited:

- deleting/truncating `MarketplaceProduct`;
- rewriting old `OperationDetailRow.product_ref`;
- changing reason/result code catalogs as a side effect;
- converting Excel operations into Product Core import operations;
- adding WB/Ozon read endpoints without endpoint-specific official docs evidence and tests;
- adding WB/Ozon write endpoints or card-field updates in CORE-2;
- storing secrets in model JSON fields, snapshots, audit, techlog, files or exports.
