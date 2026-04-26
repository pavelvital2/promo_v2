# User-Mode Deployment Report

Дата: 2026-04-26

## Scope

Выполнен user-mode preview deployment текущего Django-проекта без sudo, без изменений системного nginx/systemd, без занятия port `80` и без использования upstream `8000`.

## Runtime

- URL: `http://23.26.193.117:8080/`
- Local URL: `http://127.0.0.1:8080/`
- Health URL: `http://127.0.0.1:8080/health/`
- Bind: `0.0.0.0:8080`
- Gunicorn master PID: `421762`
- PID file: `run/gunicorn-8080.pid`
- Logs:
  - `logs/gunicorn-8080-access.log`
  - `logs/gunicorn-8080-error.log`

Запуск выполнен командой:

```bash
cd /home/pavel/projects/promo_v2
set -a && . ./.env.runtime && set +a
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres \
  .venv/bin/gunicorn config.wsgi:application \
  --bind 0.0.0.0:8080 \
  --workers 3 \
  --timeout 120 \
  --pid run/gunicorn-8080.pid \
  --access-logfile logs/gunicorn-8080-access.log \
  --error-logfile logs/gunicorn-8080-error.log \
  --daemon
```

## Environment

- Runtime env file: `.env.runtime`
- Git status: файл env не коммитится; он покрыт правилом `.env.*` в `.gitignore`.
- `DJANGO_SECRET_KEY`: generated locally, not documented.
- PostgreSQL:
  - `POSTGRES_DB=promo_v2`
  - `POSTGRES_USER=postgres`
  - `POSTGRES_HOST=127.0.0.1`
  - `POSTGRES_PORT=5432`
- `DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,23.26.193.117`
- `DJANGO_DEBUG=true`
- `DJANGO_STATIC_ROOT=staticfiles`
- `DJANGO_MEDIA_ROOT=media`

`DJANGO_DEBUG=true` выбран для safest working preview configuration: текущий user-mode запуск не настраивает nginx/static alias и не меняет Django URL/config. `collectstatic` выполнен в project-local `staticfiles`, но gunicorn сам по себе не обслуживает `/static/`; проверка `/static/admin/css/base.css` возвращает `404`. Для production нужен nginx/systemd baseline из runbook либо отдельное утверждённое static serving решение.

## Port Check

Read-only проверка портов перед запуском:

- `8080`: свободен, выбран для deployment.
- `8081`: занят существующим listener.
- `8010`: свободен.
- `8000`: занят старой Python-программой, не трогался.

После запуска `8080` слушает gunicorn master/worker processes.

## Checks

Выполнено:

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py migrate --noinput
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py collectstatic --noinput
curl -fsS -i http://127.0.0.1:8080/health/
curl -fsS -i http://23.26.193.117:8080/health/
curl -fsS -i http://127.0.0.1:8080/
curl -fsS -i http://127.0.0.1:8080/accounts/login/
```

Результаты:

- `manage.py check`: `System check identified no issues (0 silenced).`
- `migrate --noinput`: `No migrations to apply.`
- `collectstatic --noinput`: `127 static files copied to '/home/pavel/projects/promo_v2/staticfiles'.`
- `/health/`: `200 OK`, body `{"status": "ok"}`.
- `/`: `302 Found` to `/accounts/login/?next=/`.
- `/accounts/login/`: `200 OK`.

## Stop Command

Остановить user-mode gunicorn:

```bash
cd /home/pavel/projects/promo_v2
kill "$(cat run/gunicorn-8080.pid)"
```

Проверить остановку:

```bash
ss -ltnp '( sport = :8080 )'
```

## Production Limitations

- Это preview deployment пользовательским процессом, не production rollout.
- Системные `nginx` и `systemd` не изменялись и не перезапускались.
- Port `80` не использовался.
- Upstream `127.0.0.1:8000` не использовался, старая программа на `8000` не трогалась.
- Static/media production serving через nginx не настроен в рамках этой задачи.
