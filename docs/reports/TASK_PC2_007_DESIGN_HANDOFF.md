# TASK_PC2_007_DESIGN_HANDOFF

Date: 2026-05-02
Role: TASK-PC2-007 designer
Task: TASK-PC2-007 Product Core UI Integration
Verdict: READY_FOR_IMPLEMENTATION

## Scope Of This Handoff

This handoff prepares the implementation package for server-rendered Product Core UI integration after the implemented PC2-001..006 slices.

In scope:

- access-safe Product Core navigation additions for CORE-2;
- marketplace listing list/card sync status, source warnings, cache age, latest values and related operation links;
- unmatched, needs-review and conflict listing review views using exact-basis mapping only;
- imported/draft and needs-review variant review queue with explicit review-state labels and actions;
- operation detail row listing-link display from nullable `OperationDetailRow.marketplace_listing`;
- export controls for already implemented PC2-006 exports;
- UI tests for permissions, object access, safe rendering, no secret leakage and no future working ERP/card-write UI.

Out of scope for this PC2-007 implementation slice:

- active external mapping-table upload/preview/apply UI, file schema or persistence object;
- `visual_external` table workflow;
- new Product Core sync backend route or new marketplace read endpoint;
- marketplace card-field write UI, including WB `vendorCode` and Ozon `offer_id` edits;
- active sales/buyouts/returns/demand/in-work/production/shipments UI;
- identity/access catalog changes unless a separate PC2-008 or orchestrator assignment explicitly authorizes them.

No new customer question blocks this scoped handoff. The known mapping-table row/file-contract blocker is already recorded as `GAP-CORE2-007` and remains deferred/future. If the orchestrator requires PC2-007 to implement active mapping-table upload/preview/apply instead of keeping it hidden/deferred, the implementation verdict for that expanded scope becomes `BLOCKED_BY_CUSTOMER_QUESTION`.

## Documents Read

Mandatory inputs:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-007`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md` section `TASK-PC2-007`
- `docs/stages/stage-3-product-core/core-2/CORE_2_UI_UX_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_MAPPING_RULES_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_OPERATION_LINKING_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_EXCEL_EXPORT_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Additional context read because it directly constrains PC2-007 UI behavior:

- `docs/stages/stage-3-product-core/core-2/CORE_2_SCOPE.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_DESIGN_HANDOFF.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_TEST_PLAN.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_ACCEPTANCE_CHECKLIST.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md`
- closeout/reports for PC2-001..006, especially PC2-003, PC2-004, PC2-005 and PC2-006.

Read-only code context:

- `apps/web/views.py`
- `apps/web/urls.py`
- `apps/web/forms.py`
- `templates/base.html`
- `templates/web/reference_index.html`
- `templates/web/product_list.html`
- `templates/web/product_card.html`
- `templates/web/marketplace_listing_list.html`
- `templates/web/marketplace_listing_card.html`
- `templates/web/marketplace_listing_mapping.html`
- `templates/web/operation_card.html`
- `apps/product_core/models.py`
- `apps/product_core/services.py`
- `apps/product_core/exports.py`
- existing Product Core UI/export tests in `apps/web/tests.py`

## Current Code Facts

- Product Core product/listing routes already exist under `references/product-core/products/` and `references/marketplace-listings/`.
- PC2-006 export endpoints already exist for marketplace listings, unmatched listings, latest values, mapping report and operation-link report.
- `ProductVariant.review_state` exists with `manual_confirmed`, `imported_draft` and `needs_review`, but the current product list/card templates do not visibly label the review state.
- Current listing list/card templates display linked internal variant data without an explicit Product Core/variant visibility gate. PC2-007 must fix this UI leak path.
- Current listing card renders `SalesPeriodSnapshot` sections. CORE-2 active scope excludes sales/buyouts/returns as working UI, so PC2-007 must hide those sections.
- Current operation card detail rows show raw `product_ref` only. PC2-004 added nullable FK enrichment, and PC2-007 must expose the link only when visible.
- Current mapping page is manual and exact-candidate based. It does not implement mapping-table upload/apply or `visual_external`, which is correct for the scoped PC2-007 handoff.
- Current Product Core sync behavior is driven by already implemented source workflows. There is no standalone Product Core sync route in the inspected web code.

## Routes And Templates

Keep and extend existing routes:

| Route name | Path | PC2-007 work |
| --- | --- | --- |
| `web:reference_index` | `references/` | Add access-safe links to imported/draft variants and conflict/review listing queues when visible. |
| `web:internal_product_list` | `references/product-core/products/` | Keep current columns; add review/import summary only if it does not leak hidden listing details. |
| `web:internal_product_card` | `references/product-core/products/<pk>/` | Show variant `review_state`, imported source context summary, and visible linked listing state. |
| `web:marketplace_listing_list` | `references/marketplace-listings/` | Add sync status/source/cache-age columns or compact badges; gate linked variant identifiers. |
| `web:unmatched_listing_list` | `references/marketplace-listings/unmatched/` | Keep as unmatched/needs_review/conflict queue; add clear filter tabs for unmatched, needs_review and conflict. |
| `web:marketplace_listing_card` | `references/marketplace-listings/<pk>/` | Add sync run/status/error/source details, latest values, operation links and access-gated snapshot history. Remove active sales section. |
| `web:marketplace_listing_mapping` | `references/marketplace-listings/<pk>/mapping/` | Keep exact candidate/manual mapping workflow; add invalid/non-unified warnings and disabled/deferred mapping-table note only in admin/technical context if needed. |
| `web:operation_card` | `operations/<visible_id>/` | Add access-safe listing link and optional internal variant display to detail rows without changing raw `product_ref`. |
| PC2-006 exports | `references/marketplace-listings/*.csv` | Keep controls on listing toolbar only when permission/object access allow. |

Add focused new routes:

| New route name | Path | Purpose |
| --- | --- | --- |
| `web:imported_draft_variant_list` | `references/product-core/variants/imported-drafts/` | Review queue for `ProductVariant.review_state in (imported_draft, needs_review)`. |
| `web:imported_draft_variant_action` | `references/product-core/variants/<variant_pk>/review/` | POST-only confirm/leave-review/archive actions for the review queue. |

Optional route aliases are allowed if they reuse the same view/template and do not create new behavior:

- `web:marketplace_listing_conflict_list` for `mapping_status=conflict`;
- `web:marketplace_listing_review_list` for `mapping_status=needs_review`.

If aliases are added, they must still use the same access-filtered queryset and must not expose hidden counts in navigation.

New template expected:

- `templates/web/imported_draft_variant_list.html`

Existing templates to extend:

- `templates/web/reference_index.html`
- `templates/web/product_list.html`
- `templates/web/product_card.html`
- `templates/web/marketplace_listing_list.html`
- `templates/web/marketplace_listing_card.html`
- `templates/web/marketplace_listing_mapping.html`
- `templates/web/operation_card.html`

## UI Behavior

### Navigation

The Product Core navigation should expose:

- internal products;
- marketplace listings;
- unmatched listings;
- conflicts/needs-review queues;
- imported/draft variants review queue.

Navigation links appear only when the actor has the corresponding section and permission. Hidden-store counts must not appear next to links. Future warehouse, production, suppliers, BOM, packaging, labels, machine vision and marketplace card-write entries remain hidden or disabled/planned, not working empty modules.

### Listing Sync Status

Listing list/card must show safe sync state:

- last successful sync timestamp from `MarketplaceListing.last_successful_sync_at`;
- latest sync status from `MarketplaceListing.last_sync_run.status` when present;
- source from `last_source`;
- approved source/endpoint family from safe whitelisted `MarketplaceSyncRun.summary` keys when present;
- cache age computed from `last_successful_sync_at`;
- warning/error summary from `last_sync_run.summary` / `error_summary`, redacted and summarized only;
- link to the sync operation if `last_sync_run.operation_id` exists and `_can_view_operation()` allows it.

Do not show raw API payloads, request/response headers, tokens, Client-Id, Api-Key, stack traces or internal paths.

Do not add a new standalone sync POST route in PC2-007. A run control may be shown only as a disabled/planned control or a link to an already implemented source workflow. Any active new sync execution route requires a separate backend/source assignment with official endpoint evidence and tests.

### Linked Internal Data

Marketplace listing rows/cards may show linked internal product or variant identifiers only when the actor has both:

- `product_core.view`;
- `product_variant.view`.

If the actor can view the listing but lacks either internal view permission, show the listing data and mapping status, but blank or mark the internal product/variant fields as hidden. Do not render links, internal SKU, product code/name, variant name, imported source context or review state in that case.

Internal product pages remain global Product Core pages, but linked listing rows and counts must continue to use `marketplace_listings_visible_to()`.

### Imported / Draft Variants

Add an imported/draft review queue for `ProductVariant.review_state in (imported_draft, needs_review)`.

Minimum columns:

- internal SKU;
- variant name;
- parent product code/name;
- `ProductVariant.status`;
- `ProductVariant.review_state`;
- source marketplace/store/listing links only when visible;
- source sync run or operation link when visible;
- imported source context safe summary;
- updated timestamp;
- actions.

Required labeling:

- `status=active` must not be presented as manually confirmed when `review_state=imported_draft` or `needs_review`;
- show state as two separate concepts: lifecycle status and review state.

Allowed actions:

- confirm: set `review_state=manual_confirmed`;
- leave for review: set `review_state=needs_review`;
- edit: use existing variant edit route, but keep review state visible;
- archive: use the archive behavior and keep audit.

Permission behavior:

- view queue: `product_core.view` + `product_variant.view`;
- confirm and leave for review: reuse explicit `product_variant.update`;
- edit: `product_variant.update`;
- archive: `product_variant.archive`.

This reuses an explicit non-view permission and does not hide review behind generic view permission. If the orchestrator requires a new dedicated permission code for review confirmation, that belongs in PC2-008 or a separate identity/access task.

Audit behavior:

- use existing Product Variant audit pattern unless PC2-008 adds a dedicated action;
- extend the UI-side variant audit snapshot to include `review_state` and safe/redacted imported source context if the view writes review-state changes;
- do not include secrets or raw source payload.

### Mapping Review, Conflicts And Invalid Articles

The existing mapping workflow remains exact-basis and manual:

- show seller article/vendorCode/offer_id exact basis;
- show external primary id/external identifier exact basis;
- show barcode only as supplemental exact candidate/review signal;
- no fuzzy, title, brand, category, partial article, image or machine-vision scoring;
- final mapping requires explicit user confirmation and `marketplace_listing.map`;
- unmap requires `marketplace_listing.unmap`.

Listing queues must support filters for:

- marketplace;
- store;
- listing status;
- mapping status;
- source where available;
- last sync / updated date where already supported;
- search by external id, seller article, barcode, title;
- conflict class only if a stored source context has that class.

Invalid/non-unified article display:

- show listing-only state;
- explain that automatic product/variant creation was not applied;
- allow manual mapping fallback when the user has mapping permissions;
- do not imply `visual_external` or mapping-table processing is currently available.

### Mapping Table Workflow

Keep active mapping-table upload/preview/apply hidden in PC2-007.

Reason: `GAP-CORE2-007` records that the external mapping table row/file contract is deferred and blocking before any future mapping-table or `visual_external` workflow. PC2-007 must not add:

- upload form;
- preview route;
- apply route;
- file format parser;
- table persistence object;
- mapping-table export;
- `marketplace_mapping.import_table` / `marketplace_mapping.apply_table` permission seeds;
- UI that implies a table can be applied.

If active mapping-table implementation is later assigned, exact customer/orchestrator questions are:

- What exact mapping table format and required columns must CORE-2 accept?
- How must a table row identify the source listing: database listing id, marketplace/store/external_primary_id, WB `nmID`, WB `vendorCode`, Ozon `product_id`, Ozon `offer_id`, seller article, or an approved combination?
- What persistence object should preview/apply use: `Operation`, `MarketplaceSyncRun`, `FileVersion`, UI-only preview object, or another approved object?
- If a valid target `internal_sku` has no `ProductVariant`, should explicit apply create the same imported/draft product/variant as API auto-create, or remain a preview conflict?

### Operation Row Links

Operation detail rows must continue to show raw `OperationDetailRow.product_ref` exactly as stored.

Add display-only columns:

- listing link, if `marketplace_listing_id` exists and actor can view that listing store;
- linked internal variant, only if actor has both `product_core.view` and `product_variant.view`;
- otherwise blank/hidden.

If FK exists but actor lacks listing access, do not show listing store, external id, seller article, title or linked variant. Do not compute candidate links in the operation card. Do not write FK values from the UI.

### Snapshots And Latest Values

Listing list/card may show latest values only when `marketplace_snapshot.view` is granted for the listing store.

Active CORE-2 UI may show:

- latest price cache;
- latest stock cache;
- latest promotion/action participation;
- source sync run and timestamps;
- immutable price, stock and promotion snapshot history tables.

Raw-safe details:

- collapsed by default;
- shown only when `marketplace_snapshot.technical_view` is granted;
- always redacted.

Hide active sales/buyouts/returns/demand/in-work/production/shipments UI. Remove the current user-facing sales/orders snapshot summary/table from the listing card in this PC2-007 implementation. If a technical/admin context needs to acknowledge future hooks, it may show a non-workflow note such as "not filled in CORE-2" only behind technical context.

### Export Controls

Use the PC2-006 export endpoints already present:

- marketplace listings CSV;
- unmatched/conflict listings CSV;
- latest values CSV;
- mapping report CSV;
- operation-link report CSV.

Controls appear only when the actor has the needed permission and an eligible visible object scope:

- listing/unmatched/mapping exports: `marketplace_listing.export` in at least one visible store;
- latest values export: only when snapshot view is available for exported rows;
- operation-link report: operation detail visibility plus listing export scope;
- internal product export: `product_core.export`.

Do not show export controls that imply hidden-store data exists. Do not add import/upload affordances for Product Core exports.

## Permission And Access Rules

Use the existing permission matrix:

- internal product list/card: `product_core.view`;
- product create/update/archive: `product_core.create/update/archive`;
- variant view/create/update/archive: `product_variant.view/create/update/archive`;
- listing list/card: `marketplace_listing.view` per store plus current section access;
- listing sync action display: `marketplace_listing.sync` per store, but no new active route in PC2-007;
- map/unmap: `marketplace_listing.map/unmap` per store plus Product Core/variant view;
- snapshot latest/history: `marketplace_snapshot.view` per store;
- technical raw-safe snapshot details: `marketplace_snapshot.technical_view` per store;
- exports: PC2-006 export gates.

Direct deny overrides allow per existing identity/access behavior. Owner protections remain unchanged.

No UI path may leak hidden store/listing data through:

- counts;
- disabled controls;
- links;
- titles/tooltips;
- export buttons;
- operation FK display;
- sync warning summaries;
- imported source context.

## Allowed Files For Developer

Primary PC2-007 implementation files:

- `apps/web/views.py`
- `apps/web/urls.py`
- `apps/web/forms.py`
- `templates/base.html` only for small shared display classes if required;
- `templates/web/reference_index.html`
- `templates/web/product_list.html`
- `templates/web/product_card.html`
- `templates/web/marketplace_listing_list.html`
- `templates/web/marketplace_listing_card.html`
- `templates/web/marketplace_listing_mapping.html`
- `templates/web/operation_card.html`
- `templates/web/imported_draft_variant_list.html`
- focused tests in `apps/web/tests.py`

Allowed only if implementation needs read-only constants/choices and no business-rule change:

- import existing `ProductVariant.ReviewState`, `MarketplaceListing.MappingStatus`, `MarketplaceSyncRun.SyncStatus` in web code.

Allowed only if PC2-008 or orchestrator explicitly expands the task:

- `apps/identity_access/seeds.py`
- `apps/identity_access/migrations/*`
- `apps/audit/models.py`
- `apps/audit/migrations/*`
- `apps/techlog/models.py`
- `apps/techlog/migrations/*`

## Prohibited Files And Changes

Do not change:

- `apps/discounts/wb_excel/**`
- `apps/discounts/ozon_excel/**`
- `apps/discounts/wb_api/**`
- `apps/discounts/ozon_api/**`
- `apps/product_core/services.py` business rules;
- `apps/product_core/models.py` or migrations;
- `apps/product_core/exports.py` except if a narrow UI test exposes a PC2-006 regression that the orchestrator explicitly assigns;
- `apps/operations/models.py`, enrichment services or backfill command;
- Stage 1/2 Excel templates, calculations, upload flows, reason/result codes or operation status behavior;
- `OperationDetailRow.product_ref` or any historical detail values;
- marketplace API clients or write adapters;
- external mapping-table upload/preview/apply services, routes, templates, permissions, parser, file schema or persistence;
- `visual_external` workflow;
- WB/Ozon seller article/vendorCode/offer_id edit UI;
- editable internal SKU dictionary UI;
- active future ERP/warehouse/production/demand/labels pages.

## Required Tests

Suggested focused implementation command:

```bash
python manage.py test apps.web --verbosity 1 --noinput
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
```

Add or extend tests for:

- listing list hides linked internal product/variant identifiers without both `product_core.view` and `product_variant.view`;
- listing card hides linked internal identifiers and imported source context without Product Core/variant view;
- listing list/card render sync status, safe warning/error summary, cache age and operation link without secrets;
- imported/draft review queue labels `status` and `review_state` separately;
- confirm action requires `product_variant.update` and changes `review_state` to `manual_confirmed`;
- leave-for-review action requires `product_variant.update` and changes `review_state` to `needs_review`;
- archive action requires `product_variant.archive`;
- imported/draft variants are never labeled as manually confirmed before review;
- unmatched, needs_review and conflict filters render access-filtered rows only;
- mapping page shows exact candidate basis only and never fuzzy/title/image score;
- invalid/non-unified articles remain listing-only and do not show active table upload/apply controls;
- operation card shows raw `product_ref` always, listing link only with listing access, and internal variant only with Product Core/variant view;
- operation card does not modify FK or `product_ref`;
- latest price/stock/promotion values require `marketplace_snapshot.view`;
- raw-safe snapshot details require `marketplace_snapshot.technical_view` and are collapsed;
- sales/orders/buyouts/returns user-facing snapshot UI is absent from CORE-2 active screens;
- export toolbar controls appear only under PC2-006 permission/object-access rules;
- no mapping-table upload/apply route or form exists;
- no future ERP operational pages or marketplace card-field edit UI exists;
- rendered Product Core UI contains no token, Client-Id, Api-Key, bearer value, raw request/response headers, stack trace or internal path.

Regression coverage should keep the existing Product Core export tests passing. Broader `apps.product_core` tests are useful if review-state UI helpers touch Product Core fixtures, but PC2-007 should not need Product Core model/service changes.

## Audit Criteria

Implementation audit should verify:

- UI matches `CORE_2_UI_UX_SPEC.md` for the scoped active PC2-007 surfaces;
- mapping-table/`visual_external` workflow remains hidden/deferred under `GAP-CORE2-007`;
- imported/draft variants are visible in a review queue and not mislabeled as confirmed active business products;
- review actions require explicit non-view permissions and write safe audit context;
- linked internal product/variant identifiers are hidden unless both Product Core and variant view permissions are present;
- listing, snapshot, operation-link and export object access all respect store scope;
- operation card displays FK navigation without rewriting `product_ref` or historical operation outcomes;
- active snapshot UI is limited to price, stock and promotions/actions;
- current user-facing sales/orders snapshot table is removed or hidden from CORE-2 active screens;
- no working future ERP modules, editable SKU dictionary, marketplace write/card-field UI, fuzzy mapping or hidden auto-mapping is introduced;
- no secrets or raw technical payloads appear in rendered HTML.

## Stop Conditions

Stop and return to the orchestrator if implementation requires any of these decisions:

- active external mapping table upload/preview/apply;
- `visual_external` table workflow;
- a new standalone Product Core sync execution route;
- new read-only marketplace endpoint without endpoint-specific official docs evidence and mocks;
- a new dedicated permission code for imported/draft review not assigned to PC2-007;
- visible future ERP/sales/demand/production UI behavior beyond hidden/disabled/planned notes.

## Final Handoff Decision

READY_FOR_IMPLEMENTATION for the scoped PC2-007 UI integration described above.

Known deferred boundary: active external mapping-table preview/apply and `visual_external` workflow remain future work under `GAP-CORE2-007` and must not be implemented in PC2-007 without a new customer/orchestrator decision package.
