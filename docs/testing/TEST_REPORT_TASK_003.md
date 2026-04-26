# TEST_REPORT_TASK_003

## status

PASS WITH REMARKS

## tester-owned note

Роль: Тестировщик Codex CLI TASK-003 stores/cabinets/connections.

Timestamp/context: 2026-04-25 16:02:57 MSK (+0300), рабочая директория `/home/pavel/projects/promo_v2`.

Этот отчёт пересоздан тестировщиком и заменяет прежний developer-created `docs/testing/TEST_REPORT_TASK_003.md` как независимый tester-owned artifact. Проверка выполнялась поведенчески по task-scoped входам TASK-003, без аудиторской оценки архитектуры и без исправления product code.

## scenario matrix

| # | Scenario | Evidence | Status |
| --- | --- | --- | --- |
| 1 | BusinessGroup/StoreAccount create/update and visible id `STORE-NNNNNN`. | Existing stores tests plus temporary SQLite scenario runner: `business_group_create_update`, `store_visible_id_format`, `store_update_keeps_visible_id`; visible id observed as `STORE-000001`. | PASS |
| 2 | Store visible id cannot be changed after creation by normal path. | `apps.stores` test `test_visible_store_id_is_immutable_after_creation`; scenario runner `visible_id_change_blocked`; create/edit form excludes `visible_id`. | PASS |
| 3 | Store list/card доступен только по object access / global scope; пользователь без доступа не видит store. | `apps.stores` test `test_visible_stores_queryset_respects_object_access_and_direct_deny`, `test_store_views_hide_inaccessible_stores_and_render_card_history_connection`; scenario runner `store_list_object_scope`, `store_card_forbidden_without_access`, `no_access_user_sees_no_store`. | PASS |
| 4 | Local admin manages only assigned stores/cabinets. | Temporary scenario runner with `ROLE_LOCAL_ADMIN`: assigned store visible/editable, unassigned store hidden and edit denied. | PASS |
| 5 | ConnectionBlock stage 2 message visible; stage 1 API usage remains false. | `apps.stores` test `test_connection_block_is_stage_2_only_and_records_redacted_history`; scenario runner `connection_stage1_false`, `connection_stage2_message_visible`, `no_stage1_api_usage_rows`. | PASS |
| 6 | Metadata rejects nested secret-like keys. | `apps.stores` test `test_connection_block_rejects_nested_secret_like_metadata_keys`; scenario runner `nested_secret_metadata_rejected`. | PASS |
| 7 | Metadata display/history redacts protected refs/nested secrets. | `apps.stores` tests `test_connection_metadata_display_redacts_nested_secret_like_values`, `test_store_card_redacts_nested_metadata_from_legacy_rows`; scenario runner `metadata_display_redacts_nested`, `history_redacts_secret_ref`. | PASS |
| 8 | Store change history records significant changes without exposing secrets. | `apps.stores` tests `test_update_store_account_records_significant_field_history`, `test_store_access_changes_are_recorded_without_identity_model_rewrite`; scenario runner `history_records_changes`, `history_redacts_secret_ref`. | PASS |
| 9 | Archive/deactivate/delete behavior follows policy at scenario level. | `apps.stores` test `test_archive_delete_policy_blocks_used_store_connection_and_history`; scenario runner `used_store_delete_blocked`, `unused_store_physical_delete_allowed`. | PASS |
| 10 | No actual API scenario is exercised/available. | `apps/stores/**` search found no HTTP client/API execution code; WB/Ozon discount apps are placeholders for future tasks; scenario runner verified no `ConnectionBlock.is_stage1_used=True` rows. | PASS |

## commands run / results

| Command | Result |
| --- | --- |
| `.venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `.venv/bin/python manage.py test apps.stores` | BLOCKED BY ENV before scenario execution: PostgreSQL authentication failed for user `promo_v2` at `127.0.0.1:5432`; Django found 12 tests but could not create the test DB. |
| Inline Django test runner with safe in-memory SQLite override for `apps.stores` | PASS: 12 tests ran, 12 passed, `OK`. |
| Inline temporary scenario runner with safe in-memory SQLite override | PASS: 19 scenario checks passed, 0 failed. Expected 403 produced a Django `Forbidden` log line for inaccessible store card. |
| `rg -n "requests|urllib|httpx|aiohttp|...|discount|is_stage1_used|ConnectionBlock|connection" apps/stores config apps/discounts -S` | PASS for TASK-003 scope: no HTTP client/API execution code in `apps/stores`; connection block remains stage-2 preparation; WB/Ozon discount apps are placeholders for TASK-007/TASK-008. |

## defects found

No product defects found in TASK-003 behavioral scenarios.

Process/environment issue:

| Severity | Finding | Impact |
| --- | --- | --- |
| minor | Default PostgreSQL credentials are unavailable in this environment for `manage.py test apps.stores`. | Native PostgreSQL test execution is blocked here; SQLite override was used only as a safe behavioral substitute and does not prove PostgreSQL-specific behavior. |

## environment limitations

- Working directory `/home/pavel/projects/promo_v2` is not a git repository, so tester could not use `git status` or diff attribution.
- Default DB settings target PostgreSQL `promo_v2` on `127.0.0.1:5432`; test DB creation failed due password authentication.
- SQLite override was in-memory and temporary, applied only inside inline runner processes; no project settings or product code were changed.
- Formal WB/Ozon Excel acceptance artifacts are outside TASK-003 and remain governed by the artifact gate in `docs/testing/TEST_PROTOCOL.md`; no Excel/API calculation scenario was tested here.

## recommendation

С точки зрения тестировщика, по TASK-003 можно переходить к TASK-004.

Статус `PASS WITH REMARKS` выбран только из-за ограничения окружения PostgreSQL. Поведенческие сценарии TASK-003 по доступному тестовому контуру прошли.
