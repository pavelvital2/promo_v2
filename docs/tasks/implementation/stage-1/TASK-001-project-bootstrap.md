# TASK-001: Project Bootstrap

## ID

TASK-001-project-bootstrap

## Роль агента

Разработчик Codex CLI, Django bootstrap.

## Цель

Создать минимальный Django + PostgreSQL каркас этапа 1 с server-rendered UI / Django templates, базовой структурой модулей, конфигурацией тестов и deployment skeleton без реализации бизнес-логики WB/Ozon.

## Task-scoped входные документы

- `AGENTS.md`
- `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/PROJECT_STRUCTURE.md`
- `docs/stages/stage-1/PROJECT_DOCUMENTATION_PLAN.md`
- `docs/adr/ADR_LOG.md` ADR-0001, ADR-0002, ADR-0003, ADR-0005, ADR-0006
- `docs/gaps/GAP_REGISTER.md`
- `docs/testing/TEST_PROTOCOL.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`

## Релевантные разделы ТЗ

- §1.4
- §3.1-§3.4
- §4
- §22
- §25-§27

## Разрешённые файлы / области изменения

- Django project/app scaffold.
- Project dependency/config files.
- Test configuration.
- Deployment skeleton for nginx/systemd placeholders.
- Documentation updates directly caused by bootstrap.

## Запрещённые области

- WB/Ozon business logic.
- Product code for discounts, operations execution details, audit catalogs beyond skeleton.
- API-режим скидок.
- Изменение итогового ТЗ и утверждённых ADR.

## Зависимости

- Повторный аудит документации допускает старт реализации.
- `GAP-0001`, `GAP-0005`, `GAP-0006` закрыты.

## Expected output

- Рабочий Django project skeleton.
- PostgreSQL-ready settings with environment-based configuration.
- Server-rendered base template shell.
- Empty domain apps or packages matching `docs/architecture/ARCHITECTURE.md`.
- Basic health/smoke route.
- Initial test runner setup.

## Acceptance criteria

- Приложение стартует локально.
- Smoke test проходит.
- Структура явно разделяет доменные области.
- Нет бизнес-логики WB/Ozon.
- Документация обновлена по protocol, если появились новые команды/структура.

## Required checks

- Install/dependency check.
- Django system check.
- Unit/smoke tests.
- Проверка отсутствия продуктовой WB/Ozon логики в bootstrap.

## Handoff format

Использовать формат из `docs/tasks/implementation/stage-1/README.md` и передать аудитору bootstrap scope.

## Gaps/blockers

Если выбор конкретной Excel library, production web server binding или deployment command требует решения вне bootstrap, зафиксировать вопрос в handoff или `docs/gaps/GAP_REGISTER.md` по правилу `AGENTS.md`.
