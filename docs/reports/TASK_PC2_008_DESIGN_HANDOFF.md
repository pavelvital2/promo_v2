# TASK_PC2_008_DESIGN_HANDOFF

Date: 2026-05-02
Role: TASK-PC2-008 designer
Task: TASK-PC2-008 Permissions, Audit, Techlog, Redaction
Verdict: READY_FOR_IMPLEMENTATION

## Scope Decision

TASK-PC2-001..007 already implemented most CORE-2 Product Core behavior. TASK-PC2-008 must not rebuild those slices. The remaining work is a security/catalog hardening slice:

- validate the existing Product Core permission catalog, role seeds and object-access behavior;
- add missing CORE-2 audit action codes and safe service calls where current PC2 slices still use a generic action or no audit action;
- add missing CORE-2 techlog event types and safe service calls for current PC2 failure/conflict paths;
- harden redaction/no hidden-object leakage tests around UI/export/audit/techlog/snapshots;
- run targeted regression evidence.

No customer question blocks this implementation. `GAP-CORE2-007` remains deferred for the future external mapping table / `visual_external` workflow and does not block this narrowed TASK-PC2-008 scope.

## Documents Read

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-008`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md` section `TASK-PC2-008`
- `docs/stages/stage-3-product-core/core-2/CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`
- PC2-001..007 closeout/audit/recheck reports as needed

Read-only code context checked:

- `apps/identity_access/seeds.py`, models, services, migrations, tests;
- `apps/audit/models.py`, services, migrations, tests;
- `apps/techlog/models.py`, services, migrations, tests;
- `apps/product_core/models.py`, services, exports, tests;
- `apps/operations/listing_enrichment.py`, backfill command, tests;
- `apps/web/views.py`, forms, templates/tests touched by PC2-006/007;
- redaction helpers and representative tests.

## Already Covered By PC2-001..007

No new implementation is needed for these items except validation/regression:

- Product Core model fields for imported/draft lifecycle and nullable `OperationDetailRow.marketplace_listing`.
- CORE-2 structured SKU validator and API valid-article auto-link/auto-create behavior.
- Marketplace listing sync for approved current sources, duplicate external article guard and `marketplace_sync.data_integrity_error`.
- Snapshot filling for approved price/stock/promotion/action sources.
- CSV exports with object access, `product_core.export_generated` audit action and redacted latest values.
- UI permission/object-access fixes for listing/card/review/export surfaces.
- Imported/draft review actions are already gated by explicit non-view `product_variant.update`; no new dedicated review permission is required for this scope.

## Deferred / Not In Scope

Do not implement active external mapping table or `visual_external` behavior in TASK-PC2-008:

- no upload/preview/apply route, form, template, parser, persistence object or export;
- no `marketplace_mapping.import_table` / `marketplace_mapping.apply_table` seed migration in this slice;
- no audit calls for `marketplace_mapping.table_previewed` or `marketplace_mapping.table_applied` until the future mapping-table task defines the row/file contract and role seed policy.

This follows `GAP-CORE2-007` and PC2-007 handoff/recheck. Future mapping-table implementation must reopen those permissions/actions/events under a separate task.

## Permission Catalog And Role Checks

Current catalog status:

- Present Product Core permissions: `product_core.*`, `product_variant.*`, `marketplace_listing.*`, `marketplace_snapshot.*`.
- Existing review/confirm permission: reuse `product_variant.update`. It is explicit and non-view, satisfying the CORE-2 rule that review must not be hidden behind generic view permission.
- Mapping table permissions are intentionally absent from the current active implementation because the workflow is deferred.

Implementation work:

1. Add or tighten tests in `apps/identity_access/tests.py` and/or `apps/web/tests.py` proving:
   - owner has all CORE-2 Product Core permissions;
   - global admin has all non-owner-only CORE-2 Product Core permissions;
   - local admin has listing/snapshot view/export/sync/map/unmap in store scope, but not Product Core create/update/archive by default;
   - marketplace manager has Product Core/listing/snapshot view/export defaults but no map/unmap/update/archive by default;
   - observer has view-only defaults and no export/map/unmap/update/archive by default;
   - `product_variant.update` allows imported/draft confirm/leave-review only when explicitly granted by role or override;
   - direct deny still wins over role grant;
   - no user without store access can view/export hidden listings, snapshots, operation links, listing counts, audit records or techlog records for that store.
2. Keep `marketplace_mapping.import_table` and `marketplace_mapping.apply_table` out of seeds and role matrix in this slice. Add a test or static assertion only if needed to prove no active UI route/control depends on these deferred permissions.

No identity/access migration is expected unless an implementation audit explicitly rejects reuse of `product_variant.update`; if that happens, stop and route the dedicated permission/role-template decision through the orchestrator.

## Audit Action Coverage

Current gaps are technical and can be resolved without customer input.

Add audit action choices and migrations after current audit migration chain:

- `product_variant.auto_created_draft`
- `operation_detail_row.listing_fk_enriched`
- `marketplace_sync.failed`
- `marketplace_snapshot.write_failed`

Expected service calls:

- API imported/draft auto-create must use `product_variant.auto_created_draft` for the auto-created draft variant. Manual UI variant creation remains `product_variant.created`.
- Successful non-dry-run FK enrichment must write `operation_detail_row.listing_fk_enriched`. Use `OperationDetailRow` as entity, link `operation` and `store`, and include only safe fields: row id, operation id/visible id, listing id, matched key class, operation family and write source. Do not include raw `product_ref` if it may contain hidden or sensitive source payload; hashed/truncated key basis is acceptable.
- `fail_marketplace_sync_run()` must write `marketplace_sync.failed` with safe source, status, counts and operation/sync-run ids. Do not store raw exception strings unless they pass the existing secret guard.
- Snapshot helper/write failures must write `marketplace_snapshot.write_failed` with snapshot kind, listing id, sync run id, source endpoint code and safe failure class. No raw API rows, headers, token-like values or stack traces.
- Existing `product_core.export_generated`, `marketplace_listing.synced`, `marketplace_listing.mapped`, `marketplace_listing.unmapped`, `marketplace_listing.mapping_review_marked` and `marketplace_listing.mapping_conflict_marked` should be kept and covered by regression, not replaced.

Audit snapshots must remain access-safe. In particular, imported/draft review audit from UI must not put raw `store_id`, `listing_id`, `operation_id`, `sync_run_id`, hidden external ids or secret-like values from `ProductVariant.import_source_context` into a global ProductVariant audit record. Keep only non-object safe summary keys or resolve/link the audit record to the relevant store before including store-scoped ids.

Do not add `marketplace_mapping.table_previewed` or `marketplace_mapping.table_applied` calls in this slice.

## Techlog Event Coverage

Add missing CORE-2 techlog event choices, baseline severities and migration/tests after the current techlog migration chain:

| Event type | Baseline | Current TASK-PC2-008 usage |
| --- | --- | --- |
| `marketplace_sync.api_error` | error | Catalog only for future Product Core external API failures not covered by WB/Ozon-specific events. No current call-site required. |
| `marketplace_snapshot.write_error` | error | Write when snapshot persistence/redaction/validation fails. |
| `marketplace_mapping.conflict` | warning | Write for automatic exact-candidate/API mapping conflicts, not for a user's manual conflict marker. |
| `operation_detail_row.enrichment_error` | warning | Write for FK enrichment conflicts/failures with safe counts/context. Escalate to error for same-scope violation or unexpected exception. |
| `product_variant.auto_create_error` | error | Write if approved API imported/draft product/variant auto-create fails safely. |

Already-present generic/specific events should be reused:

- `marketplace_sync.started`, `marketplace_sync.completed`, `marketplace_sync.completed_with_warnings`, `marketplace_sync.failed`;
- `marketplace_sync.rate_limited`, `marketplace_sync.response_invalid`, `marketplace_sync.data_integrity_error`, `marketplace_sync.secret_redaction_violation`;
- WB/Ozon-specific API failure/redaction events from Stage 2.

Techlog payload rules:

- `safe_message` and `sensitive_details_ref` must pass `assert_no_secret_like_values`;
- even with `techlog.sensitive.view`, do not store token, API key, Client-Id, Authorization, bearer values, protected secret refs, raw headers or raw secret-like payloads;
- for FK enrichment, prefer aggregate safe conflict counts for backfill and safe per-row context only when needed for runtime diagnosis;
- do not log raw `product_ref`, raw API response, row payload, stack trace or file path when those could expose hidden store data or secrets.

## Redaction And No-Leakage Checks

Required implementation checks:

- New audit and techlog service calls reject secret-like values through existing redaction guard tests.
- Product Core snapshots and `MarketplaceListing.last_values` continue rejecting/redacting secret-like `raw_safe`, `stock_by_warehouse`, constraints and latest JSON.
- UI imported/draft review queue continues hiding hidden source store/listing/operation/sync-run identifiers; add audit snapshot coverage for the same source-context leak class.
- Product Core exports continue redacting latest values and blanking internal identifiers unless both `product_core.view` and `product_variant.view` are present.
- Operation row links continue preserving raw `product_ref` and show listing/internal identifiers only through object-access and internal-view gates.
- Audit/techlog list/card visibility continues respecting `logs.scope.limited`, object access and `techlog.sensitive.view`.
- Test output and new reports must not include real or fake long token/API key/Client-Id strings except as redacted fixtures/assertions.

## Allowed Files

Expected implementation files:

- `apps/audit/models.py`
- `apps/audit/migrations/*`
- `apps/audit/tests.py`
- `apps/techlog/models.py`
- `apps/techlog/migrations/*`
- `apps/techlog/tests.py`
- `apps/product_core/services.py`
- `apps/product_core/tests.py`
- `apps/operations/listing_enrichment.py`
- `apps/operations/management/commands/backfill_operation_detail_listing_fk.py` only if needed to pass safe context into the enrichment service
- `apps/operations/tests.py`
- `apps/web/views.py` only for imported/draft audit snapshot redaction or permission assertion fixes
- `apps/web/tests.py`
- `apps/identity_access/tests.py`

Conditionally allowed:

- `apps/identity_access/seeds.py` and `apps/identity_access/migrations/*` only if a separately approved permission-code change is assigned. No such change is expected for this handoff.
- `docs/testing/*`, `docs/reports/*` for implementation/test closeout evidence.

## Prohibited Files And Changes

Do not change:

- Stage 1/2 permission semantics or role defaults outside the checks above;
- `OperationDetailRow.product_ref`, reason/result codes, operation status/result/summary, file outputs or Excel calculation/upload behavior;
- WB/Ozon marketplace write adapters or card-field mutation;
- API connection secret readback or protected secret storage semantics;
- Product Core mapping business rules, SKU validator, auto-create field policy or title mismatch policy;
- snapshot scope for sales, buyouts, returns, demand, in-work, production or shipments;
- external mapping table / `visual_external` workflow, permissions, audit calls, techlog calls, parser, routes or UI;
- future ERP/warehouse/production/suppliers/BOM/labels/machine-vision UI.

## Required Tests

Minimum focused tests:

- identity/access permission matrix and direct deny precedence for Product Core permissions;
- imported/draft confirm/leave-review denied without `product_variant.update` and allowed with explicit grant;
- hidden store listing/snapshot/export/operation-link denial still passes;
- new audit action choices exist and service calls are written for:
  - API imported/draft auto-create;
  - FK enrichment write;
  - failed marketplace sync;
  - snapshot write failure;
- new techlog event choices exist with correct baselines and service calls for:
  - snapshot write error;
  - automatic mapping conflict;
  - FK enrichment error/conflict;
  - product variant auto-create error;
- no audit/techlog safe message, snapshots or sensitive details accept secret-like payloads;
- imported source context object ids do not leak through UI or audit snapshots when the actor lacks source object access;
- existing PC2-006 export tests for latest-value redaction and internal identifier gating remain green.

Suggested commands:

```bash
git diff --check
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.identity_access apps.audit apps.techlog apps.product_core apps.operations apps.web --verbosity 1 --noinput
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts --verbosity 1 --noinput
```

If runtime constraints require narrowing, the implementation report must list the exact executed test modules and the residual risk.

## Audit Criteria

TASK-PC2-008 is acceptable when:

- no existing Stage 1/2 permission is weakened;
- Product Core review uses explicit non-view permission and object access remains enforced;
- hidden store/listing/snapshot/operation data is absent from UI, exports, audit and techlog for unauthorized users;
- all non-deferred CORE-2 audit action gaps listed in this handoff are implemented with migrations and tests;
- all non-deferred CORE-2 techlog event gaps listed in this handoff are implemented with migrations and tests;
- secret-like values are rejected or redacted across snapshots, latest values, audit, techlog, UI, exports, test output and reports;
- mapping-table/`visual_external` permissions and workflows remain absent until the future task resolves `GAP-CORE2-007`;
- regression tests for PC2-001..007 touched surfaces remain green.

## Gaps

No new gap is opened by this handoff.

`GAP-CORE2-007` remains deferred/future for the external mapping table workflow and is not a blocker for TASK-PC2-008. If an implementer tries to add mapping-table permissions or UI in this slice, stop and route the future workflow questions through the orchestrator.

## Final Handoff Decision

READY_FOR_IMPLEMENTATION.

This handoff authorizes only the narrowed permissions/audit/techlog/redaction hardening and validation work above. It does not authorize Product Core feature expansion, mapping-table workflow, marketplace writes or any Stage 1/2 business-logic change.
