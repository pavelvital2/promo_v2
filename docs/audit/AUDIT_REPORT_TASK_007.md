# AUDIT_REPORT_TASK_007

## status

FAIL

## checked scope

- Task: `docs/tasks/implementation/stage-1/TASK-007-wb-discounts-excel.md`.
- Specifications: `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`, `docs/product/OPERATIONS_SPEC.md`, `docs/architecture/FILE_CONTOUR.md`, `docs/product/PERMISSIONS_MATRIX.md`, WB parameter parts of `docs/architecture/DATA_MODEL.md`.
- Implementation: `apps/discounts/wb_excel/**`, `apps/platform_settings/**`, integration points in `apps/operations/**` and `apps/files/**`.
- Related decisions checked: ADR-0009, ADR-0010, ADR-0011, ADR-0013; GAP-0002, GAP-0003, GAP-0004, GAP-0008.

## audit method

- Static audit of WB parsing, validation, normalization, Decimal calculation, hybrid rule order, parameter cascade, operation shell integration and output workbook writing.
- Cross-check against approved WB spec and operations/file contour requirements.
- Sanity commands only; this report is not a tester acceptance result.

## findings

### blocker

1. Business validation errors for input composition and price workbook validity are converted into `interrupted_failed` instead of a completed check with closed WB error codes/detail rows.
   - Spec requires Check WB to validate file composition/workbooks, form summary/detail audit, create no output workbook, and critical input/workbook errors must be represented as business errors. Operations spec reserves `interrupted_failed` for application/server/DB/storage failures.
   - `run_wb_check()` creates the check operation before input validation and then delegates to `run_check_sync()`; `calculate()` raises `ValidationError` from `validate_input_file_set()` for missing price, zero/too many promo files, wrong extension and size limits. `run_check_sync()` catches any exception, marks the operation `interrupted_failed`, and re-raises.
   - Price workbook open/format errors follow the same path: `_read_price_rows()` calls `_load_first_sheet()` without converting the failure into `wb_invalid_workbook` detail rows.
   - References: `apps/discounts/wb_excel/services.py:361`, `apps/discounts/wb_excel/services.py:455`, `apps/discounts/wb_excel/services.py:199`, `apps/discounts/wb_excel/services.py:703`, `apps/operations/services.py:586`.
   - Impact: items 1, 2, 7 and 8 of the audit checklist are not fully satisfied for negative input cases; TASK-007 cannot be accepted.

### major

1. Corrupt `.xlsx` handling is incomplete.
   - `_load_first_sheet()` catches `OSError`, `InvalidFileException` and `ValueError`, but not common ZIP/openpyxl failures such as `zipfile.BadZipFile`. Promo workbook code catches only `ValidationError`, so such files can escape the WB error-code path and become system interruption.
   - References: `apps/discounts/wb_excel/services.py:165`, `apps/discounts/wb_excel/services.py:173`, `apps/discounts/wb_excel/services.py:265`.

2. Numeric normalization accepts non-finite Decimal literals as valid values.
   - `parse_decimal()` returns `Decimal("NaN")` / infinity values instead of treating them as absent/non-numeric. Later comparisons or arithmetic can raise and again interrupt the operation instead of producing row-level validation errors.
   - References: `apps/discounts/wb_excel/services.py:147`, `apps/discounts/wb_excel/services.py:155`, `apps/discounts/wb_excel/services.py:227`, `apps/discounts/wb_excel/services.py:473`.

### minor

1. WB system defaults are implemented as code fallback, not seeded `SystemParameterValue` rows.
   - Effective calculation uses approved 70/55/55 and snapshots source as `system`, and store override works. However `apps/platform_settings/migrations/0001_initial.py` creates parameter tables without seeding the approved system values/definitions, so the settings data contour is only partially represented in DB.
   - References: `apps/discounts/wb_excel/services.py:51`, `apps/discounts/wb_excel/services.py:405`, `apps/discounts/wb_excel/services.py:419`, `apps/platform_settings/migrations/0001_initial.py:18`.

## conforming observations

- Required WB columns are checked for price and promo workbooks.
- The first sheet is used via `workbook[workbook.sheetnames[0]]`.
- Article normalization follows trim/string/`.0` suffix removal.
- Final calculation uses `Decimal` operations and `ROUND_CEILING`; no `float()` usage was found in WB final calculation.
- Aggregation uses min promo discount and max promo plan price for valid promo rows.
- Hybrid order in normal calculated rows matches spec: no promo first, then threshold fallback, then calculated result.
- Closed WB reason/result codes are enforced in `OperationDetailRow.clean()`.
- Check path creates no output workbook in covered successful tests.
- Process writes only the `Новая скидка` column and creates an output `FileVersion` in covered successful tests.
- No Ozon calculation/API/UI overreach was found in TASK-007 implementation scope.
- No new functionality/UX gap was silently decided in the audited WB service code; implementation defects above are enough to return the task to developer.

## PostgreSQL run result

- Commands were run with `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres`.
- `manage.py check`: passed.
- `manage.py makemigrations --check --dry-run`: no model changes detected, but Django emitted a PostgreSQL warning: database `promo_v2` does not exist.
- `manage.py test apps.discounts.wb_excel`: PostgreSQL test database was created/destroyed successfully; credentials have enough permission for the Django test run.

## sanity commands/results

- `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check` -> PASS, `System check identified no issues`.
- `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py makemigrations --check --dry-run` -> PASS for migration drift, `No changes detected`; environment warning about missing database `promo_v2`.
- `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.discounts.wb_excel` -> PASS, 6 tests OK.

## environment limitations

- Working directory is not a git repository, so git diff/status based scope verification was unavailable.
- Default PostgreSQL database `promo_v2` is absent in the local environment; only Django system check, migration dry-run metadata check and temporary test database run were verified.
- Formal customer-file acceptance remains blocked by GAP-0008/ADR-0013 artifact gate until real WB/Ozon files, checksums and expected results are provided.

## decision

TASK-007 is not accepted. Return to developer.

## recommendation

- Fix business validation/error-code handling before tester handoff.
- After developer fixes and re-audit, assign a separate tester for WB check/process acceptance, including artifact-gated customer-file comparison when customer files become available.
