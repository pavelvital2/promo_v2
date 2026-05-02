# TASK_PC2_006_DESIGN_HANDOFF

Date: 2026-05-02
Role: TASK-PC2-006 designer
Task: TASK-PC2-006 Product Core Exports And Excel Boundary
Verdict: READY_FOR_IMPLEMENTATION

## Scope Of This Handoff

This handoff prepares the implementation package for Product Core export behavior in the CORE-2 slice named in `CORE_2_AGENT_TASKS.md`: listings, latest values, mapping reports and operation link reports.

In scope:

- marketplace listing CSV export, including the existing unmatched-listing export as a filtered listing export;
- latest values CSV export with snapshot permission gating and redacted latest JSON;
- mapping report CSV for matched, unmatched, needs-review and conflict states;
- operation link report CSV for visible operation detail rows and their nullable listing FK enrichment state;
- audit for export generation/download requests;
- tests for permission/object access, headers, filters, redaction and no import side effects.

Existing internal product export remains in place and must keep its hidden-store count protection. It may be touched only for regression fixes or to add the shared export audit hook.

Out of scope for this PC2-006 implementation slice:

- external mapping-table preview/apply/export and `visual_external` table workflow, because `GAP-CORE2-007` defers the row/file contract to a future task;
- Product Core imports from any existing WB/Ozon Excel discount workflow;
- persisted XLSX Product Core exports unless a separate implementation assignment adds approved file-contour scenarios and operation classifiers;
- marketplace write endpoints or WB/Ozon card-field changes.

No new customer question blocks the scoped PC2-006 exports.

## Fix-Loop Recheck Note

This revision addresses the blocking findings from `docs/reports/TASK_PC2_006_DESIGN_AUDIT.md`:

- B1: operation-link export now has an explicit Product Core/variant view gate for internal product/variant identifiers.
- B2: export audit action is closed on `product_core.export_generated`; implementation has no fallback to another action code.

No new UX/functionality/business question is introduced by these fixes. The audit report remains as historical blocking evidence for this fix-loop.

## Export Type Reconciliation

`CORE_2_EXCEL_EXPORT_SPEC.md` contains a broader export catalog. PC2-006, as assigned in `CORE_2_AGENT_TASKS.md` and this task prompt, implements the listing/latest/mapping/operation-link slice.

| Export type from spec | PC2-006 decision |
| --- | --- |
| Internal products | Existing export remains; protect hidden-store counts and add shared audit only if the implementation touches export audit. |
| Product variants | Not part of this PC2-006 implementation slice unless the orchestrator expands the task. A variant review export needs the explicit imported/draft review permission decision named in the permissions spec. |
| Marketplace listings | Implement/extend in PC2-006. |
| Listings with latest values | Implement/extend in PC2-006. |
| Mapping report | Implement/extend in PC2-006. |
| Operation link report | Implement in PC2-006. |
| Auto-created draft/imported variants report | Not part of this PC2-006 implementation slice unless paired with the imported/draft review permission and UI/review task. Mapping/latest exports must still show `variant_review_state` for linked variants they already expose. |
| External mapping table preview/export | Deferred to a future mapping-table task by `GAP-CORE2-007`; prohibited in PC2-006. |

## Documents Read

Mandatory inputs:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-006`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md` section `TASK-PC2-006`
- `docs/stages/stage-3-product-core/core-2/CORE_2_EXCEL_EXPORT_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Additional context used because it directly constrains roles, operation links or the known mapping-table boundary:

- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_UI_UX_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_MAPPING_RULES_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_OPERATION_LINKING_SPEC.md`

Read-only code context:

- `apps/product_core/exports.py`
- `apps/product_core/models.py`
- `apps/product_core/services.py`
- `apps/web/views.py`
- `apps/web/urls.py`
- `templates/web/product_list.html`
- `templates/web/marketplace_listing_list.html`
- `templates/web/marketplace_listing_card.html`
- `templates/web/operation_card.html`
- `apps/operations/models.py`
- `apps/operations/listing_enrichment.py`
- `apps/files/models.py`
- `apps/files/services.py`
- `apps/audit/models.py`
- `apps/audit/services.py`
- `apps/identity_access/seeds.py`
- existing export tests in `apps/web/tests.py`

## Current Code Facts

- `apps/product_core/exports.py` already streams CSV for internal products, marketplace listings, unmatched listings, latest values and mapping report.
- Current listing exports already use `marketplace_listings_visible_to()` and per-row `marketplace_listing.export` checks.
- Current latest-values export redacts `MarketplaceListing.last_values`, but it still materializes listing rows even when the actor lacks `marketplace_snapshot.view`; PC2-006 should tighten latest-values row eligibility to require both listing export and snapshot view for the row store.
- Current mapping report has no audit hook and does not expose a conflict-class column.
- There is no operation-link export endpoint yet.
- `OperationDetailRow.marketplace_listing` already exists. `apps/operations/listing_enrichment.py` provides read-only resolution and conflict classes suitable for operation-link report diagnostics.
- `FileObject.Scenario` has no Product Core export scenario. Current Product Core exports are streamed responses, not persisted file-contour outputs.
- `AuditActionCode.MARKETPLACE_LISTING_EXPORTED` exists, but it is listing-specific and does not exactly cover latest-values, mapping and operation-link report generation. The CORE-2 audit spec names `product_core.export_generated`; PC2-006 must use this action for scoped export generation events. If the action is absent in code at implementation start, add it with audit migration/tests in the allowed audit files below.

## Export List

### 1. Marketplace Listings CSV

Endpoint pattern: keep/extend `web:marketplace_listing_export`.

Minimum headers:

```text
marketplace
store_visible_id
store_name
external_primary_id
seller_article
barcode
title
brand
category
listing_status
mapping_status
internal_product_code
internal_product_name
internal_variant_sku
internal_variant_name
last_successful_sync_at
last_source
updated_at
```

Rows:

- include only listings in stores where the actor has `marketplace_listing.view` and `marketplace_listing.export`;
- never include hidden stores, hidden store names or hidden listing counts;
- linked internal product/variant columns are visible only when the actor also has Product Core/variant view access. If that permission is absent, leave linked product/variant columns blank rather than leaking identifiers.

### 2. Unmatched / Conflict Listings CSV

Endpoint pattern: keep/extend `web:unmatched_listing_export`.

This is the listing export contract filtered to:

```text
internal_variant_id is null
mapping_status in unmatched, needs_review, conflict
```

It uses the same headers as marketplace listings. The UI label may stay "unmatched", but the implementation must include `needs_review` and `conflict` rows as already specified.

### 3. Listings With Latest Values CSV

Endpoint pattern: keep/extend `web:listing_latest_values_export`.

Minimum headers are listing headers plus:

```text
latest_price
latest_price_with_discount
latest_discount_percent
currency
latest_stock_total
latest_promotion_action_id
latest_promotion_status
latest_price_snapshot_at
latest_stock_snapshot_at
latest_promotion_snapshot_at
last_values_json_redacted
```

Rules:

- row requires `marketplace_listing.export` and `marketplace_snapshot.view` for the row store;
- if the actor has no `marketplace_snapshot.view` for any filtered row store, deny the latest-values export rather than streaming base listing rows disguised as latest-values rows;
- latest JSON must pass the existing redaction policy before serialization;
- do not include raw snapshot `raw_safe`, request/response headers, stack traces, tokens or secret-like values;
- promotion/action columns are filled only when the latest cache contains safe action/promotion values. If not available, leave blank.

### 4. Mapping Report CSV

Endpoint pattern: keep/extend `web:listing_mapping_report_export`.

Minimum headers:

```text
marketplace
store_visible_id
store_name
external_primary_id
seller_article
barcode
title
mapping_status
internal_product_code
internal_product_name
internal_variant_sku
internal_variant_name
variant_review_state
latest_mapping_action
latest_mapping_changed_at
latest_mapping_reason_comment
conflict_class
last_successful_sync_at
last_source
```

Rules:

- row requires `marketplace_listing.export` for the listing store;
- include all mapping states unless filtered by `mapping_status`;
- `variant_review_state` is required when a linked variant exists so imported/draft variants are not mislabeled as manually confirmed products;
- `conflict_class` may be populated only from existing structured source context or the operation enrichment resolver. Do not invent a new conflict taxonomy in this export.

### 5. Operation Link Report CSV

New endpoint pattern: add a Product Core export route, for example `references/marketplace-listings/operation-links.csv`, and show the control on the marketplace listing export toolbar only when the actor has an eligible operation/detail scope plus `marketplace_listing.export` in at least one accessible store.

Minimum headers:

```text
operation_visible_id
marketplace
store_visible_id
step_code_or_type
row_number
raw_product_ref
row_status
reason_result_code
linked_listing_external_primary_id
linked_listing_seller_article
linked_variant_internal_sku
enrichment_status
conflict_reason
```

Rules:

- the row's operation must be visible to the actor under the same operation/detail rules used by the operation card;
- the operation store must also be in the actor's `marketplace_listing.export` scope;
- linked listing identifiers are filled only when `marketplace_listing_id` exists and the actor can view/export that listing store;
- if the FK exists but listing access is missing, do not export the linked listing details. Prefer excluding the row from this report because this report's purpose is listing-link troubleshooting;
- `linked_variant_internal_sku` is filled only when the actor also has both `product_core.view` and `product_variant.view`;
- any future internal product/variant identifier columns in this report, including internal product code/name or variant name, require the same Product Core/variant view gate before output;
- if listing access permits the row but Product Core/variant view is absent, leave internal product/variant identifier columns blank. Excluding such a row is allowed only when it matches the report's troubleshooting purpose; leaking the identifiers is prohibited;
- `raw_product_ref` remains the historical raw value and must not be normalized, trimmed in output, rewritten or used to change operation results;
- do not export `final_value`, raw technical payloads, request/response data or stack traces;
- use `apps/operations/listing_enrichment.resolve_listing_for_detail_row()` or equivalent read-only resolver to produce `enrichment_status` and `conflict_reason` without writing FK values.

Recommended `enrichment_status` values:

```text
linked
not_linked
candidate_available
conflict
row_not_product_identifier
hidden_by_access
```

`conflict_reason` should use existing classes from `apps/operations/listing_enrichment.py` where available:

```text
no_listing_match
multiple_listing_matches
store_marketplace_mismatch
row_not_product_identifier
source_scope_not_approved
api_data_integrity_duplicate
```

## Filters

No arbitrary column picker is specified for PC2-006. Use fixed header contracts. If a future request needs user-selectable columns, that is a new UX/functionality decision and must not be guessed inside this task.

Task-relevant filters to support where they apply:

- `marketplace`
- `store`
- `listing_status`
- `mapping_status`
- `source`
- `category`
- `brand`
- `last_seen_from` / `last_seen_to`
- `last_successful_sync_from` / `last_successful_sync_to`
- existing `updated_from` / `updated_to`
- `q` search by external id, article, barcode, title
- `stock` for listing/latest exports
- `conflict_class` for mapping and operation-link reports when a stored/resolved class exists
- operation-link only: `operation_visible_id`, `operation_step_code`, `operation_type`, `row_status`, `reason_code`

Implementation should extend `MarketplaceListingFilterForm` and the listing export queryset narrowly. Filter choice querysets must be built from access-filtered visible rows, as the current UI already does for stores/categories/brands.

## Permission And Object Access

General rules:

- apply object access before row materialization;
- no export may leak hidden store rows, hidden store names, hidden listing identifiers, hidden linked counts or hidden operation links;
- direct deny overrides allow, except owner protections as already implemented by identity/access rules;
- internal product rows are global only for the product identity, while any linked listing counts/details must be filtered to stores visible to the actor.

Role interpretation from current docs:

- Owner: all Product Core/export/listing/snapshot permissions, all object scope, not limited by administrator deny.
- Global admin: all Product Core permissions and full object scope, except owner-only protections remain unchanged.
- Local admin: listing/snapshot view/export/sync/map/unmap only for assigned stores; product create/update/archive only if separately granted.
- Marketplace manager/operator: `product_core.view`, `product_variant.view`, `marketplace_listing.view`, `marketplace_listing.export`, `marketplace_snapshot.view` for accessible stores; map/unmap only if separately granted.
- Observer: view-only permissions only if granted; no export/map/unmap by default.

Per-export minimum:

| Export | Required permission and scope |
| --- | --- |
| Marketplace listings / unmatched listings | `marketplace_listing.export` per row store, plus listing view/object access |
| Latest values | `marketplace_listing.export` + `marketplace_snapshot.view` per row store |
| Mapping report | `marketplace_listing.export` per row store; linked product/variant values require Product Core/variant view |
| Operation link report | operation detail visibility + `marketplace_listing.export` for the operation/listing store; `linked_variant_internal_sku` and any internal product/variant identifiers additionally require both `product_core.view` and `product_variant.view` |
| Internal products regression export | `product_core.export`; linked counts filtered to visible stores |

## Excel Boundary

PC2-006 exports are read-only outputs. Downloading, editing or re-uploading a Product Core export must not create or update:

- `InternalProduct`;
- `ProductVariant`;
- `MarketplaceListing`;
- mapping links or mapping history;
- operation row FK enrichment;
- Stage 1/2 operation results.

Existing WB/Ozon Excel discount workflows remain unchanged. Do not change Stage 1 Excel templates, calculation rules, reason/result codes, check/process behavior or file upload flows.

Existing WB/Ozon Excel discount workflows must not import into Product Core. The only approved external mapping-table workflow is the future dedicated preview/diff/apply flow; it is not part of PC2-006 because `GAP-CORE2-007` defers the row/file contract.

## File, Audit And Techlog Behavior

Default PC2-006 behavior: streamed CSV responses, no persisted `FileVersion`.

Rationale:

- current Product Core exports already stream CSV;
- `FileObject.Scenario` has no Product Core export scenario;
- adding persisted Product Core output files would require a file-contour scenario, download permission mapping and operation classifier that are not currently present.

Required audit for streamed exports:

- write one audit record per successful export request after permissions are resolved;
- use `product_core.export_generated` for every scoped PC2-006 export generation event: marketplace listings, unmatched/conflict listings, latest values, mapping report and operation-link report;
- if the implementation touches the existing internal product export to add the shared audit hook, use `product_core.export_generated` for that generation event as well;
- if `product_core.export_generated` is absent from `AuditActionCode` / audit action choices, add it in this task with an audit migration and focused tests. Do not substitute `marketplace_listing.exported` for PC2-006 scoped exports;
- safe audit snapshot may include export type, actor, visible store ids, row count, redacted/safe filters, generated filename and whether output was streamed;
- audit must not include row data, unredacted search text containing secret-like values, raw JSON, request headers or stack traces.

Techlog:

- no success techlog is required for ordinary streamed exports;
- write a safe warning/error techlog only for export generation failure, redaction guard failure or suspected secret-like data in an export payload;
- techlog details must use safe identifiers/counts and no raw sensitive payload.

If a future implementation assignment explicitly selects persisted Product Core exports, it must first update file-contour docs and code with approved Product Core export scenarios. The persisted path must then:

- create an operation/run or other approved historical container for the export;
- create immutable `FileObject` / `FileVersion` output metadata with 3-day physical retention;
- link output through `OperationOutputFile` or an approved equivalent;
- set `operation_ref` / `run_ref`;
- compute checksum;
- enforce download permission and object access on download;
- audit generation and controlled downloads.

Do not store Product Core exports under existing WB/Ozon discount file scenarios.

## Allowed Files For Developer

Primary implementation files:

- `apps/product_core/exports.py`
- `apps/web/views.py`
- `apps/web/urls.py`
- `apps/web/forms.py`
- `templates/web/marketplace_listing_list.html`
- `templates/web/product_list.html` only for shared audit/regression-safe internal product export behavior
- `apps/web/tests.py`
- `apps/product_core/tests.py`

Allowed only for required CORE-2 audit catalog alignment:

- `apps/audit/models.py`
- `apps/audit/migrations/*` for adding `product_core.export_generated` when absent
- `apps/audit/tests.py` or existing audit-related tests

Allowed only if a separate implementation assignment explicitly approves persisted Product Core export files:

- `apps/files/models.py`
- `apps/files/services.py`
- `apps/files/migrations/*`
- `apps/operations/models.py`
- `apps/operations/services.py`
- related file/operation tests

## Prohibited Files And Changes

Do not change:

- `apps/discounts/wb_excel/**`
- `apps/discounts/ozon_excel/**`
- Stage 1 WB/Ozon Excel templates/resources;
- Stage 1/2 calculation, upload, reason/result-code or operation-result behavior;
- `OperationDetailRow.product_ref` or any historical operation row value;
- Product Core sync/mapping/auto-create business rules except read-only export helpers;
- WB/Ozon API clients or marketplace write adapters;
- mapping-table upload/preview/apply services, routes, templates, permissions or file schema;
- file scenarios for persisted Product Core exports unless separately assigned as described above.

## Required Tests

Permission and access:

- listing export excludes hidden store rows and hidden store names;
- internal product export counts only visible linked WB/Ozon listings;
- latest-values export requires `marketplace_snapshot.view` and does not stream latest rows for stores lacking snapshot permission;
- operation-link export requires operation detail visibility plus `marketplace_listing.export`;
- operation-link export hides or excludes FK listing details when listing access is absent;
- operation-link export leaves `linked_variant_internal_sku` and any internal product/variant identifiers blank for an actor who has operation visibility plus listing export/access but lacks `product_core.view` or `product_variant.view`;
- owner/global admin/local admin/marketplace manager/observer behavior matches the permission matrix.

Column contracts:

- each export emits the fixed headers in this handoff;
- unmapped/needs-review/conflict filtered export contains only the approved states;
- mapping report includes `variant_review_state` for linked imported/draft variants;
- operation-link report preserves raw `product_ref` exactly as stored.

Filters:

- marketplace, store, listing status, mapping status, source, category, brand, dates and search filters work from access-filtered querysets;
- operation-link filters cover operation visible id, step code/type, row status and reason code;
- conflict class filter never fabricates classes not present in existing stored/resolved data.

Redaction:

- latest JSON redacts secret-like keys and values;
- audit snapshots redact or omit unsafe filters and never include row data;
- every scoped PC2-006 export writes `product_core.export_generated` and does not use `marketplace_listing.exported` for these events;
- raw snapshot `raw_safe`, request/response headers, tokens, Client-Id, Api-Key, bearer values, stack traces and raw sensitive payloads never appear in CSV, audit, techlog or test output.

Excel boundary / side effects:

- downloading any Product Core export leaves counts unchanged for `InternalProduct`, `ProductVariant`, `MarketplaceListing`, `ProductMappingHistory`, `OperationDetailRow` and Stage 1/2 operation results;
- existing WB Excel and Ozon Excel regression tests still pass;
- no Product Core export can be uploaded into existing Excel discount workflows as an import source.

Suggested verification commands for the implementation task:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.web apps.product_core apps.operations --verbosity 1 --noinput
git diff --check
```

## Audit Criteria

Implementation audit should verify:

- Excel boundary is preserved and no existing Excel workflow imports Product Core exports;
- every export applies object access before row materialization;
- latest values require snapshot permission and use redacted serialization;
- operation-link report does not leak hidden listing details through FK, operation rows or filters;
- operation-link report does not leak `linked_variant_internal_sku` or any internal product/variant identifier without both `product_core.view` and `product_variant.view`;
- fixed header contracts match this handoff and `CORE_2_EXCEL_EXPORT_SPEC.md`;
- audit records use `product_core.export_generated` for scoped PC2-006 export generation events and are written with safe counts/context and without row data or secrets;
- no hidden store counts/details leak through internal product exports;
- external mapping-table preview/export remains absent from PC2-006 implementation;
- no persisted FileVersion path is added unless the implementation package also adds an approved Product Core file scenario and operation/file-contour docs/tests.

## Final Handoff Decision

READY_FOR_IMPLEMENTATION for the scoped PC2-006 exports: marketplace listings, unmatched/conflict listings, latest values, mapping report and operation link report.

Known deferred boundary: external mapping-table preview/apply/export remains a future task under `GAP-CORE2-007` and does not block this PC2-006 slice.
