# AUDIT_REPORT_TASK_006_ROUND_2

## status

PASS WITH REMARKS

## checked scope

- Previous audit report: `docs/audit/AUDIT_REPORT_TASK_006.md`.
- Task: `docs/tasks/implementation/stage-1/TASK-006-audit-techlog-notifications.md`.
- Specs: `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`, `docs/product/PERMISSIONS_MATRIX.md` audit/techlog rights.
- Code scope:
  - `apps/audit/services.py`
  - `apps/audit/models.py`
  - `apps/audit/tests.py` only for coverage awareness
  - `apps/techlog/services.py`
  - `apps/techlog/models.py`
  - `apps/techlog/tests.py` only for coverage awareness
  - `apps/identity_access/services.py` for permission/object access helper integration
  - `apps/audit/management/commands/cleanup_audit_techlog.py` for non-UI cleanup sanity

Audit method: static audit of previous major closure and regression risks. Sanity commands were run, but this report is not a tester pass and does not replace separate testing.

## previous findings closure table

| Previous finding | Round 2 result | Evidence |
| --- | --- | --- |
| Major 1: limited audit/techlog scope exposed store/operation-linked records through `record.user == current_user` even without store/object access. | CLOSED | `apps/audit/services.py:103`-`107` and `apps/techlog/services.py:169`-`173` now allow `Q(user=user, store__isnull=True, operation__isnull=True)` only for own global/non-store records. Store-linked and operation-linked records must match allowed store ids. Coverage awareness: `apps/audit/tests.py:122`-`163`, `apps/techlog/tests.py:124`-`158` assert own inaccessible store/operation records are hidden while own global records remain visible. |
| Major 2: techlog severity baseline was not fixed in code, so critical baseline events could be recorded with lower severity and without notification. | CLOSED | `apps/techlog/models.py:80`-`94` defines `TECHLOG_EVENT_SEVERITY_BASELINE` matching the catalog, including critical events. `apps/techlog/services.py:45`-`54` validates event type/severity and raises severity to baseline. `apps/techlog/services.py:77`-`95` always sets critical records to `notification_created` and creates `SystemNotification`, regardless of the legacy `create_notification_for_critical` argument. Coverage awareness: `apps/techlog/tests.py:190`-`204`. |

## new findings blocker/major/minor

### blocker

None.

### major

None.

### minor

1. Own global/non-store visibility carve-out is implemented and test-covered, but the product/architecture specs do not explicitly document this carve-out.
   - Evidence: `apps/audit/services.py:106`, `apps/techlog/services.py:172`.
   - Risk: low. It does not reopen Major 1 because store/operation-linked records no longer use `record.user == current_user` to bypass object access. The behavior should be documented in a future documentation cleanup if the product owner wants this carve-out as an explicit rule.

## regression checks

- Sensitive techlog details still require both record visibility and `techlog.sensitive.view`: `apps/techlog/services.py:182`-`187`.
- Full scope still returns all audit/techlog records when the user has full object scope or `logs.scope.full` plus the relevant list/card permission: `apps/audit/services.py:87`-`97`, `apps/techlog/services.py:153`-`163`.
- Audit/techlog records remain immutable through model save, queryset update and ordinary delete blocking: `apps/audit/models.py:95`-`112`, `apps/audit/models.py:180`-`194`, `apps/techlog/models.py:110`-`127`, `apps/techlog/models.py:197`-`211`.
- Cleanup remains a non-UI management command/service and deletes only expired audit/techlog records: `apps/audit/management/commands/cleanup_audit_techlog.py:12`-`40`, `apps/audit/services.py:116`-`125`, `apps/techlog/services.py:190`-`199`.
- No ordinary audit/techlog templates or UI cleanup entry points were found in `apps/*/templates`.
- No WB/Ozon/TASK-009 overreach was found in the checked scope. References outside audit/techlog are limited to app registration and seed permissions.

## sanity commands/results

- `.venv/bin/python manage.py check` - PASS: `System check identified no issues (0 silenced).`
- `.venv/bin/python manage.py makemigrations --check --dry-run` - PASS with environment warning: `No changes detected`; Django emitted a PostgreSQL authentication warning for user `promo_v2`.

No unit/integration test suite was run as an acceptance pass. Tests were inspected only for coverage awareness, per round 2 audit scope.

## environment limitations

- `/home/pavel/projects/promo_v2` is not a git repository in this environment; `git status --short` failed with `fatal: not a git repository`.
- PostgreSQL authentication for the configured default DB failed during the migration consistency check. The `makemigrations --check --dry-run` command still exited successfully and reported no model/migration drift.

## decision

TASK-006 accepted with remarks. Return to developer is not required for blocker/major issues.

## recommendation

Run a separate tester pass next for audit/techlog creation, limited/full/sensitive visibility, critical notification creation, retention cleanup, and links to operation/store/user/entity.
