# TEST_REPORT_TASK_007

Дата: 2026-04-25
Роль: Тестировщик Codex CLI TASK-007 WB discounts Excel

## status

PASS WITH REMARKS

Поведенческие сценарии WB TASK-007 пройдены на синтетических edge-case данных и существующем Django test suite. Замечания не являются дефектами TASK-007: формальная приёмка на реальных customer files остаётся заблокирована acceptance artifact gate по GAP-0008/ADR-0013, потому что реальные WB/Ozon файлы, checksums, результаты старой программы и expected results не переданы.

## scenario matrix

| # | Scenario | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Successful check with valid price/promo files creates check result, no output workbook. | pass | `test_check_writes_no_output_and_persists_closed_reason_codes`: status `completed_no_errors`, output count 0, snapshots 3, code `wb_valid_calculated`. |
| 2 | Successful process from actual check creates output workbook and changes only `Новая скидка`. | pass | `test_process_reuses_actual_check_and_writes_only_new_discount_column`: actual check reused, process `completed_success`, output workbook created, source columns/formula-like cell unchanged, only `Новая скидка` updated. |
| 3 | Input composition errors complete check with WB errors, not `interrupted_failed`. | pass | `test_business_validation_errors_complete_check_with_errors_not_interrupted`: missing files, too many promo files, wrong extension and size limit complete as `completed_with_errors` with WB detail codes and no output. |
| 4 | Corrupt workbook maps to `wb_invalid_workbook`. | pass | `test_corrupt_xlsx_is_invalid_workbook_business_error`: corrupt `.xlsx` returns row error `wb_invalid_workbook`, `problem_field=price:workbook`. |
| 5 | Missing required columns maps to `wb_missing_required_column`. | pass | `test_business_validation_errors_complete_check_with_errors_not_interrupted`: missing price column returns `wb_missing_required_column`. |
| 6 | Duplicate price article maps to `wb_duplicate_price_article` and blocks process. | pass | Duplicate price article is covered in `test_business_validation_errors_complete_check_with_errors_not_interrupted`; process block for check errors is covered by `test_out_of_range_is_row_error_and_blocks_process` and operation service rule uses only successful checks with `error_count=0`. |
| 7 | Missing/invalid current price maps to `wb_invalid_current_price`. | pass | `test_non_finite_numeric_values_are_invalid_not_interruptions`: `NaN` current price creates `wb_invalid_current_price`; price validation also treats missing/non-positive values as invalid current price. |
| 8 | Promo invalid rows become `wb_invalid_promo_row` and valid promo rows still aggregate. | pass | Temporary runner `WbTask007ExtraScenarios.test_invalid_promo_rows_do_not_block_valid_promo_aggregation`: 3 invalid promo rows persisted as `wb_invalid_promo_row`; valid rows for article `123` aggregated to `min_discount=60`, `max_plan_price=500`, `final_discount=50`. |
| 9 | No promo item uses fallback 55 and code `wb_no_promo_item`. | pass | `test_normalization_decimal_arithmetic_ceil_and_hybrid_order` and `test_non_finite_numeric_values_are_invalid_not_interruptions`: no-promo row final discount 55, code `wb_no_promo_item`. |
| 10 | Over threshold branch uses fallback 55 and code `wb_over_threshold`. | pass | `test_normalization_decimal_arithmetic_ceil_and_hybrid_order`: row final discount 55 with `wb_over_threshold`. |
| 11 | Normal calculated branch uses Decimal/ceil expected value and code `wb_valid_calculated`. | pass | `test_normalization_decimal_arithmetic_ceil_and_hybrid_order`: Decimal/ceil case produces 50 and `wb_valid_calculated`; `parse_decimal` rejects non-numeric values. |
| 12 | Out-of-range final discount gives `wb_discount_out_of_range` and process blocked. | pass | `test_out_of_range_is_row_error_and_blocks_process`: check `completed_with_errors`, one `wb_discount_out_of_range`, `press_wb_process` raises `ValidationError`, no process operation created. |
| 13 | NaN/infinity numeric values invalid. | pass | `test_non_finite_numeric_values_are_invalid_not_interruptions`: `Decimal("NaN")`, `"Infinity"`, `"-Infinity"` rejected; price row invalid and promo rows ignored with warning details. |
| 14 | Store override vs system defaults behavior if feasible. | pass | `test_seeded_wb_system_parameter_defaults_are_used_in_snapshot` and `test_store_parameter_values_override_defaults_and_change_actuality_basis`: system defaults 70/55/55 snapshotted; store override changes process value to 40 and source to `store`, causing a new actual check. |
| 15 | No Ozon/API scenario is available. | pass | Code inspection: `apps/discounts/ozon_excel` remains placeholder for TASK-008; TASK-007 explicitly forbids API mode; no Ozon/API scenario is present in WB module. |

## commands run/results

| Command | Result |
| --- | --- |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.discounts.wb_excel` | PASS: `Ran 10 tests in 15.242s`, `OK`; PostgreSQL test database was created and destroyed. |
| Temporary runner for mixed valid/invalid promo aggregation via Django test DB | PASS: `Ran 1 test in 1.303s`, `OK`; temporary module was created under `mktemp` and removed after the run. |
| `rg -n "Ozon|ozon|API|api" apps/discounts/wb_excel apps/discounts/ozon_excel docs/tasks/implementation/stage-1/TASK-007-wb-discounts-excel.md` | PASS for inspection: Ozon module is placeholder for TASK-008; TASK-007 contains API prohibition; no Ozon/API scenario in WB module. |

## defects found

No TASK-007 product defects found.

Severity table:

| Severity | Count | Notes |
| --- | --- | --- |
| Blocker | 0 | None. |
| Major | 0 | None. |
| Minor | 0 | None. |

## environment limitations

- `/home/pavel/projects/promo_v2` is not a git repository, so git-based scope verification was unavailable.
- Formal acceptance on real customer workbooks was not executed. Per GAP-0008/ADR-0013 and `docs/testing/TEST_PROTOCOL.md`, synthetic edge-case files do not replace real files, checksums, old-program results or expected row-level results.
- PostgreSQL credentials from customer input (`postgres` / `postgres`) worked for `manage.py check` and Django test database creation.
- No Ozon/API behavioral scenario exists in TASK-007 scope; Ozon Excel is TASK-008.

## old-program reference usage

Not used. No behavioral discrepancy or ambiguous business-logic result appeared during this test run. Approved TASK-007 documentation and synthetic edge-case checks were sufficient; the old program remains only a control source for future real-file comparisons.

## recommendation

Можно переходить к TASK-008. TASK-007 behavioral testing has PASS WITH REMARKS; the remaining remark is the project-level acceptance artifact gate for real customer files, not a blocker for starting Ozon Excel implementation.
