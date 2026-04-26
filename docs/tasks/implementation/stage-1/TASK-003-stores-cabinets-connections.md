# TASK-003: Stores, Cabinets, Connections

## ID

TASK-003-stores-cabinets-connections

## Роль агента

Разработчик Codex CLI, stores/connections.

## Цель

Реализовать группы/бренды, магазины/кабинеты, карточки, историю изменений, object access binding и API-блок как подготовку этапа 2 без использования API для расчёта скидок этапа 1.

## Task-scoped входные документы

- `AGENTS.md`
- `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/product/UI_SPEC.md` разделы магазинов/кабинетов/подключений
- `docs/architecture/DELETION_ARCHIVAL_POLICY.md`
- `docs/product/modules/README.md` Stores & Connections
- `docs/adr/ADR_LOG.md` ADR-0003, ADR-0006, ADR-0008
- `docs/testing/TEST_PROTOCOL.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`

## Релевантные разделы ТЗ

- §8
- §11
- §21
- §23.2
- §27

## Разрешённые файлы / области изменения

- Stores/connections Django app.
- Models/migrations for `BusinessGroup`, `StoreAccount`, `ConnectionBlock`, store history.
- Store/cabinet server-rendered views and templates needed for CRUD/history.
- Tests for object access and history.
- Documentation updates directly caused by implementation.

## Запрещённые области

- API-загрузка или API-расчёт скидок.
- WB/Ozon business rules.
- Изменение прав владельца и seed roles.
- Скрытое хранение secrets without protected reference model.

## Зависимости

- TASK-001.
- TASK-002 for users/permissions/object access.
- ADR-0008 accepted for `STORE-NNNNNN`.

## Expected output

- Store/cabinet records with visible IDs `STORE-NNNNNN`.
- Business groups and store/cabinet cards.
- Connection block marked as stage 2 preparation.
- Store access checks applied to views/actions.
- Change history for significant store/cabinet changes.

## Acceptance criteria

- Пользователь без object access не видит магазин и связанные данные.
- Локальный администратор управляет только назначенными магазинами/кабинетами.
- API-блок не используется для Excel discounts stage 1.
- Store history records significant changes without exposing protected secrets.

## Required checks

- Model/migration tests.
- Permission/object access tests.
- UI smoke tests for list/card/forms.
- Django system check.

## Handoff format

Использовать формат из `docs/tasks/implementation/stage-1/README.md`; явно указать, как реализован protected secret reference и какие поля истории сохраняются.

## Gaps/blockers

Если для реального secret storage нужен инфраструктурный выбор, зафиксировать его как implementation decision или gap, не раскрывая secret values в audit/UI/logs.
