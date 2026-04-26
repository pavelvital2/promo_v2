# TEST_REPORT_TASK_004

Дата: 2026-04-25

Роль: Тестировщик Codex CLI TASK-004 files and retention.

## status

PASS WITH REMARKS

TASK-004 поведенчески проходит проверенные сценарии файлового контура. Remark связан с окружением: штатный запуск `apps.files` tests на PostgreSQL заблокирован локальной аутентификацией, поэтому unit tests были повторно выполнены через безопасный in-process SQLite override без изменения product code.

## scope

Проверены:

- `docs/tasks/implementation/stage-1/TASK-004-files-and-retention.md`;
- `docs/testing/TEST_PROTOCOL.md`;
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`;
- `docs/product/PERMISSIONS_MATRIX.md` только для ожидаемых download/access сценариев;
- `docs/audit/AUDIT_REPORT_TASK_004_ROUND_2.md` как audit acceptance context;
- `apps/files/tests.py`;
- `apps/files/models.py`;
- `apps/files/services.py`;
- `apps/files/management/commands/cleanup_file_retention.py`.

Audit context: `AUDIT_REPORT_TASK_004_ROUND_2` имеет status `PASS`; аудит не выполнял tester acceptance, поэтому сценарии проверены отдельным тестовым прогоном.

## scenario matrix

| # | Scenario | Evidence | Status |
| --- | --- | --- | --- |
| 1 | Upload creates `FileObject` / `FileVersion` and `FILE-YYYY-NNNNNN`. | `test_upload_creates_metadata_version_checksum_and_safe_path`; SQLite test run PASS. | pass |
| 2 | Re-upload same logical/original file creates new version and preserves old version. | `test_repeated_upload_same_logical_file_creates_new_version`; verifies v2, same `file_id`, old v1 remains, old `operation_ref` remains. | pass |
| 3 | Checksums stored and differ/same as expected by content. | Unit test verifies checksum equals SHA-256 and differs for different content. Temporary scenario runner verified identical content gives identical checksum across versions. | pass |
| 4 | Storage path is server-side safe and not raw user path. | Unit test uses unsafe original name and verifies no `..`; temporary scenario runner verified raw user path is not embedded and server path uses `files/<scenario>/<store>/<file>/vNNNNNN/<uuid>.<ext>`. | pass |
| 5 | Download allowed only with scenario permission + object access + retention availability. | `test_download_requires_scenario_permission_and_store_access`; `test_expired_or_deleted_physical_file_is_unavailable_but_metadata_remains`. | pass |
| 6 | Observer cannot download output/detail by default. | `test_download_requires_scenario_permission_and_store_access` checks observer denial for output and detail report. | pass |
| 7 | Direct deny blocks download even when role allows it. | `test_individual_download_deny_overrides_role_permission`. | pass |
| 8 | Expired physical file cleanup removes/marks physical file unavailable while metadata remains. | `test_expired_or_deleted_physical_file_is_unavailable_but_metadata_remains`; `test_cleanup_dry_run_preserves_physical_file_and_status`. | pass |
| 9 | Pre-operation erroneous upload delete works only before operation/run refs and is blocked after refs/historical states. | `test_pre_operation_delete_removes_input_physical_file_and_metadata`; `test_pre_operation_delete_can_remove_one_unused_version`; `test_pre_operation_delete_rejects_operation_linked_or_generated_files`; temporary runner verified expired and unavailable versions are blocked. | pass |
| 10 | No WB/Ozon parsing/calculation scenario exists in file layer. | `rg` over `apps/files` found only scenario constants, migration choices, default module string, and command argparse; no `openpyxl`, workbook parser, formula, calculation, or discount business logic in file layer. | pass |

## commands run/results

| Command | Result |
| --- | --- |
| `.venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `.venv/bin/python manage.py test apps.files --verbosity 2` | BLOCKED BY ENV: PostgreSQL connection failed with password authentication failure for user `promo_v2` on `127.0.0.1:5432`; tests did not start. |
| In-process SQLite override: `call_command('test', 'apps.files', verbosity=2)` after setting `settings.DATABASES['default']` to SQLite `:memory:` before `django.setup()` | PASS: 9 tests ran, all OK. |
| Temporary SQLite scenario runner for same-content checksum, raw-path storage safety, expired pre-delete block, unavailable pre-delete block | PASS: all 4 scenario assertions passed. |
| `rg -n "openpyxl\|load_workbook\|Workbook\|iter_rows\|formula\|calculate\|parse\|parser\|discount\|скид\|wb_\|ozon_" apps/files` | PASS for no overreach: only file scenario constants/migrations/default module string/argparse found; no WB/Ozon Excel parsing or calculation implementation in `apps/files`. |

## defects found

None.

No blocker, major, or minor product defects were found in the tested TASK-004 behavior.

## environment limitations

- `/home/pavel/projects/promo_v2` is not a git repository from this working directory; `git status --short` fails with `fatal: not a git repository`.
- PostgreSQL test database setup is unavailable in this environment because authentication for user `promo_v2` on `127.0.0.1:5432` fails.
- SQLite override confirms Django model/service behavior for TASK-004 unit scenarios, but it is not a full substitute for PostgreSQL-specific integration confidence.
- No customer WB/Ozon acceptance artifacts were required for this file-layer task. Post-acceptance update 2026-04-26 closes the separate real comparison artifact gate described in `GAP-0008` / `ACCEPTANCE_TESTS.md` for `WB-REAL-001` / `OZ-REAL-001`.

## recommendation

Можно переходить к TASK-005.

Перед production-like acceptance рекомендуется повторить `apps.files` tests на доступном PostgreSQL test database. Это окруженческое замечание не блокирует переход к следующей implementation task, так как TASK-004 behavioral scenarios прошли под безопасным SQLite override, а product defects не обнаружены.
