# AUDIT_REPORT_TASK_004_ROUND_2

Дата: 2026-04-25

Роль: Аудитор Codex CLI TASK-004 minor fix review.

## status

PASS

Оба previous minor из `docs/audit/AUDIT_REPORT_TASK_004.md` закрыты. Новых blocker/major/minor в проверенном контуре не найдено.

## checked scope

- Root/orchestration context: `AGENTS.md`, `docs/README.md`, `docs/orchestration/AGENTS.md`, `docs/roles/READING_PACKAGES.md`.
- Previous audit: `docs/audit/AUDIT_REPORT_TASK_004.md`.
- Task: `docs/tasks/implementation/stage-1/TASK-004-files-and-retention.md`.
- Architecture docs: `docs/architecture/FILE_CONTOUR.md`, `docs/architecture/DATA_MODEL.md` file/version rows, `docs/architecture/DELETION_ARCHIVAL_POLICY.md` file rules.
- Code: `apps/files/models.py`, `apps/files/services.py`.
- Coverage awareness only: `apps/files/tests.py`.

Audit scope was limited to closure of the two minor findings and absence of new related risks. Product code was not changed. No tester acceptance was performed.

## previous minor closure table

| Previous minor | Round 2 result | Evidence |
| --- | --- | --- |
| Explicit pre-operation erroneous-upload delete service is absent. | CLOSED | `apps/files/services.py:47`-`54` defines `PreOperationDeleteResult`; `apps/files/services.py:237`-`255` allows delete only for active input files, with no operation/run links, available physical status and non-expired retention; `apps/files/services.py:289`-`314` exposes explicit `delete_pre_operation_file_upload()` and `delete_pre_operation_file_version()` services. Product delete guards remain in `apps/files/models.py:190`-`196` and `apps/files/models.py:253`-`256`, with metadata delete allowed only through the service context manager. Generated output/detail files are rejected by kind check, operation/run-linked versions are rejected, expired/unavailable versions are rejected, and retention cleanup still preserves metadata. |
| `DATA_MODEL.md` file row is not aligned with actual per-version storage metadata split. | CLOSED | `docs/architecture/DATA_MODEL.md:34` now keeps `FileObject` to logical metadata only. `docs/architecture/DATA_MODEL.md:35` now lists `FileVersion` fields including `storage_backend`, `storage_path`, `size`, `checksum_sha256`, `retention_until`, `physical_status`, `physical_deleted_at`, `operation_ref`, and `run_ref`, matching `apps/files/models.py:205`-`229`. |

## new findings

### blocker

None found.

### major

None found.

### minor

None found.

## risk checks

- Retention: `cleanup_expired_physical_files()` still deletes only physical storage object and updates `physical_status` / `physical_deleted_at`; it does not delete `FileObject` or `FileVersion` metadata (`apps/files/services.py:317`-`355`).
- Metadata preservation and version immutability: ordinary model deletes remain protected unless the pre-operation service context is active (`apps/files/models.py:190`-`196`, `apps/files/models.py:253`-`256`); repeated uploads still create new `FileVersion` rows (`apps/files/services.py:176`-`199`).
- Pre-operation delete boundary: service rejects generated files by requiring `FileObject.Kind.INPUT`, rejects operation/run-linked files through `has_operation_links()` and per-version checks, and rejects expired/unavailable versions (`apps/files/models.py:183`-`188`, `apps/files/services.py:237`-`255`).
- TASK-005 overreach: no operation models, run execution, check/process workflow, or operation business logic was added in the reviewed files.
- WB/Ozon logic: no WB/Ozon Excel parsing, calculation rules, reason/result code implementation, or workbook business processing was added in `apps/files/models.py` / `apps/files/services.py`.
- Permission bypass: no new download bypass found; download checks still route through `has_permission()` with scenario permission and store object access (`apps/files/services.py:211`-`224`). The new delete services are internal service functions with no UI/API endpoint in TASK-004 scope.

## sanity commands/results

| Command | Result |
| --- | --- |
| `python manage.py check` | ENV LIMITATION: failed before Django startup, `/bin/bash: line 1: python: command not found`. |
| `.venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `python manage.py makemigrations --check --dry-run` | ENV LIMITATION: failed before Django startup, `/bin/bash: line 1: python: command not found`. |
| `.venv/bin/python manage.py makemigrations --check --dry-run` | PASS for migration diff: `No changes detected`. Django emitted a PostgreSQL migration-history warning because local DB authentication for user `promo_v2` on `127.0.0.1:5432` failed. |

## environment limitations

- `/home/pavel/projects/promo_v2` is not a git worktree from this directory; `git status --short` fails with `fatal: not a git repository`.
- Bare `python` is unavailable; `.venv/bin/python` was used for meaningful Django sanity checks.
- Local PostgreSQL authentication failed for migration-history consistency warning during `makemigrations --check --dry-run`; model diff still completed with `No changes detected`.
- This review did not run unit tests and did not perform tester acceptance by instruction.

## decision

TASK-004 accepted for tester pass. Return to developer is not required.
