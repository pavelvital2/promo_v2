# AUDIT_REPORT_TASK_010.md

Task: `TASK-010-acceptance-and-deployment`

Date: 2026-04-25

Role: Codex CLI auditor

## Verdict

FAIL.

TASK-010 has the main acceptance/deployment artifacts in place and the executable checks passed locally, but deployment readiness is not complete. Two major issues must be fixed before handoff to an independent tester.

Can go to independent tester: no, not before the findings below are corrected and re-audited.

## Findings By Severity

### Major: daily backup policy is declared but not operationalized in the runbook

Evidence:

- ADR-0012 requires daily PostgreSQL backup, daily server file storage backup, 14-day retention, mandatory pre-update backup, and restore checks before important releases (`docs/adr/ADR_LOG.md:138`-`145`).
- The runbook repeats the daily policy (`docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md:93`-`107`) and provides pre-update backup commands (`docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md:20`-`33`).
- The implementation provides executable backup scripts (`scripts/backup_postgres.sh:1`-`31`, `scripts/backup_media.sh:1`-`23`, `scripts/pre_update_backup.sh:1`-`7`), but the scoped files do not include a cron/systemd timer or equivalent command that installs/enables the required daily backups. `rg -n "cron|systemd timer|timer|daily|backup_postgres|backup_media|pre_update_backup" ...` found only the scripts/pre-update references and policy text, not scheduling instructions.

Impact:

Production can pass a manual pre-update backup check while still not satisfying ADR-0012's daily backup requirement after deployment.

Developer instructions:

Add a documented daily backup setup procedure to `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md` and, if this project uses deploy examples for operational units, add matching example systemd timer/service or cron entries. The procedure must run both PostgreSQL and server file storage backups, keep 14-day retention, and include a verification command for listing recent backups. Keep the mandatory pre-update backup as a separate release gate.

### Major: nginx upload limit is below the documented stage-1 run limit

Evidence:

- Stage-1 acceptance requires WB limits of 25 MB per file, 100 MB per run, and up to 20 promo files (`docs/testing/ACCEPTANCE_CHECKLISTS.md:24`-`36`).
- The nginx deployment example sets `client_max_body_size 50m` (`deploy/nginx/promo_v2.conf.example:1`-`6`).

Impact:

The deployment example may reject a valid stage-1 WB run before Django sees the request if the UI submits a run upload in one multipart request. This is a deployment readiness risk independent of WB business logic.

Developer instructions:

Raise the nginx request body limit to cover the documented 100 MB run limit plus multipart overhead, for example `128m`, or document and test an upload flow that guarantees each HTTP request remains within `50m` while still supporting a 100 MB run. Add or update the deployment readiness test so this regression is caught.

## Positive Evidence

- Expected TASK-010 artifacts are present: executable acceptance plan (`docs/testing/STAGE_1_ACCEPTANCE_EXECUTION_PLAN.md:1`-`113`), control file registry (`docs/testing/CONTROL_FILE_REGISTRY.md:1`-`50`), release/update runbook (`docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md:1`-`152`), backup/restore scripts, deployment smoke script, and audit/techlog retention script.
- No fabricated WB/Ozon customer control files, checksums, old-program outputs, expected summaries, or row-level expected results were found in the scoped artifact registry. The registry keeps all real WB/Ozon rows pending and `blocked_by_artifact_gate` (`docs/testing/CONTROL_FILE_REGISTRY.md:21`-`28`).
- Formal WB/Ozon acceptance remains `blocked_by_artifact_gate`, not an unresolved GAP and not silently accepted (`docs/gaps/GAP_REGISTER.md:25`-`33`, `docs/adr/ADR_LOG.md:148`-`156`, `docs/testing/STAGE_1_ACCEPTANCE_EXECUTION_PLAN.md:89`-`113`).
- Backup scripts use PostgreSQL custom dumps and media tar archives with `BACKUP_RETENTION_DAYS:-14` (`scripts/backup_postgres.sh:4`-`31`, `scripts/backup_media.sh:4`-`23`). The pre-update wrapper calls both scripts (`scripts/pre_update_backup.sh:1`-`7`).
- Restore check validates `pg_restore --list`, `tar -tzf`, and optional restore into a non-production database guarded against `RESTORE_DB == POSTGRES_DB` (`scripts/restore_check.sh:21`-`47`).
- Audit/techlog retention is 90 days and non-UI in the architecture spec (`docs/architecture/AUDIT_AND_TECHLOG_SPEC.md:81`-`88`) and implemented through the management-command wrapper (`scripts/audit_techlog_retention_check.sh:1`-`10`).
- Nginx port decision is preserved: the example listens on `8080`, not `80`, and proxies to gunicorn on `127.0.0.1:8000` (`deploy/nginx/promo_v2.conf.example:1`-`23`). The runbook also preserves the current port-80-occupied decision (`docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md:5`-`10`, `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md:55`).
- No evidence was found in the scoped TASK-010 files that WB/Ozon business logic, permission model, check/process split, or audit/techlog separation was changed for this task. VCS changed-set verification was unavailable because `/home/pavel/projects/promo_v2` is not a git repository in this environment.

## Commands Run

All commands were run from `/home/pavel/projects/promo_v2`.

| Command | Result |
| --- | --- |
| `git status --short` | failed: not a git repository; changed-set verification by VCS unavailable. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check` | pass; no issues. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test` | pass; 100 tests, OK. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py migrate --noinput` | pass; no migrations to apply. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres PYTHON_BIN=.venv/bin/python ./scripts/audit_techlog_retention_check.sh` | pass; `DRY RUN audit_expired=0 techlog_expired=0`. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres BACKUP_DIR=/tmp/.../backups/postgres ./scripts/backup_postgres.sh` | pass; non-empty custom dump created in temp dir. |
| `DJANGO_MEDIA_ROOT=/tmp/.../media BACKUP_DIR=/tmp/.../backups/media ./scripts/backup_media.sh` | pass; non-empty media archive created in temp dir. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/restore_check.sh <dump> <media.tar.gz>` | pass; backup archives readable. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres RESTORE_DB=promo_v2_restore_audit_010_20260425T1808 ./scripts/restore_check.sh <dump> <media.tar.gz>` | pass; restored into non-production DB, then temp DB was dropped. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres BACKUP_DIR=/tmp/... DJANGO_MEDIA_ROOT=/tmp/.../media ./scripts/pre_update_backup.sh` | pass; wrapper created PostgreSQL and media backups in temp dir. |
| `.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8080 --workers 1 --timeout 120` plus `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres PYTHON_BIN=.venv/bin/python BASE_URL=http://127.0.0.1:8080 ./scripts/deployment_smoke_check.sh` | pass; `/health/` returned ok and `deployment_smoke=pass`; local gunicorn was stopped afterward. |

Temp backup directories and the temporary restore database were removed after verification.

## Scope Notes

- Destructive/prod-only steps were not run: no system nginx/systemd reload, no production backup path writes, no production restore, and no audit/techlog cleanup with `APPLY_CLEANUP=1`.
- Formal WB/Ozon customer-file acceptance was not run because the required real files, checksums, old-program results, expected summaries, row-level expected results, and edge-case sets remain behind the artifact gate.
