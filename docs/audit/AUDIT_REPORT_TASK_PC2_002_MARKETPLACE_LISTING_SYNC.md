# AUDIT REPORT TASK-PC2-002 Marketplace Listing Sync Integration

Date: 2026-05-02
Auditor: Codex CLI, auditor role
Verdict: PASS
Re-audit: after bugfix D-PC2-002-001

## Scope

Re-audited TASK-PC2-002 approved-source marketplace listing sync integration after duplicate external article guard bugfix.

Checked implementation/evidence files:

- `apps/product_core/services.py`
- `apps/product_core/tests.py`
- `docs/testing/TEST_REPORT_TASK_PC2_002_MARKETPLACE_LISTING_SYNC.md`
- current `docs/audit/AUDIT_REPORT_TASK_PC2_002_MARKETPLACE_LISTING_SYNC.md`

Read mandatory package:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_SCOPE.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-002`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md` section `TASK-PC2-002`
- `docs/stages/stage-3-product-core/core-2/CORE_2_API_SYNC_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_SNAPSHOT_FILLING_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_OPERATION_LINKING_SPEC.md`
- `docs/testing/TEST_REPORT_TASK_PC2_002_MARKETPLACE_LISTING_SYNC.md`

## Closed Findings

### D-PC2-002 - closed, remains closed

WB regular promotion rows no longer fabricate `MarketplaceListing` rows.

Evidence:

- `sync_wb_regular_promotion_rows_to_product_core()` keeps `listings_upserted_count` at `0` and only writes snapshots after deterministic existing listing match: `apps/product_core/services.py:889`-`1000`.
- Ambiguous/missing promotion listing lookup returns `None` unless exactly one same-store/same-marketplace listing matches: `apps/product_core/services.py:700`-`726`.
- Missing listing test asserts warning, no listing creation and no promotion snapshot: `apps/product_core/tests.py:1037`-`1058`.
- Existing deterministic listing test asserts successful match and promotion snapshot/latest cache update: `apps/product_core/tests.py:1060`-`1083`.
- Auto promotion test asserts no fabricated product row/listing: `apps/product_core/tests.py:1085`-`1094`.

### D-PC2-002-001 - closed

Duplicate non-empty `seller_article` rows are now treated as source data integrity warnings and affected rows are skipped, including same article plus same primary id.

Evidence:

- Duplicate detection counts source row occurrences by non-empty seller article, not distinct primary ids: `apps/product_core/services.py:604`-`610`.
- Warning/summary/techlog uses counts only and redacted `sensitive_details_ref`: `apps/product_core/services.py:613`-`652`.
- WB prices guard runs before listing upsert and `PriceSnapshot` creation: `apps/product_core/services.py:786`-`849`.
- WB regular promotions guard runs before deterministic match and `PromotionSnapshot` creation: `apps/product_core/services.py:926`-`1000`.
- Ozon Elastic guard runs before selected-action listing upsert and `PromotionSnapshot` creation: `apps/product_core/services.py:1087`-`1155`.
- Focused tests cover WB price duplicate same article + same `nmID`, WB regular promotion duplicate rows, and Ozon Elastic duplicate same article + same `product_id`: `apps/product_core/tests.py:1148`-`1222`.

## Criteria Review

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1. D-PC2-002 previous bug remains closed. | PASS | WB regular promotions do not upsert listings, skip missing/ambiguous matches through deterministic lookup, and preserve existing-listing snapshot behavior. Tests cover missing, existing deterministic and auto-promotion cases. |
| 2. D-PC2-002-001 duplicate non-empty seller_article rows skipped in WB prices, WB regular promotions, Ozon Elastic. | PASS | Shared occurrence-count duplicate detector plus per-adapter skip guards before writes; tests cover same-article/same-primary-id rows in all required adapters. |
| 3. No endpoint/call-site/write/upload changes; no full catalog expansion. | PASS | Diff is limited to `apps/product_core/services.py` and `apps/product_core/tests.py`; static scan found no HTTP client calls or marketplace write/upload code in changed Product Core files. Ozon summary keeps `not_full_catalog=True`. |
| 4. No model/migration changes. | PASS | `git diff --name-only` shows only Product Core services/tests before this audit report update; no model or migration files changed. |
| 5. Secret-like values protected in summaries/external_ids/raw_safe/techlog. | PASS | Sync summaries and error summaries call `assert_no_secret_like_values`; listing `external_ids` and snapshot `raw_safe`/constraints are guarded; techlog duplicate warning stores counts plus redacted details only. Redaction test remains present. |
| 6. Test report evidence sufficient. | PASS | Tester report records PASS after D-PC2-002 and D-PC2-002-001 retest, lists mandatory/static evidence, and includes Product Core plus Stage 1/2 regression commands. Auditor reran required Product Core checks successfully. |

## Commands Run

| Command | Result |
| --- | --- |
| `git diff --check` | PASS, no output. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.product_core --verbosity 1 --noinput` | PASS: 38 tests OK. |
| Static `rg` scans for HTTP/write/upload/endpoint patterns in changed Product Core files | PASS for no new call sites/write/upload behavior. |

## Notes

- The tester report also records successful broader regression suites: WB/Ozon Stage 2 API tests and `apps.web apps.operations apps.marketplace_products`.
- `docs/tasks/implementation/product-core/TASK_PC2_002_MARKETPLACE_LISTING_SYNC.md` remains absent per tester note. This is non-blocking for this re-audit because the orchestrator supplied the mandatory CORE-2 task section and reading package.

## Final Verdict

PASS. TASK-PC2-002 meets the re-audit criteria. Previous finding D-PC2-002 is explicitly closed and remains closed; D-PC2-002-001 is closed by implementation, focused tests and successful recheck.
