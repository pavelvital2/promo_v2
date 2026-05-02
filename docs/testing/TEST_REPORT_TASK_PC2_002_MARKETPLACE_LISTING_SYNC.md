# TEST REPORT TASK-PC2-002 Marketplace Listing Sync Integration

Date: 2026-05-02
Tester: Codex CLI, tester role
Result: PASS
Retest: after D-PC2-002 and D-PC2-002-001 bugfixes

## Scope

Retested TASK-PC2-002 approved-source slice for Product Core marketplace listing sync adapters after the WB regular promotion missing-listing bugfix and the duplicate external article guard bugfix.
Product code was not changed by the tester. This report is the only tester-edited file.

Read package:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md`
- `docs/audit/AUDIT_REPORT_TASK_PC2_002_MARKETPLACE_LISTING_SYNC.md`
- `docs/testing/TEST_REPORT_TASK_PC2_002_MARKETPLACE_LISTING_SYNC.md` previous FAIL report
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-002`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md` section `TASK-PC2-002`
- `docs/stages/stage-3-product-core/core-2/CORE_2_API_SYNC_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_DATA_FLOW.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_SNAPSHOT_FILLING_SPEC.md`

Reading note: requested file `docs/tasks/implementation/product-core/TASK_PC2_002_MARKETPLACE_LISTING_SYNC.md` is absent in this worktree. The task-scoped TASK-PC2-002 sections in CORE-2 agent tasks/reading packages were used instead.

## Commands

| Command | Result |
| --- | --- |
| `git diff --check` | PASS, no output. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run` | PASS: `No changes detected`. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.product_core --verbosity 1 --noinput` | PASS: 38 tests OK. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api.prices apps.discounts.wb_api.promotions apps.discounts.ozon_api --verbosity 1 --noinput` | PASS: 60 tests OK. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.web apps.operations apps.marketplace_products --verbosity 1 --noinput` | PASS: 71 tests OK. |

Execution note: the optional regression suite was possible in this environment and passed.

## D-PC2-002 Retest

Status: closed.

Evidence:

- Missing WB regular promotion listing: `apps/product_core/tests.py:1037` asserts `COMPLETED_WITH_WARNINGS`, `listings_upserted_count == 0`, `missing_listing_match_count == 1`, no `MarketplaceListing`, and no `PromotionSnapshot`.
- Existing deterministic listing: `apps/product_core/tests.py:1060` asserts `COMPLETED_SUCCESS`, `listings_upserted_count == 0`, `listings_matched_count == 1`, and one promotion snapshot in latest cache.
- Implementation resolves promotion rows through existing listings only: `apps/product_core/services.py:945` calls `_find_existing_listing_for_wb_promotion_row`; `apps/product_core/services.py:950` skips missing match with warning; `apps/product_core/services.py:988` reports zero listing upserts for WB promotions.
- Ambiguous match behavior is present statically: `apps/product_core/services.py:706` limits lookup to two matches and `apps/product_core/services.py:714` returns `None` unless exactly one match exists. That falls into the same skip+warning path. No dedicated ambiguous-match test was found in the diff.

## Static Diff Inspection

Changed product files in developer diff:

- `apps/product_core/services.py`
- `apps/product_core/tests.py`

No tester changes were made to product files.

Findings:

- No diff exists under `apps/discounts`, `apps/web`, `apps/operations`, or `apps/marketplace_products`.
- No new WB/Ozon HTTP client call sites were found in the changed Product Core files.
- No marketplace upload/write endpoint code was added or modified by this diff.
- Product Core adapters consume already-provided approved-source rows and store safe sync/snapshot data.

## D-PC2-002-001 Retest

Status: closed.

Evidence:

- Duplicate article detection now counts source row occurrences by non-empty `seller_article`, so same article + same primary id is treated as duplicate: `apps/product_core/services.py:604`.
- WB prices apply the duplicate guard before listing upsert and price snapshot creation; affected duplicate rows are skipped and a source data integrity warning is recorded: `apps/product_core/services.py:787`, `apps/product_core/services.py:797`, `apps/product_core/services.py:822`.
- WB regular promotions apply the same duplicate guard before deterministic listing match and promotion snapshot creation; duplicate rows are skipped with no listing matches and no snapshots: `apps/product_core/services.py:930`, `apps/product_core/services.py:941`, `apps/product_core/services.py:973`.
- Ozon Elastic applies the same duplicate guard before selected-action listing upsert and promotion snapshot creation: `apps/product_core/services.py:1091`, `apps/product_core/services.py:1101`, `apps/product_core/services.py:1125`.
- Focused tests cover WB price duplicate same article + same `nmID`, WB regular promotion duplicate rows with no snapshots, and Ozon Elastic duplicate same article + same `product_id`: `apps/product_core/tests.py:1148`, `apps/product_core/tests.py:1164`, `apps/product_core/tests.py:1206`.

Static confirmation:

- WB price duplicate same id skipped: PASS. The test asserts `COMPLETED_WITH_WARNINGS`, `affected_rows_count == 2`, `skipped_rows_count == 2`, no `MarketplaceListing` for `external_primary_id="311"`, and no `PriceSnapshot`.
- WB regular promotion duplicate skipped/no snapshots: PASS. The test asserts `COMPLETED_WITH_WARNINGS`, zero listing upserts, zero listing matches, zero promotion snapshots, two skipped rows, no `PromotionSnapshot`, and a techlog `marketplace_sync.response_invalid` warning.
- Ozon Elastic duplicate same id skipped: PASS. The test asserts `COMPLETED_WITH_WARNINGS`, `affected_rows_count == 2`, `skipped_rows_count == 2`, no `MarketplaceListing` for `external_primary_id="9011"`, and no `PromotionSnapshot`.
- D-PC2-002 previous fix preserved: PASS. WB regular promotion still does not fabricate missing listings and writes snapshots only for existing deterministic listings.

## Final Result

PASS.

No blocking defects found in the second retest. D-PC2-002 and D-PC2-002-001 are closed by tests and static inspection.
