# AUDIT_REPORT_TASK_002_ROUND_3.md

## status

PASS WITH REMARKS

## checked scope

- Previous audits: `docs/audit/AUDIT_REPORT_TASK_002_ROUND_2.md`, `docs/audit/AUDIT_REPORT_TASK_002.md`.
- Task: `docs/tasks/implementation/stage-1/TASK-002-auth-users-roles-permissions.md`.
- Specs: `docs/product/PERMISSIONS_MATRIX.md`, `docs/architecture/DELETION_ARCHIVAL_POLICY.md`.
- Code: `apps/identity_access/models.py`, `apps/identity_access/admin.py`, `apps/identity_access/services.py`, `apps/identity_access/seeds.py`.
- Tests were read only for coverage awareness: `apps/identity_access/tests.py`.
- Narrow round 3 focus: closure of the 2 residual major findings from round 2, plus regression scan for seed idempotency, owner protection, direct deny precedence, store-scope `can_manage_user()`, TASK-003/TASK-009 overreach, and WB/Ozon business logic overreach.
- Audit did not change product code. Only this report was created.

## previous findings closure table

| Previous finding | Round 3 status | Evidence / notes |
| --- | --- | --- |
| Major: system dictionaries / system role composition bypassable through ordinary ORM `QuerySet.update()` while seed/migration path must remain possible | CLOSED | `GuardedDeleteQuerySet.update()` now calls `_raise_if_system_update_is_forbidden()` (`apps/identity_access/models.py:54`-`79`). The guard blocks updates touching system `Role`, `Permission`, `SectionAccess`, and system-role `RolePermission` / `RoleSectionAccess` rows (`apps/identity_access/models.py:59`-`75`). Instance `save()`/`delete()` guards remain in place for system roles, permissions, section access and system role composition (`apps/identity_access/models.py:120`-`144`, `apps/identity_access/models.py:167`-`190`, `apps/identity_access/models.py:212`-`236`, `apps/identity_access/models.py:393`-`412`, `apps/identity_access/models.py:433`-`452`). Admin inlines for system role composition are read-only/no add/no change/no delete (`apps/identity_access/admin.py:35`-`84`). Seed uses explicit `system_dictionary_mutation()` context around `update_or_create()` / `get_or_create()` (`apps/identity_access/seeds.py:237`-`296`), so the service seed path remains available. Existing tests cover blocked `QuerySet.update()` and allowed seed restoration (`apps/identity_access/tests.py:139`-`156`, `apps/identity_access/tests.py:243`-`286`). Temporary audit sanity confirmed ordinary updates are blocked and context update plus seed restore work. |
| Major: `UserRole` assignment can be physically deleted, usage marker can be lost, then user can be physically deleted | CLOSED | `UserRole.user` and `UserRole.role` are `PROTECT` FKs (`apps/identity_access/models.py:356`-`358`), `UserRole.delete()` always raises `ProtectedError` (`apps/identity_access/models.py:368`-`372`), and `GuardedDeleteQuerySet.delete()` routes queryset deletion through instance `delete()` (`apps/identity_access/models.py:81`-`87`). `User.has_physical_delete_usage()` treats role assignment as usage (`apps/identity_access/models.py:306`-`322`), and `User.delete()` blocks used users (`apps/identity_access/models.py:345`-`353`). Admin inline deletion is disabled for `UserRole` (`apps/identity_access/admin.py:114`-`122`), and user admin deletion is blocked when `can_be_physically_deleted()` is false (`apps/identity_access/admin.py:187`-`210`). Existing tests cover model/queryset delete blocking and preserved marker (`apps/identity_access/tests.py:313`-`342`). Temporary audit sanity confirmed assignment remains after model/queryset delete attempts and the assigned user remains protected from physical delete. |
| Round 2 closed minor: owner detection consistency | STILL CLOSED / NO REGRESSION | Model and service owner checks still share `is_owner_user()` / `user_role_codes()` (`apps/identity_access/models.py:36`-`51`, `apps/identity_access/models.py:303`-`304`; `apps/identity_access/services.py:24`-`31`). Coverage includes owner via assigned role (`apps/identity_access/tests.py:193`-`210`). |
| Round 2 closed minor: `can_manage_user()` store-scope behavior | STILL CLOSED / NO REGRESSION | `can_manage_user(actor, target, store=None)` keeps owner protection, rejects full-scope targets for local admins, and requires shared active store scope for local management (`apps/identity_access/services.py:169`-`210`). Coverage remains present (`apps/identity_access/tests.py:408`-`428`). |

## new findings

### blocker

None found.

### major

None found.

### minor

None found.

## regression checks

- Seed idempotency: no regression found. Seed remains idempotent via `update_or_create()` / `get_or_create()` inside `system_dictionary_mutation()` (`apps/identity_access/seeds.py:237`-`296`) and coverage verifies repeat seed results (`apps/identity_access/tests.py:125`-`156`).
- Owner protection: no regression found. Owner cannot be managed by non-owner admins in service checks and model protections (`apps/identity_access/models.py:303`-`353`, `apps/identity_access/services.py:169`-`175`), with coverage for primary and assigned owner role paths (`apps/identity_access/tests.py:169`-`210`).
- Direct deny precedence: no regression found. Direct permission and store denies are checked before allow/full scope paths (`apps/identity_access/services.py:38`-`51`, `apps/identity_access/services.py:85`-`130`), with coverage (`apps/identity_access/tests.py:372`-`401`).
- Store-scope `can_manage_user()`: no regression found; local admin management remains scoped to shared stores (`apps/identity_access/services.py:187`-`210`, `apps/identity_access/tests.py:408`-`428`).
- TASK-003/TASK-009 overreach: not found in checked identity/access scope. TASK-002 boundary still covers auth/users/roles/permissions and forbids operations/files/WB/Ozon implementation (`docs/tasks/implementation/stage-1/TASK-002-auth-users-roles-permissions.md:38`-`52`).
- WB/Ozon business logic overreach: not found. Checked references are permission/section codes only (`apps/identity_access/seeds.py:46`-`71`, `apps/identity_access/seeds.py:100`-`115`); no workbook processing, calculation rules, check/process execution, or Excel business logic found in checked files.

## sanity commands/results

| Command | Result |
| --- | --- |
| `.venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `.venv/bin/python manage.py makemigrations --check --dry-run` | PASS for model diff: `No changes detected`; emitted environment warning because PostgreSQL credential/history check could not authenticate to `127.0.0.1:5432` as `promo_v2`. |
| `.venv/bin/python manage.py test apps.identity_access` | ENV LIMITATION: Django found 18 tests but failed before execution because PostgreSQL rejected password authentication for user `promo_v2` on `127.0.0.1:5432`. |
| SQLite override: `call_command("test", "apps.identity_access", verbosity=1)` | PASS: 18 existing identity/access tests passed. |
| Temporary SQLite ORM audit check | PASS: ordinary `QuerySet.update()` was blocked for system role, system permission, and system role composition; `system_dictionary_mutation()` allowed a temporary seed-style update and `seed_identity_access()` restored the official value; `UserRole` model/queryset deletion was blocked, assignment marker remained, and assigned user physical delete was blocked. |

## environment limitations

- Default database uses local PostgreSQL credentials for `promo_v2`; password authentication failed on `127.0.0.1:5432`, so default test execution could not create the test database.
- SQLite override was used only for sanity commands and narrow audit confirmation. It did not modify project settings, migrations, product code, or seed data.
- `/home/pavel/projects/promo_v2` is not a git worktree from this directory; `git status --short` fails with `fatal: not a git repository`.
- This is an audit pass, not a tester pass. Sanity commands are not a full test plan.

## decision

TASK-002 accepted at audit level.

## recommendation on separate tester

Yes. Run a separate tester after this audit acceptance, because this round checked architectural closure and sanity only, not a full QA/tester acceptance pass.
