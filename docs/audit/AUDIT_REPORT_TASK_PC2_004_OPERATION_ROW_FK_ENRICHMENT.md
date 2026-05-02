# AUDIT_REPORT_TASK_PC2_004_OPERATION_ROW_FK_ENRICHMENT

Date: 2026-05-02
Role: implementation auditor
Task: TASK-PC2-004 Operation Row FK Enrichment
Verdict: PASS

Product code was not changed during this audit. This audit created only this report.

## Scope

Audited implementation of nullable `OperationDetailRow.marketplace_listing` enrichment against the TASK-PC2-004 handoff, design audit, testing report and CORE-2 operation linking/model specs.

Audited changed files:

- `apps/operations/models.py`
- `apps/operations/listing_enrichment.py`
- `apps/operations/management/commands/backfill_operation_detail_listing_fk.py`
- `apps/operations/tests.py`
- touched `apps/discounts/**` services/tests
- `docs/testing/TEST_REPORT_TASK_PC2_004_OPERATION_ROW_FK_ENRICHMENT.md`

## Mandatory Documents Read

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/reports/TASK_PC2_004_DESIGN_HANDOFF.md`
- `docs/audit/AUDIT_REPORT_TASK_PC2_004_DESIGN_HANDOFF.md`
- `docs/testing/TEST_REPORT_TASK_PC2_004_OPERATION_ROW_FK_ENRICHMENT.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_OPERATION_LINKING_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_MODEL_AND_MIGRATION_PLAN.md`
- `docs/product/OPERATIONS_SPEC.md`

## Findings

No blocking findings.

The implementation stays within deterministic FK enrichment and does not change the business meaning of operation rows. `product_ref` remains the historical raw value; enrichment writes only `marketplace_listing_id` through the controlled service path.

## Criteria Review

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | `product_ref` byte-for-byte preserved; no operation summaries/status/files/reason/result/message/problem/final_value/calculation changes. | PASS | Enrichment service updates only `marketplace_listing_id` in `apps/operations/listing_enrichment.py:231`-`240`. Backfill records row count/checksum over `(id, product_ref)` in `apps/operations/listing_enrichment.py:244`-`255` and changed product_ref count in `apps/operations/listing_enrichment.py:309`-`318`. Writer hooks are additive after existing row/result persistence and do not alter summary/status/result-code assignments. |
| 2 | Resolver deterministic same-store/same-marketplace only; exact trim-only approved keys; no fuzzy/title/partial/case-fold/barcode-only matching. | PASS | Resolver scopes candidates by operation marketplace/store in `apps/operations/listing_enrichment.py:172`-`177`. Matching uses trim-only scalar comparison for `external_primary_id`, `seller_article` and approved WB/Ozon `external_ids` keys in `apps/operations/listing_enrichment.py:139`-`157`. Tests reject cross-store, duplicate, blank, case-folded, partial, barcode-only and title matches in `apps/operations/tests.py:814`-`868`. |
| 3 | Product rows linked; action/promotion summary rows unlinked. | PASS | Row classifier rejects Ozon actions and WB promotion summary reason codes in `apps/operations/listing_enrichment.py:104`-`128`. WB promotion product rows alone call enrichment in `apps/discounts/wb_api/promotions/services.py:449`-`474`; summary rows at `apps/discounts/wb_api/promotions/services.py:349`-`447` do not. Tests assert promotion product linked and summaries unlinked in `apps/discounts/wb_api/promotions/tests.py:272`-`289`; Ozon action rows remain unlinked in `apps/discounts/ozon_api/tests.py:523`-`525`. |
| 4 | Terminal guard only allows `marketplace_listing_id` update in explicit enrichment context; no direct SQL; negative fields rejected. | PASS | Terminal related-row updates are blocked except `OperationDetailRow` with exactly `{"marketplace_listing_id"}` and explicit context in `apps/operations/models.py:363`-`382`. Enrichment uses ORM `update()` inside that context, not raw SQL, in `apps/operations/listing_enrichment.py:231`-`240`. Negative tests reject `product_ref`, `row_status`, `reason_code`, `message`, `problem_field`, `final_value`, `created_at` and operation summary changes in `apps/operations/tests.py:870`-`907`. |
| 5 | Backfill dry-run default, bounded/resumable/idempotent, checksum over `(id, product_ref)`, conflict counts/classes, same-scope violation evidence. | PASS | Command defaults to dry-run unless `--write` is passed and exposes `--limit`, `--start-id`, `--end-id` in `apps/operations/management/commands/backfill_operation_detail_listing_fk.py:13`-`29`. Backfill captures high-water id, checksums, conflict/family counts and same-scope violations in `apps/operations/listing_enrichment.py:266`-`319`. Tests cover dry-run, write, idempotency and checksum stability in `apps/operations/tests.py:920`-`971`. |
| 6 | Writer hooks do not alter business behavior and do not create stale FK/product_ref mismatches, especially WB API prices post-update behavior. | PASS | Hooks call common enrichment after row creation/sync. WB API prices preserves the existing post-create `product_ref=product.sku` update, updates the in-memory row before resolving, and then enriches in `apps/discounts/wb_api/prices/services.py:257`-`281`; regression asserts final `product_ref == "101"` and FK link in `apps/discounts/wb_api/prices/tests.py:191`-`195`. |
| 7 | Existing different FK not overwritten. | PASS | Locked service path returns existing-FK resolution instead of overwriting when a row already has an FK in `apps/operations/listing_enrichment.py:231`-`235`. Resolver treats existing different FK as a conflict/no update in `apps/operations/listing_enrichment.py:185`-`197`. Test proves a different FK remains unchanged in `apps/operations/tests.py:908`-`918`. |
| 8 | No UI/report leak changes; no new marketplace writes. | PASS | No `apps/web`, template, serializer, route or permission files were changed. Added calls in API upload/download services only enrich local `OperationDetailRow` FK after existing persistence; no marketplace adapter/write request mapping was added. Ozon upload and WB upload touched lines add only local enrichment after detail-row creation in `apps/discounts/ozon_api/upload.py:575`-`589` and `apps/discounts/wb_api/upload/services.py:717`-`735`. |
| 9 | Test evidence sufficient; residual risk acceptable. | PASS | Required command suite passes. Direct regression evidence covers resolver, guard, backfill, WB Excel, WB prices, WB promotions, Ozon actions and Ozon active product linking. Tester residual risk notes representative rather than exhaustive direct FK assertions for several hooks; this is acceptable because all hooks call the same tested service and full discounts regression passed. |

## Residual Risk

The enrichment context manager is public within `apps.operations.models` and can be misused by future code to update `marketplace_listing_id` directly. Current production callers use it only through `enrich_detail_row_marketplace_listing()`, which resolves and checks same store/marketplace before writing. Existing tests prove protected fields remain blocked. This is an acceptable review risk, not a release blocker for TASK-PC2-004.

Several discount writer hooks have static placement plus full-suite regression evidence rather than direct FK assertions in every individual flow. The common service coverage and representative tests make the risk acceptable.

## Checks

- `git diff --check` - PASS.
- `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` - PASS, `System check identified no issues (0 silenced).`
- `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.operations apps.product_core --verbosity 1 --noinput` - PASS, 75 tests.
- `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts --verbosity 1 --noinput` - PASS, 102 tests.

## Conclusion

PASS. TASK-PC2-004 Operation Row FK Enrichment is acceptable. The implementation preserves `product_ref` and operation business outputs, links only deterministic same-store/same-marketplace product rows, leaves action/promotion summaries unlinked, keeps terminal immutability except for the explicit FK enrichment path, and provides bounded dry-run backfill evidence.

## Changed Files

- `docs/audit/AUDIT_REPORT_TASK_PC2_004_OPERATION_ROW_FK_ENRICHMENT.md`
