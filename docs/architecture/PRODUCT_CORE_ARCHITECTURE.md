# PRODUCT_CORE_ARCHITECTURE.md

Трассировка: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md` §1-§8, §13; итоговое ТЗ §2.4-§2.5, §7.2, §9-§10, §12, §20-§23, §27.

## Назначение

Документ defines the architecture for Stage 3.0 / CORE-1 Product Core Foundation.

## Core Decisions

- `InternalProduct` and `ProductVariant` are the company product core.
- `MarketplaceListing` is an external representation in one marketplace and one store/account.
- WB/Ozon listings are not automatically merged.
- CORE-1 may show semi-automatic candidates only as non-authoritative exact `seller_article`, `barcode` or external identifier suggestions; confirmed mapping requires explicit user confirmation with mapping permission, audit and history.
- API snapshots are historical source records; listing `last_values` is only a latest-state cache.
- Excel remains a normal operational mode and does not automatically inflate product core.

## Domain Layers

```text
Product Core
  InternalProduct
  ProductVariant
  ProductCategory
  ProductIdentifier

Marketplace Listing Layer
  MarketplaceListing
  ListingHistory
  ProductMappingHistory

Sync/Snapshot Layer
  MarketplaceSyncRun
  PriceSnapshot
  StockSnapshot
  SalesPeriodSnapshot
  PromotionSnapshot

Existing Platform Layer
  StoreAccount
  Operation / Run
  FileObject / FileVersion
  AuditRecord
  TechLogRecord
  Permissions / object access
```

## Module Boundaries

| Module | Owns | Must not own |
| --- | --- | --- |
| Product Core | internal product/variant/category/identifier | marketplace API parsing, Excel calculation |
| Marketplace Listings | external listing identity, mapping status, listing current cache | internal product identity decisions |
| Marketplace Sync | sync run and snapshot persistence | business calculation rules for discounts |
| Operations | business operation lifecycle and immutable records | audit/techlog replacement |
| Files/Exports | file versions and exports | product identity inference |
| UI | access-aware screens/workflows | hidden auto-mapping |

## Store And Object Access

`MarketplaceListing` inherits object access from `StoreAccount`.

Rules:

- user without store access cannot see the listing, its snapshots, related operations or files;
- internal products may be visible more broadly by product-core permissions;
- linked listing counts/details on internal product screens are filtered to visible stores unless the user has global/full scope;
- mapping requires both product-core rights and access to the listing store.

## Mapping Contract

The persisted relationship is:

```text
MarketplaceListing.internal_variant_id nullable -> ProductVariant.id
```

History is separate:

```text
ProductMappingHistory
```

This preserves:

- current query simplicity for common UI;
- immutable trace of map/unmap/conflict actions;
- ability to add future candidate scoring after separate approval without changing confirmed mapping semantics.

CORE-1 candidate suggestions are exact-match only and non-authoritative. Fuzzy/title/partial-article suggestions are outside CORE-1. Multiple candidates or conflicting exact matches leave the listing in `needs_review` or `conflict` until a permitted user resolves it.

## Sync And Snapshot Contract

`MarketplaceSyncRun` records a synchronization attempt for a store/marketplace/type/source.

Snapshot tables record immutable source data:

- prices;
- stocks;
- sales/orders period values;
- promotions/action participation where available.

`MarketplaceListing.last_values` may cache latest price/stock/status for UI and filtering, but it is not the source of historical truth.

## Future Hooks

Future modules should link to `ProductVariant`, not directly to WB/Ozon identifiers:

- inventory ledger;
- production jobs;
- purchase and supplier items;
- BOM/materials;
- packaging and labels;
- demand planning and shipments.

CORE-1 does not implement these modules. It only reserves stable product/variant identity and identifiers so future modules do not need to rebuild around marketplace cards.

## Migration Overview

Chosen strategy: new `MarketplaceListing` with backfill from legacy `MarketplaceProduct`; keep legacy compatibility until separate audited deprecation/removal.

Reasons:

- current code and tests use `MarketplaceProduct` broadly;
- direct rename has high regression risk;
- Stage 1/2 operations depend on `product_ref` raw references;
- legacy data must remain queryable during and after migration.

Detailed plan: `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md`.

## Secret Safety

Product core snapshots, summaries, audit, techlog, UI, exports and reports must not contain:

- WB tokens/API keys/authorization headers;
- Ozon Client-Id/Api-Key;
- bearer values;
- secret-like values;
- raw request/response payloads with secrets.

Only safe, redacted payload fragments and checksums are allowed in snapshots.
