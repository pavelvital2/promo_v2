# TEST_REPORT_TASK_PC2_004_OPERATION_ROW_FK_ENRICHMENT

Date: 2026-05-02
Role: TASK-PC2-004 tester retest after writer hooks
Task: Operation Row FK Enrichment
Verdict: PASS

## Scope

Retested previous FAIL `PC2-004-TEST-001: New-row writer hooks are deferred but handoff keeps them in scope`.

Product code was not changed during this retest. This report file is the only tester change.

Documents read:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/reports/TASK_PC2_004_DESIGN_HANDOFF.md`
- `docs/audit/AUDIT_REPORT_TASK_PC2_004_DESIGN_HANDOFF.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_OPERATION_LINKING_SPEC.md`
- previous `docs/testing/TEST_REPORT_TASK_PC2_004_OPERATION_ROW_FK_ENRICHMENT.md`

## Verdict Rationale

Previous blocker is closed.

Static verification now finds writer hooks in the approved `apps/discounts/**` families:

- WB Excel: `apps/discounts/wb_excel/services.py:707` through `apps/discounts/wb_excel/services.py:709`, called after `sync_products_for_operation()` in check/process flows.
- Ozon Excel: `apps/discounts/ozon_excel/services.py:289` through `apps/discounts/ozon_excel/services.py:291`, called after `sync_products_for_operation()` in check/process flows.
- WB API prices: `apps/discounts/wb_api/prices/services.py:277` through `apps/discounts/wb_api/prices/services.py:281`.
- WB API promotions: product rows only at `apps/discounts/wb_api/promotions/services.py:456` through `apps/discounts/wb_api/promotions/services.py:474`; summary rows are not hooked in the surrounding summary-row creation path.
- WB API calculation: `apps/discounts/wb_api/calculation/services.py:228` through `apps/discounts/wb_api/calculation/services.py:238`.
- WB API upload: drift-blocked rows at `apps/discounts/wb_api/upload/services.py:476` through `apps/discounts/wb_api/upload/services.py:486`; polled result rows at `apps/discounts/wb_api/upload/services.py:724` through `apps/discounts/wb_api/upload/services.py:735`.
- Ozon active/candidate products: `apps/discounts/ozon_api/products.py:286` through `apps/discounts/ozon_api/products.py:298`.
- Ozon product data: `apps/discounts/ozon_api/product_data.py:338` through `apps/discounts/ozon_api/product_data.py:351`.
- Ozon calculation: `apps/discounts/ozon_api/calculation.py:364` through `apps/discounts/ozon_api/calculation.py:375`.
- Ozon upload: `apps/discounts/ozon_api/upload.py:578` through `apps/discounts/ozon_api/upload.py:589`.

No inspected discount writer family now relies on backfill only. Product Core sync/export rows remain outside the inspected discount writer scope and are acceptable/non-blocking per handoff because export rows derived directly from a listing queryset need not create separate `OperationDetailRow` FK enrichment behavior.

## Static And Behavioral Verification

PASS: Ozon actions summary rows remain unlinked by design.

- No hook was added to `apps/discounts/ozon_api/actions.py`.
- Regression test asserts Ozon actions download creates detail rows with no listing FK in `apps/discounts/ozon_api/tests.py:523` through `apps/discounts/ozon_api/tests.py:525`.

PASS: promotion summary rows remain unlinked; product rows link.

- Resolver classifies only `wb_api_promotion_product_valid` / `wb_api_promotion_product_invalid` as product rows and rejects summary reason codes in `apps/operations/listing_enrichment.py:34` through `apps/operations/listing_enrichment.py:43` and `apps/operations/listing_enrichment.py:111` through `apps/operations/listing_enrichment.py:118`.
- Regression test verifies product detail linked and summary/current-filter rows unlinked in `apps/discounts/wb_api/promotions/tests.py:272` through `apps/discounts/wb_api/promotions/tests.py:289`.

PASS: WB prices final `product_ref` handling remains compatible with previous behavior.

- The existing final writer update to `product_ref=product.sku` remains in `apps/discounts/wb_api/prices/services.py:277` through `apps/discounts/wb_api/prices/services.py:279`.
- The hook updates the local row object to the final `product.sku` before resolving in `apps/discounts/wb_api/prices/services.py:280` through `apps/discounts/wb_api/prices/services.py:281`, so it does not preserve stale `nmID` if the writer changes `product_ref`.
- Regression test asserts the linked detail keeps `product_ref == "101"` and links to the listing in `apps/discounts/wb_api/prices/tests.py:191` through `apps/discounts/wb_api/prices/tests.py:195`.

PASS: operation summary/status/files/reason/result/message/final_value are unchanged by hooks.

- Added hooks call `enrich_detail_row_marketplace_listing()` after row creation and do not alter summary/status/files/reason/result/message/final_value assignments in the touched writer paths.
- The enrichment service writes only `marketplace_listing_id` in `apps/operations/listing_enrichment.py:231` through `apps/operations/listing_enrichment.py:240`.
- The terminal guard permits only `{"marketplace_listing_id"}` under the explicit enrichment context in `apps/operations/models.py:363` through `apps/operations/models.py:382`.
- Negative tests cover protected row fields and operation summary in `apps/operations/tests.py:870` through `apps/operations/tests.py:907`.

PASS: existing resolver/backfill/terminal guard still pass.

- Resolver remains same-store/same-marketplace and exact-key only in `apps/operations/listing_enrichment.py:160` through `apps/operations/listing_enrichment.py:217`.
- Backfill still records row counts, `(id, product_ref)` checksum, conflict counts, same-scope violations and changed product_ref count in `apps/operations/listing_enrichment.py:266` through `apps/operations/listing_enrichment.py:319`.
- Tests cover resolver rejection cases, different-FK no-overwrite and backfill idempotency/checksum stability in `apps/operations/tests.py:814` through `apps/operations/tests.py:971`.

PASS: direct regression evidence exists for representative writer hooks.

- WB Excel product rows link after legacy listing sync without changing `product_ref` in `apps/discounts/wb_excel/tests.py:239` through `apps/discounts/wb_excel/tests.py:250`.
- WB prices product rows link by the synced listing key in `apps/discounts/wb_api/prices/tests.py:191` through `apps/discounts/wb_api/prices/tests.py:195`.
- WB promotions product rows link while summary rows remain unlinked in `apps/discounts/wb_api/promotions/tests.py:272` through `apps/discounts/wb_api/promotions/tests.py:289`.
- Ozon active products link matching product rows and leave unmatched rows unlinked in `apps/discounts/ozon_api/tests.py:587` through `apps/discounts/ozon_api/tests.py:638`.
- Ozon actions summary rows remain unlinked in `apps/discounts/ozon_api/tests.py:523` through `apps/discounts/ozon_api/tests.py:525`.

## Command Results

1. `git diff --check` - PASS.
2. `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` - PASS, `System check identified no issues (0 silenced).`
3. `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run` - PASS, `No changes detected.`
4. `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.operations apps.product_core --verbosity 1 --noinput` - PASS, 75 tests.
5. `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts --verbosity 1 --noinput` - PASS, 102 tests. Note: an initial parallel attempt collided on the shared `test_promo_v2` database; the sequential rerun passed.
6. `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py help backfill_operation_detail_listing_fk` - PASS, help exposes dry-run default plus `--write`, `--limit`, `--start-id`, and `--end-id`.

## Residual Risk

Direct FK assertions in `apps.discounts` are representative rather than exhaustive: WB Excel, WB prices, WB promotions, Ozon actions and Ozon active products have explicit assertions, while Ozon Excel, WB calculation/upload and Ozon product_data/calculation/upload are verified by static hook placement plus the full discounts regression suite. This is acceptable for retest because the previous blocker was absence of hooks, all approved writer families now call the common tested enrichment service, and no command/regression failure was observed.

The public enrichment context manager can still be misused by future code to update `marketplace_listing_id` directly. Existing tests prove protected fields remain blocked; continued review should ensure new callers use `enrich_detail_row_marketplace_listing()` rather than opening the context manually outside the approved service path.

## Verdict

PASS.

TASK-PC2-004 retest accepts the writer-hook fix. The previous blocker is closed, summary/action rows remain unlinked by design, product rows link where deterministic listing context exists, `product_ref` and operation outcomes remain protected, and required checks pass.

## Changed Files

- `docs/testing/TEST_REPORT_TASK_PC2_004_OPERATION_ROW_FK_ENRICHMENT.md`
