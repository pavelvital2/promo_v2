# TEST_REPORT_TASK_PC2_001_DATA_MODEL_MIGRATION

Date: 2026-05-02
Role: Codex CLI tester
Retest target: TASK-PC2-001 second retest after audit bugfix A-PC2-001-001
Verdict: PASS

Production code was not changed by this retest run. Only this report was updated.

## Scope

Retested TASK-PC2-001 Data Model And Migration after audit bugfix A-PC2-001-001. This is the second retest after the auditor found that `imported_draft` variants allowed blank or whitespace-only `internal_sku`.

Inputs checked:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- previous `docs/testing/TEST_REPORT_TASK_PC2_001_DATA_MODEL_MIGRATION.md`
- `docs/audit/AUDIT_REPORT_TASK_PC2_001_DATA_MODEL_MIGRATION.md`
- current git diff for `apps/product_core/models.py`, `apps/product_core/tests.py`, and migrations

Bugfix summary was confirmed in the current diff:

- strict CORE-2 SKU validator is no longer attached as a global `internal_sku` field validator;
- strict validation is called from `ProductVariant.clean()` only when `review_state=imported_draft`;
- `ProductVariant.clean()` now rejects blank or whitespace-only `internal_sku` for `review_state=imported_draft`;
- manual legacy SKU remains allowed by model validation;
- manual blank/whitespace `internal_sku` remains allowed for `review_state=manual_confirmed`, with whitespace normalized to blank;
- `product_core.0004` no longer contains metadata-only validator `AlterField`.

## Commands And Results

| Command | Result |
| --- | --- |
| `git diff --check` | PASS. No whitespace errors. |
| `set -a; source .env.runtime; set +a; .venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `set -a; source .env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run` | PASS: `No changes detected`. |
| `set -a; source .env.runtime; set +a; .venv/bin/python manage.py test apps.product_core apps.operations --verbosity=2` | PASS: 45 tests, OK, 26.738s. Fresh test DB applied `product_core.0004` and `operations.0011`. |
| `set -a; source .env.runtime; set +a; .venv/bin/python manage.py test apps.web.tests.HomeSmokeTests.test_internal_product_and_variant_create_update_archive_flows apps.web.tests.HomeSmokeTests.test_mapping_workflow_conflict_unmap_and_create_product_variant --verbosity=2` | PASS: 2 tests, OK, 2.784s. These were the previously impacted web tests. |
| `set -a; source .env.runtime; set +a; .venv/bin/python manage.py test apps.web apps.marketplace_products apps.discounts.wb_excel apps.discounts.ozon_excel apps.discounts.wb_api apps.discounts.ozon_api --verbosity=2` | PASS: 154 tests, OK, 196.279s. |

## Inspection Results

`OperationDetailRow.marketplace_listing`:

- nullable and blank-compatible in model and migration;
- `on_delete=PROTECT` in model/migration;
- no uniqueness constraint added;
- focused tests cover nullable FK, same store/marketplace validation, `PROTECT`, and `product_ref` preservation.

`ProductVariant` lifecycle and validator:

- `review_state` choices include `manual_confirmed`, `imported_draft`, `needs_review`;
- existing `status` remains separate;
- `import_source_context` JSON field is present and checked for secret-like values in `clean()`;
- `review_state` index is present;
- migration is schema-only and does not rewrite `internal_sku` or existing rows;
- strict CORE-2 SKU validation is scoped to `review_state=imported_draft`;
- manual legacy SKU path is covered by `test_manual_confirmed_variant_allows_legacy_internal_sku`.
- `imported_draft` blank and whitespace-only SKU rejection is covered by `test_imported_draft_variant_rejects_blank_internal_sku`.
- manual blank/whitespace SKU allowance is covered by `test_manual_confirmed_variant_allows_blank_internal_sku`.

## Defect Retest

### A-PC2-001-001: CLOSED

The audit defect is closed.

Evidence:

- current model logic rejects blank or whitespace-only `internal_sku` before calling the structured CORE-2 SKU validator when `review_state=imported_draft`;
- focused regression test covers both `""` and `"   "` imported draft values and passed;
- manual confirmed blank/whitespace behavior remains intentionally allowed and passed;
- focused `apps.product_core apps.operations` suite, previously impacted web tests, and broader impacted suite all passed.

### D-PC2-001-REG-001: CLOSED

The regression reported in the previous test run is closed.

Evidence:

- previously failing web tests now pass in focused rerun;
- full impacted regression suite now passes with 154 tests OK;
- manual UI-style legacy SKU values are no longer blocked by global field validation.

## Notes

- The previously recorded runtime `migrate --noinput` and `product_ref` checksum were not rerun in this second retest because the audit bugfix was scoped to `ProductVariant.clean()` and focused ProductVariant tests. Fresh Django test DB creation still applied `product_core.0004` and `operations.0011` successfully in all relevant test runs.
- One initial parallel attempt to run the two web smoke tests overlapped with creation of the same Django test database by the focused suite and exited with `database "test_promo_v2" already exists`. The same web command was rerun sequentially and passed.
- No explicit migration rollback was run.

## Final Verdict

PASS. Required checks and impacted regression suites passed. A-PC2-001-001 is closed. D-PC2-001-REG-001 remains closed.
