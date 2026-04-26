# AUDIT_REPORT_TASK_008

## status

PASS WITH REMARKS

Remarks are limited to audit/formalization constraints: this was an audit round, not tester acceptance; the local default PostgreSQL database `promo_v2` is absent; formal customer-file acceptance remains gated by GAP-0008/ADR-0013 artifacts.

## checked scope

- Task: `docs/tasks/implementation/stage-1/TASK-008-ozon-discounts-excel.md`.
- Specification: `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md`.
- Operation specification: `docs/product/OPERATIONS_SPEC.md`.
- File contour: `docs/architecture/FILE_CONTOUR.md`.
- Permissions: `docs/product/PERMISSIONS_MATRIX.md`.
- Implementation: `apps/discounts/ozon_excel/services.py`, `apps/discounts/ozon_excel/tests.py`.
- Operation integration: `apps/operations/services.py` for check/process flow and actual check basis only.
- File integration: `apps/files/models.py`, `apps/files/services.py` for `FileVersion`/output review only.
- Related closed decisions checked: GAP-0008 and ADR-0013.
- Relevant source TZ sections explicitly named by TASK-008: §12, §16, §17, §23, §24, §27.

## audit method

- Read required root/project instructions and task-scoped package.
- Compared TASK-008 implementation against approved Ozon Excel spec, operations check/process model, file contour and permissions matrix.
- Inspected Ozon parser/calculation/output code for the exact `.xlsx` input, sheet name, row start, column letters J/K/L/O/P/R, numeric normalization, seven-rule order, check/process split and K/L-only output.
- Inspected operation shell integration for actual successful check basis, automatic check creation, output file linkage and parameter snapshot behavior.
- Inspected file service/model integration for output `FileVersion` creation and scenario/marketplace isolation.
- Ran only the requested PostgreSQL sanity commands; no old-program comparison or formal customer-file acceptance was performed.

## findings blocker/major/minor

### Blocker

None found.

### Major

None found.

### Minor

- Ozon reason/result codes are fixed by the Ozon service and covered by tests, but not centrally validated in `OperationDetailRow` the same way WB codes are. Evidence: Ozon service emits only the seven approved codes in `apps/discounts/ozon_excel/services.py:117` and `apps/discounts/ozon_excel/services.py:191`; tests assert all seven in `apps/discounts/ozon_excel/tests.py:139`. However the operation model has a closed `WB_REASON_CODES` set only in `apps/operations/models.py:160`, and `OperationDetailRow.clean()` validates only `wb_` prefixes in `apps/operations/models.py:748`. This does not break observed TASK-008 behavior, but it is weaker than the fixed-system-dictionary requirement from TZ §23.1 for Ozon reason/result codes.

## conformity notes

- Input composition matches spec: exactly one `.xlsx` is enforced in `apps/discounts/ozon_excel/services.py:161`; the required sheet `Товары и цены` is checked in `apps/discounts/ozon_excel/services.py:150`; required columns J/K/L/O/P/R are constants in `apps/discounts/ozon_excel/services.py:38` and checked by letter/position through `apps/discounts/ozon_excel/services.py:156`; data rows are read from row 4 in `apps/discounts/ozon_excel/services.py:263`.
- Numeric normalization treats nonnumeric/non-finite values as missing and avoids float fallbacks in calculation: `parse_decimal()` returns `None` for invalid/non-finite input in `apps/discounts/ozon_excel/services.py:102`; tests cover nonnumeric and `NaN` in `apps/discounts/ozon_excel/tests.py:139`.
- All seven Ozon decision rules are implemented in the approved order in `apps/discounts/ozon_excel/services.py:191`, and tests assert the ordered outcomes in `apps/discounts/ozon_excel/tests.py:139`.
- Check creates persisted summary/detail/result through `_check_executor()` and `run_check_sync()` in `apps/discounts/ozon_excel/services.py:365` and `apps/operations/services.py:586`; check uses `read_only=True` and creates no output workbook.
- Process uses the operation shell's actual successful check basis in `apps/operations/services.py:210`, `apps/operations/services.py:234`, and `apps/operations/services.py:610`; Ozon process delegates through `press_process_sync()` in `apps/discounts/ozon_excel/services.py:489`.
- Process output writes only K/L in `apps/discounts/ozon_excel/services.py:432`; K is `Да` or blank and L is `Decimal` or blank, with no zero substituted for blank.
- Workbook structure and other cells are not intentionally modified; tests compare source/output cells outside K/L in `apps/discounts/ozon_excel/tests.py:200`.
- Ozon has no WB-like user parameters: both check/process pass `parameters=[]` in `apps/discounts/ozon_excel/services.py:469` and `apps/discounts/ozon_excel/services.py:489`; tests assert no parameter snapshots in `apps/discounts/ozon_excel/tests.py:176`.
- No separate percent-discount result and no Ozon API mode were found in the audited Ozon implementation.
- File integration creates a new output `FileVersion` using the Ozon scenario and operation/run refs in `apps/discounts/ozon_excel/services.py:447`; file version metadata/storage behavior remains delegated to TASK-004 services in `apps/files/services.py:144`.
- No WB regression or Ozon/WB business-logic mixing was found in the audited TASK-008 scope.
- No functional/UX/spec gap was silently decided by the implementation in the audited files.

## PostgreSQL commands/results

Commands were run with `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres`.

| Command | Result |
| --- | --- |
| `.venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `.venv/bin/python manage.py makemigrations --check --dry-run` | PASS for migration drift: `No changes detected`. Django emitted a PostgreSQL warning because database `promo_v2` does not exist locally. |
| `.venv/bin/python manage.py test apps.discounts.ozon_excel` | PASS: 9 tests ran successfully; PostgreSQL test database was created and destroyed. |

## environment limitations

- Working directory `/home/pavel/projects/promo_v2` is not a git repository, so git diff/status based scope verification was unavailable.
- Local PostgreSQL credentials were usable for Django sanity/test execution, but the default database `promo_v2` is absent; this produced the migration-history warning during `makemigrations --check --dry-run`.
- This was an implementation audit, not a separate tester acceptance run.
- Formal acceptance with real customer Ozon files remains blocked by the GAP-0008/ADR-0013 artifact gate until real files, checksums, old-program results and expected results are provided.

## old-program reference usage

Not used. No approved-spec/business-logic discrepancy was found that required checking `https://github.com/pavelvital2/promo_WB_Ozon`; the Ozon specification and explicitly named TZ sections were sufficient for this audit.

## decision

TASK-008 accepted by audit with remarks.

## recommendation

Assign a separate tester next for Ozon check/process acceptance. The tester should keep formal customer-file comparison gated until GAP-0008/ADR-0013 artifacts are available.
