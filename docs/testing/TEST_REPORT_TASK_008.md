# TEST_REPORT_TASK_008

Дата: 2026-04-25
Роль: Тестировщик Codex CLI TASK-008 Ozon discounts Excel

## status

PASS WITH REMARKS

Поведенческие сценарии Ozon TASK-008 пройдены на синтетических edge-case данных и существующем Django test suite. Post-acceptance update 2026-04-26: прежнее замечание по отсутствующим real customer artifacts закрыто для `WB-REAL-001` / `OZ-REAL-001`; checksums, результаты старой программы и expected results зарегистрированы в `docs/testing/CONTROL_FILE_REGISTRY.md`.

## scenario matrix

| # | Scenario | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Valid check reads sheet `Товары и цены` from row 4 and creates result without output workbook. | pass | `test_check_writes_no_output_and_stores_no_parameters`: check `completed_no_errors`, detail row 4 has `use_max_boost_price`, output count 0, source K/L unchanged. |
| 2 | Process creates output workbook and changes only K/L. | pass | `test_process_reuses_actual_check_and_writes_only_k_l`: actual check reused, process `completed_success`, output workbook created, all cells except data-row K/L match source. |
| 3 | Rule 1 `missing_min_price`: K/L blank. | pass | `test_decision_rules_exact_order_and_normalization` maps row 4 to `missing_min_price`; `test_process_reuses_actual_check_and_writes_only_k_l` verifies output `K4=None`, `L4=None`. |
| 4 | Rule 2 `no_stock`: R missing or <=0 -> K/L blank. | pass | Row 5 in `test_decision_rules_exact_order_and_normalization` maps R=0 to `no_stock`; process writes only participating rows and leaves skipped rows blank. |
| 5 | Rule 3 `no_boost_prices`: O/P missing -> K/L blank. | pass | Row 6 in `test_decision_rules_exact_order_and_normalization` maps to `no_boost_prices`; skipped rows have blank K/L output behavior. |
| 6 | Rule 4 `use_max_boost_price`: P>=J -> K=`Да`, L=P numeric. | pass | Row 7 maps to `use_max_boost_price`; process output has `K7="Да"`, `L7=120`. |
| 7 | Rule 5 `use_min_price`: P<J and O>=J -> K=`Да`, L=J numeric. | pass | Row 8 maps to `use_min_price`; process output has `K8="Да"`, `L8=100`. |
| 8 | Rule 6 `below_min_price_threshold`: O<J -> K/L blank. | pass | Row 9 maps to `below_min_price_threshold`; process output has `K9=None`, `L9=None`. |
| 9 | Rule 7 `insufficient_ozon_input_data` fallback -> K/L blank. | pass | Row 10 maps to `insufficient_ozon_input_data`; skipped-row output behavior is covered by K/L blank assertions and K/L-only write loop. |
| 10 | Missing sheet / missing required columns produce business check errors, not system interruption. | pass | `test_business_validation_errors_complete_check_with_errors`: missing sheet and missing required column complete as `completed_with_errors`, create detail rows, no output workbook. |
| 11 | Blank cells remain blank, not zero/text surrogate. | pass | Output assertions use `None` for blank K/L cells; numeric L assertions are `120` and `100`, not text. |
| 12 | No Ozon user parameters/API/percent discount scenario exists. | pass | `test_check_writes_no_output_and_stores_no_parameters` asserts zero parameter snapshots; `press_ozon_process` passes `parameters=[]`; code search found no Ozon API or percent-discount implementation in Ozon module. |
| 13 | Central Ozon reason code validation rejects unapproved code if feasible through existing tests. | pass | `apps.operations.tests.OperationsShellTests.test_ozon_detail_reason_codes_are_centrally_validated` passed and rejects `unapproved_ozon_code`. |

## commands run/results

| Command | Result |
| --- | --- |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.discounts.ozon_excel` | PASS: `Ran 9 tests in 15.705s`, `OK`; PostgreSQL test database was created and destroyed. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.operations.tests.OperationModelTask008Tests.test_ozon_detail_reason_codes_are_centrally_validated` | INVALID TEST PATH: Django returned `AttributeError` because the class name was wrong; this was a tester command mistake, not a product failure. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.operations.tests.OperationsShellTests.test_ozon_detail_reason_codes_are_centrally_validated` | PASS: `Ran 1 test in 1.086s`, `OK`; PostgreSQL test database was created and destroyed. |
| `rg -n "ozon.*(parameter\|percent\|процент\|api)\|OZON.*(PARAM\|API\|PERCENT)\|parameter_snapshots\|mode=\"api\"\|discount_percent\|percent_discount" apps docs/product docs/tasks/implementation/stage-1/TASK-008-ozon-discounts-excel.md docs/audit/AUDIT_REPORT_TASK_008_ROUND_2.md -i` | PASS for inspection: no Ozon API/percent/user-parameter implementation found in Ozon module; matching parameter code is WB/general operation code or documentation prohibition. |

## defects found

No TASK-008 product defects found.

Severity table:

| Severity | Count | Notes |
| --- | --- | --- |
| Blocker | 0 | None. |
| Major | 0 | None. |
| Minor | 0 | None. |

## environment limitations

- `/home/pavel/projects/promo_v2` is not a git repository, so git-based scope verification was unavailable.
- Formal acceptance on real customer Ozon workbooks was not executed. Per `docs/testing/TEST_PROTOCOL.md`, synthetic edge-case files do not replace real files, checksums, old-program results or expected row-level results.
- PostgreSQL credentials from customer input (`postgres` / `postgres`) worked for `manage.py check` and Django test database creation.
- The scenario evidence is based on existing Django tests and code inspection. No temporary scenario runner was needed.

## old-program reference usage

Not used. No behavioral discrepancy or ambiguous business-logic result appeared during this test run. Approved TASK-008 documentation and existing edge-case tests were sufficient; the old program remains only a control source for future real-file comparisons.

## recommendation

Можно переходить к TASK-009. TASK-008 behavioral testing has PASS WITH REMARKS; post-acceptance update 2026-04-26 closes the earlier project-level artifact remark for the registered real comparison artifacts.
