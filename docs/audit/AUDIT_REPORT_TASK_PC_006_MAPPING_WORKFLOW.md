# AUDIT_REPORT_TASK_PC_006_MAPPING_WORKFLOW.md

Task: TASK-PC-006 Mapping Workflow
Role: Stage 3 / Product Core auditor
Status: AUDIT PASS
Date: 2026-05-02

## Scope

Re-audit after the first `AUDIT FAIL` blocker `PC-006-001`.

Reviewed task package and required documents:

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-006-mapping-workflow.md`
- `docs/product/PRODUCT_CORE_SPEC.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- resolved `GAP-0023` in `docs/gaps/GAP_REGISTER.md`
- `ADR-0038` in `docs/adr/ADR_LOG.md`

Reviewed implementation files requested by orchestrator:

- `apps/web/views.py`
- `apps/product_core/services.py`
- `apps/web/tests.py`

No product code was changed during this re-audit.

## Blocking Findings

None.

## Re-Audit Notes

The previous blocker is closed.

- `apps/web/views.py` `leave_unmatched` now always calls `unmap_listing()` after permission and form validation, including when the listing is already `unmatched`.
- `apps/product_core/services.py` `unmap_listing()` routes through `record_product_mapping_change()`, which records `ProductMappingHistory` and `AuditRecord` for `ProductMappingHistory.MappingAction.UNMAP`.
- For an already-unmatched listing, the service keeps `internal_variant = None` and `mapping_status = unmatched`; no automatic mapping or candidate-based confirmation is introduced.
- Permission/object access remains enforced by the view query through `marketplace_listings_visible_to()` and by service-level `_assert_mapping_permission()` requiring store access, `marketplace_listing.map`/`marketplace_listing.unmap`, `product_core.view`, and `product_variant.view`.
- Candidate suggestions remain exact-only by `seller_article`, `barcode`, or external identifier tokens. They can mark `needs_review`/`conflict`, but they do not set `matched` or assign `internal_variant`.
- No historical `OperationDetailRow` rewrite was found in the reviewed mapping workflow.

Regression coverage was added in `apps/web/tests.py`:

- `test_leave_unmatched_records_history_and_audit_for_already_unmatched_listing` verifies explicit `leave_unmatched` on an already-unmatched listing writes `ProductMappingHistory`, writes `AuditRecord`, leaves `internal_variant` unchanged as `None`, and keeps `mapping_status = unmatched`.

## Checks

Implementer/orchestrator reported after the fix:

- `check` OK
- `makemigrations --check --dry-run` OK
- `git diff --check` OK
- tests `apps.web apps.product_core apps.identity_access apps.audit apps.operations`: 103 tests OK

Auditor local checks:

- `.venv/bin/python manage.py check` passed.
- `.venv/bin/python manage.py makemigrations --check --dry-run` reported `No changes detected`; Django also warned that local PostgreSQL authentication for user `promo_v2` failed while checking migration consistency.
- `git diff --check` passed.
- `.venv/bin/python manage.py test apps.web apps.product_core apps.identity_access apps.audit apps.operations --keepdb` found 103 tests but did not execute because local PostgreSQL authentication for user `promo_v2` failed.

## Verdict

`AUDIT PASS`.

TASK-PC-006 Mapping Workflow satisfies the re-audit scope: explicit `leave_unmatched` writes mapping history and audit, leaves status/internal variant unchanged for already-unmatched listings, preserves object access and permissions, and does not introduce automatic confirmed mapping.
