# TEST_REPORT_TASK_010.md

Task ID: TASK-010-acceptance-and-deployment

Date: 2026-04-25

Role: Codex CLI developer, acceptance and deployment readiness

## Summary

Prepared executable acceptance/deployment readiness package for stage 1 without inventing customer WB/Ozon artifacts. Formal WB/Ozon acceptance remains `blocked_by_artifact_gate` until real files, checksums, old-program results, expected summary, row-level expected results and edge-case sets are delivered and recorded.

Audit fix update on 2026-04-25: corrected both major findings from `docs/audit/AUDIT_REPORT_TASK_010.md`.

- Daily backup policy is operationalized through documented systemd timer/service examples and runbook setup commands. Daily PostgreSQL and media/file storage backups are scheduled together; retention remains 14 days in the backup scripts; mandatory pre-update backup remains a separate release gate.
- Nginx upload limit in the deployment example is raised to `128m`, covering the documented WB 100 MB per-run limit plus multipart overhead. Deployment readiness tests now assert this limit.

## Changed Files

| File | Change |
| --- | --- |
| `.env.example` | PostgreSQL example credentials aligned with TASK-010; backup retention env added. |
| `requirements.txt` | Added `gunicorn` for production WSGI baseline. |
| `deploy/systemd/promo_v2.service.example` | Replaced placeholder WSGI command with actual gunicorn command. |
| `deploy/systemd/promo_v2-daily-backup.service.example` | Added daily oneshot backup service running PostgreSQL and media backups. |
| `deploy/systemd/promo_v2-daily-backup.timer.example` | Added daily systemd timer example for backup schedule. |
| `deploy/nginx/promo_v2.conf.example` | Raised `client_max_body_size` from `50m` to `128m` for the 100 MB WB run limit plus multipart overhead. |
| `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md` | Added actual backup/update/smoke/restore/retention commands for current project. |
| `docs/testing/CONTROL_FILE_REGISTRY.md` | Added artifact-gated control file registry. |
| `docs/testing/STAGE_1_ACCEPTANCE_EXECUTION_PLAN.md` | Added executable acceptance plan. |
| `docs/testing/TEST_REPORT_TASK_010.md` | Added handoff report and audit fix update. |
| `scripts/backup_postgres.sh` | Added PostgreSQL backup script with 14-day retention. |
| `scripts/backup_media.sh` | Added server file storage backup script with 14-day retention. |
| `scripts/pre_update_backup.sh` | Added mandatory pre-update backup wrapper. |
| `scripts/restore_check.sh` | Added backup readability and optional non-production restore check script. |
| `scripts/deployment_smoke_check.sh` | Added Django/nginx health smoke script. |
| `scripts/audit_techlog_retention_check.sh` | Added non-UI audit/techlog retention dry-run/apply wrapper. |
| `apps/web/tests.py` | Added deployment readiness tests for config/scripts/docs gates. |

## Acceptance Areas

| Area | Status | Evidence / Notes |
| --- | --- | --- |
| WB formal acceptance | blocked_by_artifact_gate | Real WB files, checksums, old program results, expected summary and row-level expected results are not provided. No fake artifacts created. |
| Ozon formal acceptance | blocked_by_artifact_gate | Real Ozon files, checksums, old program results, expected summary and row-level expected results are not provided. No fake artifacts created. |
| Edge-case control sets | blocked_by_artifact_gate for formal acceptance | Registry placeholders added; expected artifacts still pending. |
| Operations acceptance | pass | Full automated suite passed. |
| Files and file retention | pass | Full automated suite passed. |
| Security/access | pass | Full automated suite passed. |
| Audit/techlog separation | pass | Full automated suite passed. |
| Audit/techlog 90-day retention | pass | `scripts/audit_techlog_retention_check.sh` dry-run passed after migrations: `audit_expired=0 techlog_expired=0`. |
| Deployment smoke | pass | `scripts/deployment_smoke_check.sh` passed against local gunicorn on `127.0.0.1:8080`; production nginx/systemd smoke remains to repeat on server. |
| Backup/restore readiness | pass | PostgreSQL backup, media backup, archive readability check and optional non-production restore DB check passed locally. |
| Daily backup operationalization | pass | Runbook now includes systemd timer/service setup, manual smoke start, recent backup verification commands, and cron fallback. |
| Nginx upload deployment limit | pass | `deploy/nginx/promo_v2.conf.example` sets `client_max_body_size 128m`; deployment readiness test asserts at least `128m`. |

## Commands To Run

```bash
. .venv/bin/activate
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres python manage.py check
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres python manage.py test
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/audit_techlog_retention_check.sh
BASE_URL=http://127.0.0.1:8080 POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/deployment_smoke_check.sh
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/pre_update_backup.sh
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/restore_check.sh <postgres_dump> <media_tar_gz>
```

## Executed Checks

| Command | Result |
| --- | --- |
| `python -m pip install -r requirements.txt` | pass; installed `gunicorn==23.0.0`. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres python manage.py check` | pass; no issues. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres python manage.py migrate --noinput` | pass on local `promo_v2` DB. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres python manage.py test apps.web.tests.DeploymentReadinessTests` | pass; 3 tests. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres python manage.py test` | pass; 100 tests in 80.962s. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check` | pass; no issues after audit fixes. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.web.tests.DeploymentReadinessTests` | pass; 3 tests after audit fixes. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test` | pass; 100 tests in 87.329s after audit fixes. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/audit_techlog_retention_check.sh` | pass after migrations; dry-run returned `audit_expired=0 techlog_expired=0`. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres BACKUP_DIR=<tmp> ./scripts/backup_postgres.sh` | pass; custom-format dump created and non-empty. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres BACKUP_DIR=<tmp> DJANGO_MEDIA_ROOT=<repo>/media ./scripts/backup_media.sh` | pass; media archive created and non-empty. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/restore_check.sh <dump> <media.tar.gz>` | pass; `pg_restore --list` and `tar -tzf` succeeded. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres RESTORE_DB=promo_v2_restore_check_<timestamp> ./scripts/restore_check.sh <dump> <media.tar.gz>` | pass; restored into a non-production DB, then dropped the restore DB. |
| `BASE_URL=http://127.0.0.1:8080 POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/deployment_smoke_check.sh` | pass against local gunicorn on port `8080`; output included `deployment_smoke=pass`. |

Initial `cleanup_audit_techlog --dry-run` before migrations failed because local DB `promo_v2` did not yet contain tables. After creating the local DB and applying migrations, the check passed.

## Gaps And Blockers

No new GAP was opened.

`GAP-0007`, `GAP-0008` and `GAP-0009` remain resolved by ADR-0012/ADR-0013/ADR-0014. The only remaining formal acceptance blocker is the artifact gate from ADR-0013.

## Handoff To Auditor

Auditor should verify:

- no customer WB/Ozon artifacts or expected results were fabricated;
- nginx remains on port `8080`;
- runbook commands match Django + PostgreSQL + gunicorn + systemd skeleton;
- backup policy is daily PostgreSQL + daily server storage backup with 14-day retention and mandatory pre-update backup;
- restore check is manual/non-production and recorded before important releases;
- audit/techlog cleanup is 90-day, regulated, and non-UI only.
