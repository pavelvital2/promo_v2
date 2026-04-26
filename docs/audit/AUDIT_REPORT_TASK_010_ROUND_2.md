# AUDIT_REPORT_TASK_010_ROUND_2.md

Task: `TASK-010-acceptance-and-deployment`

Date: 2026-04-25

Role: Codex CLI auditor, round 2 after fixes for `docs/audit/AUDIT_REPORT_TASK_010.md`

## Verdict

PASS.

The two major findings from the first TASK-010 audit are closed. Daily backup is now operationalized through documented systemd timer/service examples plus a cron fallback, and the nginx upload limit now covers the documented 100 MB per-run upload limit with multipart overhead. Deployment readiness regression tests cover both areas.

Can go to independent tester: yes for TASK-010 deployment/readiness verification. Formal WB/Ozon acceptance still remains behind the ADR-0013 customer artifact gate until real control files, checksums, old-program results, expected summaries and row-level expected results are delivered.

## Findings

No blocker or major findings.

## Evidence

### Finding 1 from round 1: daily backup policy operationalization

Status: CLOSED.

Evidence:

- `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md:95`-`108` keeps the approved ADR-0012 policy: daily PostgreSQL backup, daily server file storage backup, 14-day retention, mandatory pre-update backup, and restore checks.
- `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md:110`-`146` adds an executable daily setup procedure: install backup directories, install `promo_v2-daily-backup.service` and `promo_v2-daily-backup.timer`, run `systemctl daemon-reload`, enable the timer, perform a manual service smoke run, list the timer, verify recent PostgreSQL and media backups with `find`, and use a cron fallback if systemd timer is not used.
- `deploy/systemd/promo_v2-daily-backup.service.example:1`-`13` defines a oneshot service in `/opt/promo_v2` using `/etc/promo_v2/env` and runs both `/opt/promo_v2/scripts/backup_postgres.sh` and `/opt/promo_v2/scripts/backup_media.sh`.
- `deploy/systemd/promo_v2-daily-backup.timer.example:1`-`8` schedules the backup daily at `02:15` with `Persistent=true`.
- `scripts/backup_postgres.sh:4` and `scripts/backup_media.sh:4` retain `BACKUP_RETENTION_DAYS:-14`.
- `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md:20`-`34` keeps pre-update backup as a separate release gate via `scripts/pre_update_backup.sh`.
- `apps/web/tests.py:55`-`88` checks executable operational scripts, backup retention defaults, systemd daily backup service/timer content, and recent-backup verification commands in the runbook.

### Finding 2 from round 1: nginx upload limit

Status: CLOSED.

Evidence:

- `deploy/nginx/promo_v2.conf.example:1`-`7` keeps nginx on port `8080` and sets `client_max_body_size 128m`, covering the 100 MB stage-1 run limit plus multipart overhead.
- `apps/web/tests.py:42`-`53` parses `deploy/nginx/promo_v2.conf.example` and asserts `client_max_body_size >= 128m`, while preserving `listen 8080`, no `listen 80`, and proxying to `127.0.0.1:8000`.
- `docs/testing/TEST_REPORT_TASK_010.md:14`-`17` and `docs/testing/TEST_REPORT_TASK_010.md:55` record the audit-fix update and the readiness status for the nginx upload deployment limit.

### Unrelated scope check

No evidence was found in the scoped TASK-010 deployment/readiness artifacts that WB/Ozon business logic, rights model, check/process separation, or audit/techlog cleanup semantics were changed to close these findings.

Scope note: `/home/pavel/projects/promo_v2` is not a git repository in this environment, so VCS changed-set verification was unavailable. Static review was limited to the files listed in the round-2 audit scope and targeted searches across deployment docs/scripts/tests.

## Commands

All commands were run from `/home/pavel/projects/promo_v2`.

| Command | Result |
| --- | --- |
| `git status --short` | not available: `fatal: not a git repository (or any of the parent directories): .git` |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check` | pass: `System check identified no issues (0 silenced).` |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.web.tests.DeploymentReadinessTests` | pass: 3 tests, OK |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test` | pass: 100 tests, OK |

## Risks / Notes

- Production systemd/nginx reloads and production backup writes were not executed during this audit.
- Formal WB/Ozon acceptance is still not complete until ADR-0013 customer artifacts are provided; this is an artifact gate, not a new GAP.

## Итог

PASS. TASK-010 can be passed to an independent tester for deployment/readiness verification.
