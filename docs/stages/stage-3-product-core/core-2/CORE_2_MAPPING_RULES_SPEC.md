# CORE_2_MAPPING_RULES_SPEC.md

Статус: исполнительная проектная документация CORE-2, обновлена после AUDIT PASS по решениям заказчика; готова к follow-up audit/recheck.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§7.2-7.3, §9.2, §9.4, §11.7.

## Назначение

Define exact normalized article matching, deferred external mapping table behavior and conflict behavior for linking `MarketplaceListing` to `ProductVariant`.

For the narrowed TASK-PC2-003 implementation slice, this specification allows only API exact valid article linkage and API imported/draft auto-create. External mapping table / `visual_external` workflow is deferred to a separate future task and must not be implemented in TASK-PC2-003.

## Business Key

`ProductVariant.internal_sku` is the company-side business key for normalized article matching.

For current CORE-2 linkage logic, `internal_sku` is unique product/variant identity: one valid internal article equals one unique `ProductVariant`. Auto-created parent `InternalProduct.internal_code` must use the same `internal_sku`.

## Internal SKU Format

CORE-2 uses a fixed structured internal SKU format for patches/chevrons. The validator and dictionaries are fixed in docs/code for CORE-2; editable dictionaries in the UI are future scope and must not be added by this stage.

Baseline shape:

```text
<product_type>[_<purpose>][_<kit>][_<structure>]_<content_type><numeric_suffix>
```

Allowed CORE-2 dictionary:

| Group | Allowed values / rule | Notes |
| --- | --- | --- |
| product type | `nash`, `chev` | Required first token. |
| purpose/placement | `pz`, `back` | Optional. |
| kit | `kitN`, for example `kit2` | Optional fixed token family; accepted concrete values must be listed in code/config docs for CORE-2. |
| structure | `mvd`, `fsin`, `rg`, `fso`, `fsb`, `fssp` | Optional. |
| content type | `text`, `pict` | Required prefix of the final token. |
| numeric suffix | zero-padded number, baseline width 4 | Required suffix of the final token, for example `0001`. |

Valid examples:

- `nash_kit2_rg_pict0001`
- `chev_pz_kit2_text0001`
- `nash_mvd_pict0001`
- `chev_back_mvd_text0001`

Values outside this fixed format are invalid/non-unified for automatic matching. They may still be stored on `MarketplaceListing` as external article values.

Marketplace identifiers:

- WB `seller_article` / `vendorCode`;
- Ozon `offer_id`;
- marketplace product ids such as WB `nmID` and Ozon `product_id`.

Marketplace product ids remain technical source keys. They can identify a listing but cannot replace internal SKU as company product identity.

## Matching Modes

CORE-2 design recognizes three matching modes:

1. normalized seller article already present via approved API;
2. mapping table from the external normalization tool, deferred out of narrowed TASK-PC2-003;
3. manual mapping fallback.

TASK-PC2-003 implements only mode 1 plus API auto-create/imported_draft. Mode 2 requires a future task with its own file/table contract, preview/apply UI or service scope, permissions, audit and tests.

### API Article Auto-Match

For API rows, the application compares only valid structured articles:

```text
trim(MarketplaceListing.seller_article or vendorCode or offer_id)
  ==
trim(ProductVariant.internal_sku)
```

The API value must also pass the internal SKU format validator above. No additional transformation is approved in CORE-2:

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
| One active/non-archived `ProductVariant.internal_sku` exactly matches a valid API article and no listing conflict exists | Link listing to the existing variant, set mapping `matched`, write `ProductMappingHistory` and audit with source basis. |
| Multiple variants match same article | `conflict`; no auto-link. |
| Existing listing already linked to another variant with same article conflict | `conflict`; no auto-link. |
| Variant/product archived | Do not auto-link; manual review only if UI allows archived visibility by permission. |
| No variant match, but API article is valid internal SKU format and no conflict exists | Auto-create/select the safe `InternalProduct` parent and create `ProductVariant` as imported/draft under the customer-approved shell policy below; link listing, set mapping `matched`, write audit/history. |
| Article is invalid/non-unified | Create/update `MarketplaceListing` only. No automatic `InternalProduct`/`ProductVariant`. Mapping-table and `visual_external` actions are future workflow, not part of narrowed TASK-PC2-003. |

`matched` records the listing-to-variant link state. For auto-created variants, the variant itself remains imported/draft until review; UI and exports must not label it as a manually confirmed active business product.

Auto-created parent shell policy for API article auto-create:

- `InternalProduct.internal_code = internal_sku`;
- `InternalProduct.name` is the marketplace title from the first load where this valid article is found; if title is blank, fallback to `internal_sku`;
- `InternalProduct.product_type = finished_good`;
- `InternalProduct.status = active`;
- `InternalProduct.category = null`;
- human-readable traits/categories computed from the article are stored in `InternalProduct.attributes`;
- automatic category tree creation is prohibited;
- `InternalProduct.comments = ""`;
- `ProductVariant.internal_sku = internal_sku`;
- `ProductVariant.name` uses the same first-title/fallback rule;
- `ProductVariant.status = active`;
- `ProductVariant.review_state = imported_draft`;
- source context records API sync/source, article basis and whether the parent was newly created or safely reused.

If a single active/non-archived `InternalProduct.internal_code = internal_sku` already exists and no `ProductVariant` exists, create the imported/draft variant under that product; do not create a second `InternalProduct`. If parent/variant selection is not uniquely safe, do not create a product or variant and use the conflict rules below.

When the same `internal_sku` later appears from another store/marketplace, link the listing to the existing `ProductVariant`; do not create a duplicate product or variant. If the later marketplace title differs from the first stored `InternalProduct`/`ProductVariant` title, do not overwrite those names, store the new value only on `MarketplaceListing.title`, keep the listing link `matched`, and set `ProductVariant.review_state = needs_review` for operator review. The system must not infer semantic meaning from the title difference.

## Multi-Store / Multi-Marketplace Links

Multiple stores and marketplaces may share one `ProductVariant`, even when external articles differ. Same variant across WB/Ozon is allowed when exact API article, confirmed mapping table or manual mapping establishes the link.

Duplicate external articles within the same marketplace/store are considered impossible by marketplace constraints. If an API returns such impossible duplicates, classify the sync row group as API data integrity error, write techlog/safe summary, do not auto-link and do not auto-create variants for those rows.

## External Mapping Table Mode

CORE-2 recognizes a dedicated mapping-table workflow from the external normalization tool. This is not a hidden side effect of Excel discount workflows.

Implementation status: deferred out of narrowed TASK-PC2-003. No mapping table preview/apply service, upload/apply UI, file schema, table persistence object or `visual_external` table workflow may be added in TASK-PC2-003. A future task must define the row/file contract and implementation scope before this mode is built.

Required behavior:

- upload/import table into a preview state;
- show diff: new links, changed links, unchanged rows, missing listings, missing variants, invalid `internal_sku`, conflicts and access-denied rows;
- apply no links until a permitted user explicitly confirms the preview;
- on apply, write `ProductMappingHistory`, audit and safe summary;
- never bypass object access or mapping permissions;
- reject or isolate rows with duplicate target/source conflicts;
- keep invalid/non-unified external articles listing-only unless the table supplies a valid target `internal_sku` and the user confirms the apply action.

If a mapping table target `internal_sku` is valid but the `ProductVariant` is absent, implementation must show this explicitly in preview. Creating an imported/draft product/variant from that row is allowed only as an explicit confirmed apply action with the same audit/history and imported/draft labeling as API auto-create.

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

Customer decision 2026-05-02 approves Option B for API exact valid article linkage:

```text
Create ProductVariant as imported/draft from exact normalized article
only when source is approved marketplace API sync,
article format is valid,
no conflict exists,
audit/history are written,
and user can review/confirm/archive.
```

Required interpretation for Option B:

- auto-created variant is not an active confirmed business product by default;
- listing mapping status is set to `matched`, while the variant review state remains `imported_draft`;
- auto-created `InternalProduct` follows the shell field policy in "Existing Variant Match";
- history/audit must preserve that the link was system-created from valid API article or explicitly confirmed mapping table row, not manually confirmed;
- UI must show imported/draft state clearly;
- audit records the source sync run and article basis;
- report/export lists auto-created draft/imported variants for review.

Option C, automatic active confirmed business product without imported/draft review state, is not approved for CORE-2.

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
- an existing database state makes the same `internal_sku` resolve to more than one active/non-archived product/variant candidate;
- an archived/disallowed parent or variant with the same `internal_sku` prevents safe unique selection;
- same external id resolves to multiple listings in same store/marketplace due to data inconsistency;
- same external article appears more than once within the same marketplace/store in an API response;
- normalized article matches an archived/disallowed variant and an active variant simultaneously;
- source row lacks enough data to choose safely but suggests more than one candidate;
- mapping table row changes an existing mapping without explicit confirmed apply.

Conflict cases never auto-confirm and never auto-create a confirmed mapping.

If the unique exact variant is selected but the incoming marketplace title differs from the stored product/variant name, this is not a mapping conflict by itself. Keep the link `matched`, retain the original product/variant names, update `MarketplaceListing.title`, and mark the `ProductVariant` as `needs_review`.

## Prohibited Matching

Implementation must not:

- auto-merge WB and Ozon listings by similar title;
- map by marketplace title, brand or category;
- use image recognition or external machine vision;
- rewrite WB `vendorCode` or Ozon `offer_id` in CORE-2;
- apply external normalization mapping files without preview/diff/conflict handling and explicit user confirmation;
- let Excel create confirmed mappings through existing discount workflows.
