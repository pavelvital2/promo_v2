# CORE_2_SCOPE.md

Статус: исполнительная проектная документация CORE-2, подготовлена для audit-gate.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§1-8, §11.1, §14-§15.

## Назначение

CORE-2 integrates the implemented Product Core foundation with real WB/Ozon operations without replacing Stage 1/2 workflows.

Target chain:

```text
Approved WB/Ozon API and existing operations
  -> MarketplaceListing
  -> ProductVariant / InternalProduct
  -> snapshots and nullable operation row links
  -> Product Core exports and UI
```

CORE-2 is a design and implementation stage only after documentation audit. Product code, tests and migrations remain prohibited until this package receives `AUDIT PASS` and every affected implementation slice has no blocking GAP.

## Preconditions

- CORE-1 release validation accepted as `PASS WITH NOTES` without blocking defects:
  - `docs/reports/CORE_1_RELEASE_VALIDATION_REPORT.md`
  - `docs/audit/AUDIT_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md`
- CORE-1 invariants remain active:
  - `MarketplaceProduct` stays as legacy compatibility data.
  - `OperationDetailRow.product_ref` remains immutable raw history.
  - Excel remains operational input/output and is not Product Core source of truth.
  - API secrets stay only in protected secret storage and never in UI/logs/audit/techlog/files/snapshots/exports.

## In Scope

| Block | CORE-2 result |
| --- | --- |
| Marketplace listing sync integration | Adapter design for approved WB/Ozon sources into `MarketplaceListing` and `MarketplaceSyncRun`. New endpoints are prohibited unless already approved in current docs/code; otherwise `GAP-CORE2-002`. |
| Normalized article linkage | Exact comparison of already normalized seller article/vendorCode/offer_id to `ProductVariant.internal_sku` under `ADR-0043`. No fuzzy/title/image matching. |
| ProductVariant auto-create policy | Design recommendation is Option B, but implementation is blocked by `GAP-CORE2-001` until customer decision. |
| Operation row enrichment | Nullable `OperationDetailRow.marketplace_listing_id` design that never rewrites `product_ref`, results, summaries, files or reason/result codes. Scope is gated by `GAP-CORE2-003`. |
| Snapshot filling | Fill only from already approved flows/endpoints. Unsupported snapshot sources remain foundation-only and are gated by `GAP-CORE2-004`. |
| Exports and Excel boundary | Product Core exports for variants/listings/mapping/snapshots with object access and redaction. Existing Excel logic is not changed. |
| UI integration | Existing Product Core UI extended for sync status, linked/unlinked listings, imported/draft variants if approved, conflicts, operation row links, latest snapshots and exports. |
| Permissions/audit/techlog | Store-scoped object access, audit actions, techlog events, secret redaction and security tests for CORE-2. |
| Regression | Mandatory Stage 1 WB/Ozon Excel, Stage 2.1 WB API, Stage 2.2 Ozon Elastic, Product Core UI/export/permissions and legacy compatibility regression. |

## Non-Scope

CORE-2 must not implement:

- warehouse ledger;
- production;
- suppliers;
- purchases;
- industrial BOM;
- packaging workflows;
- labels;
- demand planning formulas;
- machine vision;
- external article normalization program;
- automatic WB/Ozon vendorCode/offer_id changes;
- new discount formulas;
- fuzzy/title/image auto-merge;
- legacy `MarketplaceProduct` deletion/removal;
- historical operation result rewrite;
- new WB/Ozon endpoints without current documented/code source and GAP resolution.

Future ERP sections may appear only as hidden or disabled planned entry points and must not look operational.

## Protected Invariants

- Stage 1 WB Excel and Ozon Excel remain standard operational workflows.
- Stage 2.1 WB API and Stage 2.2 Ozon Elastic behavior is not changed except for additive Product Core links/snapshots that pass regression.
- `Operation.type=check/process` remains only for check/process scenarios; API and Product Core operations use `Operation.step_code`.
- `MarketplaceListing` is store/marketplace-specific external listing identity.
- `InternalProduct` / `ProductVariant` are company-side product identity.
- `product_ref` is immutable raw history; nullable FK enrichment is reversible.
- Excel never automatically creates internal products/variants or confirmed mappings.
- Secrets are redacted from every safe contour.

## Dependencies

- CORE-1 Product Core models, mapping workflow, exports and permissions.
- Existing WB Stage 2.1 sources:
  - `GET /api/v2/list/goods/filter`
  - approved WB promotion endpoints for regular promotion rows.
- Existing Ozon Stage 2.2 sources:
  - `GET /v1/actions`
  - `/v1/actions/products`
  - `/v1/actions/candidates`
  - `/v3/product/info/list`
  - `/v4/product/info/stocks`
- Open customer/source decisions in `GAP-CORE2-001`..`GAP-CORE2-005`.

## Acceptance Overview

CORE-2 documentation is audit-ready only if:

- all documents listed in TZ §3.2 exist;
- ADR-0042..ADR-0046 are recorded;
- GAP-CORE2-001..005 are explicit and not hidden as assumptions;
- implementation tasks are task-scoped with reading packages, prohibited changes, tests and audit criteria;
- migration/backup/rollback plan is non-destructive;
- Stage 1/2 and legacy compatibility are protected;
- implementation remains blocked until documentation `AUDIT PASS`.

## ADR

- ADR-0042: CORE-2 Product Core Integration Boundary
- ADR-0043: Normalized Article As Business Key
- ADR-0044: OperationDetailRow MarketplaceListing FK Enrichment
- ADR-0045: Auto-created ProductVariant Policy
- ADR-0046: CORE-2 Snapshot Semantics

## GAP

- GAP-CORE2-001: ProductVariant auto-create mode
- GAP-CORE2-002: Approved WB/Ozon listing sources
- GAP-CORE2-003: OperationDetailRow enrichment scope
- GAP-CORE2-004: Snapshot filling scope
- GAP-CORE2-005: External normalization mapping import
