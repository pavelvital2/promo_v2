# CORE_2_API_SYNC_SPEC.md

Статус: исполнительная проектная документация CORE-2, подготовлена для audit-gate.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§7.1, 7.5, 7.8, §11.5.

## Назначение

Define which existing WB/Ozon sources CORE-2 may use for listing/snapshot sync and how they map to Product Core. New endpoints are not assumed.

## Approved Source Matrix

| Marketplace | Source | CORE-2 allowed use | Limit |
| --- | --- | --- | --- |
| WB | `GET /api/v2/list/goods/filter` | WB listing upsert and `PriceSnapshot` from Stage 2.1 prices download source. | Read-only. Rate limits from `docs/architecture/API_CONNECTIONS_SPEC.md`. |
| WB | `GET /api/v1/calendar/promotions`, `details`, `nomenclatures` | `PromotionSnapshot` for regular promotion product rows only when listing match is deterministic. | Auto promotions do not expose product rows; do not fabricate rows. |
| Ozon | `GET /v1/actions` | Action context for existing Stage 2.2 Elastic flow; not a catalog listing source. | Read-only connection/actions scope. |
| Ozon | `/v1/actions/products`, `/v1/actions/candidates` | Ozon listing upsert for selected Elastic action product set and promotion participation snapshots. | Not full catalog. Exact official schema verified at implementation time per ADR-0033. |
| Ozon | `/v3/product/info/list` | Supplement selected Ozon Elastic rows with product info and `offer_id`/name/min_price where available. | Only for selected action product set; do not treat as approved full catalog sync. |
| Ozon | `/v4/product/info/stocks` | `StockSnapshot` for selected Ozon Elastic product rows. | Only for selected action product set. |

`GAP-CORE2-002` remains open for full WB/Ozon listings source decisions, especially full Ozon catalog/listings. A future implementation task must not add a new endpoint to close this gap by assumption.

## Sync Operation Contract

Product Core sync operations use `Operation.step_code` and not `Operation.type=check/process`.

Minimum CORE-2 step codes:

| Step code | Meaning |
| --- | --- |
| `marketplace_listings_sync` | Read approved source and upsert listings. |
| `marketplace_prices_sync` | Write price snapshots from approved price source. |
| `marketplace_stocks_sync` | Write stock snapshots from approved stock source. |
| `marketplace_promotions_sync` | Write promotion snapshots from approved promotion/action source. |
| `marketplace_full_catalog_refresh` | Allowed only for sources explicitly approved by `GAP-CORE2-002` resolution. |

## Request / Response Handling

### WB Prices

- Base: `https://discounts-prices-api.wildberries.ru`
- Endpoint: `GET /api/v2/list/goods/filter`
- Pagination follows Stage 2.1 implementation contract.
- Minimum mapped fields:
  - `nmID` -> `external_primary_id` candidate / `external_ids.nmID`;
  - `vendorCode` -> `seller_article` and `external_ids.vendorCode`;
  - `skus`, `sizeIDs`, `techSizeNames` -> `external_ids`;
  - price/discount/currency fields -> `PriceSnapshot` where present and valid.

### WB Promotions

- Current promotion list/details/nomenclatures follow Stage 2.1.
- Regular promotion product rows may create `PromotionSnapshot`.
- Auto promotion rows are not synthesized because approved docs state WB API does not expose product rows for auto promotions.

### Ozon Elastic Sources

- Stage 2.2 Ozon endpoints are scoped to selected Elastic action context.
- Minimum mapped fields:
  - `product_id` -> `external_primary_id` candidate and `external_ids.product_id`;
  - `offer_id` -> `seller_article` and `external_ids.offer_id`;
  - `sku`/`fbo_sku`/`fbs_sku` when available -> `external_ids`;
  - product name -> `title`;
  - action participation/action price -> `PromotionSnapshot`;
  - stock rows from `/v4/product/info/stocks` -> `StockSnapshot`.
- Exact Ozon field names follow official current schema and existing Stage 2.2 contract tests. If a needed field is absent, the row remains unlinked/unfilled with safe warning.

## Rate Limits And Retry

| Source | Baseline |
| --- | --- |
| WB Prices and Discounts | 10 requests / 6 seconds, interval 600 ms, burst 5. |
| WB Promotions Calendar | 10 requests / 6 seconds, interval 600 ms, burst 5. |
| Ozon Stage 2.2 reads | Page/request chunk default 100, minimum interval 500 ms, bounded retry for reads only. |

Retry rules:

- retry only idempotent reads;
- no automatic replay of write endpoints;
- 429 uses bounded backoff;
- exhausted retry fails operation/sync with safe error summary;
- partial rows are kept as row warnings where possible.

## Token Handling

- WB token and Ozon Client-Id/Api-Key are read only through `protected_secret_ref`.
- Secret values are not copied to request snapshots, sync summaries, error summaries, audit, techlog, files, exports or UI.
- Redaction guard failures create techlog `marketplace_sync.secret_redaction_violation`.

## Sync Statuses

Use existing `MarketplaceSyncRun.SyncStatus`:

- `created`;
- `running`;
- `completed_success`;
- `completed_with_warnings`;
- `completed_with_error`;
- `interrupted_failed`.

Completed successful or warning syncs may update listing latest cache. Failed/interrupted syncs must not erase last successful cache.

## Tests And Mocks

Future implementation must include:

- mocked WB pagination and rate-limit retry;
- mocked Ozon Elastic action/product/product-info/stocks fixtures;
- schema mismatch tests;
- partial failure tests;
- no-write-endpoint tests for sync tasks;
- redaction tests for request/response/snapshot/audit/techlog/export;
- duplicate active sync guard tests;
- object access tests for sync result visibility.
