# TASK-002: Auth, Users, Roles, Permissions

## ID

TASK-002-auth-users-roles-permissions

## Роль агента

Разработчик Codex CLI, identity/access.

## Цель

Реализовать пользователей, аутентификацию, роли, права, section access, индивидуальные разрешения/запреты, object access и seed-набор ролей по ADR-0007.

## Task-scoped входные документы

- `AGENTS.md`
- `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/DELETION_ARCHIVAL_POLICY.md`
- `docs/product/UI_SPEC.md` разделы администрирования пользователей/ролей/доступов
- `docs/adr/ADR_LOG.md` ADR-0001, ADR-0006, ADR-0007, ADR-0008
- `docs/gaps/GAP_REGISTER.md`
- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`

## Релевантные разделы ТЗ

- §8
- §11
- §20
- §21
- §23.2
- §27

## Разрешённые файлы / области изменения

- Identity/access Django app.
- User/role/permission models and migrations.
- Seed migrations/management commands for system roles/permissions.
- Auth views/templates needed for login/logout and admin user screens.
- Tests for permissions and owner protection.
- Related documentation updates.

## Запрещённые области

- WB/Ozon расчёты.
- Operations execution.
- Files storage implementation beyond object access dependencies.
- Изменение seed-решения ADR-0007 без заказчика.

## Зависимости

- TASK-001.
- ADR-0007 accepted.
- ADR-0008 accepted for `USR-NNNNNN`.

## Expected output

- Auth/login works with secure password storage.
- System roles and permissions are immutable through regular UI where required.
- Owner has full access and cannot be restricted by administrators.
- Direct deny overrides allow.
- Store/object access model exists for later store binding.
- Visible user identifiers follow `USR-NNNNNN`.

## Acceptance criteria

- Владелец не может быть удалён, заблокирован или лишён критичных прав администратором.
- Глобальный администратор не может ограничивать владельца.
- Локальный администратор ограничен object scope.
- Менеджер не управляет ролями и системными правами.
- Наблюдатель не меняет данные и не скачивает output/detail by default.

## Required checks

- Unit tests for permission resolution.
- Tests for owner protection.
- Tests for direct deny precedence.
- Migration/seed idempotency check.
- Django system check.

## Handoff format

Использовать формат из `docs/tasks/implementation/stage-1/README.md`; приложить seed-role summary и список permission codes.

## Gaps/blockers

Если найдено право, необходимое для UI/operation, но отсутствующее в `docs/product/PERMISSIONS_MATRIX.md`, не добавлять скрыто: обновить документацию по protocol и при спорности зафиксировать gap.
