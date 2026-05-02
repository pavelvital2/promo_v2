# CORE_2_EXCEL_EXPORT_SPEC.md

Статус: исполнительная проектная документация CORE-2, обновлена после AUDIT PASS по решениям заказчика; готова к follow-up audit/recheck.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§7.6, 7.9, §11.9.

## Назначение

Define Product Core exports for CORE-2 while preserving Excel as operational input/output, not Product Core source of truth.

Existing Product Core exports may remain CSV/Excel-compatible CSV. XLSX output requires file contour and task approval if selected during implementation.

## Export Types

| Export | Purpose | Minimum permission |
| --- | --- | --- |
| Internal products | Company product list with visible linked listing counts. | `product_core.export` |
| Product variants | Variant review list, including imported/draft state. | `product_core.export` / `product_variant.view` |
| Marketplace listings | Listing table filtered by marketplace/store/status/mapping status. | `marketplace_listing.export` per store |
| Listings with latest values | Listings plus latest price/stock/promotion cache. | `marketplace_listing.export` + `marketplace_snapshot.view` |
| Mapping report | Matched/unmatched/needs_review/conflict listing-to-variant report. | `marketplace_listing.export` |
| Operation link report | Rows enriched with listing FK for troubleshooting. | operation view + listing export/access |
| Auto-created draft/imported variants report | Review queue for customer-approved imported/draft variants. | product export + review permission |
| External mapping table preview/export | Diff/conflict/no-op preview for uploaded mapping table before explicit apply. | mapping import/apply permission + object access |

## Filters

Exports must support task-relevant filters:

- marketplace: WB/Ozon;
- store/account;
- listing status;
- mapping status;
- variant review/import state;
- mapping table import/apply status where relevant;
- last seen / last successful sync date;
- source;
- category/brand when available;
- conflict class;
- operation step code for operation link report.

## Columns

### Marketplace Listings

Minimum columns:

- marketplace;
- store visible id;
- store name;
- external primary id;
- seller article;
- barcode;
- title;
- brand;
- category;
- listing status;
- mapping status;
- internal product code;
- internal product name;
- internal variant sku;
- internal variant name;
- last successful sync at;
- last source;
- updated at.

### Latest Values Extension

Include only when user has snapshot permission:

- latest price;
- latest price with discount;
- latest discount percent;
- currency;
- latest stock total;
- latest promotion/action id/status where available;
- latest snapshot timestamps;
- redacted latest values JSON if exported.

### Operation Link Report

Minimum columns:

- operation visible id;
- marketplace;
- store visible id;
- step code/type;
- row number;
- raw `product_ref`;
- row status;
- reason/result code;
- linked listing external primary id if visible;
- linked listing seller article if visible;
- linked variant internal SKU if visible;
- enrichment status/conflict reason.

## Permissions And Object Access

- A row is exported only if the actor can view/export the underlying object.
- Internal product exports must not leak hidden store details through unfiltered linked counts.
- Listing exports require store object access.
- Snapshot latest values require snapshot view permission.
- Technical raw-safe details require technical view permission and still must be redacted.

## Excel Boundary

Existing WB/Ozon Excel workflows continue unchanged.

Exports are not imports. Downloading or editing a Product Core export does not create or update `InternalProduct`, `ProductVariant`, `MarketplaceListing`, mapping or operation results.

Existing WB/Ozon Excel discount workflows must not import into Product Core.

CORE-2 does allow the dedicated external normalization mapping table workflow defined in `CORE_2_MAPPING_RULES_SPEC.md`: upload, preview/diff/conflicts, explicit confirmation, audit/history, object access and redaction. This workflow applies mapping links and, only when explicitly confirmed, may create imported/draft variants for valid target internal SKUs.

## Redaction

Exports must not contain:

- WB token/API key/authorization header;
- Ozon Client-Id/Api-Key;
- bearer/API key values;
- secret-like metadata;
- raw request/response headers;
- stack traces;
- inaccessible store data.

All JSON columns must pass the existing redaction policy before serialization.

## File/Audit Behavior

If export output is persisted:

- create `Operation` with Product Core export step code where required;
- link `FileVersion`;
- write audit `marketplace_listing.exported` or equivalent product export action;
- preserve file immutability.

If export is streamed without persistence, implementation must still enforce permissions and may audit download where controlled by existing file/audit policy.
