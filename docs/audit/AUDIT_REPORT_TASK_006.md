# AUDIT_REPORT_TASK_006

## status

FAIL

## checked scope

- Task: `docs/tasks/implementation/stage-1/TASK-006-audit-techlog-notifications.md`.
- Specs: `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`, `docs/architecture/DATA_MODEL.md` audit/techlog/notification parts, `docs/product/PERMISSIONS_MATRIX.md` audit/techlog rights, `docs/product/OPERATIONS_SPEC.md` separation/link concepts, `docs/architecture/DELETION_ARCHIVAL_POLICY.md`.
- Source TZ sections checked by task scope: §20, §21, §22.6, §23.1, §27.
- Code scope: `apps/audit/**`, `apps/techlog/**`, `apps/operations/**` for separation/links, `apps/identity_access/**` for permission helpers, `apps/stores/**` for store scope integration.

## audit method

Static audit of models, services, seed permissions, migrations and task tests against the documented requirements. Sanity commands were run, but this audit is not a tester pass and does not replace a separate test cycle.

## findings

### blocker

None.

### major

1. Limited log scope can expose records outside current store/object access when the record user is the requesting user.
   - `apps/audit/services.py:103`-`107` filters limited audit records with `Q(user=user)` in addition to allowed stores/operations.
   - `apps/techlog/services.py:145`-`149` applies the same pattern for techlog.
   - This conflicts with `docs/product/PERMISSIONS_MATRIX.md` and `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`: without access to a store/cabinet, a user must not see related audit/techlog records except through global/full scope. A user who previously acted in a store and later lost access can still see records tied to that inaccessible store/operation because `user=user` bypasses the store filter.

2. Techlog severity baseline from the documented event catalog is not represented/fixed, so critical event notification creation is not guaranteed.
   - `apps/techlog/models.py:43`-`78` fixes only event type choices, but does not encode the documented severity baseline for each event type.
   - `apps/techlog/services.py:37`-`50` accepts arbitrary `severity` from the caller.
   - `apps/techlog/services.py:54`-`71` creates `SystemNotification` only when the caller-provided severity equals `critical`.
   - Documented critical-baseline events such as `file.storage_save_error`, `operation.execution_failed`, `database.error`, and `backup.restore_check_failed` can therefore be recorded with a lower severity and no notification. This weakens the fixed techlog catalog and violates the minimal notification contour for critical events requiring attention.

### minor

None.

## positive checks

- `AuditRecord` and `TechLogRecord` are separate models/tables from `Operation` and link back through protected FKs: `apps/audit/models.py:118`-`148`, `apps/techlog/models.py:116`-`149`, `apps/operations/models.py:348`-`498`.
- Audit action codes match the documented TASK-006 catalog and are represented as fixed choices: `apps/audit/models.py:36`-`80`.
- WB reason/result codes remain separate in operation detail rows and are not mixed into audit action codes: `apps/operations/models.py:160`-`172`, `apps/operations/models.py:748`-`751`.
- Audit/techlog records are immutable through model save and queryset update; ordinary deletes are blocked except retention cleanup context: `apps/audit/models.py:95`-`112`, `apps/audit/models.py:180`-`194`, `apps/techlog/models.py:93`-`110`, `apps/techlog/models.py:180`-`194`.
- Retention is 90 days and cleanup is a management command/service, not UI: `apps/audit/models.py:16`, `apps/techlog/models.py:16`, `apps/audit/management/commands/cleanup_audit_techlog.py:12`-`40`.
- Cleanup services delete only `AuditRecord` and `TechLogRecord`; operations/files/snapshots/detail rows are not targeted: `apps/audit/services.py:116`-`125`, `apps/techlog/services.py:166`-`175`.
- Sensitive techlog details are hidden unless the user can view the record and has `techlog.sensitive.view`: `apps/techlog/services.py:158`-`163`.
- Notification model and service contour exists for critical techlog records when severity is correctly passed as `critical`: `apps/techlog/models.py:197`-`263`, `apps/techlog/services.py:70`-`84`.

## sanity commands/results

- `.venv/bin/python manage.py check` - PASS: `System check identified no issues (0 silenced).`
- `.venv/bin/python manage.py makemigrations --check --dry-run` - PASS with environment warning: `No changes detected`; Django emitted a warning that PostgreSQL connection check failed due password authentication failure for user `promo_v2`.

No unit/integration test suite was run as an acceptance pass; tester verification remains separate.

## environment limitations

- `/home/pavel/projects/promo_v2` is not a git repository in this environment; `git status --short` failed with `fatal: not a git repository`.
- PostgreSQL authentication for the configured default DB failed during migration consistency check, though `makemigrations --check --dry-run` still returned `No changes detected`.

## decision

TASK-006 is not accepted. Return to developer for correction of limited-scope visibility and fixed techlog severity/notification behavior.

## recommendation

After developer fixes, run a separate tester pass for audit/techlog creation, limited/full/sensitive visibility, retention cleanup, notification creation, and links to operation/store/user/entity.
