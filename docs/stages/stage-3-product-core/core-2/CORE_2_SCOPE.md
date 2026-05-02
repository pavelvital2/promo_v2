# CORE_2_SCOPE.md

Статус: исполнительная проектная документация CORE-2, обновлена после AUDIT PASS по решениям заказчика; готова к follow-up audit/recheck.

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

CORE-2 is a design and implementation stage only after documentation audit. The original design package received audit/recheck PASS on 2026-05-02; these post-audit decision updates require follow-up audit/recheck before implementation. Product code, tests and migrations remain prohibited until the updated package is accepted and a separate task-scoped implementation assignment is issued.

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
| Marketplace listing sync integration | Adapter design for approved current WB/Ozon sources and endpoint-specific official read-only catalog/listing APIs into `MarketplaceListing` and `MarketplaceSyncRun`. Every added source requires official docs confirmation, pagination/rate-limit/retry/redaction rules and mock tests. Marketplace writes are out of CORE-2. |
| Normalized article linkage | Exact comparison of already normalized seller article/vendorCode/offer_id to valid structured `ProductVariant.internal_sku` under `ADR-0043`. No fuzzy/title/image matching. Invalid/non-unified articles create/update listings only. |
| ProductVariant auto-create policy | Customer-approved Option B: valid API article in internal SKU format auto-creates `InternalProduct` + `ProductVariant` as `imported/draft` if absent, or links an existing active `ProductVariant`; mapping becomes `matched` with audit/history. |
| Operation row enrichment | Nullable `OperationDetailRow.marketplace_listing_id` design applies to new rows and old rows where deterministic safe match exists. It never rewrites `product_ref`, results, summaries, files or reason/result codes. |
| Snapshot filling | Fill prices, stocks and promotions/actions only when source data is already available/approved. Sales/buyouts/returns/demand/in-work/production/shipments remain nullable future architecture hooks, not active CORE-2 UI/workflows. |
| Exports and Excel boundary | Product Core exports for variants/listings/mapping/snapshots with object access and redaction. Existing Excel logic is not changed. |
| UI integration | Existing Product Core UI extended for sync status, linked/unlinked listings, imported/draft variants, mapping table preview/apply, conflicts, operation row links, latest snapshots and exports. |
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
- external article normalization program implementation, except receiving/applying an approved mapping table through the CORE-2 preview/confirmation workflow;
- WB/Ozon card-field writes in CORE-2, including price changes, action participation changes, card parameter changes, seller article/vendorCode/offer_id changes and other marketplace write updates;
- new discount formulas;
- fuzzy/title/image auto-merge;
- legacy `MarketplaceProduct` deletion/removal;
- historical operation result rewrite;
- WB/Ozon write endpoints or read endpoints without endpoint-specific official documentation evidence and CORE-2 tests.

Out of CORE-2 does not mean out of promo_v2 forever. A future audited promo_v2 capability may update marketplace cards by API, including prices, action participation, card parameters, seller article and other fields allowed by WB/Ozon official APIs.

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
- Customer decisions for `GAP-CORE2-001`..`GAP-CORE2-005` recorded on 2026-05-02; implementation still must follow the resolved constraints and endpoint/artifact gates in those entries.

## Acceptance Overview

CORE-2 updated documentation is follow-up audit-ready only if:

- all documents listed in TZ §3.2 exist;
- ADR-0042..ADR-0046 are recorded;
- GAP-CORE2-001..005 decisions and remaining implementation constraints are explicit and not hidden as assumptions;
- implementation tasks are task-scoped with reading packages, prohibited changes, tests and audit criteria;
- migration/backup/rollback plan is non-destructive;
- Stage 1/2 and legacy compatibility are protected;
- implementation remains blocked until updated documentation follow-up audit/recheck is accepted and task-scoped implementation starts.

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
