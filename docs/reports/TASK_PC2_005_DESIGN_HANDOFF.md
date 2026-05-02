# TASK_PC2_005_DESIGN_HANDOFF

Date: 2026-05-02
Role: TASK-PC2-005 designer
Task: TASK-PC2-005 Snapshot Filling
Verdict: READY_FOR_IMPLEMENTATION

## Scope Of This Handoff

This handoff prepares the implementation package for filling Product Core snapshots from approved current read-only flows only.

In scope:

- WB `PriceSnapshot` from the Stage 2.1 prices source `GET /api/v2/list/goods/filter`;
- WB regular-promotion `PromotionSnapshot` rows only when a deterministic listing match exists;
- Ozon Elastic selected action `PromotionSnapshot` rows from active/candidate product sets;
- Ozon Elastic selected product-set `StockSnapshot` rows from `/v4/product/info/stocks`;
- `MarketplaceListing.last_values` update only from `MarketplaceSyncRun` completion statuses `completed_success` and `completed_with_warnings`;
- safe raw fragments/checksums, source endpoint codes, sync run context, operation links where available, redaction tests.

Out of scope:

- product-code implementation in this designer task;
- new marketplace source endpoints;
- WB stock snapshots;
- Ozon base price snapshots from Elastic `action_price`, `min_price` or `min_price`-like fields;
- fake WB auto-promotion product rows;
- `SalesPeriodSnapshot` active filling;
- demand, in-work, production, shipment, replenishment or cross-marketplace formulas;
- any active UI/workflow for sales, buyouts, returns, demand, in-work, production or shipments.

`GAP-CORE2-002` and `GAP-CORE2-004` are resolved by customer decision on 2026-05-02. No `BLOCKED_BY_CUSTOMER_QUESTION` is raised for TASK-PC2-005.

## Documents Read

Mandatory task inputs:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-005`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md` section `TASK-PC2-005`
- `docs/stages/stage-3-product-core/core-2/CORE_2_SNAPSHOT_FILLING_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_API_SYNC_SPEC.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Read-only code context:

- `apps/product_core/models.py`
- `apps/product_core/services.py`
- Stage 2 API service files under `apps/discounts/wb_api/**` and `apps/discounts/ozon_api/**` found by `rg`.

## Current Code Facts

- `MarketplaceSyncRun` already has the required sync types and statuses, active-run uniqueness, same-store/same-marketplace validation, and secret guards for `summary` / `error_summary`.
- `MarketplaceListing` already has `last_values`, `last_successful_sync_at`, `last_sync_run`, `last_source`, and unique `(marketplace, store, external_primary_id)`.
- `PriceSnapshot`, `StockSnapshot`, `SalesPeriodSnapshot` and `PromotionSnapshot` already exist with `listing`, `sync_run`, nullable `operation`, source endpoint, raw-safe storage and model-level context validation.
- `apps/product_core/services.py` already has generic snapshot helpers:
  - `start_marketplace_sync_run()`;
  - `complete_marketplace_sync_run()`;
  - `fail_marketplace_sync_run()`;
  - `create_price_snapshot()`;
  - `create_stock_snapshot()`;
  - `create_sales_period_snapshot()`;
  - `create_promotion_snapshot()`.
- `complete_marketplace_sync_run()` applies `MarketplaceListing.last_values` only after a successful/warning sync completion. `fail_marketplace_sync_run()` does not apply cache updates.
- The generic cache helper can read sales snapshots if some future task creates them. TASK-PC2-005 must not add any call path that creates `SalesPeriodSnapshot`.
- `sync_wb_price_rows_to_product_core()` already upserts WB listings and writes price snapshots from approved WB price rows, with duplicate article skip, redaction guard and failed-sync cache preservation.
- `sync_wb_regular_promotion_rows_to_product_core()` already writes WB regular promotion snapshots only for existing deterministic listing matches and has an explicit no-fabrication path for auto promotions.
- `sync_ozon_elastic_action_rows_to_product_core()` already upserts selected Ozon Elastic action product listings and writes promotion participation snapshots. It is scoped to `active`, `candidate` and `candidate_and_active`, not full catalog.
- Current Stage 2 services do not import or call the Product Core sync adapters. WB prices still persist legacy `MarketplaceProduct` and operation detail rows; Ozon product data currently joins `/v3/product/info/list` and `/v4/product/info/stocks` into operation canonical rows but does not write `StockSnapshot`.

## Existing Behavior Vs Remaining Work

| Area | Existing implemented behavior | Remaining implementation work |
| --- | --- | --- |
| Sync run lifecycle | Start, complete, fail, duplicate active guard, redaction guard, techlog records. | Reuse unchanged. Do not bypass completion semantics. |
| Latest cache | Updates from snapshots only in `complete_marketplace_sync_run()`; failed sync preserves previous cache. | Add tests for every new call path proving source-operation failure and Product Core sync failure do not erase previous cache. |
| WB prices | Product Core adapter exists and writes `PriceSnapshot` from normalized WB price rows. | Wire Stage 2.1 successful price download rows to the adapter without changing source operation status/result codes. |
| WB promotions | Product Core adapter exists for regular product rows and skips auto promotions without fabricated listings/snapshots. | Wire Stage 2.1 successful regular promotion product rows to the adapter. Auto-promotion rows must not be fed as fake products. |
| Ozon Elastic actions | Product Core adapter exists for active/candidate/collision action rows and writes `PromotionSnapshot`. | Wire Stage 2.2 successful active/candidate product downloads to the adapter. |
| Ozon stock | Stage 2.2 product data service already fetches and normalizes safe stock rows and computes source `present` sum for operation diagnostics. | Add a Product Core stock adapter and wire successful product data download rows to it. |
| Sales/buyouts/returns | Model/service foundation exists. | Do not create active adapters, formulas, UI/workflow or exports in TASK-PC2-005. |

## Allowed Files

Primary implementation files:

- `apps/product_core/services.py` for the Ozon stock adapter and narrowly scoped adapter helpers;
- `apps/product_core/tests.py` for snapshot service and adapter tests;
- safe fixtures in existing test modules or fixture folders.

Allowed only for call-site wiring from already approved read-only flows:

- `apps/discounts/wb_api/prices/services.py`
- `apps/discounts/wb_api/promotions/services.py`
- `apps/discounts/ozon_api/products.py`
- `apps/discounts/ozon_api/product_data.py`
- matching tests in `apps/discounts/wb_api/prices/tests.py`, `apps/discounts/wb_api/promotions/tests.py`, `apps/discounts/ozon_api/tests.py`

Allowed only if implementation proves a non-business technical event code is required:

- `apps/techlog/models.py` plus migration/tests for a fixed technical event. Prefer existing `marketplace_sync.*`, `marketplace_sync.data_integrity_error` and marketplace API event codes when sufficient.

No model or migration change is expected for TASK-PC2-005. Existing snapshot models already support the required scope.

## Prohibited Files And Changes

Do not change:

- WB/Ozon marketplace write adapters or upload payload policies;
- marketplace card fields, prices, action participation, seller article/vendorCode/offer_id on WB/Ozon;
- source operation status/result codes, reason codes, row statuses, row messages, output files or calculation results;
- `OperationDetailRow.product_ref` values;
- Product Core mapping rules, SKU validator, `ProductVariant` / `InternalProduct` auto-create policy;
- web-panel UI, routes, templates, view permissions or exports for future hooks;
- models/migrations unless an auditor-approved implementation issue proves a schema blocker;
- WB stock snapshots or any new endpoint use;
- `SalesPeriodSnapshot` creation from WB/Ozon sales/orders/buyout/return sources;
- demand, production, in-work, shipment or replenishment formulas.

## Endpoint And Snapshot Matrix

| Source | Allowed Product Core effect | Implementation status | Required guard |
| --- | --- | --- | --- |
| WB `GET /api/v2/list/goods/filter` | Upsert WB listing and write `PriceSnapshot` when price and currency are present. | Adapter exists; Stage 2 call-site wiring remains. | Read-only only, WB rate/retry policy, redacted raw-safe, duplicate article skip. |
| WB promotion calendar/details/nomenclatures | Write `PromotionSnapshot` for regular product rows with deterministic existing listing match. | Adapter exists; Stage 2 call-site wiring remains. | No fake auto-promotion rows; missing listing means warning and no snapshot. |
| WB auto promotions without nomenclature rows | No listing-level snapshot. | Adapter has no-fabrication path. | Count/report safely if called; do not create listing or snapshot. |
| Ozon `GET /v1/actions` | Action selection/context only. | Stage 2 flow exists. | No `MarketplaceListing`, `PriceSnapshot`, `StockSnapshot` or `PromotionSnapshot` from action summary rows. |
| Ozon `/v1/actions/products` and `/v1/actions/candidates` | Upsert selected action product listings and write `PromotionSnapshot`. | Adapter exists; Stage 2 call-site wiring remains. | Selected Elastic action set only, not full catalog; no write endpoints. |
| Ozon `/v3/product/info/list` | Supplement selected rows with `offer_id`, name and safe product info where available. | Stage 2 fetch/join exists. | Do not create `PriceSnapshot` from `min_price` or Elastic price constraints. |
| Ozon `/v4/product/info/stocks` | Write `StockSnapshot` for selected Elastic product rows. | Product Core adapter missing. | Sum exact `present` values only; preserve zero stock; no in-way mapping unless source gives exact in-way fields. |
| Sales/buyouts/returns/demand/in-work/production/shipments | Nullable future hooks only. | Foundation exists. | No active CORE-2 adapter, workflow, UI, formula or export semantics. |
| Any additional read-only catalog/listing endpoint | Only if endpoint-specific official evidence, pagination/rate/retry/redaction rules and tests are added in the implementation task. | Not needed for TASK-PC2-005. | Otherwise blocked for that implementation slice; do not invent endpoint semantics. |

## Ozon Stock Adapter Contract

Add a narrowly scoped adapter such as `sync_ozon_elastic_stock_rows_to_product_core()` in `apps/product_core/services.py`.

Inputs:

- `store`;
- canonical rows from `apps/discounts/ozon_api/product_data.py` successful operation summary;
- `action_id`;
- source `operation`;
- `requested_by`;
- launch method default `service`.

Sync run:

- `marketplace=Marketplace.OZON`;
- `sync_type=MarketplaceSyncRun.SyncType.STOCKS`;
- `source=ListingSource.OZON_API_ACTIONS`;
- `approved_source="ozon_product_info_stocks"`;
- include `action_id`, `not_full_catalog=True`, source operation id and safe row counts in summary.

Row rules:

1. Require `product_id`; otherwise skip with warning.
2. Use only selected action product rows already represented by the Ozon Elastic source basis.
3. Upsert or update the listing from safe selected-row context: `product_id` as `external_primary_id`, `offer_id` as `seller_article`, product name as `title`, Ozon IDs in `external_ids`.
4. If duplicate external article values occur within one marketplace/store sync input, skip affected rows and record the existing data-integrity techlog path.
5. Use `stock_info.stocks[]` as the only current stock source.
6. Compute `total_stock` as the arithmetic sum of parseable `present` values across returned stock rows. This is an approved source aggregation, not demand/replenishment logic.
7. Preserve exact zero stock as `total_stock=0` when at least one `present` value was returned and parsed.
8. If no stock row has a parseable `present`, do not write `StockSnapshot`; count a safe warning.
9. Store `stock_by_warehouse` as redacted/safe source rows, for example `{"rows": [...]}`. Do not collapse duplicate warehouse/type rows in a way that loses source evidence.
10. Keep `in_way_to_client` and `in_way_from_client` nullable unless a future approved source gives exact in-way values. Do not map Ozon `reserved` to in-way fields.
11. `raw_safe` may include `action_id`, `product_id`, `offer_id`, `source_group`, stock row count and a checksum/reference. It must not include credentials, headers or raw sensitive API payload.
12. `source_endpoint` must be `ozon_product_info_stocks`.

## Call-Site Wiring Contract

The implementation should wire Product Core adapters from successful Stage 2 read-only operation flows only.

Required wiring:

- WB prices: after successful/warning `download_wb_prices()` persistence, pass normalized rows or equivalent safe row dicts to `sync_wb_price_rows_to_product_core(..., operation=operation, requested_by=actor)`.
- WB promotions: after successful/warning current promotion persistence, pass real regular promotion product rows to `sync_wb_regular_promotion_rows_to_product_core(..., operation=operation, requested_by=actor)`. Do not pass action summary rows as product rows.
- Ozon active/candidate products: after successful/warning `download_active_products()` / `download_candidate_products()` persistence, pass selected product rows to `sync_ozon_elastic_action_rows_to_product_core(..., operation=operation, requested_by=actor)`.
- Ozon product data: after successful/warning `download_product_data()` persistence, pass canonical product data rows to the new Ozon stock adapter.

Failure isolation:

- A failed source operation must not start or complete a Product Core snapshot sync from that failed source result.
- If a Product Core adapter fails after the source operation was completed successfully, the source operation status/result code/output files must remain unchanged. The Product Core `MarketplaceSyncRun` records its own failed status and techlog.
- Product Core adapter warnings may be represented in the `MarketplaceSyncRun.summary`; do not rewrite Stage 2 source operation summaries unless the implementation task explicitly approves an additive, non-business diagnostic reference.

Transaction boundary:

- Do not allow a Product Core sync exception to roll back an already completed Stage 2 operation.
- If wiring is inside an atomic source persistence function, catch and isolate Product Core sync failures or move the call to a safe post-completion boundary.

## Tests Required

Product Core service tests:

- snapshot context validation rejects listing/store/marketplace mismatch;
- successful `completed_success` and `completed_with_warnings` syncs update `last_values`;
- failed/interrupted sync preserves old `last_values`, `last_sync_run` and `last_successful_sync_at`;
- `create_stock_snapshot()` redaction guard rejects secret-like `raw_safe` and `stock_by_warehouse`;
- `create_sales_period_snapshot()` remains uncalled by all TASK-PC2-005 adapters;
- WB price adapter writes `PriceSnapshot` and cache from approved rows;
- WB price adapter skips missing price/currency rows safely;
- WB regular promotion adapter writes snapshots only for deterministic existing listings;
- WB auto promotion path creates no listing and no `PromotionSnapshot`;
- Ozon action adapter writes `PromotionSnapshot`, not `PriceSnapshot`;
- Ozon stock adapter writes `StockSnapshot` with `total_stock` equal to sum of `present`;
- Ozon stock adapter preserves zero stock when source present values sum to `0`;
- Ozon stock adapter skips rows with no parseable `present`;
- Ozon stock adapter keeps `in_way_to_client` / `in_way_from_client` null;
- duplicate external article rows are skipped with safe data-integrity techlog;
- duplicate active sync guard still applies.

Stage 2 integration tests:

- WB prices successful download creates a Product Core price sync run and one `PriceSnapshot` for a valid row;
- WB prices failed download creates no successful Product Core sync and preserves previous Product Core cache;
- WB promotions successful regular product download creates `PromotionSnapshot` only for product rows, not promotion summary rows;
- WB auto promotion download creates no fake Product Core listing/snapshot;
- Ozon active/candidate downloads create selected-set Product Core listings and `PromotionSnapshot`;
- Ozon product data download creates `StockSnapshot` from `/v4/product/info/stocks` canonical rows;
- Ozon product info `min_price`, Elastic `action_price`, min/max constraints do not create `PriceSnapshot`;
- no marketplace write endpoint is called by any snapshot-filling path;
- Product Core adapter failure does not mutate source operation status/result code/output files;
- redaction tests cover request/response snapshots, sync summaries, error summaries, audit, techlog and exports.

Existing test modules to extend:

- `apps/product_core/tests.py`
- `apps/discounts/wb_api/prices/tests.py`
- `apps/discounts/wb_api/promotions/tests.py`
- `apps/discounts/ozon_api/tests.py`

Recommended focused command set for implementation verification:

```bash
python manage.py test apps.product_core apps.discounts.wb_api.prices apps.discounts.wb_api.promotions apps.discounts.ozon_api
git diff --check
```

## Audit Criteria

Implementation audit should verify:

- snapshot scope matches `GAP-CORE2-004`: active prices, stocks and promotions/actions only;
- `SalesPeriodSnapshot` and future operational hooks remain inactive in CORE-2;
- no demand, production, in-work, shipment, replenishment or cross-marketplace formulas were added;
- no WB auto-promotion fake product rows, listings or promotion snapshots are created;
- Ozon Elastic action price and product info `min_price` are not written as base prices;
- Ozon stock `total_stock` is sourced only from `/v4/product/info/stocks` `present` rows for the selected action product set;
- latest cache is updated only after `MarketplaceSyncRun` `completed_success` / `completed_with_warnings`;
- failed Product Core sync preserves previous latest cache;
- source operation status/result codes and output files are unchanged by Product Core sync failures;
- no new source endpoint appears unless the implementation package includes endpoint-specific official evidence, pagination/rate/retry/redaction rules and mock/contract tests;
- no marketplace write endpoint is called;
- secret-like values are rejected or redacted from snapshots, summaries, errors, audit, techlog, files and exports;
- object access for snapshot visibility/export remains enforced by existing Product Core snapshot permission helpers or paired UI/export tests.

## Stop Conditions For Developer

Stop and return to orchestrator if implementation requires any of the following:

- a new WB/Ozon source endpoint without endpoint-specific official read-only evidence and tests;
- WB stock semantics;
- Ozon full-catalog sync from Elastic sources;
- base Ozon price semantics from `action_price`, `min_price` or Elastic min/max constraints;
- demand, production, in-work, shipment, replenishment or sales/buyout/return formulas;
- active web-panel UX/functionality for future hooks;
- changing Stage 2 source operation business result/status semantics.

These are not open blockers for the current handoff because TASK-PC2-005 can be implemented using the approved current read-only flows.

## Final Verdict

READY_FOR_IMPLEMENTATION for TASK-PC2-005 Snapshot Filling.
