# TEST_REPORT_TASK_010_FINAL.md

Task ID: TASK-010-acceptance-and-deployment

Date: 2026-04-25

Role: Codex CLI tester, independent deployment/readiness verification after PASS audit

## Verdict

PASS for TASK-010 deployment/readiness.

Post-acceptance update 2026-04-26: formal WB/Ozon real output comparison is no longer `blocked_by_artifact_gate` for the registered artifacts. `WB-REAL-001` and `OZ-REAL-001` are recorded in `docs/testing/CONTROL_FILE_REGISTRY.md` and accepted in `docs/testing/TEST_REPORT_STAGE_1_FORMAL_ACCEPTANCE.md`. No files or expected results were fabricated.

## Scope

Tested deployment/readiness behavior after `docs/audit/AUDIT_REPORT_TASK_010_ROUND_2.md` PASS:

- Django system check and full automated test suite;
- `apps.web.tests.DeploymentReadinessTests`;
- PostgreSQL backup, media backup and pre-update backup in temporary directories;
- backup readability and safe optional restore into a temporary non-production database;
- audit/techlog retention dry-run;
- deployment smoke against local gunicorn on `127.0.0.1:8080`;
- static inspection of nginx and systemd examples without installing system services.

## Environment

- Project root: `/home/pavel/projects/promo_v2`
- Python: `.venv/bin/python`, Python 3.12.3
- Django: 5.2.13
- gunicorn: 23.0.0
- PostgreSQL credentials used: `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres`
- Local smoke URL: `http://127.0.0.1:8080`

## Scenarios And Results

| Test ID | Scenario | Command / Evidence | Actual result | Status |
| --- | --- | --- | --- | --- |
| T010-FINAL-001 | Django deployment system check | `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check` | `System check identified no issues (0 silenced).` | pass |
| T010-FINAL-002 | Full automated suite | `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test` | 100 tests passed in 88.659s. | pass |
| T010-FINAL-003 | Deployment readiness tests | `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.web.tests.DeploymentReadinessTests` | 3 tests passed. | pass |
| T010-FINAL-004 | PostgreSQL backup in temp dir | `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres BACKUP_DIR=/tmp/promo_v2_task010_final.M1gz1R/postgres_backups ./scripts/backup_postgres.sh` | Created non-empty custom-format dump: `promo_v2_20260425T182320Z.dump`, 198879 bytes. | pass |
| T010-FINAL-005 | Media backup in temp dir | `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres BACKUP_DIR=/tmp/promo_v2_task010_final.M1gz1R/media_backups DJANGO_MEDIA_ROOT=/tmp/promo_v2_task010_final.M1gz1R/media_src ./scripts/backup_media.sh` | Created non-empty archive: `media_20260425T182321Z.tar.gz`, 194 bytes. | pass |
| T010-FINAL-006 | Mandatory pre-update backup wrapper in temp dir | `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres BACKUP_DIR=/tmp/promo_v2_task010_preupdate.dAfkiI/pre_update_backups DJANGO_MEDIA_ROOT=/tmp/promo_v2_task010_preupdate.dAfkiI/media_src ./scripts/pre_update_backup.sh` | Created both non-empty files: PostgreSQL dump 198879 bytes and media archive 195 bytes. | pass |
| T010-FINAL-007 | Restore check archive readability | `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/restore_check.sh <dump> <media.tar.gz>` | `restore_check=backup_archives_readable`; `pg_restore --list` and `tar -tzf` succeeded. | pass |
| T010-FINAL-008 | Optional safe non-production DB restore | `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres RESTORE_DB=promo_v2_restore_check_final_20260425212332 ./scripts/restore_check.sh <dump> <media.tar.gz>` | Restore succeeded into temporary DB; DB was dropped after the check. | pass |
| T010-FINAL-009 | Audit/techlog retention dry-run | `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres PYTHON_BIN=.venv/bin/python ./scripts/audit_techlog_retention_check.sh` | `DRY RUN audit_expired=0 techlog_expired=0`. | pass |
| T010-FINAL-010 | Deployment smoke against local gunicorn | Started `.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8080 --workers 1 --timeout 120`; then ran `BASE_URL=http://127.0.0.1:8080 POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres PYTHON_BIN=.venv/bin/python ./scripts/deployment_smoke_check.sh` | `health_ok=http://127.0.0.1:8080/health/` and `deployment_smoke=pass`; gunicorn was stopped after the check. | pass |
| T010-FINAL-011 | Nginx example readiness | Read `deploy/nginx/promo_v2.conf.example` | Contains `listen 8080;`, `client_max_body_size 128m;`, and `proxy_pass http://127.0.0.1:8000;`. No system nginx was changed. | pass |
| T010-FINAL-012 | Systemd service/timer example readiness | Read `deploy/systemd/promo_v2.service.example`, `deploy/systemd/promo_v2-daily-backup.service.example`, `deploy/systemd/promo_v2-daily-backup.timer.example` | Application unit uses gunicorn on `127.0.0.1:8000`; daily backup service is `Type=oneshot` and runs PostgreSQL and media backup scripts; timer has `OnCalendar=*-*-* 02:15:00` and `Persistent=true`. No system services were installed. | pass |

## Artifact Areas

| Area | Status | Reason |
| --- | --- | --- |
| WB formal acceptance | accepted | `WB-REAL-001` registered, checksummed and compared with old-program result. |
| Ozon formal acceptance | accepted | `OZ-REAL-001` registered, checksummed and compared with old-program result. |
| Future edge-case control sets | optional_future_artifact | Existing automated edge-case coverage remains; future customer artifacts are registered separately if introduced. |

## Defects

No TASK-010 deployment/readiness defects were found during this independent test pass.

## Residual Risks

- Production nginx reload, production systemd service installation and real VPS timer execution were not performed in this local test pass.
- Restore check verified archive readability and technical restore into a temporary DB; full business-level restore validation in a production-like contour remains a release/runbook activity.
- Future new customer artifacts require separate registration before formal comparison for that new set.

## Changed Files

- `docs/testing/TEST_REPORT_TASK_010_FINAL.md`
