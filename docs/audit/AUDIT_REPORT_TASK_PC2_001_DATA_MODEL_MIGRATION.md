# AUDIT_REPORT_TASK_PC2_001_DATA_MODEL_MIGRATION

Date: 2026-05-02
Role: Codex CLI auditor
Task: TASK-PC2-001 Data Model And Migration
Initial verdict: AUDIT FAIL
Recheck target: A-PC2-001-001 after developer fix and tester PASS
Current verdict: AUDIT PASS
Implementation accepted: yes

## Scope Audited

Input documents read:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-001`
- `docs/stages/stage-3-product-core/core-2/CORE_2_SCOPE.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_MODEL_AND_MIGRATION_PLAN.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_OPERATION_LINKING_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_MAPPING_RULES_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`
- `docs/testing/TEST_REPORT_TASK_PC2_001_DATA_MODEL_MIGRATION.md`
- current git diff for implementation

Audited implementation files:

- `apps/operations/models.py`
- `apps/operations/tests.py`
- `apps/operations/migrations/0011_operationdetailrow_marketplace_listing.py`
- `apps/product_core/models.py`
- `apps/product_core/tests.py`
- `apps/product_core/migrations/0004_productvariant_import_source_context_and_more.py`
- `docs/testing/TEST_REPORT_TASK_PC2_001_DATA_MODEL_MIGRATION.md`

## Recheck 2026-05-02 After A-PC2-001-001 Fix

Verdict: AUDIT PASS

Implementation accepted: yes.

### Recheck Scope

Read/verified:

- this original audit report and historical finding A-PC2-001-001;
- `docs/testing/TEST_REPORT_TASK_PC2_001_DATA_MODEL_MIGRATION.md` second retest PASS;
- current git diff and untracked migration/report files for `apps/product_core`, `apps/operations`, `docs/audit`, `docs/testing`;
- CORE-2 task/scoped requirements for `TASK-PC2-001`, model/migration plan, operation linking, mapping rules, ADR-0044, ADR-0045, `GAP-CORE2-001`, `GAP-CORE2-003`.

### A-PC2-001-001 Closure

A-PC2-001-001 is closed.

- `apps/product_core/models.py:220`-`235`: `ProductVariant.clean()` strips `internal_sku`, rejects blank/whitespace values when `review_state=imported_draft`, then applies the CORE-2 structured SKU validator.
- `apps/product_core/tests.py:181`-`199`: focused regression covers both `""` and `"   "` imported draft values.
- `apps/product_core/tests.py:154`-`163`: manual confirmed blank/whitespace SKU remains allowed and normalized to blank. This is accepted for `manual_confirmed`; CORE-2 strict auto-create validation applies to `imported_draft`, and the previous regression requirement preserved manual/legacy SKU behavior.

### Previous Positive Checks Reconfirmed

- Nullable FK: `apps/operations/models.py:892`-`899` adds `OperationDetailRow.marketplace_listing` with `null=True`, `blank=True`, `on_delete=PROTECT`, and an index. `sqlmigrate operations 0011` shows nullable FK SQL and `CREATE INDEX "operations_operationdetailrow_marketplace_listing_id_98eb0c22"`.
- Same-store/same-marketplace validation remains in `apps/operations/models.py:921`-`927`.
- Migrations remain non-destructive:
  - `apps/product_core/migrations/0004_productvariant_import_source_context_and_more.py` only adds `import_source_context`, `review_state`, and a `review_state` index.
  - `apps/operations/migrations/0011_operationdetailrow_marketplace_listing.py` only adds nullable FK `marketplace_listing`.
- `product_ref` immutability is preserved by the checked diff: no migration or model change rewrites `OperationDetailRow.product_ref`; focused test evidence still covers FK assignment preserving raw `product_ref`.
- Legacy `MarketplaceProduct` is not deleted, renamed, truncated, or replaced by this diff.
- No Stage 1/2 business logic, reason/result catalog, Excel/API calculation, web workflow, permissions, audit, or techlog code changes were found in the current diff outside the scoped model/migration/test files.

### Tester PASS Evidence Assessment

Tester PASS evidence is sufficient for this recheck:

- `git diff --check`: PASS.
- `manage.py check`: PASS.
- `manage.py makemigrations --check --dry-run`: PASS.
- `manage.py test apps.product_core apps.operations --verbosity=2`: PASS, 45 tests.
- previously impacted web tests: PASS.
- broader impacted Stage 1/2/Product Core regression suite: PASS, 154 tests.

The tester notes that explicit migration rollback was not rerun in the second retest. This is accepted as non-blocking for this fix because A-PC2-001-001 changed model validation only, the fresh test database applied `product_core.0004` and `operations.0011`, and auditor `sqlmigrate` inspection reconfirmed schema-only/non-destructive migrations.

### Auditor Commands Run For Recheck

```text
git diff --check
PASS

set -a; source .env.runtime; set +a; .venv/bin/python manage.py check
PASS: System check identified no issues (0 silenced).

set -a; source .env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
PASS: No changes detected.

set -a; source .env.runtime; set +a; .venv/bin/python manage.py test apps.product_core apps.operations --verbosity=2
PASS: Ran 45 tests, OK.

set -a; source .env.runtime; set +a; .venv/bin/python manage.py sqlmigrate operations 0011
PASS: nullable FK SQL includes FK constraint and FK index.

set -a; source .env.runtime; set +a; .venv/bin/python manage.py sqlmigrate product_core 0004
PASS: schema-only ProductVariant field/index SQL inspected.
```

### Remaining Findings

None.

### Final Recheck Verdict

AUDIT PASS. Implementation accepted: yes. A-PC2-001-001 is closed; D-PC2-001-REG-001 remains closed by tester evidence and auditor spot checks. No new gaps or spec-blocking questions were found.

## Original Findings From Initial Audit (Historical)

### Major: A-PC2-001-001 imported_draft allows blank internal_sku

`ProductVariant.clean()` calls `validate_core2_internal_sku()` when `review_state=imported_draft`, but the validator returns successfully for blank values:

- `apps/product_core/models.py:21` strips the value;
- `apps/product_core/models.py:23` returns when the stripped value is empty;
- `apps/product_core/models.py:223` uses that same validator for imported draft variants.

This means an imported/draft variant with `internal_sku=""` passes `full_clean()`. I verified this with a local Django shell check:

```text
blank imported_draft passes
```

This violates the CORE-2 requirement that imported/draft auto-created variants are based on a valid structured internal SKU article. Blank is not a structured SKU and is not a valid auto-create basis.

Tests cover valid structured examples and nonblank invalid examples such as `SKU-001`, but do not cover blank or whitespace-only `imported_draft` SKU:

- `apps/product_core/tests.py:154` covers nonblank invalid SKU rejection;
- no test asserts blank imported/draft SKU rejection.

Required fix:

- reject blank/whitespace-only `internal_sku` when `review_state=imported_draft`;
- add a focused regression test for blank/whitespace imported draft SKU;
- keep manual/legacy SKU behavior allowed for `manual_confirmed` as required by D-PC2-001-REG-001 retest.

## Original Positive Checks From Initial Audit

Scope is otherwise clean. Current implementation diff is limited to allowed model, migration, focused test and test report changes. I found no Stage 1/2 calculation code changes, no reason/result catalog changes, and no legacy `MarketplaceProduct` deletion.

`OperationDetailRow.marketplace_listing` satisfies the audited model contract:

- nullable and blank-compatible;
- `on_delete=PROTECT`;
- no uniqueness constraint;
- indexed by Django FK index; `sqlmigrate operations 0011` shows `CREATE INDEX "operations_operationdetailrow_marketplace_listing_id_98eb0c22"`;
- same store/cabinet and same marketplace validation is present in `OperationDetailRow.clean()`;
- `product_ref` is not rewritten by the migration or model change.

Migrations are schema-only/non-destructive for this task:

- `product_core.0004` adds `import_source_context`, `review_state`, and a `review_state` index;
- `operations.0011` adds nullable FK `marketplace_listing`;
- no data migration deletes or truncates `MarketplaceProduct`;
- no migration rewrites `OperationDetailRow.product_ref`.

D-PC2-001-REG-001 is closed by retest evidence:

- global strict field validator was removed;
- manual legacy SKU remains allowed in model validation;
- impacted web tests and broader impacted suite passed according to the test report.

## Original Commands Run

```text
git diff --check
PASS

set -a; source .env.runtime; set +a; .venv/bin/python manage.py check
PASS: System check identified no issues (0 silenced).

set -a; source .env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
PASS: No changes detected.

set -a; source .env.runtime; set +a; .venv/bin/python manage.py test apps.product_core apps.operations --verbosity=2
PASS: 43 tests, OK.

set -a; source .env.runtime; set +a; .venv/bin/python manage.py sqlmigrate operations 0011
PASS: nullable FK SQL includes FK constraint and index.

set -a; source .env.runtime; set +a; .venv/bin/python manage.py sqlmigrate product_core 0004
PASS: schema-only ProductVariant fields/index SQL inspected.
```

## Original Test Evidence Assessment

Sufficient:

- focused model tests for nullable FK, same store/marketplace validation, `PROTECT`, and `product_ref` preservation;
- focused ProductVariant tests for explicit review state, separation from `status`, valid structured SKU examples, nonblank invalid SKU rejection, and manual legacy SKU allowance;
- impacted suite evidence in test report;
- product_ref checksum evidence in test report;
- migration/check evidence in test report and auditor rerun.

Insufficient:

- no negative test for blank or whitespace-only `internal_sku` with `review_state=imported_draft`.

## Original Follow-ups

1. Fix A-PC2-001-001 and rerun focused ProductVariant tests plus `apps.product_core apps.operations`.
2. Keep D-PC2-001-REG-001 regression coverage: manual legacy SKU must remain allowed outside `imported_draft`.
3. Future auto-create service tasks must call model validation or an equivalent service-level validator before persisting imported/draft variants.
