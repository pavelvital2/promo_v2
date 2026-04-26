# TASK-006: Audit, Techlog, Notifications

## ID

TASK-006-audit-techlog-notifications

## Роль агента

Разработчик Codex CLI, audit/techlog.

## Цель

Реализовать раздельные audit records, techlog records, sensitive visibility and system notifications without mixing them with operations.

## Task-scoped входные документы

- `AGENTS.md`
- `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/audit/AUDIT_PROTOCOL.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/DELETION_ARCHIVAL_POLICY.md`
- `docs/gaps/GAP_REGISTER.md` closed GAP-0009
- `docs/adr/ADR_LOG.md` ADR-0014
- `docs/testing/TEST_PROTOCOL.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`

## Релевантные разделы ТЗ

- §20
- §21
- §22.6
- §23.1
- §27

## Разрешённые файлы / области изменения

- Audit Django app.
- Techlog Django app.
- Notifications model/service.
- Server-rendered list/card templates for audit/techlog if not deferred to TASK-009.
- Tests for visibility, filters, links and sensitive details.
- Documentation updates directly caused by implementation.

## Запрещённые области

- Storing business operation history only in audit/techlog.
- Showing sensitive technical details without `techlog.sensitive.view`.
- Implementing audit/techlog cleanup through ordinary UI.
- Changing WB reason/result codes.

## Зависимости

- TASK-001.
- TASK-002.
- TASK-005.

## Expected output

- Immutable audit records for significant user/admin actions.
- Techlog records for system events/errors/failures.
- Sensitive details protected by permission.
- Critical system notifications available for UI.
- Links to users, stores, operations where applicable.

## Acceptance criteria

- Audit and techlog are separate tables/services and separate UI concepts.
- Limited log scope hides objects outside user access.
- Sensitive details are unavailable without the specific right.
- No ordinary UI deletion of audit/techlog records exists.
- Audit/techlog retention is 90 days and cleanup, if implemented in this task, is a regulated non-UI procedure.

## Required checks

- Unit tests for audit/techlog creation.
- Permission tests for limited/full/sensitive visibility.
- Integration test linking operation to audit/techlog.
- Django system check.

## Handoff format

Использовать формат из `docs/tasks/implementation/stage-1/README.md`; explicitly state how 90-day retention and non-UI cleanup are handled or deferred.

## Gaps/blockers

No open audit/techlog retention gap remains for GAP-0009. Do not add ordinary UI deletion for audit/techlog records.
