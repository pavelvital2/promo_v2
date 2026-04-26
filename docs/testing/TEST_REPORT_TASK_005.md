# TEST_REPORT_TASK_005

Дата: 2026-04-25

Роль: Тестировщик Codex CLI TASK-005 operations/run/execution.

## status

PASS WITH REMARKS

Поведенческие сценарии TASK-005 пройдены на `apps.operations` test suite и дополнительном временном scenario runner с безопасным SQLite override. Штатный PostgreSQL test run в текущем окружении заблокирован authentication failure для пользователя `promo_v2`; это зафиксировано как ограничение окружения, не как дефект продукта.

## scope

- `docs/tasks/implementation/stage-1/TASK-005-operations-run-execution.md`
- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`
- `docs/product/OPERATIONS_SPEC.md` only for expected scenario behavior
- `docs/audit/AUDIT_REPORT_TASK_005_ROUND_2.md` as audit acceptance context
- `apps/operations/tests.py`
- `apps/operations/models.py`
- `apps/operations/services.py`

Product code не изменялся. Документация изменена только этим тестовым отчётом.

## scenario matrix

| ID | Scenario | Evidence | Status |
| --- | --- | --- | --- |
| 1 | Run and Operation visible ids `RUN-YYYY-NNNNNN` / `OP-YYYY-NNNNNN`. | `test_create_check_operation_visible_ids_file_links_and_snapshots`; regex assertions for both IDs. | pass |
| 2 | Check operation lifecycle and terminal statuses. | `apps.operations` tests cover created/running/completed/error/interrupted paths; extra scenario runner confirmed `completed_no_errors`, `completed_with_warnings`, `completed_with_errors`. | pass |
| 3 | Process with existing actual successful check reuses it and creates separate process. | `test_press_process_reuses_existing_actual_check`: check executor is not called, one existing check remains, process references basis check. | pass |
| 4 | Press process without actual check creates separate check first, then process only if allowed. | `test_press_process_without_actual_check_creates_check_then_process`: separate check/process operations, check completes before process. | pass |
| 5 | Auto-check with errors blocks process creation. | `test_press_process_does_not_create_process_when_auto_check_has_errors`: process executor is not called and no process operation exists. | pass |
| 6 | Confirmable warnings require explicit confirmation and permission; facts are recorded. | `test_process_with_warning_basis_requires_confirmation_fact`, `test_confirm_warnings_permission_required_when_enforced`; extra scenario runner confirmed allowed user with `confirm_warnings` records `WarningConfirmation`. | pass |
| 7 | `WarningConfirmation` immutable after creation. | `test_warning_confirmation_is_immutable_after_creation`; model/queryset guards reject update/save/delete paths. | pass |
| 8 | Completed/terminal operations immutable for result/file links/snapshots/details. | `test_terminal_operation_and_related_records_are_immutable`; extra scenario runner confirmed terminal immutability for `ProcessResult`, input/output file links, parameter snapshots, and detail rows. | pass |
| 9 | Interrupted failure sets `interrupted_failed` and does not auto-resume. | `test_interrupted_failed_is_terminal_and_does_not_auto_resume`: failing executor marks operation/run interrupted and `start_operation()` rejects restart. | pass |
| 10 | Repeated process cannot reuse output `FileVersion`. | `test_output_file_version_cannot_be_reused_across_process_operations`; service/model validation rejects second use. | pass |
| 11 | Module/mode mismatch check basis rejected. | `test_explicit_check_basis_mode_mismatch_is_rejected`; actuality metadata includes `module` and `mode`. | pass |
| 12 | No WB/Ozon calculation scenario is exercised/available in operations layer. | `rg` over `apps/operations` found only shell scenario mapping/reason constants and no imports from `apps.discounts`, `openpyxl`, workbook processing, formulas, or calculation execution. | pass |

## commands run/results

| Command | Result |
| --- | --- |
| `.venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `.venv/bin/python manage.py test apps.operations` | BLOCKED by environment: PostgreSQL authentication failed for `promo_v2` on `127.0.0.1:5432`; Django found 14 tests but could not create/connect test DB. |
| Inline Django test runner with `settings.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}`, command target `test apps.operations --verbosity 2` | PASS: 14 tests run, 14 ok. |
| Inline temporary scenario runner with same SQLite override | PASS: printed `SCENARIO_RUNNER_OK`; confirmed status branches, terminal related immutability, and warning confirmation with permission/fact recording. |
| `rg -n "from apps\\.discounts|import apps\\.discounts|wb_excel|ozon_excel|openpyxl|workbook|calculate|calculation|formula|discount" apps/operations` | PASS for scenario 12: no calculation/import hooks found; only scenario mapping, output kind, tests, and WB reason constants appeared. |

## defects found

None.

## environment limitations

- PostgreSQL credentials for `promo_v2@127.0.0.1:5432` are unavailable/invalid in this environment, so formal PostgreSQL-backed `apps.operations` test execution is blocked.
- SQLite override is a safe behavioral fallback for this tester run, but it is not full PostgreSQL parity. DB-specific constraints should still be re-run in an environment with working PostgreSQL credentials before release hardening.
- Real WB/Ozon Excel acceptance artifacts are not required for this operations-layer task; scenario 12 confirms calculation behavior is not present in `apps.operations`.

## recommendation

Можно переходить к TASK-006. Перед релизной приёмкой рекомендуется повторить `.venv/bin/python manage.py test apps.operations` на рабочем PostgreSQL test database.
