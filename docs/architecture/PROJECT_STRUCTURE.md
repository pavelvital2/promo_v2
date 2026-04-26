# PROJECT_STRUCTURE.md

Трассировка: ТЗ §26.5, §27.

## Документационная структура

Корень проекта содержит:

- `itogovoe_tz_platforma_marketplace_codex.txt` - источник истины;
- `promt_start_project.txt` - стартовая инструкция оркестратора;
- `AGENTS.md` - короткая точка входа Codex CLI;
- `docs/README.md` и `docs/DOCUMENTATION_MAP.md` - карта документации;
- `docs/orchestration/` - правила агентов, оркестрация, шаблоны, handoff и protocols;
- `docs/architecture/` - архитектурные документы этапа 1;
- `docs/product/` - UI, права, операции и WB/Ozon specs;
- `docs/tasks/implementation/stage-1/` - задачи реализации этапа 1.

## Будущая структура кода

Стек этапа 1 утверждён в ADR-0006: Django + PostgreSQL + server-rendered UI / Django templates. До отдельной задачи реализации код продукта не создаётся.

Будущая структура кода должна быть Django-проектом с доменными Django apps или внутренними пакетами, которые явно разделяют:

- identity/access;
- stores/connections;
- products;
- operations/execution;
- files/storage;
- discounts/wb/excel;
- discounts/ozon/excel;
- settings;
- audit;
- tech log;
- exports;
- UI;
- tests;
- deployment/runbooks.

Точные имена Django project/apps фиксируются задачей `docs/tasks/implementation/stage-1/TASK-001-project-bootstrap.md` и не должны смешивать независимые доменные границы.

## Правила размещения

- WB и Ozon Excel logic размещаются в разных модульных областях.
- Общая модель operations/files/settings не дублируется в marketplace-модулях.
- API-блоки будущего этапа не должны смешиваться с Excel-process logic.
- Tests располагаются рядом с кодом или в выделенном тестовом контуре по выбранному стеку, но должны сохранять traceability на ТЗ/спецификации.

## Запреты

- Не создавать код продукта на фазе подготовки документации.
- Не смешивать будущие production entities с рабочими сущностями этапа 1 без архитектурной необходимости.
- Не использовать старую программу как архитектурную основу.

## Фактическая bootstrap-структура TASK-001

TASK-001 создал минимальный Django scaffold без прикладной бизнес-логики:

- `manage.py` - Django CLI entrypoint;
- `config/` - settings, URLConf, ASGI/WSGI;
- `apps/` - пустые доменные Django apps по границам архитектуры;
- `templates/base.html` и `apps/web/templates/web/home.html` - минимальная server-rendered template shell;
- `apps/web/` - только bootstrap routes `/` и `/health/`;
- `requirements.txt` и `.env.example` - зависимости и env baseline для PostgreSQL-ready settings;
- `deploy/nginx/` и `deploy/systemd/` - deployment placeholders для nginx/systemd.

Команды локальной проверки bootstrap:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
# Настроить PostgreSQL env values до migrate/runserver.
python manage.py check
python manage.py test
python manage.py runserver 127.0.0.1:8000
```
