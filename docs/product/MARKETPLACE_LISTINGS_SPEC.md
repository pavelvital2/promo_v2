# MARKETPLACE_LISTINGS_SPEC.md

Трассировка: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md` §5.1.2-§5.1.5, §7.4-§7.12, §8, §13.

## Назначение

`MarketplaceListing` is the external listing/offer/card layer for WB/Ozon. It belongs to one marketplace and one `StoreAccount`; it may be linked to one internal `ProductVariant`.

## MarketplaceListing

Minimum fields:

| Field | Rule |
| --- | --- |
| `id` | database PK |
| `marketplace` | `wb` or `ozon` |
| `store_id` | required `StoreAccount` |
| `internal_variant_id` | nullable link to `ProductVariant` |
| `external_primary_id` | primary external id for this marketplace/store |
| `external_ids` | JSON for marketplace-specific identifiers |
| `seller_article` | seller/vendor/offer article if provided |
| `barcode` | external barcode if provided |
| `title` | marketplace title, not internal name |
| `brand` | marketplace brand if provided |
| `category_name` | marketplace category name |
| `category_external_id` | nullable marketplace category id |
| `listing_status` | fixed dictionary |
| `mapping_status` | fixed dictionary |
| `last_values` | latest-state cache |
| `first_seen_at`, `last_seen_at` | discovery timestamps |
| `last_successful_sync_at` | last successful API/source sync |
| `last_sync_run_id` | nullable link to sync run |
| `last_source` | excel, wb_api_prices, ozon_api_actions, manual_import, migration, future source |
| `created_at`, `updated_at` | timestamps |

## External IDs

WB `external_ids` must support:

- `nmID`;
- `vendorCode`;
- `skus`;
- `sizeIDs`;
- `techSizeNames`.

Ozon `external_ids` must support:

- `product_id`;
- `offer_id`;
- `sku`;
- `fbo_sku`;
- `fbs_sku`.

Implementation may store normalized strings to keep cross-source comparisons stable.

## Listing Status

| Status | Meaning |
| --- | --- |
| `active` | seen in the latest successful relevant sync or currently active by source |
| `not_seen_last_sync` | known listing was absent in the latest relevant sync |
| `inactive` | marketplace/source marks it inactive or not available |
| `archived` | retained but hidden from default operational views |
| `sync_error` | latest sync for this listing failed or produced invalid row state |

Status must be visible in UI using human-readable labels. Raw `null`, `None`, `NaN` and internal error fragments must not be shown as user-facing status.

## Mapping Status

| Status | Meaning |
| --- | --- |
| `unmatched` | listing has no internal variant link |
| `matched` | link to internal variant is confirmed |
| `needs_review` | possible candidate or manual review marker exists |
| `conflict` | conflicting data or multiple candidates require resolution |
| `archived` | listing/mapping is not used in current work |

`matched` can be set only by explicit user action or a future audited import/algorithm that still records confirmation according to approved rules.

## Mapping Rules

Forbidden:

- auto-merge WB and Ozon listings by similar title;
- auto-map by barcode alone without user confirmation;
- auto-map by partial article match;
- backfill internal products/variants from marketplace rows during migration.

Allowed:

- manual link to existing variant;
- manual creation of new product+variant and immediate link;
- manual creation of new variant under existing product and immediate link;
- manual unmap;
- mark `needs_review` or `conflict`;
- show non-authoritative candidate suggestions in CORE-1 only from exact `seller_article`, `barcode` or external identifier matches.

Candidate suggestion contract:

- suggestions are never authoritative and never create `matched` automatically;
- final mapping requires explicit confirmation by a user with mapping permission;
- confirmation writes audit and `ProductMappingHistory`;
- fuzzy title matching, similarity scoring and partial seller article matching are out of CORE-1;
- multiple candidate suggestions or conflicting exact matches must keep/set `needs_review` or `conflict` until a permitted user resolves the mapping.

## Sync Runs And Snapshots

### MarketplaceSyncRun

Fields:

- `operation_id nullable`;
- `marketplace`;
- `store_id`;
- `sync_type`: `listings`, `prices`, `stocks`, `sales`, `orders`, `promotions`, `full_catalog_refresh`, `mapping_import`;
- `source`;
- `launch_method`: `manual`, `automatic`, `service`, `api`;
- `status`;
- `started_at`, `finished_at`;
- `requested_by nullable`;
- `summary`;
- `error_summary`;
- `created_at`.

### PriceSnapshot

Stores source/time/run/listing price data:

- `listing_id`;
- `sync_run_id`;
- `operation_id nullable`;
- `snapshot_at`;
- `price`;
- `price_with_discount nullable`;
- `discount_percent nullable`;
- `currency`;
- `raw_safe`;
- `source_endpoint`;
- `created_at`.

### StockSnapshot

Stores stock data:

- `listing_id`;
- `sync_run_id`;
- `operation_id nullable`;
- `snapshot_at`;
- `total_stock nullable`;
- `stock_by_warehouse`;
- `in_way_to_client nullable`;
- `in_way_from_client nullable`;
- `raw_safe`;
- `source_endpoint`;
- `created_at`.

### SalesPeriodSnapshot

Stores period data with nullable metrics:

- `listing_id`;
- `sync_run_id`;
- `operation_id nullable`;
- `period_start`, `period_end`;
- `orders_qty nullable`;
- `sales_qty nullable`;
- `buyout_qty nullable`;
- `returns_qty nullable`;
- `sales_amount nullable`;
- `currency nullable`;
- `raw_safe`;
- `source_endpoint`;
- `created_at`.

Sales/orders/buyout formulas are not approved for demand/production analytics in CORE-1. They require a separate specification before operational use.

### PromotionSnapshot

Foundation only. Full coverage of all WB/Ozon promotion/action APIs is not in CORE-1 unless a separate audited task adds it.

Fields:

- `listing_id`;
- `sync_run_id`;
- `operation_id nullable`;
- `marketplace_promotion_id`;
- `action_name`;
- `participation_status`;
- `action_price nullable`;
- `constraints`;
- `reason_code nullable`;
- `raw_safe`;
- `source_endpoint`;
- `created_at`.

## History

`ListingHistory` records:

- listing appeared;
- key field updated;
- status changed;
- source sync reference;
- operation/sync run/user if available.

`ProductMappingHistory` records:

- map;
- unmap;
- conflict marker;
- needs review marker;
- previous variant;
- new variant;
- user;
- source context.

History is append-only through normal UI.

## Legacy Compatibility

Current `MarketplaceProduct` is treated as legacy marketplace product data. During CORE-1 migration it is copied/backfilled to `MarketplaceListing` and retained until a later audited removal/deprecation task.

`OperationDetailRow.product_ref` stays raw and historical. Nullable listing FK enrichment is allowed only by deterministic, audited migration rules.
