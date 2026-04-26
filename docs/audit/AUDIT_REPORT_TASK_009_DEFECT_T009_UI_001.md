# AUDIT_REPORT_TASK_009_DEFECT_T009_UI_001

Дата аудита: 2026-04-25.

Роль: Аудитор Codex CLI TASK-009 tester defect fix audit.

## status

PASS

## checked scope

- Defect: `T009-UI-001`.
- Tester input: `docs/testing/TEST_REPORT_TASK_009.md`.
- Implementation files: `templates/web/operation_card.html`, `apps/web/views.py`, `apps/web/tests.py`.
- Permission spec: `docs/product/PERMISSIONS_MATRIX.md`.

Проверка ограничена исправлением `T009-UI-001` и отсутствием регрессии в связанных UI/permission checks. Код продукта не изменялся.

## method

- Static audit of operation card output/detail download rendering.
- Static audit of view context flags used by the operation card.
- Static audit of focused regression test for separate output/detail permissions.
- Required PostgreSQL-backed Django checks.

Working directory note: `/home/pavel/projects/promo_v2` is not a git repository, so git diff/status evidence is unavailable. Audit conclusion is based on current task-scoped files.

## requirements check

| Requirement | Result | Evidence |
| --- | --- | --- |
| Output download link uses `can_download_output`. | PASS | `templates/web/operation_card.html` renders non-`detail_report` output links only when `link.file_version.is_physically_available and can_download_output`. |
| Detail report download link uses `can_download_detail`. | PASS | `templates/web/operation_card.html` branches on `link.output_kind == "detail_report"` and renders the link only when `link.file_version.is_physically_available and can_download_detail`. |
| User with detail permission but without output permission can see/use detail link. | PASS | `apps/web/tests.py` creates a user with `wb_discounts_excel.download_detail_report` and without `download_output`, asserts output link absent, detail link present, and direct detail download returns HTTP 200. |
| User without detail permission cannot see detail link. | PASS | The same test deactivates `download_detail_report`, grants `download_output`, then asserts output link present and detail link absent. |
| No business/permission model change or unrelated UI regression. | PASS | `apps/web/views.py` computes and passes separate flags from the existing permission codes; direct download authorization remains in `apps.files.services.open_file_version_for_download`. No permission matrix or business model change was found in the checked scope. |

## findings

### blocker

None.

### major

None.

### minor

None.

## commands/results

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check
```

Result: PASS.

```text
System check identified no issues (0 silenced).
```

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.web
```

Result: PASS.

```text
Creating test database for alias 'default'...
.............
----------------------------------------------------------------------
Ran 13 tests in 17.203s

OK
Destroying test database for alias 'default'...
Found 13 test(s).
System check identified no issues (0 silenced).
```

## decision

accepted

Исправление `T009-UI-001` принято. Повторный тестировщик по этому дефекту не требуется; можно продолжать следующий orchestration step.
