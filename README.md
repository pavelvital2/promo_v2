# Promo V2

Stage 1 bootstrap for a Django + PostgreSQL modular monolith with server-rendered Django templates.

## Local Bootstrap

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Configure PostgreSQL values in .env before running migrations or runserver.
python manage.py check
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

The bootstrap includes only empty domain apps, a base template shell, and smoke routes. WB/Ozon business logic, roles, permissions, operations, files, audit, and tech log implementation are intentionally reserved for later tasks.

## Deployment Skeleton

The nginx example in `deploy/nginx/promo_v2.conf.example` listens on port `8080`. TASK-001 audit changed the placeholder from `80` because port `80` is already occupied by the server's existing nginx service.

The Django upstream remains `127.0.0.1:8000`; `deploy/systemd/promo_v2.service.example` runs `gunicorn config.wsgi:application` on that upstream.

TASK-010 operational scripts:

- `scripts/pre_update_backup.sh` runs mandatory PostgreSQL and media backups before production updates.
- `scripts/restore_check.sh` validates backup archives and can restore into a non-production database via `RESTORE_DB`.
- `scripts/deployment_smoke_check.sh` runs `manage.py check` and verifies `/health/` through nginx.
- `scripts/audit_techlog_retention_check.sh` runs the regulated non-UI audit/techlog retention check.
