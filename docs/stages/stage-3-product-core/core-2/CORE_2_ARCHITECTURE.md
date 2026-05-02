# CORE_2_ARCHITECTURE.md

Статус: исполнительная проектная документация CORE-2, подготовлена для audit-gate.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§5-9, §11.2, §14.

## Назначение

Document the CORE-2 target architecture that connects approved WB/Ozon API and existing operations to Product Core while preserving Stage 1/2 compatibility.

## Target Scheme

```text
WB Stage 2.1 approved sources          Ozon Stage 2.2 approved sources
GET /api/v2/list/goods/filter          actions/products/candidates
promotion nomenclature rows            product info/stocks for selected action set
        |                                      |
        +--------------+-----------------------+
                       |
                MarketplaceSyncRun
                       |
                MarketplaceListing
                       |
       exact normalized article linkage
                       |
              ProductVariant
                       |
              InternalProduct

Existing OperationDetailRow.product_ref
        |
nullable deterministic enrichment only
        v
OperationDetailRow.marketplace_listing_id
```

## Model Relationships

| Entity | CORE-2 role | Boundary |
| --- | --- | --- |
| `InternalProduct` | Company-side product container | Not created by Excel; auto-create through API is blocked until `GAP-CORE2-001` decision. |
| `ProductVariant` | Company-side sellable/internal variant; `internal_sku` is business key | Existing active/manual variants remain unchanged. Imported/draft lifecycle needs `GAP-CORE2-001` decision before implementation. |
| `MarketplaceListing` | External WB/Ozon listing in one store/account | External ids are technical source keys, not internal identity. |
| `MarketplaceSyncRun` | Source/run context for listing/snapshot filling | One active sync per marketplace/store/sync type; failed sync does not erase latest cache. |
| Snapshot tables | Immutable source records | Latest UI cache is derived from successful sync only. |
| `OperationDetailRow` | Immutable operation row history with raw `product_ref` | `marketplace_listing_id` is nullable enrichment and can be cleared without data loss. |
| `MarketplaceProduct` | Legacy compatibility layer | Not deleted, renamed, truncated or silently replaced in CORE-2. |

## Sequence Overview

```text
1. User/service starts approved sync operation for a store.
2. System creates Operation with Product Core step_code if persisted lifecycle is needed.
3. System creates MarketplaceSyncRun.
4. API adapter reads only approved endpoint/source.
5. Adapter upserts MarketplaceListing by marketplace + store + external_primary_id.
6. Adapter writes safe snapshots when source semantics are approved.
7. Mapping service evaluates exact normalized article candidates.
8. If customer-approved auto-create policy allows it, draft/imported variants may be created under strict rules.
9. Operation row enrichment writes nullable FK where deterministic and unique.
10. UI/exports show only object-accessible listings, snapshots and operation links.
```

## Source Of Truth Matrix

| Data | Source of truth | Cache/report | Notes |
| --- | --- | --- | --- |
| Internal product identity | `InternalProduct` / `ProductVariant` | Product Core UI/export | Marketplace fields do not overwrite internal identity. |
| External listing identity | Marketplace API/source row, persisted in `MarketplaceListing` | Listing list/card | Unique by marketplace + store + external primary id. |
| Company article | `ProductVariant.internal_sku` | `ProductIdentifier` as supplemental identifiers | `internal_sku` is business key, not marketplace technical key. |
| Marketplace technical ids | `MarketplaceListing.external_primary_id` / `external_ids` | Operation details, snapshots | Used for deterministic lookup and source traceability. |
| Historical operation row ref | `OperationDetailRow.product_ref` | Detail reports | Immutable raw value. |
| Current latest values | Successful snapshot-derived `MarketplaceListing.last_values` | Listing UI/export | Not historical source of truth. |
| Historical source values | Snapshot rows linked to sync run/source operation | Audit/testing/analytics base | Raw-safe only. |
| Secrets | Protected secret storage only | Never exported/logged | No token/API key/Client-Id leak. |

## Stage 1/2 Boundaries

- Stage 1 Excel check/process logic, files, reason/result codes and operation results do not change.
- Stage 2.1 WB API operation sequence and upload safety do not change.
- Stage 2.2 Ozon Elastic action selection, calculation, review, deactivate safety and upload behavior do not change.
- CORE-2 may add object-access-aware links from operation rows to listings only when deterministic.
- CORE-2 may create Product Core sync/snapshot operations, but does not reclassify old operations.

## Future ERP Boundary

CORE-2 reserves Product Core identity for future warehouse, production, suppliers, BOM, packaging and labels. It does not implement those modules and does not add working UI, operational states, calculations or migrations for them.

Future ERP modules must link to `ProductVariant`, not to WB/Ozon ids or Excel rows directly.

## Audit Gate

Implementation is prohibited until:

- documentation audit result is `AUDIT PASS`;
- affected GAP entries are resolved or the implementation task explicitly excludes the blocked slice;
- task-scoped implementation package names allowed files, prohibited changes, tests and audit criteria.
