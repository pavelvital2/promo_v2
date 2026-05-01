# STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md

Трассировка: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md` §5.1.5, §7, §13; итоговое ТЗ §9, §12-§13, §20-§22, §27.

## Назначение

План describes how current `MarketplaceProduct` is migrated into the external listing layer without deleting data, breaking Stage 1/2 operations, or rewriting historical rows.

## Current Inventory

Observed dependencies:

- `apps/marketplace_products/models.py`: `MarketplaceProduct`, `MarketplaceProductHistory`.
- `apps/marketplace_products/services.py`: creates/updates products from `OperationDetailRow.product_ref`.
- `apps/discounts/wb_excel/services.py`: syncs products after WB Excel operations.
- `apps/discounts/ozon_excel/services.py`: syncs products after Ozon Excel operations.
- `apps/discounts/wb_api/prices/services.py`: updates products from WB prices API.
- `apps/web/views.py`: product list/card uses `MarketplaceProduct`.
- `apps/operations/models.py`: `OperationDetailRow.product_ref` is raw string and is used by multiple Stage 1/2 flows.
- Tests in `apps/web`, `apps/marketplace_products`, `apps/discounts/*`, `apps/operations` cover product/detail behavior.

Current constraints:

- `MarketplaceProduct` unique on `(marketplace, store, sku)`.
- History is linked with `operation` and `file_version`.
- Completed operations and detail rows are immutable through normal UI/admin paths.

## Considered Options

| Option | Summary | Decision |
| --- | --- | --- |
| A | Rename `MarketplaceProduct` model/table to `MarketplaceListing` | Rejected for CORE-1 v1 because imports, tests and historical assumptions are broad |
| B | Create new `MarketplaceListing`, backfill from `MarketplaceProduct`, keep legacy compatibility layer | Selected |
| C | Keep physical `MarketplaceProduct` and document it as listing | Rejected as target because it keeps conceptual ambiguity |

## Selected Migration Strategy

CORE-1 uses option B:

1. Create new internal product models and new listing/snapshot/history models.
2. Backfill `MarketplaceListing` from every `MarketplaceProduct`.
3. Keep `internal_variant_id = null` for backfilled listings.
4. Set `mapping_status = unmatched` unless a future audited import/mapping rule explicitly says otherwise.
5. Preserve `MarketplaceProduct` rows and `MarketplaceProductHistory` as deprecated compatibility data.
6. Add nullable FK enrichment from new rows/detail rows to `MarketplaceListing` only where safe.
7. Update product/listing UI to use `MarketplaceListing` while preserving historical operation links.
8. Do not remove `MarketplaceProduct` until a later audited deprecation/removal task with backup/rollback/regression exists.

## Backfill Mapping Rules

For each `MarketplaceProduct`:

| MarketplaceProduct | MarketplaceListing |
| --- | --- |
| `marketplace` | `marketplace` |
| `store_id` | `store_id` |
| `sku` | `external_primary_id` if no better marketplace id exists; also `seller_article` where appropriate |
| `external_ids` | `external_ids` |
| `title` | `title` |
| `barcode` | `barcode` |
| `status` | mapped to `listing_status` |
| `last_values` | `last_values` |
| `first_detected_at` | `first_seen_at` |
| `last_seen_at` | `last_seen_at`, and if from API success then candidate for `last_successful_sync_at` |

No internal product/variant is created during backfill.

## Operation Detail Compatibility

`OperationDetailRow.product_ref` remains:

- the immutable raw product reference used by old operations;
- required for Stage 1/2 detail reports and old tests;
- not replaced by internal SKU or listing primary key.

Future nullable enrichment:

```text
OperationDetailRow.marketplace_listing_id nullable
```

Allowed only when all are true:

- operation marketplace and store match listing marketplace/store;
- raw `product_ref` safely matches listing external id/seller article under a documented deterministic rule;
- enrichment does not change operation summary, result, file, reason/result code or user-visible historical outcome.

## Backup, Rollback And Validation

Before migration implementation:

- run PostgreSQL backup;
- run file storage backup if migration touches file-linked entities or reports;
- record row counts for `MarketplaceProduct`, `MarketplaceProductHistory`, `Operation`, `OperationDetailRow`;
- validate duplicate candidates for listing uniqueness before writing constraints;
- prepare reversible migration for schema steps where Django supports it;
- document non-reversible data copy limitations if any.

Rollback expectations:

- schema rollback must not delete legacy `MarketplaceProduct`;
- if copied `MarketplaceListing` rows are rolled back, legacy rows remain authoritative for old Stage 1/2 flows;
- any nullable FK enrichment can be cleared safely without modifying `product_ref`.

## Validation Checks

Implementation task must provide data checks equivalent to:

- every legacy `MarketplaceProduct` has exactly one backfilled listing or a documented duplicate/conflict record;
- listing count by marketplace/store matches legacy product count after duplicate policy is applied;
- no backfilled listing has `internal_variant_id`;
- every backfilled listing has `mapping_status=unmatched`;
- existing Stage 1/2 operations remain queryable by `product_ref`;
- no audit/techlog/snapshot/file stores API secrets.

## Regression Requirements

Migration cannot be accepted until:

- Stage 1 WB Excel regression passes;
- Stage 1 Ozon Excel regression passes;
- Stage 2.1 WB API regression passes;
- Stage 2.2 Ozon Elastic regression passes;
- product/listing UI object access tests pass;
- migration rollback/re-run safety checks pass on a sanitized copy or test DB.

## Prohibited Migration Actions

- Delete, truncate, overwrite or silently rename `MarketplaceProduct` without separate audited plan.
- Create internal products automatically from Excel/API rows.
- Auto-merge WB and Ozon listings.
- Rewrite historical operation summaries, files or detail rows.
- Change Stage 1/2 business logic, reason/result codes or check/process semantics.

