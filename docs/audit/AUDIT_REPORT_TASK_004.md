# AUDIT_REPORT_TASK_004

Дата: 2026-04-25

Роль: Аудитор Codex CLI TASK-004 files and retention.

## status

PASS WITH REMARKS

Причина: blocker/major нарушений не найдено. Реализация соответствует основным требованиям TASK-004 по metadata/versioning/checksum/safe path/retention/download checks и не заходит в WB/Ozon Excel business logic или TASK-005. Есть minor-замечания по будущему pre-operation delete пути и дрейфу строки `FileObject` в `DATA_MODEL.md` относительно фактической per-version модели.

## checked scope

- Root/orchestration: `AGENTS.md`, `docs/README.md`, `docs/orchestration/AGENTS.md`, `docs/roles/READING_PACKAGES.md`.
- Task: `docs/tasks/implementation/stage-1/TASK-004-files-and-retention.md`.
- Architecture/product specs: `docs/architecture/FILE_CONTOUR.md`, `docs/architecture/DATA_MODEL.md` file/version parts, `docs/architecture/DELETION_ARCHIVAL_POLICY.md` file rules, `docs/product/PERMISSIONS_MATRIX.md` download/scenario rights, `docs/product/OPERATIONS_SPEC.md` file-operation relation concepts only.
- Code: `apps/files/**`; `apps/stores/**` and `apps/identity_access/**` only for object-access integration review.
- Sanity-only awareness: `apps/files/tests.py` was read, and `apps.files` tests were attempted but not treated as tester acceptance.

Audit did not change product code. Only this audit report was created.

## audit method

- Compared `FileObject` / `FileVersion` fields, migration and visible id behavior against task and architecture docs.
- Reviewed upload path for repeated versions, checksum persistence, raw filename handling and storage path construction.
- Reviewed retention cleanup command and service behavior for physical deletion with metadata/history refs preserved.
- Reviewed download permission path against scenario permission, store/object access, retention availability and direct deny helper behavior.
- Reviewed operation/run relation scope for placeholder-only implementation and absence of TASK-005 overreach.
- Searched checked scope for WB/Ozon workbook parsing, calculation rules, reason/result code logic and Excel business logic overreach.
- Reviewed deletion/archive protections for file metadata against `DELETION_ARCHIVAL_POLICY.md`.
- Reviewed `FILE_CONTOUR.md` TASK-004 hook for accuracy against implemented command/path behavior.
- Ran requested minimal sanity commands. Tests were only sanity, not a tester pass.

## findings

### blocker

None found.

### major

None found.

### minor

1. No explicit pre-operation erroneous-upload delete service is present.

   Required context: deletion policy allows erroneous file upload deletion before operation when there are no operation/audit/techlog/history links (`docs/architecture/DELETION_ARCHIVAL_POLICY.md:11`-`14`, `docs/architecture/DELETION_ARCHIVAL_POLICY.md:32`-`33`), and the operations spec expects an active scenario draft context that can upload, replace and delete files before operation start (`docs/product/OPERATIONS_SPEC.md:56`).

   Evidence: `FileObject.delete()` blocks deletion once any version exists (`apps/files/models.py:173`-`179`), and `FileVersion.delete()` always raises `ProtectedError` (`apps/files/models.py:236`-`237`). The implemented TASK-004 service surface has create/download/retention cleanup only (`apps/files/services.py:135`-`266`).

   Impact: current behavior is conservative and protects metadata/history, so it does not block TASK-004 acceptance. Before UI active-scenario work, developer should add or explicitly document a controlled pre-operation erroneous-upload deletion path if the orchestrator assigns that behavior to files/UI scope.

2. `DATA_MODEL.md` file row is not fully aligned with the implemented per-version storage metadata split.

   Required context: `DATA_MODEL.md` lists `FileObject` key fields as including `storage_path`, `size`, and `retention_until` (`docs/architecture/DATA_MODEL.md:34`), while `FileVersion` carries `checksum`, uploader and creation metadata (`docs/architecture/DATA_MODEL.md:35`). `FILE_CONTOUR.md` now documents per-version storage path and retention cleanup preserving `FileObject` / `FileVersion` metadata (`docs/architecture/FILE_CONTOUR.md:20`, `docs/architecture/FILE_CONTOUR.md:44`).

   Evidence: implementation keeps logical file metadata on `FileObject` (`apps/files/models.py:77`-`99`) and stores `storage_path`, `size`, checksum and `retention_until` on each `FileVersion` (`apps/files/models.py:188`-`210`). This split is coherent with repeated versions and with the path shape `.../<file_visible_id>/vNNNNNN/...`, but `DATA_MODEL.md:34` remains misleading for future implementers.

   Impact: no runtime defect found. Treat as documentation drift to clarify in a later documentation task; this audit was instructed not to edit docs except this report.

## conforming observations

- `FileObject` / `FileVersion` models and migration exist with store/scenario/kind metadata, version number, original name, content type, storage path, size, SHA-256 checksum, uploader, retention fields, physical status and placeholder refs (`apps/files/models.py:59`-`237`, `apps/files/migrations/0001_initial.py:18`-`70`).
- `FILE-YYYY-NNNNNN` visible id is generated from system timezone year and protected from ordinary update after creation (`apps/files/models.py:77`, `apps/files/models.py:126`-`164`), matching `DATA_MODEL.md:221`-`240` and `GAP_REGISTER.md:66`-`82`.
- Repeated upload to the same logical `FileObject` creates `version_no + 1` and a new storage path; existing versions are not overwritten (`apps/files/services.py:163`-`190`).
- Checksum is calculated while writing the physical file and persisted as `checksum_sha256` (`apps/files/services.py:94`-`115`, `apps/files/services.py:178`-`187`).
- Storage path is server-side and does not trust raw filenames: basename is stripped, extension is sanitized, path includes scenario/store/file/version and UUID (`apps/files/services.py:58`-`80`). `FILE_CONTOUR.md` describes the same command/path strategy (`docs/architecture/FILE_CONTOUR.md:44`).
- Retention is fixed at 3 days for physical files (`apps/files/services.py:23`, `apps/files/services.py:176`), and cleanup deletes only the physical storage object or marks it missing while preserving metadata rows (`apps/files/services.py:228`-`266`, `apps/files/management/commands/cleanup_file_retention.py:1`-`26`).
- Download checks reject archived metadata, unavailable physical status, expired retention, missing scenario permission, missing object access and direct deny through `has_permission()` (`apps/files/services.py:202`-`225`, `apps/identity_access/services.py:97`-`132`). Download permission codes match scenario rights for output/detail (`apps/files/services.py:23`-`28`, `apps/files/services.py:195`-`199`, `docs/product/PERMISSIONS_MATRIX.md:47`-`65`).
- Individual deny and store deny precedence remain in the existing identity helper path (`apps/identity_access/services.py:38`-`51`, `apps/identity_access/services.py:85`-`130`).
- Operation/run relation is placeholder-only through `operation_ref` / `run_ref`; no operation models or check/process execution were added in TASK-004 scope (`apps/files/models.py:211`-`212`, `apps/files/services.py:146`-`147`, `apps/operations/models.py:1`).
- No WB/Ozon Excel parsing or business calculation logic was found in `apps/files/**`; discount apps remain placeholders for TASK-007/TASK-008.
- File metadata deletion protections preserve historical `FileVersion` records and protect linked store/user refs through `PROTECT` relations (`apps/files/models.py:78`-`96`, `apps/files/models.py:188`-`214`, `apps/files/models.py:173`-`179`, `apps/files/models.py:236`-`237`).

## sanity commands/results

| Command | Result |
| --- | --- |
| `python manage.py check` | ENV LIMITATION: `python: command not found`. Retried with local venv interpreter. |
| `.venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `python manage.py makemigrations --check --dry-run` | ENV LIMITATION: `python: command not found`. Retried with local venv interpreter. |
| `.venv/bin/python manage.py makemigrations --check --dry-run` | PASS for model diff: `No changes detected`; emitted PostgreSQL authentication warning while checking migration history for `promo_v2` on `127.0.0.1:5432`. |
| `.venv/bin/python manage.py test apps.files` | SANITY ONLY / BLOCKED BY ENV: Django found 6 tests but failed before execution because PostgreSQL rejected password authentication for user `promo_v2` on `127.0.0.1:5432`. This is not a tester pass. |

## environment limitations

- `/home/pavel/projects/promo_v2` is not a git worktree from this directory; `git status --short` fails with `fatal: not a git repository`.
- Bare `python` is unavailable; `.venv/bin/python` was used for Django sanity commands.
- Default database settings target local PostgreSQL as `promo_v2`; authentication failed for migration-history warning and test database creation.
- I did not use a SQLite override for TASK-004 tests, to keep this audit separate from tester execution.
- Product code and non-audit documentation were not changed.

## decision

TASK-004 accepted at audit level with remarks. Return to developer is not required for blocker/major fixes.

## recommendation

Run a separate tester next. The existing tests and sanity commands are useful implementation evidence, but this report is an architecture/task-boundary audit, not formal tester acceptance.
