# CORE_2_SNAPSHOT_FILLING_SPEC.md

Статус: исполнительная проектная документация CORE-2, обновлена после AUDIT PASS по решениям заказчика; готова к follow-up audit/recheck.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§7.5, 9.5, §11.8.

## Назначение

Define which Product Core snapshots CORE-2 may fill from approved/read-only flows and which future metrics remain nullable hooks only.

## Snapshot Scope

Customer decision 2026-05-02 approves CORE-2 snapshot filling for prices, stocks and promotions/actions when the data is already available from approved/read-only sources. Sales, buyouts, returns, demand, in-work, production and shipments remain future architecture hooks only: nullable foundation, no active CORE-2 UI/workflow and no formulas.

| Snapshot / hook | CORE-2 behavior | Source |
| --- | --- | --- |
| `PriceSnapshot` | Fill when price data is present in approved source rows. | WB `GET /api/v2/list/goods/filter`; future official read-only price/catalog sources with endpoint evidence. |
| `StockSnapshot` | Fill when stock data is present in approved source rows. | Stage 2.2 `/v4/product/info/stocks`; future official read-only stock/catalog sources with endpoint evidence. |
| `PromotionSnapshot` | Fill for promotions/actions when listing-level source rows are present and approved. | WB regular promotion product rows; Ozon Elastic action participation; future official read-only action/promotion sources with endpoint evidence. |
| Sales/buyouts/returns/demand/in-work/production/shipments | Future architecture hooks only; nullable foundation, no active CORE-2 workflow/UI, no derived formulas. | Separate future specification required. |

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

## Future Metrics / Operational Hooks

Sales, buyouts, returns, demand, in-work, production and shipments have marketplace-specific or internal-process meanings. CORE-2 does not define demand, production, shipment or replenishment formulas.

Rules:

- fields `orders_qty`, `sales_qty`, `buyout_qty`, `returns_qty`, `sales_amount`, `currency` remain nullable;
- no calculation of production need or stock replenishment;
- no active UI/workflow for demand, in-work, production or shipments;
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
- Source semantic not approved/evidenced: snapshot not written; source decision/reference recorded.
- Secret-like value detected: snapshot write blocked and techlog critical event recorded.
- Partial source row: write nullable fields only when exact source value exists.

## Tests

Future implementation must test:

- snapshot context validation: listing/store/marketplace matches sync run;
- successful sync updates cache;
- failed sync preserves old cache;
- nullable sales/buyout/return fields;
- no active CORE-2 UI/workflow for demand/in-work/production/shipments hooks;
- WB auto promotions no fabricated product snapshots;
- Ozon stock `present` aggregation for selected action set;
- secret redaction guard;
- object access for snapshot UI/export.
