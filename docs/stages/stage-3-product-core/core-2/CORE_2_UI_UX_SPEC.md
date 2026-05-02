# CORE_2_UI_UX_SPEC.md

Статус: исполнительная проектная документация CORE-2, обновлена после AUDIT PASS по решениям заказчика; готова к follow-up audit/recheck.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§7.7, 7.9, §11.10.

## Назначение

Define UI behavior for CORE-2 functions only. This document does not authorize warehouse, production, suppliers, BOM, packaging, labels, machine vision or CORE-2 marketplace card-field write UI.

Marketplace card updates by API, including prices, action participation, card parameters, seller article/vendorCode/offer_id and other allowed fields, are future promo_v2 capability outside CORE-2.

## Navigation

CORE-2 extends existing Product Core screens:

```text
Товары компании
  Внутренние товары
  Варианты товаров
  Сопоставление WB/Ozon
  Несопоставленные листинги
  Конфликты сопоставления
  Импортированные/draft варианты

Маркетплейсы
  WB
    Товары / листинги
    Цены
    Акции
  Ozon
    Товары / листинги
    Акции -> Эластичный бустинг
```

Future entries for warehouse/production/suppliers/labels may remain hidden or disabled/planned only. Listing-level stock latest values may appear only as CORE-2 snapshot/cache data, not as a warehouse workflow.

CORE-2 must not add a UI for editing the fixed internal SKU dictionary. Dictionary maintenance is docs/code-level in CORE-2; editable dictionaries are future scope.

## Listing Sync Status

Listing list/card shows:

- last successful sync at;
- last sync status;
- source;
- safe warning/error summary;
- last source endpoint family;
- current cache age;
- link to sync operation if visible.

Actions:

- run approved sync only if user has `marketplace_listing.sync` and store access;
- disabled state if source lacks endpoint-specific official docs evidence/tests;
- no button for endpoints outside approved read-only CORE-2 source policy.

## Linked / Unlinked Listings

Marketplace listings list supports:

- marketplace;
- store/account;
- listing status;
- mapping status;
- source;
- last sync date;
- search by external id, seller article, barcode, title.

Rows show linked internal product/variant only when visible. Hidden store data must not leak through counts or links.

## Imported / Draft Variants

UI must show:

- article/internal SKU;
- source marketplace/store;
- source sync run;
- linked listing if any;
- draft/imported review state;
- conflict reason;
- actions allowed by permission: confirm, edit, archive, leave for review.

No UI may label imported/draft variants as active confirmed products before review.

## Invalid / Non-Unified External Articles

When an API listing article is blank, invalid or not in valid internal SKU format, UI must show the listing without automatic `ProductVariant` creation. Allowed actions:

- rerun/process via `visual_external` where that external normalization route is available;
- upload mapping table, preview diff/conflicts and explicitly apply confirmed links;
- manual mapping fallback.

These actions must not imply fuzzy/title/image matching and must not modify WB/Ozon seller article fields in CORE-2.

## Mapping Review And Conflicts

Review pages cover:

- unmatched listings;
- `needs_review`;
- `conflict`;
- duplicate exact article matches;
- duplicate external id/listing candidates;
- invalid/non-unified external articles;
- mapping table preview conflicts;
- API data integrity duplicate rows.

UI must display exact basis only:

- seller article/vendorCode/offer_id exact value;
- external id exact value;
- barcode as supplemental signal.

UI must not show fuzzy/title/image score or imply automatic correctness.

## Operation Row Link Visibility

Operation detail table may show:

- raw `product_ref` always as historical value;
- listing link if `marketplace_listing_id` exists and actor has listing view access;
- linked variant/internal product if actor has Product Core view access;
- enrichment status if report view requires it.

If actor cannot view the listing, UI hides listing details and keeps raw `product_ref`.

## Snapshot / Latest Values

Listing card shows:

- latest price cache if visible;
- latest stock cache if visible;
- latest promotion/action participation if visible;
- source sync run and timestamp;
- immutable snapshot history table behind snapshot view permission;
- raw-safe details collapsed and technical-view gated.

Future metric hooks for sales/buyouts/returns/demand/in-work/production/shipments show no working empty module. UI may show "not filled in CORE-2" in technical/admin context, not as a user workflow.

## Exports

Export actions appear only when permission and object access allow:

- listing export;
- unmatched/conflict export;
- latest values export;
- mapping report;
- operation link report if implemented.

Export controls must not appear for users who would receive an empty result only because of hidden object access unless the existing UI pattern already supports empty access-safe lists.

## Error Messages

Messages must be human-readable and secret-safe:

- source lacks CORE-2 approval/evidence;
- connection not active;
- rate limited;
- schema changed/invalid response;
- duplicate exact article candidate;
- operation row cannot be linked safely;
- snapshot source not approved/evidenced;
- secret redaction guard blocked persistence.

No raw API payload, header, token, Client-Id, Api-Key, stack trace or internal path is shown.

## Prohibited UI

Do not add operational UI for:

- warehouse;
- production;
- suppliers;
- purchases;
- BOM;
- packaging;
- labels;
- machine vision;
- changing WB/Ozon card fields in CORE-2, including seller article/vendorCode/offer_id;
- Product Core import through existing Excel discount workflows; external mapping table is allowed only through CORE-2 preview/apply workflow;
- confirmed auto-mapping by fuzzy/title/image logic.
