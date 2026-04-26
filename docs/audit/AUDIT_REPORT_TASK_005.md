# AUDIT_REPORT_TASK_005

Дата: 2026-04-25

Роль: Аудитор Codex CLI TASK-005 operations/run/execution shell.

## status

FAIL

Причина: найден blocker по core acceptance TASK-005. Реализация содержит модели `Run` / `Operation`, check/process split, check-basis links, actuality comparator и interrupted_failed shell, но не реализует documented flow нажатия "Обработать" без актуальной проверки: отдельная check должна создаваться автоматически и только затем process, если проверка допустима.

## checked scope

- Root/orchestration context: `AGENTS.md`, `docs/README.md`, `docs/orchestration/AGENTS.md`, `docs/roles/READING_PACKAGES.md`.
- Task: `docs/tasks/implementation/stage-1/TASK-005-operations-run-execution.md`.
- Product/architecture specs: `docs/product/OPERATIONS_SPEC.md`, `docs/architecture/DATA_MODEL.md` operation/run parts, `docs/architecture/FILE_CONTOUR.md` file-version relation concepts, `docs/architecture/DELETION_ARCHIVAL_POLICY.md` operations immutability/delete policy, `docs/product/PERMISSIONS_MATRIX.md` operation/scenario rights.
- Code: `apps/operations/**`.
- Integration review only: `apps/files/**` for `FileVersion` integration; `apps/stores/**` and `apps/identity_access/**` for FK/access integration.

Audit did not change product code. Only this audit report was created. This is not tester acceptance.

## audit method

- Compared implemented models, migrations and service APIs against TASK-005 expected output and `OPERATIONS_SPEC.md`.
- Checked visible id formats, mandatory operation/run fields, status dictionaries, check/process separation and check-basis relation.
- Reviewed check actuality comparator for marketplace, store, input file set, concrete file versions, parameter snapshots and business logic version.
- Reviewed warning confirmation representation, permissions integration surface and immutability guards for terminal operations and related records.
- Reviewed failure path for `interrupted_failed` and absence of auto-resume.
- Reviewed `FileVersion` links for TASK-004-compatible FK usage and absence of historical metadata deletion/overwrite in the operations layer.
- Searched for WB/Ozon row calculation/business rules and TASK-006 audit/techlog overreach.
- Ran requested sanity commands only; no formal test pass was performed.

## findings

### blocker

1. The "Process without actual check" acceptance flow is not implemented.

   Required: `OPERATIONS_SPEC.md` states that pressing "Обработать" must reuse an actual successful check if present; if no actual successful check exists, the system automatically creates a separate check and, if there are no errors, continues with a separate process (`docs/product/OPERATIONS_SPEC.md:68`-`75`). TASK-005 acceptance repeats this requirement (`docs/tasks/implementation/stage-1/TASK-005-operations-run-execution.md:69`).

   Evidence: the service layer exposes `find_actual_successful_check()` (`apps/operations/services.py:216`), `create_check_operation()` (`apps/operations/services.py:297`), and `create_process_operation()` (`apps/operations/services.py:350`), but no service/API shell composes the documented "press process" workflow. `create_process_operation()` requires a pre-existing `check_basis_operation` and raises if it is not actual (`apps/operations/services.py:376`-`384`); it never creates or executes the missing check. `run_process_sync()` only starts and completes an already-created process operation (`apps/operations/services.py:543`-`552`).

   Impact: a core TASK-005 acceptance path is absent. Downstream WB/Ozon modules or UI would have to invent orchestration behavior outside the approved operations shell, which risks mixing business flow decisions into later tasks.

### major

1. Warning confirmation permission is not enforced by the operations service when confirmation facts are recorded.

   Required context: warning confirmation is a distinct scenario right in the permissions matrix (`docs/product/PERMISSIONS_MATRIX.md:58`). The operation flow requires explicit confirmation before process when confirmable warnings exist (`docs/product/OPERATIONS_SPEC.md:92`-`103`).

   Evidence: `create_process_operation(..., enforce_permissions=True)` checks only `run_process` (`apps/operations/services.py:367`-`375`). If `confirmed_warning_codes` is provided, `WarningConfirmation` is created immediately (`apps/operations/services.py:385`-`411`), but there is no `confirm_warnings` permission check.

   Impact: callers using the TASK-005 service permission hook can record warning confirmation facts without the documented confirmation permission. This is an access-control gap at the execution shell boundary.

2. `WarningConfirmation` facts are mutable before process completion through instance save.

   Required: deletion/archive policy marks `WarningConfirmation` as not edited or deleted by ordinary means (`docs/architecture/DELETION_ARCHIVAL_POLICY.md:37`). Operation specs treat warning confirmation facts as historical operation facts (`docs/product/OPERATIONS_SPEC.md:99`-`103`, `docs/product/OPERATIONS_SPEC.md:149`).

   Evidence: queryset updates are blocked for existing confirmations (`apps/operations/models.py:212`-`216`), and deletes are protected (`apps/operations/models.py:731`-`732`). However, `WarningConfirmation.save()` blocks updates only when the check or process operation is terminal (`apps/operations/models.py:723`-`729`). A confirmation created while process status is still `created` can be edited via instance `.save()` until the process completes.

   Impact: the recorded "who/when/which warnings/check/process" fact is not consistently immutable during the operation lifecycle.

3. Output file versions can be reused across process operations.

   Required: repeated processing creates a new operation and a new output file when output is formed (`docs/product/OPERATIONS_SPEC.md:107`). File contour prohibits replacing completed operation files and requires historical links to specific versions (`docs/architecture/FILE_CONTOUR.md:24`, `docs/architecture/FILE_CONTOUR.md:93`-`97`).

   Evidence: `complete_process_operation()` accepts any `result.output_file_version` and creates `OperationOutputFile` for it (`apps/operations/services.py:481`-`491`). `OperationOutputFile` has uniqueness only on `(operation, output_kind)` (`apps/operations/models.py:538`-`545`); there is no uniqueness/validation preventing the same `FileVersion` from becoming output for another process operation. `_mark_file_version_used()` also does not reject an already operation-linked file version; it only avoids overwriting `operation_ref` / `run_ref` if already set (`apps/operations/models.py:563`-`570`).

   Impact: a repeat process can be linked to a historical output `FileVersion` instead of a newly formed output file version, weakening the operation-file history contract.

### minor

1. Direct check-basis validation does not include module/mode in `is_check_actual_for_request()`.

   Evidence: operation actuality metadata compares marketplace, store, input files, parameter snapshots and logic version (`apps/operations/services.py:150`-`176`, `apps/operations/services.py:179`-`193`). `find_actual_successful_check()` filters module/mode before calling it (`apps/operations/services.py:216`-`249`), but `create_process_operation()` accepts an explicit `check_basis_operation` and calls only the comparator (`apps/operations/services.py:376`-`384`). Model validation requires only that the basis is a successful check, not that basis module/mode match the process (`apps/operations/models.py:401`-`408`).

   Impact: current stage-1 scenario set is narrow, so the practical risk is limited. As the model already includes `module` and future `mode=api`, the direct service boundary should not rely on callers to pre-filter scenario compatibility.

2. Status dictionaries are implemented in Python validation but are not attached as field choices or database constraints for `Operation.status`.

   Evidence: status constants match the spec (`apps/operations/models.py:89`-`104`), and `Operation.clean()` rejects a status that does not match operation type (`apps/operations/models.py:380`-`387`). The actual field is `models.CharField(max_length=64)` without choices (`apps/operations/models.py:320`-`321`; migration at `apps/operations/migrations/0001_initial.py:28`-`29`). Non-terminal queryset updates are not value-validated by `OperationQuerySet.update()` (`apps/operations/models.py:181`-`190`).

   Impact: ordinary `.save()` paths are protected, but bulk update or admin-style direct updates can store non-dictionary statuses before terminal state. This is lower severity because terminal immutability is enforced and no operations admin UI was found in scope.

## conforming observations

- `Run` and `Operation` models include the required core fields and generate `RUN-YYYY-NNNNNN` / `OP-YYYY-NNNNNN` visible ids (`apps/operations/models.py:222`-`308`, `apps/operations/models.py:311`-`456`).
- Check and process are separate operation types; process requires and stores `check_basis_operation` (`apps/operations/models.py:84`-`87`, `apps/operations/models.py:399`-`408`, `apps/operations/services.py:350`-`412`).
- Check and process statuses match `OPERATIONS_SPEC.md` values in the Python dictionaries (`apps/operations/models.py:89`-`104`).
- Actuality comparison covers marketplace, store, input file roles/ordinals and concrete `file_version_id`, parameter snapshot values/source/version/effective time, and `logic_version` (`apps/operations/services.py:116`-`147`, `apps/operations/services.py:150`-`213`).
- Terminal operation immutability is broadly enforced for operation saves, queryset updates, deletes, file links, parameter snapshots, result rows and detail rows (`apps/operations/models.py:181`-`206`, `apps/operations/models.py:425`-`456`, `apps/operations/models.py:459`-`471`, `apps/operations/models.py:506`-`510`, `apps/operations/models.py:557`-`561`, `apps/operations/models.py:597`-`600`, `apps/operations/models.py:621`-`624`, `apps/operations/models.py:650`-`653`, `apps/operations/models.py:684`-`687`).
- Failure handling marks check/process operation and run as `interrupted_failed`; restart of terminal interrupted operation is blocked by terminal immutability, and no auto-resume service was found (`apps/operations/services.py:513`-`552`, `apps/operations/models.py:425`-`430`).
- Operation input/output file links use `FileVersion` FKs with `PROTECT` and do not delete or overwrite TASK-004 file metadata (`apps/operations/models.py:474`-`570`; file metadata delete protections at `apps/files/models.py:190`-`196`, `apps/files/models.py:253`-`256`).
- No WB/Ozon row calculation, Excel parsing, workbook business rules or Ozon/WB calculation algorithms were found in `apps/operations/**`; discount apps remain placeholders for later tasks.
- No TASK-006 audit/techlog implementation overreach was found in `apps/operations/**`; audit/techlog remain separate placeholder apps.

## sanity commands/results

| Command | Result |
| --- | --- |
| `git status --short` | ENV LIMITATION: `/home/pavel/projects/promo_v2` is not a git worktree from this directory; command failed with `fatal: not a git repository`. |
| `python manage.py check` | ENV LIMITATION: failed before Django startup, `/bin/bash: line 1: python: command not found`. |
| `python manage.py makemigrations --check --dry-run` | ENV LIMITATION: failed before Django startup, `/bin/bash: line 1: python: command not found`. |
| `.venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `.venv/bin/python manage.py makemigrations --check --dry-run` | PASS for migration diff: `No changes detected`. Django emitted a PostgreSQL migration-history warning because local DB authentication for user `promo_v2` on `127.0.0.1:5432` failed. |

## environment limitations

- Working directory is not visible as a git repository from `/home/pavel/projects/promo_v2`; git status could not be used to inspect unrelated changes.
- Bare `python` is unavailable; `.venv/bin/python` was used for meaningful Django sanity commands.
- Local PostgreSQL authentication failed during migration-history consistency check; `makemigrations --check --dry-run` still completed model diff with `No changes detected`.
- Unit/integration tests were not run by design: this audit intentionally did not mix audit with tester execution.

## decision

TASK-005 is not accepted. Return to developer.

Minimum return scope:

- Add the documented "press process" orchestration shell: reuse actual successful check when present; otherwise create separate check, execute/complete it through the provided executor boundary, and create process only if allowed.
- Enforce `confirm_warnings` permission when warning confirmation is recorded through service permission checks.
- Make `WarningConfirmation` facts immutable consistently after creation.
- Prevent reuse of output `FileVersion` as generated output for another process operation, or document and implement an equivalent invariant that guarantees each repeated process forms a new output file version.

## recommendation

Run a separate tester next only after developer fixes and a follow-up audit pass. Current sanity commands are implementation evidence, not tester acceptance.
