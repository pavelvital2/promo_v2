# TEST_REPORT_TASK_001

Дата тестирования: 2026-04-25

Роль: независимый тестировщик Codex CLI.

## Статус

PASS

TASK-001 bootstrap готов к приемке в проверенном контуре: Django imports/check проходят, миграции инспектируются и локальная БД не требует unapplied migrations, smoke health route проходит, deployment skeleton присутствует и сохраняет nginx port `8080`.

## Ограничение области

Проверка выполнялась в текущей рабочей копии проекта, где уже присутствуют реализации последующих задач stage 1. Поэтому глобальное сканирование `apps/` показывает WB/Ozon Excel, operations, audit, files и UI-логику последующих TASK-003..TASK-010. Это не трактуется как дефект TASK-001 bootstrap, но означает, что критерий "нет WB/Ozon business logic in TASK-001" невозможно независимо подтвердить по всей текущей рабочей копии как чистому snapshot TASK-001.

## Проверенные сценарии

| Сценарий | Результат |
| --- | --- |
| Project dependencies and Python environment | PASS |
| Django project imports and system check | PASS |
| Migrations can be inspected | PASS |
| Local/test DB migration readiness | PASS |
| Basic health route if present | PASS |
| Bootstrap-safe focused tests | PASS |
| Deploy skeleton exists | PASS |
| nginx skeleton preserves port `8080`; port `80` remains occupied | PASS |
| `apps.core` focused tests | N/A: `apps.core` отсутствует |
| No WB/Ozon business logic expected in TASK-001 | PASS for bootstrap/deploy scope; residual risk for current full workspace snapshot |

## Команды

| Команда | Результат |
| --- | --- |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python --version` | `Python 3.12.3` |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python -m pip check` | `No broken requirements found.` |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check` | `System check identified no issues (0 silenced).` |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py showmigrations --plan` | PASS; migration graph loads, listed migrations are applied in local DB |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py migrate --check` | PASS; exit code 0, no unapplied migrations reported |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py makemigrations --check --dry-run` | `No changes detected`; exit code 0 |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.web` | PASS; `Ran 16 tests ... OK` |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.web.tests.BootstrapSmokeTests` | PASS; health route smoke `Ran 1 test ... OK` |
| `ss -H -tulpen 'sport = :8080'` | PASS; no listener, port free |
| `ss -H -tulpen 'sport = :80'` | PASS for expected conflict; `nginx.service` listens on `0.0.0.0:80` |

## Наблюдения

- `deploy/nginx/promo_v2.conf.example` содержит `listen 8080;` и upstream `proxy_pass http://127.0.0.1:8000;`.
- `deploy/systemd/promo_v2.service.example` содержит `gunicorn config.wsgi:application --bind 127.0.0.1:8000`.
- `README.md` документирует, что nginx example использует `8080`, потому что `80` занят существующим nginx service.
- Health route присутствует как `web:health` на `/health/` и возвращает `{"status": "ok"}` по smoke test.
- `apps.core` отсутствует, поэтому вместо него использованы bootstrap-safe тесты `apps.web`.

## Остаточные риски

- Текущая рабочая копия уже включает продуктовую WB/Ozon логику последующих задач, поэтому отчет не подтверждает историческую чистоту snapshot TASK-001 по всему дереву `apps/`.
- `migrate --check` подтверждает состояние текущей локальной БД с заданными env `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres`; отдельное применение миграций на новой пустой базе не выполнялось вручную, но тесты `apps.web` успешно создали и удалили test database.
- Перед production rollout порт nginx нужно повторно проверить на целевом сервере.
