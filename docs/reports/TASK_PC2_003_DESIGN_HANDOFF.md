# TASK_PC2_003_DESIGN_HANDOFF

Date: 2026-05-02
Role: TASK-PC2-003 designer
Task: TASK-PC2-003 Normalized Article Linkage And Auto-Create
Verdict: READY_FOR_IMPLEMENTATION

## Scope Of This Handoff

This handoff prepares the developer package for the narrowed TASK-PC2-003 API linkage slice.

In scope:

- exact trimmed valid API article linkage to existing `ProductVariant`;
- API auto-create of `InternalProduct` + imported/draft `ProductVariant` when no variant exists and no conflict exists;
- audit/history/source-context integration for the approved automatic API path;
- conflict/listing-only handling for unsafe, blank or invalid article cases.

Out of scope:

- external mapping table preview/apply;
- `visual_external` table workflow;
- upload/apply UI, table persistence object, row/file contract, mapping-table permissions or mapping-table tests;
- any web-panel UX not already specified for the API linkage slice.

`GAP-CORE2-006` is resolved by customer decision. `GAP-CORE2-007` is deferred to a separate future task and is non-blocking for this narrowed TASK-PC2-003 slice. This handoff does not itself authorize product-code changes outside a separate implementation assignment.

## Documents Read

Mandatory task inputs:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/reports/TASK_PC2_003_DESIGN_HANDOFF.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-003`
- `docs/stages/stage-3-product-core/core-2/CORE_2_MAPPING_RULES_SPEC.md`

Additional task-scoped/context documents:

- `docs/PROJECT_NAVIGATOR.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md` section `TASK-PC2-003`

Read-only code context for package accuracy:

- `apps/product_core/models.py`
- `apps/product_core/services.py`
- `apps/audit/models.py`
- `apps/identity_access/seeds.py`

## Fixed Customer Decisions

The developer must implement these decisions exactly:

1. `internal_sku` is the unique product/variant key for current logic: one article equals one unique variant.
2. On the first valid API article/internal_sku with no conflict, create a pair: `InternalProduct` + `ProductVariant`.
3. `InternalProduct.internal_code = internal_sku`.
4. `InternalProduct.name` comes from the marketplace title from the first load where the valid article is found; if title is blank, fallback to `internal_sku`.
5. `InternalProduct.product_type = finished_good`, `status = active`, `category = null`, `comments = ""`.
6. Human-readable traits/categories computed from the article are stored in `InternalProduct.attributes`; automatic category tree creation is prohibited.
7. `ProductVariant.internal_sku = internal_sku`, name follows the same first-title/fallback rule, status is active, review state is `imported_draft`.
8. Repeated same `internal_sku` from another store/marketplace links the listing to the existing `ProductVariant`; it must not create a new product.
9. If the same `internal_sku` later arrives with a different human-readable title, do not overwrite the first `InternalProduct`/`ProductVariant` names. Store the new title on `MarketplaceListing.title`, keep the listing link `matched`, and set `ProductVariant.review_state = needs_review`. Do not infer title meaning.
10. If the database contains an impossible `internal_sku` conflict or cannot safely select a unique active/non-archived product/variant, create no new product and use the safe `conflict`/review rule from the mapping spec.

## Developer Package

### Expected Files

Primary implementation files:

- `apps/product_core/services.py`
  - add the API exact article linkage helpers near the existing sync/mapping helpers;
  - call them from approved API sync flows after listing upsert and before sync completion;
  - keep rows skipped by duplicate external article detection excluded from auto-link/auto-create;
  - add a system/API-safe mapping history path or refactor the shared persistence core so approved API auto-link does not fake manual UI permissions.
- `apps/product_core/models.py`
  - reuse `validate_core2_internal_sku`;
  - no model change is expected for the narrowed slice unless implementation proves current fields are insufficient and a separate migration/doc update is assigned.
- `apps/product_core/tests.py`
  - add focused unit/integration tests listed below.

Allowed only if the implementation assignment explicitly permits it:

- `apps/audit/models.py` plus migration/tests, if new audit action codes are required. Otherwise reuse existing Product Core/listing mapping audit codes with `AuditSourceContext.API` or `SERVICE`.

Prohibited in this task:

- `apps/web/*`, templates, forms, upload handlers or UI routes for mapping tables/`visual_external`;
- `apps/identity_access/*` permission additions for mapping-table import/apply;
- marketplace API write adapters or WB/Ozon card-field mutation.

### Expected Functions

Function names are advisory; responsibilities are mandatory:

- trim-only API article helper: returns blank as not matchable; no case folding, transliteration or punctuation changes;
- valid API article helper: calls `validate_core2_internal_sku` after trim and rejects invalid/non-unified values for automatic matching;
- unique active variant resolver by exact `ProductVariant.internal_sku`;
- safe parent resolver/creator for `InternalProduct.internal_code = internal_sku`;
- imported/draft variant creator with the customer-approved field policy;
- API linkage helper for one `MarketplaceListing` and one approved sync context;
- system/API-safe mapping history writer that records `ProductMappingHistory`, audit, source article, sync run, endpoint/source family and whether the variant was existing or auto-created;
- conflict marker for multiple candidates, archived/disallowed ambiguity, existing conflicting listing link and impossible `internal_sku` state;
- title mismatch marker that preserves product/variant names, updates only `MarketplaceListing.title`, keeps mapping `matched`, and sets `ProductVariant.review_state=needs_review`.

## Required Behavior Tests

Minimum Product Core tests:

- valid SKU examples are accepted: `nash_kit2_rg_pict0001`, `chev_pz_kit2_text0001`, `nash_mvd_pict0001`, `chev_back_mvd_text0001`;
- invalid examples are rejected for automatic matching: legacy SKU, uppercase, hyphenated, wrong content type, wrong suffix width, `kit0`, blank;
- exact trim-only match links an existing active/non-archived variant and writes `ProductMappingHistory` plus audit;
- leading/trailing whitespace matches after trim; internal whitespace, hyphen changes, case changes and partial strings do not match;
- blank or invalid/non-unified article creates/updates `MarketplaceListing` only and never creates `InternalProduct`/`ProductVariant`;
- valid API article with no variant creates `InternalProduct` and `ProductVariant` with the resolved field policy and `review_state=imported_draft`;
- existing single non-archived `InternalProduct.internal_code = internal_sku` without a variant is reused as parent;
- repeated same `internal_sku` across another store/marketplace links to the same variant and creates no duplicate product/variant;
- later different marketplace title for the same `internal_sku` preserves first product/variant names, stores the new listing title and marks variant `needs_review`;
- archived product/variant or unsafe multi-candidate state does not auto-link or auto-create;
- listing already linked to another variant is handled as conflict and is not overwritten;
- duplicate non-empty external article in one marketplace/store sync group writes safe techlog/summary and skips auto-link/auto-create for affected rows;
- no title/brand/category/image/barcode-only/fuzzy match can create `matched`;
- audit/history source context is safe/redacted and identifies API/service source, article basis and sync run.

Suggested future implementation commands:

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.product_core --verbosity 1 --noinput
```

## Prohibited Behavior

Do not implement:

- fuzzy, title-only, image, similarity score, substring, partial article, transliteration or case-folded matching;
- automatic active confirmed `ProductVariant` creation;
- a new product when the same `internal_sku` already resolves to a safe existing variant;
- overwriting first `InternalProduct`/`ProductVariant` names because of later marketplace titles;
- WB `vendorCode`, WB seller article, Ozon `offer_id`, price, action participation or card-parameter writes;
- Product Core import through existing WB/Ozon Excel discount workflows;
- editable UI dictionaries for the fixed CORE-2 SKU dictionary;
- external mapping table preview/apply, `visual_external`, table upload/apply UI, table file schema or mapping-table permission/audit scope in TASK-PC2-003.

## Acceptance Criteria

TASK-PC2-003 narrowed API slice is acceptable when:

- exact valid API article matching follows `ADR-0043` and no forbidden transformation is present;
- existing active/non-archived variant auto-link writes `matched`, `ProductMappingHistory`, audit and safe source context;
- API auto-create follows the resolved `GAP-CORE2-006` `InternalProduct` shell policy and leaves the variant `imported_draft`;
- repeated same `internal_sku` across stores/marketplaces reuses one `ProductVariant`;
- later differing marketplace title keeps link `matched`, preserves first product/variant names and marks the variant `needs_review`;
- invalid/non-unified listings remain listing-only;
- duplicate/conflict cases never auto-confirm and never create a new product/variant;
- no WB/Ozon card fields are written;
- existing manual mapping remains explicit-user-confirmation based;
- tests prove exact match, blank/no match, valid/invalid SKU formats, auto-create fields, duplicate/conflict behavior, repeated SKU reuse, title mismatch review, no fuzzy/title/image matching, and audit/history;
- `GAP-CORE2-007` deferred scope is respected: no mapping-table/`visual_external` workflow appears in code, tests or UI.

## Final Handoff Decision

READY_FOR_IMPLEMENTATION for narrowed TASK-PC2-003 API exact valid article linkage + auto-create/imported_draft.

External mapping table / `visual_external` workflow is explicitly deferred to a separate future task and is not blocking this slice.
