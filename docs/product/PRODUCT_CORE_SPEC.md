# PRODUCT_CORE_SPEC.md

Трассировка: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md` §5.1.1, §7.1-§7.3, §9; итоговое ТЗ §9-§10.

## Назначение

`InternalProduct` and `ProductVariant` define the internal product identity of the company. They are not WB/Ozon cards and are not created automatically by Excel uploads.

## InternalProduct

Purpose: internal product, material, kit, semi-finished item, packaging item or service/design artifact.

Minimum fields:

| Field | Rule |
| --- | --- |
| `id` | database PK |
| `visible_id` / `internal_code` | stable human-visible internal code; no marketplace secret/data |
| `name` | required human-readable name |
| `product_type` | fixed dictionary |
| `category_id` | nullable link to `ProductCategory` |
| `status` | fixed dictionary |
| `attributes` | JSON for non-key descriptive attributes |
| `comments` | internal comments |
| `created_at`, `updated_at` | timestamps |
| `created_by`, `updated_by` | user links where available |

### Product Type Dictionary

CORE-1 fixed dictionary:

- `finished_good`
- `material`
- `packaging`
- `semi_finished`
- `kit`
- `service_or_design_artifact`
- `unknown`

CORE-1 does not attach warehouse/production automation to these values. Future modules may add behavior only through audited documentation and migrations.

### Product Status Dictionary

- `active` - available for normal work;
- `inactive` - not currently used, but retained;
- `archived` - hidden from default operational views, retained for history.

Physical deletion follows `docs/architecture/DELETION_ARCHIVAL_POLICY.md` principles and is prohibited after use in listings/mappings/operations/history.

## ProductVariant

Purpose: concrete internal variant used for listings, future stock, production and supplier links.

Minimum fields:

| Field | Rule |
| --- | --- |
| `id` | database PK |
| `product_id` | required link to `InternalProduct` |
| `internal_sku` | optional/required per implementation validation; unique if present |
| `name` | variant name/label |
| `barcode_internal` | nullable internal barcode |
| `variant_attributes` | JSON for size/color/model/pack quantity etc. |
| `status` | `active`, `inactive`, `archived` |
| `created_at`, `updated_at` | timestamps |

Variant attributes may include:

- size;
- color;
- model;
- embroidery type;
- packaging type;
- pack quantity.

These attributes are descriptive in CORE-1 and do not drive production/BOM logic yet.

## ProductCategory

Purpose: lightweight internal classification.

Minimum fields:

- `id`;
- `parent_id nullable`;
- `name`;
- `status`;
- `sort_order`;
- timestamps.

Category is not a marketplace category and must not be overwritten by WB/Ozon category names.

## ProductIdentifier

Purpose: store internal and external identifiers related to a `ProductVariant` without making them the primary identity.

Minimum fields:

| Field | Rule |
| --- | --- |
| `variant_id` | required |
| `identifier_type` | fixed dictionary |
| `value` | required normalized string |
| `source` | manual, migration, import, api, future source |
| `is_primary` | one primary per variant/type/source where enforced |
| `created_at` | timestamp |

Identifier type dictionary:

- `internal_sku`
- `internal_barcode`
- `supplier_sku`
- `wb_vendor_code`
- `ozon_offer_id`
- `legacy_article`

Adding business-significant identifier types requires documentation update and migration.

## Creation And Update Rules

- Users with `product_core.create` may create internal products.
- Users with `product_variant.create` may create variants.
- Existing Excel check/process operations do not create internal products or variants.
- Explicit import into product core, if implemented later, must be a separate operation/import workflow with diff, confirmation, audit and rollback notes.
- Archiving a product does not delete linked variants/listings/history.

## Relationship To Marketplace Listings

`ProductVariant` can be linked to multiple `MarketplaceListing` records. The same internal variant may be sold:

- in several WB stores;
- in several Ozon stores;
- on both marketplaces;
- with different external ids, prices, discounts, stocks and statuses.

Marketplace data does not overwrite internal product identity.

