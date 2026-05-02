# CORE_2_OPERATION_LINKING_SPEC.md

Статус: исполнительная проектная документация CORE-2, подготовлена для audit-gate.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§7.4, 7.9, §11.6.

## Назначение

Define how existing and new operation detail rows receive nullable links to `MarketplaceListing` without changing historical results.

## Model Contract

```text
OperationDetailRow.product_ref
  remains raw immutable historical reference

OperationDetailRow.marketplace_listing_id nullable
  optional deterministic enrichment
```

The FK is a navigation/report enrichment only. It is not part of Stage 1/2 business calculation, not a replacement for `product_ref`, and not required for operation validity.

## Enrichment Rules

FK may be written only if all conditions are true:

1. operation has marketplace and store/account;
2. listing marketplace and store match operation marketplace and store;
3. detail row `product_ref` is non-empty;
4. the row represents a product/listing identifier, not an action/promotion summary identifier;
5. exactly one listing matches by approved deterministic key;
6. no duplicate/conflict candidate exists in the same store/marketplace;
7. write does not change operation summary, status, result files, warning confirmations, row status, reason/result code, message, problem field, final value or `product_ref`;
8. user-visible history remains understandable if FK is later cleared.

## Deterministic Matching Keys

Allowed lookup keys, scoped by operation marketplace and store:

- `MarketplaceListing.external_primary_id`;
- `MarketplaceListing.seller_article`;
- scalar values in `MarketplaceListing.external_ids` only when source-specific mapping is documented;
- `MarketplaceListing.barcode` only as supplemental conflict/review signal, not as sole enrichment key unless a future GAP/ADR approves it.

Forbidden:

- title matching;
- partial article matching;
- fuzzy matching;
- image/machine vision;
- cross-store or cross-marketplace lookup;
- using hidden store listings the actor cannot access for UI display.

## Operation Scope

`GAP-CORE2-003` remains open for final customer-approved operation type/step scope. Until resolved, future implementation tasks may only implement a slice explicitly approved by the orchestrator/auditor.

Recommended safe scope for customer decision:

| Operation family | Recommended FK behavior |
| --- | --- |
| Stage 1 WB Excel detail rows | Backfill only when `product_ref` exactly matches a unique WB listing article/external id in the same store. |
| Stage 1 Ozon Excel detail rows | Backfill only when `product_ref` exactly matches a unique Ozon listing offer/id in the same store. |
| `wb_api_prices_download` | Link product rows by WB `nmID`/`vendorCode` where unique. |
| `wb_api_promotions_download` | Link regular promotion product rows by `nmID`; do not link promotion summary rows or auto promotions without product rows. |
| `wb_api_discount_calculation` / `wb_api_discount_upload` | Link product rows by WB product identifier where unique. |
| `ozon_api_actions_download` | Do not link action summary rows. |
| `ozon_api_elastic_active_products_download` / `candidates_download` | Link rows by Ozon `product_id`/`offer_id` where unique. |
| `ozon_api_elastic_product_data_download` | Link product info/stocks rows by Ozon `product_id`/`offer_id` where unique. |
| `ozon_api_elastic_calculation` / `upload` | Link product result rows by Ozon `product_id`/`offer_id` where unique. |
| Product Core sync/export operations | Link only rows that are explicitly listing rows; export rows need not create FK if file rows are derived directly from listing queryset. |

## Old Rows

Backfill for old rows is optional per approved task scope and must be:

- idempotent;
- chunked/bounded;
- resumable;
- safe to re-run;
- conflict-counting;
- reversible by clearing FK;
- covered by Stage 1/2 regression tests.

Old rows that cannot be matched remain unchanged.

## New Rows

New operation services should write FK at row creation when:

- the listing is already known from the same source row/sync context;
- matching is deterministic;
- write does not require hidden cross-scope lookup;
- the operation service already has Product Core dependencies approved for that task.

If Product Core is unavailable or a listing cannot be safely resolved, the row is still valid with `product_ref` only.

## Conflict Logging

Conflict classes:

- `no_listing_match`;
- `multiple_listing_matches`;
- `store_marketplace_mismatch`;
- `row_not_product_identifier`;
- `secret_redaction_guard_failed`;
- `source_scope_not_approved`.

Bulk/backfill conflicts are summarized in operation/sync summary and techlog without secrets. Row-level user messages must be human-readable and must not show raw stack traces.

## UI And Report Effect

- Operation card may show a listing link only if the actor has access to both the operation and the listing store.
- If FK exists but actor lacks listing access, UI shows raw `product_ref` without leaking hidden listing details.
- Exports may include listing identifiers only under `marketplace_listing.export` and object access.
- FK presence must not change historical reason/result code interpretation.

## Tests

Future implementation must cover:

- FK nullable schema and rollback;
- same-store/same-marketplace match;
- cross-store/cross-marketplace rejection;
- duplicate candidate conflict;
- product_ref immutability;
- terminal operation immutability;
- old row backfill idempotency;
- UI object access for links;
- Stage 1/2 regression.
