# AUDIT_REPORT_TASK_002_ROUND_2.md

## status

FAIL

## checked scope

- Previous audit: `docs/audit/AUDIT_REPORT_TASK_002.md`.
- Task: `docs/tasks/implementation/stage-1/TASK-002-auth-users-roles-permissions.md`.
- Specs: `docs/product/PERMISSIONS_MATRIX.md`, `docs/architecture/DELETION_ARCHIVAL_POLICY.md`.
- ADR: `docs/adr/ADR_LOG.md` entries ADR-0007 and ADR-0008.
- Code: `apps/identity_access/models.py`, `apps/identity_access/admin.py`, `apps/identity_access/services.py`, `apps/identity_access/seeds.py`, `apps/identity_access/tests.py`, `apps/identity_access/migrations/0003_alter_storeaccess_store_alter_storeaccess_user_and_more.py`.
- Boundary check: `apps/stores/models.py` as TASK-002 object-access stub boundary.
- Audit did not change product code. Only this report was created.

## audit method

- Re-read required orchestration docs and task-scoped inputs.
- Compared fixes against the 2 major and 2 minor findings from `AUDIT_REPORT_TASK_002.md`.
- Inspected model/admin/service/seed/migration code with line references.
- Checked ADR-0007 seed composition against `PERMISSIONS_MATRIX.md`.
- Scanned TASK-002 implementation files for TASK-003/TASK-009 overreach and WB/Ozon business logic.
- Ran minimal sanity commands requested by the task. This was not a tester pass and does not replace separate QA.

## previous findings closure table

| Previous finding | Round 2 status | Evidence / notes |
| --- | --- | --- |
| Major: immutable system roles, permissions, section access and system role composition through admin/model APIs | PARTIALLY CLOSED | Instance `save()`/`delete()` guards and admin readonly/inline restrictions were added for system dictionaries and system role composition (`apps/identity_access/models.py:94`, `apps/identity_access/models.py:141`, `apps/identity_access/models.py:186`, `apps/identity_access/models.py:366`, `apps/identity_access/models.py:406`; `apps/identity_access/admin.py:22`, `apps/identity_access/admin.py:35`, `apps/identity_access/admin.py:61`). However ORM `QuerySet.update()` remains unguarded because `GuardedDeleteQuerySet` overrides only `delete()` (`apps/identity_access/models.py:54`). Minimal SQLite confirmation changed a system permission with `Permission.objects.filter(...).update(...)`. |
| Major: deletion/archive policy for users/access/history | PARTIALLY CLOSED | Non-owner used `User.delete()` now blocks used users (`apps/identity_access/models.py:280`, `apps/identity_access/models.py:319`), access/history FKs were moved to `PROTECT` in migration 0003 (`apps/identity_access/migrations/0003_alter_storeaccess_store_alter_storeaccess_user_and_more.py:16`), active permission/section/store access and history rows are protected (`apps/identity_access/models.py:474`, `apps/identity_access/models.py:521`, `apps/identity_access/models.py:572`, `apps/identity_access/models.py:602`, `apps/identity_access/models.py:630`). But non-owner `UserRole` assignment rows can still be physically deleted directly or through admin inline, which can erase the only usage marker and then permit physical user deletion (`apps/identity_access/models.py:330`, `apps/identity_access/models.py:342`; `apps/identity_access/admin.py:114`). |
| Minor: owner detection consistency | CLOSED | Model and service owner detection now share `is_owner_user()` / `user_role_codes()` (`apps/identity_access/models.py:36`, `apps/identity_access/models.py:50`, `apps/identity_access/models.py:276`; `apps/identity_access/services.py:24`, `apps/identity_access/services.py:30`). Existing tests cover owner via assigned role (`apps/identity_access/tests.py:173`). |
| Minor: `can_manage_user()` store-scope behavior | CLOSED FOR TASK-002 | `can_manage_user()` now accepts optional `store`, rejects owner/full-scope targets for local admins, and falls back to shared active store access when no explicit store is passed (`apps/identity_access/services.py:169`). Existing tests cover global admin, shared store, wrong store, other-store user, global admin target, and owner target (`apps/identity_access/tests.py:326`). This remains a TASK-003 integration handoff for future real store screens. |

## new findings

### blocker

None found.

### major

1. System dictionary and system role composition immutability is still bypassable through ORM bulk update APIs.

   Requirement: TASK-002 expects system roles and permissions to be immutable through regular UI where required (`docs/tasks/implementation/stage-1/TASK-002-auth-users-roles-permissions.md:63`). The deletion/archive policy says `Permission / SectionAccess` are immutable system dictionaries and their composition changes only through migration/ADR (`docs/architecture/DELETION_ARCHIVAL_POLICY.md:22`). ADR-0007 fixes the seed role composition and says the permissions matrix is the source for seed details (`docs/adr/ADR_LOG.md:69`, `docs/adr/ADR_LOG.md:75`).

   Evidence: `Role`, `Permission`, `SectionAccess`, `RolePermission`, and `RoleSectionAccess` protect instance `save()`/`delete()`, but their shared queryset only overrides `delete()` and does not override or block `update()` (`apps/identity_access/models.py:54`, `apps/identity_access/models.py:82`, `apps/identity_access/models.py:133`, `apps/identity_access/models.py:178`, `apps/identity_access/models.py:356`, `apps/identity_access/models.py:396`). A minimal temporary SQLite check changed `roles.edit` using `Permission.objects.filter(code="roles.edit").update(name="AUDIT MUTATION CHECK")`, returning `queryset_update_system_permission_rows=1; changed=True`.

   Impact: system permission labels/scopes, role metadata, and role composition rows can still be mutated outside seed/migration paths without triggering the new guards. This leaves the previous major finding only partially closed for model APIs.

2. User role assignment deletion can still violate the user/access/history archival policy.

   Requirement: once a user participated in the system through assignment, physical deletion is forbidden; blocking/deactivation/archive and preserved history are required (`docs/architecture/DELETION_ARCHIVAL_POLICY.md:11`, `docs/architecture/DELETION_ARCHIVAL_POLICY.md:20`). User/access changes must preserve history rather than silently erasing applied access.

   Evidence: `User.has_physical_delete_usage()` treats `self.roles.exists()` as a usage marker (`apps/identity_access/models.py:280`). But `UserRole.delete()` only protects owner role assignment and allows deletion of every non-owner assignment (`apps/identity_access/models.py:330`, `apps/identity_access/models.py:342`). `UserRoleInline` has no `can_delete = False` or delete permission guard, unlike permission/section/store access inlines (`apps/identity_access/admin.py:114`, `apps/identity_access/admin.py:124`, `apps/identity_access/admin.py:130`, `apps/identity_access/admin.py:136`). A minimal temporary SQLite check showed: `usage_before_userrole_delete=True`, then after deleting the assignment `usage_after_userrole_delete=False`, then the user could be physically deleted: `user_exists_after_assignment_deleted=False`.

   Impact: a non-owner user who was assigned only through the M2M role path can have the assignment erased and then be physically deleted, losing the fact that the assignment existed. This keeps the previous deletion/archive major finding partially open for role assignment/access history.

### minor

None new.

## additional checks

- TASK-003 overreach: not found in checked scope. `apps/stores/models.py` remains a minimal `BusinessGroup` / `StoreAccount` stub for object access (`apps/stores/models.py:1`).
- TASK-009 overreach: not found in checked scope. TASK-002 contains auth/login/admin-related surfaces allowed by the task; no stage-1 web panel screens were introduced in inspected identity/access code.
- ADR-0007 seed matrix unauthorized changes: not found. Role codes and seed permission sets remain aligned with the approved role set and matrix (`apps/identity_access/seeds.py:18`, `apps/identity_access/seeds.py:195`).
- WB/Ozon business logic: not found. Scan found permission and section codes only; no workbook processing, calculation rules, check/process execution, or Excel business logic in TASK-002 implementation files.

## sanity commands run/results

| Command | Result |
| --- | --- |
| `.venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `.venv/bin/python manage.py makemigrations --check --dry-run` | PASS for model diff: `No changes detected`; environment warning from unavailable PostgreSQL credential/history check. |
| `.venv/bin/python manage.py test apps.identity_access` | ENV LIMITATION: failed before tests because PostgreSQL rejected password for user `promo_v2` on `127.0.0.1:5432`. Django discovered 16 tests before failing to create the test database. |
| SQLite override: `call_command("test", "apps.identity_access", verbosity=1)` | PASS: 16 existing identity/access tests passed. |
| `.venv/bin/python manage.py showmigrations identity_access stores --plan` | ENV LIMITATION: failed due to the same PostgreSQL password rejection. |
| SQLite override: `showmigrations identity_access stores --plan` | PASS graph visibility: `identity_access` migrations 0001/0002/0003 and `stores` 0001 listed. |
| Temporary SQLite ORM audit check | CONFIRMED residual risks: system permission changed through `QuerySet.update()`; non-owner `UserRole` deletion removed usage marker and allowed physical user deletion. |

## environment limitations

- Default database connection uses PostgreSQL credentials for `promo_v2`; local password authentication failed on `127.0.0.1:5432`.
- SQLite override was used only for minimal audit sanity and risk confirmation. It did not modify project settings, migrations, or product code.
- This is an audit pass, not a tester pass. Existing tests were run only as sanity after code inspection.

## decision

TASK-002 is not accepted. Return to developer.

## recommendation on separate tester

Run a separate tester only after the two residual major findings above are fixed and re-audited. A tester pass now would be premature because acceptance is blocked at audit level.
