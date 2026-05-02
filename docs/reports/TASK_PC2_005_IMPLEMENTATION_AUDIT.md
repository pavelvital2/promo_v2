# TASK_PC2_005_IMPLEMENTATION_AUDIT

Date: 2026-05-02
Role: TASK-PC2-005 implementation auditor
Task: TASK-PC2-005 Snapshot Filling
Verdict: PASS

## Documents Checked

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/reports/TASK_PC2_005_DESIGN_HANDOFF.md`
- `docs/reports/TASK_PC2_005_DESIGN_AUDIT.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_SNAPSHOT_FILLING_SPEC.md`
- current `git diff`

## Diff Scope

Implementation changes are limited to the approved Product Core adapter and Stage 2 read-only call-site files:

- `apps/product_core/services.py`
- `apps/product_core/tests.py`
- `apps/discounts/wb_api/prices/services.py`
- `apps/discounts/wb_api/prices/tests.py`
- `apps/discounts/wb_api/promotions/services.py`
- `apps/discounts/wb_api/promotions/tests.py`
- `apps/discounts/ozon_api/products.py`
- `apps/discounts/ozon_api/product_data.py`
- `apps/discounts/ozon_api/tests.py`

No model, migration, UI, marketplace write adapter or upload policy changes were present in the audited diff.

## Audit Checks

| Check | Result |
| --- | --- |
| Scope remains only approved/read-only price, stock, promotion/action snapshots. | PASS. WB prices write `PriceSnapshot` only from `wb_prices_list_goods_filter`; WB regular promotion product rows write `PromotionSnapshot` only after deterministic listing match; Ozon selected Elastic product rows write `PromotionSnapshot`; Ozon selected product data writes `StockSnapshot`. |
| No `SalesPeriodSnapshot` active path; no demand/production formulas/UI. | PASS. `create_sales_period_snapshot()` remains a foundation helper only. New call-sites are limited to the four approved adapters. No demand, production, in-work, shipment, replenishment or UI path appears in the diff. |
| No fake WB auto product rows/snapshots. | PASS. WB promotions skip auto promotions before nomenclature fetching and before Product Core sync wiring. Adapter auto path records warning metadata only and creates no listing/snapshot. |
| Ozon stock snapshots only from selected Elastic product data `/v4/product/info/stocks`, `present` sum, zero preserved, in-way null. | PASS. Product data basis is built from latest successful active/candidate selected action operations; stock fetch uses `product_info_stocks`; stock adapter sums parseable `stock_info.stocks[].present`, preserves zero, skips rows without parseable `present`, stores source rows safely, and sets in-way fields to null. |
| Ozon `action_price` / `min_price` does not create `PriceSnapshot`. | PASS. Ozon action adapter writes `action_price` into `PromotionSnapshot`; product-data `min_price` remains diagnostic/calculation source data. Tests assert no `PriceSnapshot` for Ozon action and product-data sync runs. |
| Latest cache updates only through successful Product Core completion; failed source/Product Core sync preserves source operation status/result/output. | PASS. `complete_marketplace_sync_run()` is the only cache update path. Stage 2 wiring runs only after successful `_persist_success`; Product Core exceptions are caught after source completion and recorded to techlog without mutating source operation status/result/output. Failed source operation tests assert no Product Core run. |
| Secret guards and safe snapshots are adequate. | PASS. Existing `assert_no_secret_like_values` guards remain on sync summaries, error summaries, snapshot raw fields, stock warehouse fragments and listing external IDs. New stock raw payload stores action/product/offer/source metadata plus checksum, not raw credentials/headers. |
| Tests cover meaningful behavior. | PASS. Tests cover adapter success/skip cases, no fake WB auto rows, Ozon no price snapshots, Ozon stock present sum and zero stock, null in-way fields, duplicate article warnings, source failure no Product Core sync, Product Core failure isolation for WB prices, and redaction guards. |

## Verification

Commands run by auditor:

```bash
git diff --check
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.product_core apps.discounts.wb_api.prices apps.discounts.wb_api.promotions apps.discounts.ozon_api
```

Results:

- `git diff --check`: PASS
- focused suite: PASS, 113 tests, PostgreSQL env, `OK`

The developer-reported focused suite result matched the auditor rerun.

## Residual Risks

- Product Core failure isolation is explicitly tested for WB prices; Ozon and WB promotion call-sites use the same post-success try/except pattern, but do not each have a dedicated mocked adapter-failure integration test in the audited diff.
- Secret guard coverage relies on shared `assert_no_secret_like_values` behavior and representative redaction tests; it is adequate for this slice, but future endpoints must add endpoint-specific redaction tests before snapshot filling.
- `MarketplaceListing.last_values` still has generic support for sales snapshots from the foundation model. This is acceptable because TASK-PC2-005 adds no active sales snapshot creation path.

## Final Verdict

PASS. TASK-PC2-005 implementation matches the approved Snapshot Filling handoff and CORE-2 snapshot scope.
