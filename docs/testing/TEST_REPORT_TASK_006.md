# TEST_REPORT_TASK_006

## status

PASS WITH REMARKS

## scope

Роль: тестировщик Codex CLI TASK-006 audit/techlog/notifications.

Проверялись поведенческие сценарии TASK-006 по task-scoped входам:

- `docs/tasks/implementation/stage-1/TASK-006-audit-techlog-notifications.md`
- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md` только для expected scenario behavior
- `docs/product/PERMISSIONS_MATRIX.md` только для expected visibility rights
- `docs/audit/AUDIT_REPORT_TASK_006_ROUND_2.md` как audit acceptance context
- `apps/audit/tests.py`
- `apps/techlog/tests.py`
- `apps/audit/models.py`, `apps/audit/services.py`
- `apps/techlog/models.py`, `apps/techlog/services.py`

Метод: поведенческие Django test прогон и дополнительный временный scenario runner для проверки cleanup с operation/file links. Архитектурная оценка не выполнялась.

## scenario matrix

| ID | Scenario | Expected | Actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| T006-S01 | AuditRecord creation with action code, user/store/operation/entity links. | Audit record создаётся с action code, user, operation, derived store, entity fields и обратной ссылкой из operation. | `apps.audit` test создал audit record для `operation.check_started`; store был выведен из operation, operation link и retention 90 дней подтверждены. | pass | SQLite override: `apps.audit.tests.AuditTask006Tests.test_audit_record_links_operation_and_is_immutable`. |
| T006-S02 | TechLogRecord creation with event type, severity baseline normalization, critical notification creation. | Techlog создаётся с event type; severity не ниже baseline; critical создаёт notification и `notification_created`. | Critical baseline для `operation.execution_failed` поднял `info` до `critical`; создан `SystemNotification`. Non-critical baseline `application.exception` поднял `info` до `error` без critical notification. | pass | SQLite override: `test_critical_baseline_normalizes_lower_severity_and_creates_notification`, `test_non_critical_baseline_does_not_create_critical_notification_without_grounds`. |
| T006-S03 | Limited scope hides store/operation-linked records without object access even when `record.user == current user`. | Собственное авторство не обходит object access для store/operation-linked records. | Limited user не видел собственные записи, связанные с недоступным store и недоступной operation, в audit и techlog. | pass | SQLite override: `test_limited_and_full_audit_visibility_scopes`, `test_limited_full_and_sensitive_techlog_visibility_scopes`. |
| T006-S04 | Limited scope can see own global/non-store/non-operation records if non-sensitive. | Limited user видит собственные global records без store/operation link при наличии list права и limited scope. | Own global audit и own global techlog попадали в limited queryset. | pass | SQLite override: audit/techlog visibility tests. |
| T006-S05 | Full scope can see broader records but still cannot see sensitive details without `techlog.sensitive.view`. | Full scope расширяет видимость records; sensitive details требуют отдельного права. | Global admin/full user видел broader records и получил sensitive details, так как seed global admin содержит `techlog.sensitive.view`. Отдельный negative case без sensitive права покрыт limited user на visible techlog record. | pass | SQLite override: techlog visibility test. |
| T006-S06 | Sensitive details visible only with `techlog.sensitive.view`. | `sensitive_details_ref` возвращается только при record visibility и `techlog.sensitive.view`. | Limited user видел record, но `sensitive_details_for` вернул пустую строку; full user с sensitive правом получил ref. Невидимый record также вернул пустую строку. | pass | SQLite override: `test_limited_full_and_sensitive_techlog_visibility_scopes`. |
| T006-S07 | Audit/techlog records are immutable through normal save/update/delete paths. | Normal `save`, queryset `update`, model `delete`, queryset `delete` не изменяют и не удаляют записи. | AuditRecord и TechLogRecord бросали `ValidationError` на save/update и `ProtectedError` на delete/queryset delete. | pass | SQLite override: audit/techlog immutability tests. |
| T006-S08 | Cleanup command/service removes only expired audit/techlog records by regulated path and does not touch operations/files. | Regulated cleanup удаляет только records с expired `retention_until`; operation и file metadata/links сохраняются. | Unit tests подтвердили сохранность operation. Дополнительный scenario runner создал FileObject, FileVersion и OperationInputFile; cleanup удалил 1 expired audit и 1 expired techlog, fresh/critical records, operation, file object, file version и operation-input link остались. | pass | SQLite override tests plus temporary scenario runner output. |
| T006-S09 | SystemNotification is created for critical techlog events requiring attention. | Critical techlog event создаёт notification с operation/store links и safe message. | `file.storage_save_error` создал `SystemNotification`, topic/message/operation/store соответствовали techlog record. | pass | SQLite override: `test_critical_techlog_creates_system_notification`; temporary scenario runner. |
| T006-S10 | Audit/techlog do not replace operation records; only link to them. | Audit/techlog records связаны с operation, но operation record сохраняется отдельно. | Operation имела related audit/techlog records; cleanup audit/techlog не удалил operation. Scenario runner дополнительно подтвердил сохранность operation и input file link. | pass | SQLite override tests plus temporary scenario runner. |

## commands run/results

| Command | Result |
| --- | --- |
| `.venv/bin/python manage.py check` | PASS. `System check identified no issues (0 silenced).` |
| `.venv/bin/python manage.py test apps.audit apps.techlog` | BLOCKED in default PostgreSQL environment. Test DB creation failed with password authentication failure for user `promo_v2` at `127.0.0.1:5432`. |
| `DJANGO_SETTINGS_MODULE=<temporary_sqlite_settings> .venv/bin/python manage.py test apps.audit apps.techlog` | PASS. Found 10 tests, ran 10 tests, all OK. Temporary settings used SQLite `:memory:` and did not modify product code. |
| Temporary SQLite scenario runner for cleanup with operation/file links | PASS. Output showed `audit_deleted: 1`, `techlog_deleted: 1`, expired records absent, fresh/critical records present, `operation_exists: True`, `file_object_exists: True`, `file_version_exists: True`, `operation_input_link_exists: True`, `critical_notification_exists: True`. |

## defects found

No TASK-006 behavioral defects were found in the tested scope.

| Severity | Defect | Status |
| --- | --- | --- |
| blocker | None. | n/a |
| major | None. | n/a |
| minor | None. | n/a |

## environment limitations

- Default PostgreSQL test run was blocked by unavailable credentials for user `promo_v2`; acceptance behavior was verified with a safe temporary SQLite override.
- SQLite does not provide PostgreSQL-specific coverage. The tested scenarios are ORM/service-level behavior and did not depend on PostgreSQL-specific SQL features.
- `/home/pavel/projects/promo_v2` is not a git repository in this environment; `git status --short` failed with `fatal: not a git repository`.
- Real WB/Ozon customer acceptance artifacts are outside TASK-006 scope and were not used.

## recommendation

Можно переходить к TASK-007. Статус TASK-006 testing: PASS WITH REMARKS из-за недоступного PostgreSQL окружения, без найденных behavioral defects.
