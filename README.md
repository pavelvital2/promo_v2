# Promo V2

Django + PostgreSQL modular monolith for WB/Ozon promotion discount workflows.

Current repository state: Stage 2.1 WB API is implemented and release-ready according to the Stage 2.1 release report. Stage 1 Excel workflows remain supported and are not replaced by the API mode.

## Current Scope

Implemented areas include:

- server-rendered Django web panel;
- users, roles, permissions and object access;
- marketplaces, stores/cabinets and API connection records;
- operation lifecycle, files, audit trail and tech log;
- WB and Ozon Stage 1 Excel check/process flows;
- WB Stage 2.1 API flow:
  - API connection and secret reference handling;
  - WB prices download and price Excel export;
  - WB current promotions download and promotion Excel exports for regular promotions with products;
  - WB discount calculation from API sources using the accepted WB logic;
  - explicit WB discount API upload flow with drift check and status polling;
  - Stage 2.1 UI screens, tests, audit and release evidence.

Stage 2.2 Ozon API is not part of the completed Stage 2.1 release scope.

## WB API Limitations

WB API current promotion support has an important boundary:

- regular current promotions can be listed, detailed and exported when WB returns product rows;
- WB auto promotions can be listed and their summary/details can be stored;
- WB `promotions/nomenclatures` does not provide product rows for auto promotions, so the application must not invent auto-promotion product rows from WB API data.

For WB auto-promotion calculations, an external product source is still required, for example an export from the WB seller cabinet. WB API can still be used separately for product cards, stocks, orders and sales where those APIs are available.

This decision is formalized in `docs/adr/ADR_LOG.md` as ADR-0021.

## Documentation

Start with:

- `docs/DOCUMENTATION_MAP.md` - documentation navigation map;
- `docs/stages/stage-2/STAGE_2_SCOPE.md` - Stage 2 split and boundaries;
- `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md` - executable Stage 2.1 WB scope;
- `docs/tasks/implementation/stage-2/IMPLEMENTATION_TASKS.md` - TASK-011..TASK-017 index;
- `docs/reports/STAGE_2_1_WB_RELEASE_READINESS.md` - current release-readiness evidence;
- `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md` - release/update operations.

The source TZ remains the source of truth for audits and disputed requirements. Agents should use task-scoped reading packages instead of rereading the full TZ for every task.

## Local Development

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Configure PostgreSQL and Django values in .env before running migrations or runserver.
python manage.py check
python manage.py migrate
python manage.py test
python manage.py runserver 127.0.0.1:8000
```

The default settings are PostgreSQL-ready and read database values from environment variables:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

`manage.py runserver` performs Django's migration check and therefore requires a reachable PostgreSQL database with the configured credentials.

## Preview Deployment

The documented user-mode preview deployment runs gunicorn on port `8080` without changing system nginx/systemd:

- local health URL: `http://127.0.0.1:8080/health/`;
- public preview URL used in the deployment report: `http://23.26.193.117:8080/`;
- PID file: `run/gunicorn-8080.pid`;
- logs: `logs/gunicorn-8080-access.log`, `logs/gunicorn-8080-error.log`.

See `docs/reports/DEPLOYMENT_USER_MODE_REPORT.md` for the exact command and limitations.

## Deployment Skeleton

The nginx example in `deploy/nginx/promo_v2.conf.example` listens on port `8080`. TASK-001 audit changed the placeholder from `80` because port `80` is already occupied by the server's existing nginx service.

The Django upstream in the deployment skeleton remains `127.0.0.1:8000`; `deploy/systemd/promo_v2.service.example` runs `gunicorn config.wsgi:application` on that upstream. The preview deployment intentionally uses a separate user-mode `8080` process.

Operational scripts:

- `scripts/pre_update_backup.sh` runs mandatory PostgreSQL and media backups before production updates.
- `scripts/restore_check.sh` validates backup archives and can restore into a non-production database via `RESTORE_DB`.
- `scripts/deployment_smoke_check.sh` runs `manage.py check` and verifies `/health/` through nginx.
- `scripts/audit_techlog_retention_check.sh` runs the regulated non-UI audit/techlog retention check.
