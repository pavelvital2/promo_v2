# TASK-005: Operations, Run, Execution

## ID

TASK-005-operations-run-execution

## Роль агента

Разработчик Codex CLI, operations/execution.

## Цель

Реализовать operation/run model, statuses, check/process split, check-basis links, актуальность проверки, interrupted_failed handling and execution layer shell for WB/Ozon modules.

## Task-scoped входные документы

- `AGENTS.md`
- `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/adr/ADR_LOG.md` ADR-0003, ADR-0004, ADR-0006, ADR-0008
- `docs/testing/TEST_PROTOCOL.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`

## Релевантные разделы ТЗ

- §12
- §17
- §20
- §22
- §23
- §27

## Разрешённые файлы / области изменения

- Operations/execution Django app.
- Models/migrations for `Run`, `Operation`, operation-file links, snapshots, warning confirmations, detail row base model.
- Shared execution services/interfaces for check/process modules.
- Tests for statuses, immutability, актуальность check and interrupted_failed.

## Запрещённые области

- WB/Ozon row calculation rules.
- Using audit or techlog as replacement for operation records.
- Combining check and process into one operation.
- Auto-resume after failure.

## Зависимости

- TASK-001.
- TASK-002.
- TASK-003.
- TASK-004.
- ADR-0008 accepted for `OP-YYYY-NNNNNN` and `RUN-YYYY-NNNNNN`.

## Expected output

- `Run` and `Operation` records with approved visible IDs.
- Separate check/process operations.
- Process stores check basis.
- Check актуальность comparator covers marketplace, store, file set, file versions, parameters and logic version.
- Operations become immutable after completion.

## Acceptance criteria

- Pressing process without актуальная check creates separate check and then process only if allowed.
- Warnings confirmation is recorded when required.
- Failures move operation to `interrupted_failed` and do not auto-resume.
- Rerun creates new operations.

## Required checks

- Unit/integration tests for operation lifecycle.
- Tests for check-basis актуальность.
- Tests for immutable completed operation.
- Django system check.

## Handoff format

Использовать формат из `docs/tasks/implementation/stage-1/README.md`; include state transition summary and interfaces expected by WB/Ozon tasks.

## Gaps/blockers

If a module-specific status/reason code is missing, do not invent it in operations layer. Route to the relevant module task and `docs/gaps/GAP_REGISTER.md`.
