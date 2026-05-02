# CORE_2_DATA_FLOW.md

Статус: исполнительная проектная документация CORE-2, подготовлена для audit-gate.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§6-7, §11.3.

## Назначение

Describe CORE-2 flows from approved WB/Ozon sources through listings, mapping, snapshots, operation links, UI and exports.

Generic flow:

```text
WB/Ozon API -> sync run -> listing -> variant/mapping -> snapshots -> operation links -> export/UI
```

## Flow 1: WB Price/Listings Sync From Stage 2.1 Prices

| Step | Contract |
| --- | --- |
| Input | Existing approved WB source `GET /api/v2/list/goods/filter` from Stage 2.1 prices. |
| Processing | Create Product Core operation/sync run; page through goods; normalize source row into `MarketplaceListing` fields; write `PriceSnapshot` where price data is valid; update latest cache only after successful sync. |
| Output | `MarketplaceListing` rows with WB ids/articles/title-safe fields where present; `PriceSnapshot`; operation details and safe summary. |
| Audit | `marketplace_listing.synced`, optional `marketplace_listing.status_changed`, export/download audit when applicable. |
| Error handling | Auth/rate/timeout/schema errors fail the sync safely; partial source rows become row warnings; failed sync does not erase last successful values. |
| Retry/partial failure | Retry only idempotent reads under existing WB rate policy; no WB writes are introduced by this flow. |
| Secrets | Token/authorization headers never enter sync run summary, snapshots, techlog, audit, files or exports. |

## Flow 2: WB Promotion Rows To Promotion Snapshots

| Step | Contract |
| --- | --- |
| Input | Existing Stage 2.1 current promotion flow and regular promotion nomenclature rows. |
| Processing | For regular promotions, attach product rows to listings only by deterministic store/marketplace/product identifier match. Auto promotions without nomenclatures remain action-level data and must not fabricate product rows. |
| Output | `PromotionSnapshot` for listing-level regular promotion participation when listing match is unique. |
| Audit | Promotion snapshot writes are summarized under sync/operation audit; conflicts use techlog and operation details. |
| Error handling | No product row for WB auto promotion is created; row conflicts remain unlinked. |
| Retry/partial failure | Same WB read retry limits as Stage 2.1; no write endpoints. |
| Secrets | Raw-safe only. |

## Flow 3: Ozon Elastic Scoped Listings From Stage 2.2

| Step | Contract |
| --- | --- |
| Input | Existing approved Ozon Elastic sources: `/v1/actions`, `/v1/actions/products`, `/v1/actions/candidates`, `/v3/product/info/list`, `/v4/product/info/stocks`. |
| Processing | For the selected Elastic action product set only, upsert Ozon `MarketplaceListing` rows when product id/offer id/sku fields are available and deterministic. No full Ozon catalog/listing sync is designed without `GAP-CORE2-002` resolution. |
| Output | Ozon listings for selected action rows; `StockSnapshot` from product info/stocks; `PromotionSnapshot` from action participation; safe operation summary. |
| Audit | Listing synced, snapshot writes and conflict markers as needed. |
| Error handling | Schema mismatch or missing identifiers prevents listing upsert for that row and records safe warning. |
| Retry/partial failure | Ozon read retries follow ADR-0034. No new Ozon write endpoint is introduced. |
| Secrets | Client-Id/Api-Key never appear in safe payloads, logs, snapshots or exports. |

## Flow 4: Exact Normalized Article Linkage

| Step | Contract |
| --- | --- |
| Input | `MarketplaceListing.seller_article` / WB `vendorCode` / Ozon `offer_id` that external normalization has already unified to company article. |
| Processing | Compare exact trimmed value to `ProductVariant.internal_sku`. Do not case-fold, split, transliterate, strip hyphens or use title/image/barcode fuzziness. |
| Output | Existing variant candidate, `needs_review`, `conflict`, or customer-approved draft/imported variant behavior. |
| Audit | Mapping review/conflict markers and any approved auto-create event. |
| Error handling | Blank, duplicate or ambiguous values remain unmatched/conflict. |
| Retry/partial failure | Deterministic and re-runnable. |
| Secrets | Not applicable; source values are product identifiers and still subject to object access. |

## Flow 5: Operation Row FK Enrichment

| Step | Contract |
| --- | --- |
| Input | Existing or new `OperationDetailRow` with raw `product_ref`. |
| Processing | If row marketplace/store matches exactly one listing and row semantics represent a product/listing identifier, write nullable `marketplace_listing_id`. |
| Output | Access-aware link from operation row to listing/card. |
| Audit | `operation_detail_row.listing_fk_enriched` for backfill/bulk enrichment; safe summary counts. |
| Error handling | Conflicts are logged and row remains with raw `product_ref` only. |
| Retry/partial failure | Backfill is idempotent; clearing FK does not affect `product_ref`. |
| Secrets | Detail values and diagnostics are redacted. |

## Flow 6: Exports/UI

| Step | Contract |
| --- | --- |
| Input | Visible Product Core/listing/snapshot/operation data. |
| Processing | Apply object access and permission gates before row selection and before linked-count aggregation. |
| Output | Product/listing/mapping/snapshot export files; UI list/card/review pages. |
| Audit | Export generated/downloaded when controlled. |
| Error handling | Permission denial hides inaccessible rows and links; no hidden store inference through counts. |
| Retry/partial failure | Export can be regenerated as a new operation/file where persisted. |
| Secrets | Redaction is mandatory for `last_values`, `raw_safe`, summaries, errors and file contents. |
