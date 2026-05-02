# CORE_2_SNAPSHOT_FILLING_SPEC.md

Статус: исполнительная проектная документация CORE-2, подготовлена для audit-gate.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§7.5, 9.5, §11.8.

## Назначение

Define which Product Core snapshots CORE-2 may fill from existing approved flows and which remain foundation-only.

## Snapshot Scope

`GAP-CORE2-004` remains open for customer/orchestrator confirmation of final CORE-2 snapshot scope. This document defines the safe recommended minimum based on current approved docs.

| Snapshot | CORE-2 recommended behavior | Source |
| --- | --- | --- |
| `PriceSnapshot` | Fill for WB price rows from approved Stage 2.1 price source. | `GET /api/v2/list/goods/filter` |
| `StockSnapshot` | Fill for Ozon Elastic selected product set when `/v4/product/info/stocks` data is available. | Stage 2.2 product data join |
| `SalesPeriodSnapshot` | Foundation-only in CORE-2 unless a separately approved source exists. | No approved sales/buyout/returns source in current package. |
| `PromotionSnapshot` | Fill for WB regular promotion product rows and Ozon Elastic selected action participation. | Stage 2.1 promotions, Stage 2.2 Elastic actions/products/candidates |

WB auto promotions without nomenclatures must not create listing-level promotion snapshots.

## Source Run Semantics

Every snapshot must link to:

- `MarketplaceListing`;
- `MarketplaceSyncRun`;
- `Operation` where available;
- source endpoint code;
- safe source timestamp or period;
- raw-safe payload fragment/checksum without secrets.

Snapshots are append-only source records. Updating `MarketplaceListing.last_values` is a derived cache update from successful sync completion, not a replacement for snapshot history.

## PriceSnapshot

Minimum mapping:

- listing;
- sync run;
- operation if the source was operation-backed;
- snapshot timestamp;
- price;
- price with discount if source provides it;
- discount percent if source provides it;
- currency;
- source endpoint;
- `raw_safe`.

Ozon Elastic `action_price` belongs to `PromotionSnapshot.action_price`, not `PriceSnapshot`, unless a future approved Ozon base-price source is documented.

## StockSnapshot

Minimum mapping:

- listing;
- sync run;
- operation;
- snapshot timestamp;
- `total_stock` if source semantics are approved;
- `stock_by_warehouse` redacted/safe;
- nullable in-way fields only when source provides exact values.

For current Ozon Elastic scope, `total_stock` may use the approved Stage 2.2 sum of `present` across all returned stock rows. WB stock filling is not approved by current docs.

## SalesPeriodSnapshot

Sales, buyouts and returns have marketplace-specific meanings. CORE-2 does not define demand or production formulas.

Rules:

- fields `orders_qty`, `sales_qty`, `buyout_qty`, `returns_qty`, `sales_amount`, `currency` remain nullable;
- no calculation of production need or stock replenishment;
- no cross-marketplace aggregation formula;
- any future source requires separate specification and tests.

## PromotionSnapshot

WB:

- regular promotion nomenclature rows may produce listing-level snapshots;
- auto promotions without product rows remain action-level data in existing WB Stage 2.1 artifacts and do not create fake product snapshots.

Ozon:

- Elastic selected action active/candidate rows may produce participation snapshots;
- `action_price`, min/max constraints and participation status are stored only when source row provides them safely.

## Latest Cache

`MarketplaceListing.last_values` may cache:

- latest price fields;
- latest stock fields;
- latest promotion flags;
- latest snapshot timestamps;
- source sync run id/reference;
- redacted/safe values only.

Cache updates happen after sync status is `completed_success` or `completed_with_warnings`. Failed sync does not erase previous cache.

## Error Handling

- Missing listing match: snapshot not written; safe warning counted.
- Source semantic not approved: snapshot not written; GAP/reference recorded.
- Secret-like value detected: snapshot write blocked and techlog critical event recorded.
- Partial source row: write nullable fields only when exact source value exists.

## Tests

Future implementation must test:

- snapshot context validation: listing/store/marketplace matches sync run;
- successful sync updates cache;
- failed sync preserves old cache;
- nullable sales/buyout/return fields;
- WB auto promotions no fabricated product snapshots;
- Ozon stock `present` aggregation for selected action set;
- secret redaction guard;
- object access for snapshot UI/export.
