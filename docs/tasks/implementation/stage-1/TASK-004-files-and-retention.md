# TASK-004: Files and Retention

## ID

TASK-004-files-and-retention

## Роль агента

Разработчик Codex CLI, files/storage.

## Цель

Реализовать файловый контур: metadata, versions, physical storage, checksums, operation-ready links, retention rules and download permission checks.

## Task-scoped входные документы

- `AGENTS.md`
- `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/DELETION_ARCHIVAL_POLICY.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/adr/ADR_LOG.md` ADR-0003, ADR-0006, ADR-0008, ADR-0012, ADR-0014
- `docs/testing/TEST_PROTOCOL.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`

## Релевантные разделы ТЗ

- §13
- §17
- §21
- §22
- §23.2
- §24
- §27

## Разрешённые файлы / области изменения

- Files/storage Django app.
- Models/migrations for `FileObject`, `FileVersion`, operation link placeholders if needed.
- Upload/download services and validation shared by WB/Ozon tasks.
- Retention metadata and cleanup command for physical files after approved fixed file-retention rule.
- Tests for versions, checksum, download rights and retention behavior.

## Запрещённые области

- Deleting operation metadata/history when physical file expires.
- Overwriting existing file versions.
- Implementing WB/Ozon calculation logic.
- Weakening approved backup policy from ADR-0012.

## Зависимости

- TASK-001.
- TASK-002 for permissions.
- TASK-003 for store access.
- ADR-0008 accepted for `FILE-YYYY-NNNNNN`.

## Expected output

- File metadata and versioning work.
- Upload creates new `FileVersion` even for same original name.
- Checksum stored.
- Physical files retain according to documented 3-day file rule; metadata/history retained according to docs.
- Download enforces scenario permission, object access and retention availability.

## Acceptance criteria

- Completed operation file links cannot be overwritten by file replacement.
- Expired physical file is unavailable for download but historical metadata remains.
- Observer cannot download output/detail by default.
- File storage is compatible with later WB/Ozon task requirements.

## Required checks

- Unit tests for versioning/checksum.
- Permission tests for download.
- Retention behavior tests.
- Django system check.

## Handoff format

Использовать формат из `docs/tasks/implementation/stage-1/README.md`; указать storage path strategy and retention command behavior.

## Gaps/blockers

No open backup policy gap remains for GAP-0007. If retention cleanup for audit/techlog is requested, follow ADR-0014 and do not add ordinary UI deletion.
