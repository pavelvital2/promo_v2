# PRODUCT_CORE_UI_SPEC.md

Трассировка: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md` §5.1.6, §9, §12; итоговое ТЗ §5-§6, §11, §18-§20.

## Назначение

UI CORE-1 provides access-aware product core and marketplace listing screens. It must be useful as a working table, but it must not display future warehouse/production/labels modules as implemented functionality.

The wbarcode reference report may inform navigation/table ergonomics only. It is not a source of business logic, data structure, payments, advertising, subscriptions or product architecture.

## Navigation

Target hierarchy:

```text
Товары компании
  Внутренние товары
  Варианты товаров
  Сопоставление WB/Ozon
  Несопоставленные листинги

Маркетплейсы
  WB
    Товары / листинги
    Цены
    Акции
    Остатки
    Продажи
    В производство - future entry point
    Поставки - future entry point
  Ozon
    Товары / листинги
    Цены
    Акции
    Остатки
    Продажи
    В производство - future entry point
    Поставки - future entry point
```

Only implemented screens are interactive. Future entry points are disabled or marked as planned, without empty operational tables.

## Internal Product List

Minimum columns:

- internal code / visible id;
- name;
- product type;
- category;
- variant count;
- visible linked WB listings count;
- visible linked Ozon listings count;
- status;
- updated at.

Filters/search:

- product type;
- category;
- status;
- linked/unlinked listings;
- search by name, internal SKU, internal barcode.

Actions:

- open product card;
- create product if `product_core.create`;
- export visible rows if `product_core.export`;
- archive if `product_core.archive`.

Counts involving listings must respect store object access. A user without access to a store must not infer hidden store listing details from unfiltered counts.

## Internal Product Card

Blocks:

- main data;
- variants;
- identifiers;
- linked WB/Ozon listings filtered by access;
- change history;
- audit links where available.

Future blocks:

- stock;
- production;
- suppliers;
- BOM;
- packaging;
- labels.

These future blocks are hidden by default or shown only as disabled/planned entry points. They must not look like working CORE-1 modules.

## Marketplace Listings List

Minimum columns:

- marketplace;
- store/account;
- external primary id;
- seller article;
- barcode;
- marketplace title;
- brand;
- marketplace category;
- listing status;
- mapping status;
- linked internal variant;
- latest price;
- latest stock;
- last successful sync at;
- last source.

Filters/search:

- marketplace;
- store;
- listing status;
- mapping status;
- category;
- brand;
- stock presence;
- update date;
- search by external id, article, title, barcode.

Actions:

- open listing card;
- export visible rows if permitted;
- run supported sync if task implemented and user has right;
- go to mapping workflow if permitted.

## Marketplace Listing Card

Blocks:

- marketplace data;
- external identifiers;
- linked internal variant;
- latest snapshots summary;
- price snapshots;
- stock snapshots;
- sales/orders period snapshots;
- promotion snapshots;
- listing history;
- mapping history;
- related operations;
- related files;
- last sync errors.

Technical raw-safe data is collapsed by default and visible only to users with technical view permissions.

## Unmatched Listings

Purpose: list `MarketplaceListing` records where `internal_variant_id is null` and `mapping_status` is `unmatched`, `needs_review` or `conflict`.

Filters:

- marketplace;
- store;
- source;
- mapping status;
- last seen date;
- seller article/barcode/title.

Actions:

- link to existing variant;
- create product+variant and link;
- create variant under existing product and link;
- mark needs review;
- leave unmatched;
- export unmatched visible rows.

## Mapping Workflow

Minimum flow:

1. User opens unmatched listing.
2. System displays listing details and access-safe existing variant search.
3. System displays non-authoritative candidates, if present, only from exact `seller_article`, `barcode` or external identifier matches.
4. User chooses one action:
   - link existing variant;
   - create product+variant and link;
   - create variant under existing product and link;
   - mark as `needs_review`;
   - leave unmatched.
5. System writes audit and mapping history.
6. Old operation rows are not edited except approved nullable FK enrichment.

Candidate suggestion rules:

- suggestions are UI/workflow aids, not authority;
- fuzzy/title/partial-article suggestions are out of CORE-1;
- a suggestion can become `matched` only after explicit confirmation by a user with mapping permission;
- confirmation writes audit and `ProductMappingHistory`;
- multiple candidates or conflicting exact matches keep/set `needs_review` or `conflict` until the user resolves them.

Unmap flow:

- show current mapping;
- require user with `marketplace_listing.unmap`;
- write audit/history;
- set `internal_variant_id = null`;
- set mapping status according to user action: `unmatched`, `needs_review` or `conflict`.

## Excel Boundary UI

Existing WB/Ozon Excel screens continue to work without internal product requirement.

Any import from Excel into product core/listings must be a separate explicit workflow:

```text
upload Excel -> validate -> show diff -> warn impact -> confirm -> create import operation -> audit/history
```

If that workflow is not implemented in CORE-1, UI must not imply that Excel upload will update the internal catalog.

## Export UI

CORE-1 exports:

- internal products;
- marketplace listings;
- unmatched listings;
- listings with latest prices/stocks;
- mapping report.

Exports must apply the same object access as UI. Internal product exports must not leak hidden listing/store details.
