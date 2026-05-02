# TASK_PC2_004_DESIGN_HANDOFF

Date: 2026-05-02
Role: TASK-PC2-004 designer
Task: TASK-PC2-004 Operation Row FK Enrichment
Verdict: READY_FOR_IMPLEMENTATION

## Scope Of This Handoff

This handoff prepares the implementation package for nullable `OperationDetailRow.marketplace_listing` enrichment.

In scope:

- deterministic same-store/same-marketplace resolver from operation detail rows to `MarketplaceListing`;
- FK write for new operation detail rows where source context or deterministic lookup is already available;
- optional idempotent backfill for old rows where a safe unique match exists;
- safe conflict logging and run evidence;
- pre/post row count plus checksum/hash evidence over `(id, product_ref)`;
- tests proving `product_ref` and historical operation outcomes remain unchanged.

Out of scope:

- product-code implementation in this designer task;
- any mutation of `OperationDetailRow.product_ref`;
- operation result/status/file/reason/result-code recalculation;
- linking action/promotion summary rows as product rows;
- cross-store or cross-marketplace lookup;
- UI/report link display unless a paired UI implementation task explicitly includes it.

`GAP-CORE2-003` is resolved by customer decision on 2026-05-02. No `BLOCKED_BY_CUSTOMER_QUESTION` is raised for TASK-PC2-004.

## Documents Read

Mandatory task inputs:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-004`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md` section `TASK-PC2-004`
- `docs/stages/stage-3-product-core/core-2/CORE_2_OPERATION_LINKING_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_MODEL_AND_MIGRATION_PLAN.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Read-only code context:

- `apps/operations/models.py`
- `apps/product_core/models.py`
- `apps/marketplace_products/services.py`
- operation detail writers found by `rg "OperationDetailRow|product_ref" apps/discounts apps/operations`

## Current Code Facts

- `OperationDetailRow.marketplace_listing` already exists in the current codebase with nullable `PROTECT` FK and index-compatible ForeignKey behavior. See `apps/operations/models.py` and migration `apps/operations/migrations/0011_operationdetailrow_marketplace_listing.py`.
- `OperationDetailRow.clean()` already validates same store and same marketplace for a non-null FK.
- `OperationDetailRow.save()` and `OperationRelatedQuerySet.update()` currently block mutations for terminal operations. Old-row backfill therefore needs a deliberately narrow enrichment path; normal `save()` / `objects.update()` cannot be used for completed historical operations.
- `MarketplaceListing` has the approved deterministic fields: `external_primary_id`, `external_ids`, `seller_article`, `barcode`, unique `(marketplace, store, external_primary_id)`, and same-store marketplace validation through the listing/store model contract.
- Legacy `MarketplaceProduct` rows are mirrored into `MarketplaceListing` by `sync_listing_from_legacy_product()`, using legacy `sku` as `MarketplaceListing.external_primary_id` and safe external IDs as listing metadata.
- Current `apps/discounts/**` operation detail writers create rows with `product_ref` only; no inspected writer currently supplies `marketplace_listing`.

## Allowed Files

Primary implementation files:

- `apps/operations/listing_enrichment.py` or a closely scoped helper in `apps/operations/services.py`;
- `apps/product_core/services.py` only for shared listing lookup helpers if the resolver belongs next to existing Product Core listing services;
- `apps/operations/management/commands/backfill_operation_detail_listing_fk.py` plus package `__init__.py` files, if backfill is delivered as a command;
- additive calls in approved writer files:
  - `apps/discounts/wb_excel/services.py`
  - `apps/discounts/ozon_excel/services.py`
  - `apps/discounts/wb_api/prices/services.py`
  - `apps/discounts/wb_api/promotions/services.py`
  - `apps/discounts/wb_api/calculation/services.py`
  - `apps/discounts/wb_api/upload/services.py`
  - `apps/discounts/ozon_api/products.py`
  - `apps/discounts/ozon_api/product_data.py`
  - `apps/discounts/ozon_api/calculation.py`
  - `apps/discounts/ozon_api/upload.py`
- tests in `apps/operations/tests.py`, `apps/product_core/tests.py`, and touched `apps/discounts/**/tests.py`;
- `apps/operations/models.py` only for a minimal, explicit service guard needed to set `marketplace_listing_id` on terminal rows during approved enrichment/backfill, without weakening general operation immutability;
- `apps/operations/migrations/*` only if the implementation branch does not already contain the nullable FK migration equivalent to current `0011`.

Allowed only if implementation proves a fixed enum is required for safe techlog:

- `apps/techlog/models.py` plus migration/tests for a non-business technical event type such as operation detail listing enrichment conflict. Do not add reason/result codes.

## Prohibited Files And Changes

Do not change:

- `OperationDetailRow.product_ref`, including whitespace, case, string form or legacy values;
- operation summary, result/status/error/warning counts, output files, warning confirmations, reason/result codes, row status, messages, problem fields or final values;
- Stage 1 WB/Ozon Excel calculation logic;
- Stage 2.1 WB API business logic, upload status mapping or quarantine/drift behavior;
- Stage 2.2 Ozon Elastic calculation/upload behavior;
- Product Core mapping rules, `ProductVariant`, `InternalProduct` auto-create rules or SKU normalization;
- WB/Ozon API write adapters or marketplace card fields;
- `apps/web/*`, templates, serializers, routes or permissions unless a separate paired UI/report task explicitly assigns them.

## Resolver Rules

Resolver input:

- `OperationDetailRow` with its `Operation`;
- optional source row/listing context for new-row writes;
- operation family classifier from `Operation.mode`, `Operation.module`, `Operation.operation_type`, and `Operation.step_code`.

Required resolver behavior:

1. Require operation `marketplace` and `store_id`.
2. Require non-empty `product_ref` after `strip()` for matching only. Do not write the stripped value back.
3. Reject rows classified as action/promotion summaries or technical operation-level failure rows that do not represent a product/listing identifier.
4. Search only listings with the same `marketplace` and `store_id`.
5. Match by approved deterministic keys:
   - `MarketplaceListing.external_primary_id`;
   - `MarketplaceListing.seller_article`;
   - source-specific scalar values in `MarketplaceListing.external_ids`;
   - WB allowed external IDs: `nmID`, `vendorCode`;
   - Ozon allowed external IDs: `product_id`, `offer_id`.
6. Treat source scalars as exact string values after trim for comparison. Do not case-fold, transliterate, remove punctuation, remove internal spaces or do partial matching.
7. Use `MarketplaceListing.barcode` only as a supplemental conflict/review signal. It must not be the sole positive match key in TASK-PC2-004.
8. If exactly one candidate remains, return it.
9. If no candidate, multiple candidates, same key duplicate, wrong store/marketplace or unapproved source scope exists, return no listing and emit a safe conflict class.
10. If the row already has the same FK, return idempotent no-op.
11. If the row already has a different FK, do not overwrite it in TASK-PC2-004; count a safe conflict and require a separate correction task.

Approved conflict classes:

- `no_listing_match`
- `multiple_listing_matches`
- `store_marketplace_mismatch`
- `row_not_product_identifier`
- `secret_redaction_guard_failed`
- `source_scope_not_approved`
- `api_data_integrity_duplicate`

Conflict logs must not include secrets, raw API tokens, raw request headers or stack traces. Safe identifiers may include operation id/visible id, row id, row number, marketplace, store id, operation family, conflict class and hashed/truncated key basis.

## Operation Families

| Family | Current writer context | FK behavior |
| --- | --- | --- |
| Stage 1 WB Excel detail rows | `apps/discounts/wb_excel/services.py` creates `product_ref=detail.article`; `sync_products_for_operation()` mirrors legacy products to listings after details are persisted. | Link product rows after legacy listing sync or through backfill when `product_ref` exactly matches a unique WB listing `external_primary_id`, `seller_article`, `external_ids.nmID` or `external_ids.vendorCode` in the same store. Blank output-write error rows stay unlinked. |
| Stage 1 Ozon Excel detail rows | `apps/discounts/ozon_excel/services.py` creates `product_ref=detail.product_ref`; legacy sync mirrors listings. | Link product rows after legacy listing sync or through backfill when `product_ref` exactly matches a unique Ozon listing `external_primary_id`, `seller_article`, `external_ids.product_id` or `external_ids.offer_id` in the same store. Blank output-write error rows stay unlinked. |
| `wb_api_prices_download` | `apps/discounts/wb_api/prices/services.py` writes price product rows by WB `nmID`; Product Core price sync can upsert listings from `nmID`/`vendorCode`. | Link product rows by unique same-store WB `nmID`/`vendorCode`. Preserve current `product_ref` exactly; do not add any recalculation. |
| `wb_api_promotions_download` | `apps/discounts/wb_api/promotions/services.py` writes promotion summary rows and regular promotion product rows. | Link only regular product rows with `product_ref=product.nm_id`. Do not link promotion summary rows, current-filter rows, regular-promotion summary rows or auto-promotion rows without product rows. |
| `wb_api_discount_calculation` | `apps/discounts/wb_api/calculation/services.py` writes product result rows using Stage 1 detail article. | Link product rows by unique same-store WB listing key when available. No calculation/result summary changes. |
| `wb_api_discount_upload` | `apps/discounts/wb_api/upload/services.py` writes product upload rows by `nmID`. | Link product rows by unique same-store WB listing key for both drift-blocked and polled upload result detail rows. No upload status mapping changes. |
| `ozon_api_actions_download` | `apps/discounts/ozon_api/actions.py` writes action rows with `product_ref=action_id`. | Do not link. These are action summary rows, not product/listing rows. |
| `ozon_api_elastic_active_products_download` / `ozon_api_elastic_candidate_products_download` | `apps/discounts/ozon_api/products.py` writes action product rows with `product_ref=product_id`. | Link rows by unique same-store Ozon `product_id` / `offer_id` listing key where available. |
| `ozon_api_elastic_product_data_download` | `apps/discounts/ozon_api/product_data.py` writes canonical product info/stocks rows with `product_ref=product_id`. | Link product info/stocks rows by unique same-store Ozon `product_id` / `offer_id` listing key. |
| `ozon_api_elastic_calculation` | `apps/discounts/ozon_api/calculation.py` writes product result rows with `product_ref=product_id`. | Link product result rows by unique same-store Ozon listing key. No calculation changes. |
| `ozon_api_elastic_upload` | `apps/discounts/ozon_api/upload.py` writes upload result rows with `product_ref=product_id`. | Link product upload rows by unique same-store Ozon listing key. No upload confirmation or result-code changes. |
| Product Core sync/export operations | Product Core operations are defined in docs; current inspected `apps/discounts` writers do not cover Product Core export rows. | Link only explicit listing rows. Export rows derived directly from a listing queryset do not need to create `OperationDetailRow` FK as a separate enrichment behavior. |

## Backfill Scope

Backfill is optional but approved when safe. It must be delivered as an idempotent, bounded, resumable command or migration step with dry-run capability.

Eligible rows:

- existing rows in approved operation families;
- `marketplace_listing_id is null`, or already linked to the same deterministic listing as no-op;
- non-empty `product_ref`;
- row classified as product/listing row;
- unique same-store/same-marketplace deterministic match.

Rows to skip unchanged:

- blank `product_ref`;
- action/promotion summary rows;
- rows outside approved operation families;
- rows with no listing match;
- rows with duplicate/multiple candidate matches;
- rows where the existing FK points to a different listing;
- rows where validating same store/marketplace would fail.

Backfill must not update historical `Operation.summary`. For old terminal operations, record conflicts in the command report and techlog, not by changing completed operation summaries. For new non-terminal sync flows, enrichment counts may be included only in the already-created Product Core sync/run summary when that summary is part of the same workflow and does not change business result/status semantics.

Because the current ORM guard blocks terminal operation related updates, implementation must use one controlled approach only:

- add a narrow service context/guard in the operations model/service layer that permits only `OperationDetailRow.marketplace_listing_id` updates for approved enrichment/backfill, after resolver validation and inside transaction boundaries.

Direct SQL bypass is not an approved approach for old terminal rows.

The narrow guard must leave general operation immutability intact and must be impossible to use for changes to `OperationDetailRow.product_ref`, `row_status`, `reason_code`, `message`, `problem_field`, `final_value`, `created_at`, operation summary/status, or operation files. It must also leave all other terminal-related mutations blocked.

## Evidence Requirements

Before any schema/data enrichment run on existing rows, record:

- total `OperationDetailRow` count;
- checksum/hash over `(id, product_ref)` ordered by id for all pre-existing rows;
- eligible row count by operation family;
- duplicate candidate counts by marketplace/store/key where feasible.

After the run, record:

- total `OperationDetailRow` count;
- the same checksum/hash over `(id, product_ref)` for the same pre-existing row id set;
- enriched count by operation family;
- skipped count by operation family;
- conflict count by conflict class;
- same-store/same-marketplace violation count for non-null FK, expected `0`;
- rows with changed `product_ref`, expected `0`.

SQL-equivalent checksum evidence is acceptable:

```sql
select
  count(*) as row_count,
  md5(string_agg(id::text || ':' || coalesce(product_ref, '<NULL>'), '|' order by id)) as product_ref_checksum
from operations_operationdetailrow;
```

For a bounded run, implementation may store the pre-existing id set or high-water mark and compute the same evidence over that exact set.

## Required Tests

Resolver tests:

- same-store/same-marketplace exact `external_primary_id` match;
- same-store/same-marketplace exact `seller_article` match;
- WB `external_ids.nmID` / `vendorCode` match;
- Ozon `external_ids.product_id` / `offer_id` match;
- cross-store and cross-marketplace rejection;
- duplicate candidate conflict;
- blank `product_ref` rejection;
- forbidden fuzzy/title/partial/case-folded/barcode-only matching.

Writer/backfill tests:

- new Stage 1 WB Excel detail rows can be enriched after legacy listing sync without changing `product_ref`;
- new Stage 1 Ozon Excel detail rows can be enriched after legacy listing sync without changing `product_ref`;
- WB API prices product rows link by `nmID`/`vendorCode`;
- WB API promotions link only product rows and skip promotion summary/auto rows;
- WB API calculation/upload product rows link without status/result-code changes;
- Ozon actions download rows remain unlinked;
- Ozon active/candidate/product-data/calculation/upload product rows link by `product_id`/`offer_id`;
- old-row backfill is idempotent and safe to re-run;
- terminal operation FK enrichment path cannot update any field except `marketplace_listing_id`, including negative assertions for `product_ref`, `row_status`, `reason_code`, `message`, `problem_field`, `final_value`, `created_at`, operation summary/status and operation files;
- pre/post `(id, product_ref)` row count and checksum evidence is stable;
- conflict logging is safe/redacted and contains counts/classes;
- FK can be cleared in rollback/correction without touching `product_ref`;
- Stage 1 WB Excel, Stage 1 Ozon Excel, Stage 2.1 WB API and Stage 2.2 Ozon Elastic regression tests still pass.

UI/report visibility tests are required only if this implementation is paired with a UI/report task:

- actor with operation access but without listing access sees raw `product_ref` and no hidden listing details;
- actor with both operation and listing store access can see the listing link;
- exports include listing identifiers only under `marketplace_listing.export`.

Suggested verification commands:

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.operations apps.product_core --verbosity 1 --noinput
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts --verbosity 1 --noinput
```

## Audit Criteria

TASK-PC2-004 is acceptable when:

- `ADR-0044` and resolved `GAP-CORE2-003` are followed;
- `marketplace_listing_id` is nullable, reversible and not required for operation validity;
- every written FK points to the same operation store and marketplace;
- all old-row enrichment is deterministic, idempotent and conflict-counting;
- action/promotion summary rows remain unlinked;
- `product_ref` is byte-for-byte unchanged for all existing rows, proven by row count and checksum/hash evidence;
- operation summary/status/result/files/warning confirmations/reason/result codes/messages/problem fields/final values are unchanged;
- no hidden listing details leak through UI/report paths if such paths are touched;
- conflict logs are safe and do not include secrets or raw stack traces;
- implementation report records enriched operation families, skipped rows, conflict counts and backfill evidence.

## Final Handoff Decision

READY_FOR_IMPLEMENTATION for TASK-PC2-004 Operation Row FK Enrichment.

No UX/functionality/business customer question remains open for this task scope. The implementation must stay inside deterministic FK enrichment and preserve historical operation rows exactly except for the nullable FK value.
