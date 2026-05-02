# AUDIT_REPORT_TASK_PC_003_SYNC_SNAPSHOT.md

Task: TASK-PC-003 Sync Run And Snapshot Foundation
Date: 2026-05-01
Role: Stage 3 / Product Core auditor
Status: AUDIT PASS

## Scope

Audited files:

- `apps/product_core/models.py`
- `apps/product_core/services.py`
- `apps/product_core/migrations/0003_active_sync_run_guard.py`
- `apps/product_core/tests.py`

Read package/docs:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-003-listings-sync-foundation.md`
- `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- related ADR context: ADR-0039, ADR-0040

## Audit Findings

No blockers found.

Checklist:

- Duplicate active sync guard: PASS. `MarketplaceSyncRun` has a conditional unique constraint for active statuses `created`/`running`, and `start_marketplace_sync_run` checks under transaction with `select_for_update` and converts DB race `IntegrityError` to `DuplicateActiveSyncRun`.
- Failed sync preserves last successful cache: PASS. `fail_marketplace_sync_run` updates only sync run status/error metadata and techlog. It does not call `_apply_successful_sync_cache`, so `MarketplaceListing.last_values`, `last_sync_run` and `last_successful_sync_at` remain from the last successful run.
- Latest listing cache updates only on successful sync: PASS. Cache mutation is isolated in `_apply_successful_sync_cache`, called by `complete_marketplace_sync_run` after status becomes `completed_success` or `completed_with_warnings`.
- Snapshot operation/listing/sync context validation: PASS. Snapshot models validate listing/sync store and marketplace consistency, and operation store/marketplace consistency when operation is present. Service helpers only attach snapshots to active sync runs.
- Raw-safe secret redaction/guard: PASS. Snapshot `raw_safe`, sync run `summary`/`error_summary`, stock warehouse details and promotion constraints are guarded with `assert_no_secret_like_values`; tests cover service and direct model-save rejection.
- No new WB/Ozon API business flows/scheduling/calculation/upload changes in PC-003 scope: PASS. Audited PC-003 files add sync/snapshot foundation logic only; they do not add external API calls, mandatory scheduling, calculation rules or upload flows.

## Verification Notes

The audit takes into account reported local checks:

- `check` OK
- `makemigrations --check --dry-run` OK
- `git diff --check` OK
- product_core/marketplace_products/identity_access/audit/techlog/operations/web/discounts WB/Ozon regression run: 132 tests OK

Additional static audit confirmed that `apps/product_core/migrations/0003_active_sync_run_guard.py` adds `uniq_active_marketplace_sync_run` and the initial product_core migration does not already add that same constraint, so the PC-003 guard is not duplicated in the migration chain.

## Residual Risk

The worktree contains unrelated dirty/untracked files outside the audited PC-003 file list. They were not treated as PC-003 product-code changes in this audit.
