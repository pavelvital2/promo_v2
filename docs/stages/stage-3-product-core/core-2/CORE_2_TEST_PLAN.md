# CORE_2_TEST_PLAN.md

Статус: исполнительная проектная документация CORE-2, обновлена после AUDIT PASS по решениям заказчика; готова к follow-up audit/recheck.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§7.9, §11.12, §14-§15.

## Назначение

Define mandatory tests for CORE-2 implementation tasks and release validation.

## Unit Tests

- normalized article exact comparison;
- structured internal SKU validator for `nash`/`chev` patch/chevron examples and invalid formats;
- blank/duplicate article behavior;
- no fuzzy/title/image matching;
- listing upsert idempotency by marketplace/store/external primary id;
- sync status transitions;
- snapshot creation context validation;
- failed sync preserves latest cache;
- operation row FK deterministic match/reject;
- redaction guard for sync summaries, snapshots and exports.

## Integration Tests

- WB prices source -> listing -> price snapshot -> latest cache;
- WB regular promotion product row -> promotion snapshot;
- WB auto promotion without nomenclatures -> no fabricated product snapshot;
- Ozon Elastic action product set -> listing/promotion snapshot;
- Ozon product info/stocks -> stock snapshot for selected action set;
- mapping candidate status from exact normalized article;
- API valid article auto-links existing active variant;
- API valid article auto-creates imported/draft product/variant when absent;
- invalid/non-unified article creates listing only;
- external mapping table preview/diff/conflict/apply with explicit confirmation;
- operation detail row link visible with permissions and hidden without access.

## Migration Tests

- nullable FK schema is applied;
- old rows remain valid with null FK;
- FK backfill idempotent;
- FK backfill conflict rows remain unchanged;
- rollback/clear FK leaves `product_ref` intact;
- pre/post row count plus checksum/hash over `(id, product_ref)` is preserved for old rows;
- `MarketplaceProduct` row counts unchanged;
- no pending model/migration drift after implementation.

## Permissions Tests

- `marketplace_listing.sync` required to start sync;
- `marketplace_listing.view` required for listing card/link;
- `marketplace_listing.export` required for export rows;
- `marketplace_snapshot.view` required for latest snapshot export;
- mapping/unmapping requires mapping permission and store access;
- hidden store counts do not leak through internal product exports;
- operation row FK link hidden when listing object access is missing.

## UI Tests

- listing sync status and errors render safely;
- unmatched/needs_review/conflict filters;
- mapping review page shows exact candidate basis only;
- imported/draft variants page labels review state correctly and does not show drafts as manually confirmed products;
- invalid/non-unified listing actions show `visual_external`, mapping table and manual mapping where permitted;
- mapping table preview shows diff/conflicts before apply;
- operation detail row link behavior;
- snapshot latest values and technical raw-safe collapse/gating;
- future ERP blocks hidden or disabled/planned;
- no CORE-2 marketplace card-field write UI, including vendorCode/offer_id changes.

## Export Tests

- row filtering by store/object access;
- columns match spec;
- latest values require snapshot permission;
- JSON fields redacted;
- no secrets in CSV/XLSX/file output;
- Excel exports do not trigger imports or mappings.

## API Mock Tests

- WB pagination success/partial/failure;
- WB rate-limit/backoff;
- Ozon ADR-0034 read retry behavior;
- Ozon schema mismatch;
- no endpoint calls without current docs/code approval or endpoint-specific official read-only evidence;
- official-docs evidence and fixtures for any added read-only catalog/listing source;
- impossible duplicate external article/data-integrity handling;
- no write endpoints in sync tasks;
- token/header redaction in request/response snapshots.

## Regression Tests

CORE-2 release cannot pass without:

- Stage 1 WB Excel regression;
- Stage 1 Ozon Excel regression;
- Stage 2.1 WB API regression;
- Stage 2.2 Ozon Elastic regression;
- Product Core UI regression;
- Product Core permissions regression;
- Product Core exports regression;
- legacy `MarketplaceProduct` compatibility regression;
- operation immutability regression.

## Security / Secret Tests

Secret-like values must be rejected or redacted in:

- sync summaries;
- snapshot `raw_safe`;
- listing `last_values`;
- operation summary/details;
- audit records;
- techlog records;
- exports/files;
- UI pages;
- test/release reports.

## Acceptance Evidence

Each implementation task handoff must list:

- exact commands run;
- tests passing/failing;
- fixtures/mocks used;
- regression groups affected;
- open defects;
- resolved GAP/ADR decision references and remaining implementation gates;
- screenshots/browser smoke evidence for UI-facing tasks where required by auditor.
