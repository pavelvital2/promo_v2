# CORE_2_MAPPING_RULES_SPEC.md

Статус: исполнительная проектная документация CORE-2, подготовлена для audit-gate.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§7.2-7.3, §9.2, §9.4, §11.7.

## Назначение

Define exact normalized article matching and conflict behavior for linking `MarketplaceListing` to `ProductVariant`.

## Business Key

`ProductVariant.internal_sku` is the company-side business key for normalized article matching.

Marketplace identifiers:

- WB `seller_article` / `vendorCode`;
- Ozon `offer_id`;
- marketplace product ids such as WB `nmID` and Ozon `product_id`.

Marketplace product ids remain technical source keys. They can identify a listing but cannot replace internal SKU as company product identity.

## Comparison Rule

CORE-2 uses the TZ premise that external normalization already happened outside promo_v2. The application compares:

```text
trim(MarketplaceListing.seller_article or vendorCode or offer_id)
  ==
trim(ProductVariant.internal_sku)
```

No additional transformation is approved in CORE-2:

- no case folding;
- no hyphen/space removal inside article;
- no transliteration;
- no substring/partial matching;
- no title/brand/category matching;
- no image or machine vision matching.

Blank values are not matchable.

## Existing Variant Match

| Condition | Result |
| --- | --- |
| One active/non-archived `ProductVariant.internal_sku` exactly matches article and no listing conflict exists | Candidate can be deterministic; final behavior depends on approved auto-link policy for CORE-2. Without approval, mark `needs_review`. |
| Multiple variants match same article | `conflict`; no auto-link. |
| Existing listing already linked to another variant with same article conflict | `conflict`; no auto-link. |
| Variant/product archived | Do not auto-link; manual review only if UI allows archived visibility by permission. |
| No variant match | `unmatched`, or auto-create draft/imported only after `GAP-CORE2-001` resolution. |

## External Id And Barcode Role

External ids:

- identify/update `MarketplaceListing`;
- help operation row FK enrichment;
- may appear as exact non-authoritative candidate basis through `ProductIdentifier`;
- do not override `internal_sku`.

Barcode:

- may be shown as supplemental candidate/review signal;
- is not enough for automatic confirmed mapping in CORE-2;
- duplicate barcode candidates produce `conflict`.

## ProductVariant Auto-Create Policy

`GAP-CORE2-001` is open and blocks implementation. Design recommendation is Option B:

```text
Create ProductVariant as imported/draft from exact normalized article
only when source is approved marketplace API sync,
article format is valid,
no conflict exists,
audit/history are written,
and user can review/confirm/archive.
```

Safe interpretation for Option B:

- auto-created variant is not an active confirmed business product by default;
- mapping is not treated as customer-confirmed until review;
- UI must show imported/draft state clearly;
- audit records the source sync run and article basis;
- report/export lists auto-created draft/imported variants for review.

Option C, automatic active variant plus confirmed mapping, is not recommended for CORE-2 and must not be implemented without explicit customer decision and new audit.

## Manual Review Actions

Allowed actions for users with mapping rights and listing object access:

- link listing to existing variant;
- create product/variant manually and link;
- create variant under existing product and link;
- mark `needs_review`;
- mark `conflict`;
- leave unmatched;
- unmap listing.

Every map/unmap/review/conflict action writes `ProductMappingHistory` and audit.

## Conflict Rules

Set or retain `mapping_status=conflict` when:

- multiple variants match the same normalized article;
- one listing has conflicting existing mapping;
- same external id resolves to multiple listings in same store/marketplace due to data inconsistency;
- normalized article matches an archived/disallowed variant and an active variant simultaneously;
- source row lacks enough data to choose safely but suggests more than one candidate.

Conflict cases never auto-confirm and never auto-create a confirmed mapping.

## Prohibited Matching

Implementation must not:

- auto-merge WB and Ozon listings by similar title;
- map by marketplace title, brand or category;
- use image recognition or external machine vision;
- rewrite WB `vendorCode` or Ozon `offer_id`;
- import external normalization mapping files unless `GAP-CORE2-005` is resolved and a separate audited import mode exists;
- let Excel create confirmed mappings through existing discount workflows.
