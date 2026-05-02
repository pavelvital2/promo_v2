# CORE_2_AGENT_TASKS.md

Статус: исполнительная проектная документация CORE-2, подготовлена для audit-gate.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§12-13, §11.14.

## Назначение

Task-scoped decomposition for future CORE-2 implementation. These tasks are not executable until documentation audit result is `AUDIT PASS`.

## Global Preconditions

- Documentation audit result: `AUDIT PASS`.
- No blocking GAP for the affected slice.
- Current branch/worktree checked by orchestrator.
- Backup/runbook requirements understood for migration tasks.
- Stage 1/2 regression scope preserved.

## Global Prohibited Changes

- No warehouse, production, suppliers, purchases, BOM, packaging, labels, machine vision.
- No legacy `MarketplaceProduct` removal.
- No `product_ref` rewrite.
- No Stage 1/2 business logic or reason/result code changes.
- No unapproved WB/Ozon endpoints.
- No Excel import into Product Core hidden inside existing Excel workflows.
- No secret exposure in any safe contour.

## TASK-PC2-001 Data Model And Migration

Role: Developer.

Goal: add nullable `OperationDetailRow.marketplace_listing_id` and any audited model additions approved for CORE-2.

Input docs: package `TASK-PC2-001` from `CORE_2_READING_PACKAGES.md`.

Allowed/expected files:

- `apps/operations/models.py`;
- generated operations migration;
- Product Core model/migration files only if approved by `GAP-CORE2-001`;
- focused model/migration tests.

Prohibited changes:

- legacy `MarketplaceProduct` deletion;
- Stage 1/2 calculation code;
- existing reason/result code catalogs unless explicitly required by audited model change;
- data rewrite of `product_ref`.

Implementation steps:

1. Add nullable FK with index and `PROTECT`.
2. Add optional imported/draft lifecycle only if `GAP-CORE2-001` is resolved.
3. Generate non-destructive migration.
4. Add validation tests and rollback notes.

Tests:

- `manage.py makemigrations --check --dry-run` after migration creation in expected mode;
- migration apply/rollback in test DB where feasible;
- FK null compatibility;
- terminal operation immutability unaffected.

Audit criteria:

- FK is nullable/reversible;
- no legacy deletion;
- no `product_ref` rewrite;
- no unapproved auto-create model behavior.

Handoff: changed files, migration name, validation commands, risk notes.

## TASK-PC2-002 Marketplace Listing Sync Integration

Role: Developer.

Goal: integrate approved WB/Ozon sources with `MarketplaceListing` and `MarketplaceSyncRun`.

Input docs: package `TASK-PC2-002`.

Allowed/expected files:

- Product Core sync services/adapters;
- existing Stage 2 API adapter call sites only where additive and approved;
- tests/fixtures/mocks.

Prohibited changes:

- new endpoints not listed in `CORE_2_API_SYNC_SPEC.md`;
- marketplace write endpoints for sync;
- Stage 2 upload behavior changes;
- secret persistence in snapshots/logs.

Implementation steps:

1. Implement WB prices listing adapter.
2. Implement WB regular promotion product-row adapter if in approved slice.
3. Implement Ozon Elastic scoped adapter only for selected action set.
4. Record sync runs, safe summaries and techlog failures.
5. Keep failed sync from erasing latest cache.

Tests:

- WB/Ozon mocked source success/failure;
- pagination/rate-limit retry;
- no unapproved endpoint call;
- duplicate active sync guard;
- redaction.

Audit criteria:

- endpoint list matches docs;
- object access unaffected;
- no new writes to WB/Ozon.

Handoff: source matrix, fixtures, tests, open `GAP-CORE2-002` impact.

## TASK-PC2-003 Normalized Article Linkage And Auto-Create

Role: Developer.

Goal: implement exact normalized article linkage behavior approved for CORE-2.

Input docs: package `TASK-PC2-003`.

Allowed/expected files:

- Product Core mapping/linkage services;
- mapping history/audit integration;
- tests.

Prohibited changes:

- fuzzy/title/image matching;
- automatic confirmed mapping outside approved policy;
- vendorCode/offer_id mutation;
- auto-create while `GAP-CORE2-001` is open.

Implementation steps:

1. Implement exact trimmed article comparison.
2. Mark needs_review/conflict for deterministic candidates.
3. If customer approves Option B, implement draft/imported creation with review/audit/report.
4. Keep conflict cases unconfirmed.

Tests:

- exact match;
- blank/no match;
- duplicate conflict;
- no fuzzy/partial/title match;
- auto-create behavior only when approved;
- audit/history.

Audit criteria:

- ADR-0043 and ADR-0045 followed;
- no hidden business assumption;
- `GAP-CORE2-001` resolution reflected.

Handoff: chosen policy, tests, mapping examples, remaining risks.

## TASK-PC2-004 Operation Row FK Enrichment

Role: Developer.

Goal: write nullable listing FK for new and/or old operation detail rows within approved scope.

Input docs: package `TASK-PC2-004`.

Allowed/expected files:

- operation/product-core enrichment service;
- additive calls in approved Stage 1/2 services;
- data backfill command/migration if approved;
- tests.

Prohibited changes:

- any `product_ref` mutation;
- operation result/status/file/reason code changes;
- linking action/promotion summary rows as product rows;
- cross-store/cross-marketplace lookup.

Implementation steps:

1. Implement deterministic resolver.
2. Add new-row FK write where source context has listing.
3. Add idempotent backfill only after `GAP-CORE2-003` scope resolution.
4. Log conflicts safely.
5. Update UI/report link display if paired with UI task.

Tests:

- same-store match;
- duplicate conflict;
- cross-store rejection;
- old row idempotency;
- permission visibility;
- Stage 1/2 regression.

Audit criteria:

- raw history unchanged;
- FK reversible;
- scope matches resolved GAP/task.

Handoff: enriched operation families, skipped rows, conflict counts, tests.

## TASK-PC2-005 Snapshot Filling

Role: Developer.

Goal: fill Product Core snapshots from approved current flows.

Input docs: package `TASK-PC2-005`.

Allowed/expected files:

- Product Core snapshot services/adapters;
- safe fixtures;
- tests.

Prohibited changes:

- demand/production formulas;
- unsupported sales/buyout/return semantics;
- fake WB auto promotion product rows;
- unapproved source endpoints.

Implementation steps:

1. Fill WB price snapshots.
2. Fill approved promotion snapshots.
3. Fill Ozon Elastic stock snapshots for selected product set.
4. Keep unsupported snapshot types foundation-only.
5. Update latest cache only after successful sync.

Tests:

- snapshot context validation;
- nullable fields;
- failed sync cache preservation;
- source-specific semantics;
- redaction.

Audit criteria:

- snapshot scope matches `GAP-CORE2-004` resolution or excludes blocked types;
- no secret leakage;
- no formulas added.

Handoff: filled snapshot types, foundation-only types, tests.

## TASK-PC2-006 Product Core Exports And Excel Boundary

Role: Developer.

Goal: implement or extend exports for CORE-2 listings, latest values, mapping and operation links.

Input docs: package `TASK-PC2-006`.

Allowed/expected files:

- Product Core export services/views/templates;
- file/audit integration if persisted exports are added;
- tests.

Prohibited changes:

- Excel import workflow;
- changing Stage 1 Excel templates/business rules;
- exporting hidden store data;
- exporting secrets/raw sensitive payload.

Implementation steps:

1. Add/extend export querysets and columns.
2. Apply object access and permission filtering before row materialization.
3. Redact JSON/latest values.
4. Audit persisted export generation/download where required.

Tests:

- permission/object access exports;
- column contract;
- redaction;
- no import side effects.

Audit criteria:

- Excel boundary preserved;
- no hidden counts/details leak;
- exports match spec.

Handoff: export list, sample headers, tests, file/audit behavior.

## TASK-PC2-007 Product Core UI Integration

Role: Frontend/UI developer.

Goal: expose CORE-2 sync, mapping, conflict, snapshot, operation-link and export behavior in server-rendered UI.

Input docs: package `TASK-PC2-007`.

Allowed/expected files:

- web views/forms/templates/urls/static for Product Core pages;
- focused UI tests.

Prohibited changes:

- future ERP working UI;
- mass vendorCode/offer_id edit UI;
- hidden auto-mapping;
- unapproved imported/draft variant page while `GAP-CORE2-001` is open.

Implementation steps:

1. Add sync status and source warnings.
2. Add conflicts/review pages and filters.
3. Add operation row link visibility.
4. Add snapshot/latest values display.
5. Add approved exports controls.

Tests:

- permissions and object access;
- UI rendering for statuses/errors;
- no future ERP operational pages;
- no secret in rendered HTML.

Audit criteria:

- UI matches `CORE_2_UI_UX_SPEC.md`;
- UX/functionality gaps are not guessed.

Handoff: routes/templates, screenshots or route smoke evidence, tests.

## TASK-PC2-008 Permissions, Audit, Techlog, Redaction

Role: Developer/security-focused agent.

Goal: implement CORE-2 permission gates, audit events, techlog events and secret redaction tests.

Input docs: package `TASK-PC2-008`.

Allowed/expected files:

- identity/access seeds/migrations if new permissions approved;
- audit/techlog catalogs and service calls;
- redaction helpers/tests.

Prohibited changes:

- weakening existing Stage 1/2 permissions;
- secret readback;
- techlog sensitive details with token/API key/Client-Id;
- hidden object access bypass.

Implementation steps:

1. Add or reuse permission codes.
2. Add audit actions and techlog events.
3. Enforce object access on linked rows/snapshots/exports.
4. Expand redaction tests.

Tests:

- permission matrix;
- audit/techlog creation;
- redaction guard;
- hidden store denial.

Audit criteria:

- no privilege regression;
- required audit/techlog events recorded safely;
- secret tests pass.

Handoff: permissions/actions/events added, tests, redaction evidence.

## TASK-PC2-009 Regression And Acceptance

Role: Tester.

Goal: run CORE-2 acceptance and regression evidence.

Input docs: package `TASK-PC2-009`.

Allowed/expected files:

- test reports under `docs/testing/` or `docs/reports/`;
- no product code changes.

Prohibited changes:

- fixing product code inside tester task unless separately assigned;
- changing expected results to pass tests.

Implementation steps:

1. Run CORE-2 unit/integration/UI/export/security tests.
2. Run Stage 1/2 regression groups.
3. Run Product Core regression groups.
4. Record limitations and defects.

Tests:

- as listed in `CORE_2_TEST_PLAN.md`.

Audit criteria:

- evidence is reproducible;
- failures classified;
- no hidden limitations.

Handoff: test report, commands, PASS/FAIL, defects.

## TASK-PC2-010 Documentation And Rollout Closeout

Role: Tech writer / release agent.

Goal: update documentation, runbook and release report after implementation/testing.

Input docs: package `TASK-PC2-010`.

Allowed/expected files:

- docs changed by implementation;
- release/test/audit reports;
- documentation map/status updates.

Prohibited changes:

- changing business rules without ADR/GAP;
- hiding open defects;
- editing source TZ.

Implementation steps:

1. Sync docs with actual implementation.
2. Update maps/status/reading packages.
3. Prepare release validation handoff.
4. Record open limitations and rollback notes.

Tests:

- documentation link/path checks;
- release report consistency with test evidence.

Audit criteria:

- docs match implemented behavior;
- audit trail and reports complete.

Handoff: changed docs, release readiness summary, remaining risks.
