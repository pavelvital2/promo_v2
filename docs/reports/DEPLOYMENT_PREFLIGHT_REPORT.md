# DEPLOYMENT_PREFLIGHT_REPORT.md

Дата: 2026-04-25 21:42 MSK.

Роль: DevOps/deployment preflight agent. Проверка выполнена безопасными read-only командами на текущем сервере. Systemd/nginx не изменялись, сервисы не перезапускались, production paths не создавались и не модифицировались. `migrate` не запускался.

## Status

`PARTIAL`

Кодовая копия и Django/PostgreSQL readiness выглядят готовыми к следующему deployment gate, но фактический rollout заблокирован до выбора deployment параметров и отдельного разрешения на privileged/system changes. На текущем сервере есть инфраструктурные конфликты, которые нужно учесть до установки:

- порт `80` уже занят активным `nginx.service`;
- порт `8000`, который указан как gunicorn upstream в `deploy/systemd/promo_v2.service.example`, уже занят процессом `/home/pavel/projects/promo/.venv/bin/python -m promo.presentation`;
- `sudo -n true` не проходит: текущему пользователю нужен интерактивный пароль для sudo;
- baseline production directories отсутствуют: `/opt/promo_v2`, `/etc/promo_v2`, `/var/lib/promo_v2`, `/var/backups/promo_v2`, `/var/www/promo_v2`;
- `nginx -T` без sudo не может завершить полный config dump из-за `Permission denied` на `/run/nginx.pid`, хотя синтаксис до этого этапа сообщает `syntax is ok`.

## Documents Read

- `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md`
- `docs/testing/TEST_REPORT_TASK_010_FINAL.md`
- `docs/reports/STAGE_1_FINAL_STATUS_REPORT.md`
- `deploy/nginx/promo_v2.conf.example`
- `deploy/systemd/promo_v2.service.example`
- `deploy/systemd/promo_v2-daily-backup.service.example`
- `deploy/systemd/promo_v2-daily-backup.timer.example`
- `.env.example`
- `README.md`

## Environment Findings

| Area | Result |
| --- | --- |
| Current user | `pavel`, uid/gid `1000`, groups include `sudo`, `docker` |
| Non-interactive sudo | unavailable: `sudo -n true` exits `1`, `sudo: a password is required` |
| Python | `/usr/bin/python3`, Python `3.12.3`; `.venv/bin/python` also Python `3.12.3` |
| Gunicorn | `.venv/bin/gunicorn`, version `23.0.0` |
| Django entrypoint | `manage.py` exists and is executable |
| Django check | `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check` passed: `System check identified no issues (0 silenced).` |
| PostgreSQL client | `/usr/bin/psql` |
| PostgreSQL access | `PGPASSWORD=postgres psql -h 127.0.0.1 -p 5432 -U postgres -d postgres` works |
| PostgreSQL version | PostgreSQL `16.13` on Ubuntu |
| Database `promo_v2` | exists |
| Django migrations table | reachable; `django_migrations` count is `32` |
| Migration plan | `manage.py migrate --plan` reports `No planned migration operations.` |
| Collectstatic safety check | `collectstatic --dry-run` with temporary `DJANGO_STATIC_ROOT` succeeded and reported `127 static files` |
| Port `80` | occupied, listener on `0.0.0.0:80` |
| Port `8080` | free in `ss` output |
| Port `8000` | occupied on `127.0.0.1:8000` by PID `23306`, command `/home/pavel/projects/promo/.venv/bin/python -m promo.presentation` |
| nginx | installed at `/usr/sbin/nginx`, version `1.24.0`, `nginx.service` active and enabled |
| systemd | installed at `/usr/bin/systemctl`, systemd `255` |
| Existing promo_v2 units | none listed by `systemctl list-unit-files 'promo_v2*'` and `systemctl list-units 'promo_v2*' --all` |
| nginx enabled sites | `orchestrator_v3`, `orchestrator_v4`, `promo`, `wb-parser-v1` |
| Production paths | `/opt/promo_v2`, `/etc/promo_v2`, `/var/lib/promo_v2`, `/var/backups/promo_v2`, `/var/www/promo_v2` are missing |

## Risks And Blockers

1. `PARTIAL` until operator provides final deployment inputs and approves privileged changes.
2. Upstream port conflict: baseline systemd example binds gunicorn to `127.0.0.1:8000`, but that port is currently used by another local application. Either free `8000` intentionally or approve a different upstream port and update nginx/systemd consistently.
3. Public port conflict: port `80` is already owned by existing nginx. The project nginx example intentionally uses `listen 8080`; using `80` requires a separate routing/server_name decision.
4. No non-interactive sudo. Commands that install directories, units, nginx configs, reload services or create production paths need an interactive sudo session or another approved privilege path.
5. Production filesystem layout has not been created. Deployment cannot proceed until `/opt/promo_v2`, `/etc/promo_v2`, `/var/lib/promo_v2`, `/var/backups/promo_v2`, `/var/www/promo_v2` ownership and permissions are explicitly approved.
6. Production secrets are not available in this working copy. `.env.example` contains only placeholders such as `DJANGO_SECRET_KEY=change-me`.
7. Formal WB/Ozon production acceptance remains `blocked_by_artifact_gate` per final stage status; this is not a deployment mechanics defect, but it blocks production acceptance sign-off.

## Commands Executed

```bash
id
whoami
sudo -n true
command -v python3
python3 --version
test -x .venv/bin/python && .venv/bin/python --version
test -x .venv/bin/gunicorn && .venv/bin/gunicorn --version
test -f manage.py && ls -l manage.py
command -v psql
PGPASSWORD=postgres psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -Atc "select current_user, current_database(), version();"
PGPASSWORD=postgres psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -Atc "select datname from pg_database where datname='promo_v2';"
ss -ltnp '( sport = :80 or sport = :8080 or sport = :8000 )'
command -v nginx
nginx -v
command -v systemctl
systemctl --version | sed -n '1,2p'
systemctl is-active nginx
systemctl is-enabled nginx
systemctl status nginx --no-pager --lines=0
for p in /opt/promo_v2 /etc/promo_v2 /var/lib/promo_v2 /var/backups/promo_v2 /var/www/promo_v2; do if [ -e "$p" ]; then ls -ld "$p"; else printf 'missing %s\n' "$p"; fi; done
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check
tmpdir=$(mktemp -d /tmp/promo_v2_collectstatic_preflight.XXXXXX); POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres DJANGO_STATIC_ROOT="$tmpdir/static" .venv/bin/python manage.py collectstatic --noinput --dry-run; status=$?; rm -rf "$tmpdir"; exit $status
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py migrate --plan
ps -fp 23306
systemctl list-unit-files 'promo_v2*' --no-pager
systemctl list-units 'promo_v2*' --all --no-pager
ls -la /etc/nginx/sites-enabled /etc/nginx/conf.d
nginx -T
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py dbshell -- -Atc "select count(*) from django_migrations;"
```

## Safe Next Commands After Approval

These are the exact next deployment commands that are reasonable after the operator confirms inputs and grants permission for production changes. Do not run them without a separate orchestrator task/approval.

```bash
cd /home/pavel/projects/promo_v2
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py migrate --plan
```

If privileged deployment is approved and the deployment target remains the documented baseline:

```bash
sudo install -d -o www-data -g www-data -m 0750 /opt/promo_v2 /etc/promo_v2 /var/lib/promo_v2/media /var/backups/promo_v2/postgres /var/backups/promo_v2/media
sudo install -d -o www-data -g www-data -m 0755 /var/www/promo_v2/static
sudo install -m 0640 -o root -g www-data <approved-production-env-file> /etc/promo_v2/env
```

Because `127.0.0.1:8000` is currently occupied, choose one of these before installing service/nginx configs:

```bash
# Option A: free 127.0.0.1:8000 through the owner of PID 23306, then use the examples unchanged.

# Option B: approve a different upstream, for example 127.0.0.1:8001, and update both:
# - deploy/systemd/promo_v2.service.example ExecStart --bind
# - deploy/nginx/promo_v2.conf.example proxy_pass
```

After production env, paths and port decision are approved:

```bash
cd /opt/promo_v2
. .venv/bin/activate
set -a && . /etc/promo_v2/env && set +a
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres python manage.py check
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres python manage.py migrate --noinput
python manage.py collectstatic --noinput
sudo nginx -t
```

Service install/start/reload remains a separate privileged rollout step:

```bash
sudo install -m 0644 deploy/systemd/promo_v2.service.example /etc/systemd/system/promo_v2.service
sudo install -m 0644 deploy/systemd/promo_v2-daily-backup.service.example /etc/systemd/system/promo_v2-daily-backup.service
sudo install -m 0644 deploy/systemd/promo_v2-daily-backup.timer.example /etc/systemd/system/promo_v2-daily-backup.timer
sudo systemctl daemon-reload
sudo systemctl enable --now promo_v2
sudo systemctl enable --now promo_v2-daily-backup.timer
sudo nginx -t
sudo systemctl reload nginx
BASE_URL=http://127.0.0.1:8080 POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/deployment_smoke_check.sh
```

## Required Deployment Inputs

- Production domain/server_name and whether public entrypoint should be existing `80/443` nginx routing or the documented `8080` listener.
- Production `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, and `DJANGO_CSRF_TRUSTED_ORIGINS`.
- Approved installation path. Baseline docs use `/opt/promo_v2`.
- Approved runtime user/group and file ownership. Baseline docs use `www-data:www-data`.
- Decision for upstream bind conflict on `127.0.0.1:8000`: free the port or use another local port.
- PostgreSQL production parameters: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`.
- Backup paths and retention confirmation. Baseline: `/var/backups/promo_v2/postgres`, `/var/backups/promo_v2/media`, retention `14` days.
- Static/media paths confirmation. Baseline: `/var/www/promo_v2/static`, `/var/lib/promo_v2/media`.
- Sudo/access mode for privileged changes. Current user `pavel` has sudo group membership but no non-interactive sudo.

