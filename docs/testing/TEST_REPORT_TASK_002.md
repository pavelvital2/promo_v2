# TEST_REPORT_TASK_002

Дата: 2026-04-25

Роль: Тестировщик Codex CLI TASK-002 identity/access.

## status

PASS WITH REMARKS

Причина remarks: штатный PostgreSQL test run не смог создать test database из-за недоступных credentials. Поведенческие сценарии и существующие unit tests выполнены через безопасный in-memory SQLite override без изменения product code, migrations или settings.

## scope

Проверены поведенческие сценарии TASK-002 по task-scoped входам:

- `docs/tasks/implementation/stage-1/TASK-002-auth-users-roles-permissions.md`;
- `docs/testing/TEST_PROTOCOL.md`;
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`;
- `docs/product/PERMISSIONS_MATRIX.md` только как источник ожидаемых сценариев доступа;
- `docs/audit/AUDIT_REPORT_TASK_002_ROUND_3.md` как audit acceptance context;
- `apps/identity_access/tests.py`;
- `apps/identity_access/models.py`, `apps/identity_access/services.py`, `apps/identity_access/admin.py` только для понимания scenario hooks.

Тестировщик не выполнял архитектурный аудит и не менял product code.

## scenario matrix

| ID | Scenario | Status | Evidence / notes |
| --- | --- | --- | --- |
| T2-SC-01 | Seed roles/permissions создаются и повторный seed не дублирует данные | PASS | Existing tests passed; temporary scenario run checked counts for roles, permissions, sections, role_permissions, role_sections and repeated `seed_identity_access()` stats = 0 created rows. |
| T2-SC-02 | Owner имеет полный доступ и не блокируется/не архивируется/не удаляется | PASS | Checked all known permission codes for owner; blocked status/archive save; model and queryset delete; direct permission, section and store denies against owner. |
| T2-SC-03 | Global admin не может управлять owner | PASS | Checked no `users.owner.manage`, `can_manage_user(global_admin, owner) == False`, status change denied, admin change denied for owner user and owner role. |
| T2-SC-04 | Direct deny перекрывает allow | PASS | Checked user permission deny overrides role allow for store-specific scenario permission; store deny overrides full object scope for global admin. |
| T2-SC-05 | Local admin ограничен store scope для управления пользователями | PASS | Checked `users.edit` allowed only in assigned WB store; cross-store and full-scope management denied; owner/global-admin targets denied. |
| T2-SC-06 | Manager не имеет users/roles/system permissions, но имеет WB/Ozon scenario permissions в доступном store scope | PASS | Checked admin/system permissions denied; WB/Ozon scenario permission set allowed in assigned stores and denied in inaccessible store. |
| T2-SC-07 | Observer view-only, без upload/run/process/edit/download output/detail по умолчанию | PASS | Checked view/result/detail-view permissions allowed per matrix; upload/run/confirm/process/rerun/edit/download output/download detail report denied by default. |
| T2-SC-08 | Login route/template smoke works if feasible | PASS | `GET reverse("login")` returned 200 with form; valid login POST returned 302 in SQLite smoke environment using allowed host `localhost`. |
| T2-SC-09 | Admin/model behavior для protected delete/update сценариев на уровне пользовательских действий | PASS | Checked admin delete/change guards for protected users and system dictionaries; inline add/change/delete guards; model/queryset update protections for system role, permission and role composition. |

## commands run / results

| Command | Result |
| --- | --- |
| `.venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `.venv/bin/python manage.py test apps.identity_access` | BLOCKED BY ENV: Django found 18 tests but failed before execution because PostgreSQL rejected password authentication for user `promo_v2` on `127.0.0.1:5432`. |
| SQLite override: `call_command("test", "apps.identity_access", verbosity=1)` | PASS: 18 existing identity/access tests passed. |
| Temporary SQLite scenario run for TASK-002 matrix | PASS: 9/9 behavioral scenarios passed. |

Two preliminary temporary scenario script attempts were corrected before the final run: one reused the same manager after applying a direct deny, and one used Django test client's default `testserver` host while project `ALLOWED_HOSTS` allows `localhost,127.0.0.1`. These were test harness issues, not product defects.

## defects found

No product defects found in the checked TASK-002 behavior.

| Severity | Defect | Status |
| --- | --- | --- |
| Blocker | None | - |
| Major | None | - |
| Minor | None | - |

## environment limitations

- Default DB settings target PostgreSQL `promo_v2` on `127.0.0.1:5432`; password authentication failed for user `promo_v2`, so the штатный test database run was not executable in this environment.
- SQLite override was used only for tests/smoke scenarios in memory. It does not fully prove PostgreSQL-specific behavior.
- Login smoke was checked through Django test client with `HTTP_HOST=localhost`, matching current `ALLOWED_HOSTS`.
- `/home/pavel/projects/promo_v2` is not a git worktree from this directory; `git status --short` is unavailable.
- Formal stage-1 acceptance remains subject to the broader acceptance artifact gate for WB/Ozon control files described in `GAP-0008`; this does not block TASK-002 tester recommendation.

## recommendation

С точки зрения тестировщика TASK-002 можно переходить к TASK-003.

Условие для полного confidence: при доступных PostgreSQL credentials повторить `.venv/bin/python manage.py test apps.identity_access` в штатной DB-конфигурации.
