# STAGE_1_ACCEPTANCE_EXECUTION_PLAN.md

Трассировка: ТЗ §22, §24, §25-§27.

## Scope

Executable acceptance plan for TASK-010. Formal WB/Ozon comparison remains `blocked_by_artifact_gate` until the artifacts listed in `docs/testing/CONTROL_FILE_REGISTRY.md` are delivered and recorded.

## Environment

Baseline stack: Django + PostgreSQL + server-rendered UI.

Use PostgreSQL credentials required by TASK-010:

```bash
export POSTGRES_DB=promo_v2
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
```

Nginx acceptance uses port `8080`. Do not move the project skeleton back to port `80` without a new deployment decision.

## Automated Checks

Run from repository root:

```bash
. .venv/bin/activate
python manage.py check
python manage.py test
```

## Deployment Smoke

Local/server smoke check:

```bash
. .venv/bin/activate
BASE_URL=http://127.0.0.1:8080 POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/deployment_smoke_check.sh
```

Expected result:

- `python manage.py check` passes;
- `/health/` returns `{"status": "ok"}`;
- nginx is still configured to listen on `8080`.

## Backup/Restore Check

Pre-update backup:

```bash
. .venv/bin/activate
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/pre_update_backup.sh
```

Manual restore check, never over production:

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres \
  ./scripts/restore_check.sh <postgres_dump> <media_tar_gz>

POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres RESTORE_DB=promo_v2_restore_check_<timestamp> \
  ./scripts/restore_check.sh <postgres_dump> <media_tar_gz>
```

Expected result:

- PostgreSQL dump is readable by `pg_restore --list`;
- media archive is readable by `tar -tzf`;
- optional `RESTORE_DB` restore succeeds in a non-production database;
- manual verification confirms users, stores, operations, file versions, parameter snapshots and audit/techlog links.

## Audit/Techlog Retention Check

```bash
. .venv/bin/activate
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/audit_techlog_retention_check.sh
```

Expected result:

- dry-run prints expired audit/techlog counts;
- cleanup is applied only with `APPLY_CLEANUP=1` under regulated non-UI procedure;
- operations, file metadata, parameter snapshots and detail rows remain untouched.

## Acceptance Area Matrix

| Area | Test IDs | Execution | Expected TASK-010 status |
| --- | --- | --- | --- |
| WB formal comparison | ACC-WB-001..ACC-WB-008 | Run after customer artifacts are registered in `CONTROL_FILE_REGISTRY.md` | blocked_by_artifact_gate |
| Ozon formal comparison | ACC-OZ-001..ACC-OZ-005 | Run after customer artifacts are registered in `CONTROL_FILE_REGISTRY.md` | blocked_by_artifact_gate |
| Operations | ACC-OPS-001..ACC-OPS-002 | Automated tests plus UI smoke | pass if suite passes |
| Files/retention | ACC-FILE-001..ACC-FILE-002 | Automated tests plus `cleanup_file_retention --dry-run` where relevant | pass if suite passes |
| Security/access | ACC-SEC-001 | Automated tests plus owner/limited UI smoke | pass if suite passes |
| Audit/techlog | ACC-AUD-001 | Automated tests plus `audit_techlog_retention_check.sh` | pass if suite passes |
| Deployment | Release/update runbook | `deployment_smoke_check.sh` against running nginx/systemd | pass only after server smoke succeeds |
| Backup/restore | ADR-0012 policy | `pre_update_backup.sh` and `restore_check.sh` in safe contour | pass only after manual restore check succeeds |

## Formal WB/Ozon Execution After Artifact Delivery

1. Register every control set in `CONTROL_FILE_REGISTRY.md`.
2. Verify checksums before test execution.
3. Run check mode and process mode through the UI or approved management/test harness.
4. Compare output workbook only by allowed cells/columns:
   - WB: `Новая скидка`; all other cells/rows unchanged.
   - Ozon: K and L only; all other columns/sheets unchanged.
5. Compare summary and row-level results against registered expected artifacts.
6. Record every difference with classification: old program defect, ТЗ issue, approved new-system difference, or defect.

Formal acceptance is not complete while any required real customer artifact remains pending.
