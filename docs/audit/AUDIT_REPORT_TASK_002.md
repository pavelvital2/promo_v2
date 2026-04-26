# AUDIT_REPORT_TASK_002.md

## status

FAIL

## checked scope

- Task: `docs/tasks/implementation/stage-1/TASK-002-auth-users-roles-permissions.md`.
- Specs: `docs/product/PERMISSIONS_MATRIX.md`, identity/access parts of `docs/architecture/DATA_MODEL.md`, user/role rules from `docs/architecture/DELETION_ARCHIVAL_POLICY.md`.
- ADR: `docs/adr/ADR_LOG.md` entries ADR-0007 and ADR-0008.
- Code: `apps/identity_access/**`, `apps/stores/models.py`, `apps/stores/migrations/0001_initial.py`, `config/settings.py`, `config/urls.py`, `templates/registration/login.html`, `templates/base.html`.
- Audit did not implement fixes and did not change product code or source specs.

## commands run/results

| Command | Result |
| --- | --- |
| `.venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `.venv/bin/python manage.py test apps.identity_access` | ENV LIMITATION: failed before tests because PostgreSQL rejected password for user `promo_v2` on `127.0.0.1:5432`. |
| SQLite override: `call_command('test', 'apps.identity_access', verbosity=2)` | PASS: 11 identity/access tests passed. |
| `.venv/bin/python manage.py makemigrations --check --dry-run` | PASS: `No changes detected`; warning only from unavailable PostgreSQL credential/history check. |
| SQLite override: `migrate`; `seed_identity_access`; `seed_identity_access` | PASS: repeat seed returned `roles=0, permissions=0, sections=0, role_permissions=0, role_sections=0`. |
| SQLite override: full `call_command('test', verbosity=1)` | PASS: 13 tests passed. |
| `rg` scan for WB/Ozon/business logic in implementation files | PASS: found permission codes/placeholders only; no WB/Ozon calculation, Excel processing, or operation execution logic in TASK-002 implementation. |

## findings

### blocker

None found.

### major

1. System roles, permissions and section access are mutable through Django admin, despite the TASK-002/system dictionary immutability requirements.

   Requirements: TASK-002 expects system roles and permissions to be immutable through regular UI where required (`docs/tasks/implementation/stage-1/TASK-002-auth-users-roles-permissions.md:62`-`64`); data model says system dictionaries are fixed and not user-editable (`docs/architecture/DATA_MODEL.md:11`); deletion policy says `Permission / SectionAccess` are immutable system dictionaries and changes go only through migration/ADR (`docs/architecture/DELETION_ARCHIVAL_POLICY.md:20`).

   Evidence: `SystemDictionaryAdmin` blocks delete only, not change (`apps/identity_access/admin.py:22`-`26`). `PermissionAdmin` and `SectionAccessAdmin` have no `has_change_permission`/readonly protection for `is_system=True` (`apps/identity_access/admin.py:52`-`63`). `RoleAdmin` blocks change only for owner role by non-owner, but other system roles and their `RolePermissionInline` / `RoleSectionAccessInline` remain editable (`apps/identity_access/admin.py:39`-`49`, `apps/identity_access/admin.py:29`-`36`). Model-level `Role`, `Permission`, and `SectionAccess` protect only `delete()`, not `save()` mutation (`apps/identity_access/models.py:41`-`44`, `apps/identity_access/models.py:65`-`68`, `apps/identity_access/models.py:88`-`91`).

   Impact: an admin UI user can alter system permission dictionaries or seed role composition without ADR/migration, including roles fixed by ADR-0007. This violates TASK-002 acceptance expectations and the system dictionary policy.

2. Physical deletion policy for non-owner users and access/history rows is not enforced.

   Requirements: deletion policy allows physical deletion of `User` only before first login, assignment, audit or operation; after use, user must be blocked/deactivated/archived and history must be preserved (`docs/architecture/DELETION_ARCHIVAL_POLICY.md:13`-`17`, `docs/architecture/DELETION_ARCHIVAL_POLICY.md:20`). The data model requires significant user/access changes and block/archive actions to be recorded in history (`docs/architecture/DATA_MODEL.md:105`-`113`).

   Evidence: `User.delete()` protects only owner and otherwise physically deletes (`apps/identity_access/models.py:179`-`182`). Dependent assignment/access/history models use `on_delete=CASCADE` for user links, including `UserRole`, `UserPermissionOverride`, `UserSectionAccessOverride`, `StoreAccess`, `UserChangeHistory`, and `UserBlockHistory` (`apps/identity_access/models.py:185`-`187`, `apps/identity_access/models.py:235`-`253`, `apps/identity_access/models.py:275`-`293`, `apps/identity_access/models.py:315`-`331`, `apps/identity_access/models.py:359`-`372`, `apps/identity_access/models.py:382`-`395`). `UserAdmin.has_delete_permission()` blocks only owner deletion (`apps/identity_access/admin.py:130`-`138`).

   Impact: regular admin deletion can remove a non-owner user together with role assignments, object access, permission overrides, and user history even after the account was used. That contradicts the archival/history requirements.

### minor

1. Owner detection is inconsistent between model-level protections and service-level permission checks.

   Evidence: `User.is_owner` checks only `primary_role` (`apps/identity_access/models.py:157`-`159`), while `services.is_owner()` treats either `primary_role` or M2M `roles` as owner membership (`apps/identity_access/services.py:22`-`32`). Model-level protections for owner delete/status/deny rely on `User.is_owner` (`apps/identity_access/models.py:161`-`181`, `apps/identity_access/models.py:265`-`272`, `apps/identity_access/models.py:305`-`312`, `apps/identity_access/models.py:349`-`356`).

   Impact: if an owner role is assigned through `roles` rather than `primary_role`, service checks and model protections can disagree. Current tests create owner with `primary_role`, so the tested path is protected.

2. Object access implementation remains a permissible TASK-002 stub, but local user-management scope is not fully modeled yet.

   Evidence: `StoreAccess` exists and deny overrides allow for concrete stores (`apps/identity_access/models.py:315`-`356`, `apps/identity_access/services.py:39`-`52`), and stores are a minimal dependency stub (`apps/stores/models.py:1`-`74`). `can_manage_user()` has no store/target-store parameter and therefore cannot express local admin management of users within assigned stores (`apps/identity_access/services.py:161`-`168`).

   Impact: acceptable as a TASK-002/TASK-003 boundary note only if TASK-003 implements the missing target-object binding. It should be explicitly handed off.

## passed checks against requested points

- TASK-002 and permissions matrix: permission catalog and seed role names match ADR-0007 / `PERMISSIONS_MATRIX.md` in the inspected code (`apps/identity_access/seeds.py:17`-`29`, `apps/identity_access/seeds.py:31`-`200`).
- Custom user model is configured via `AUTH_USER_MODEL = "identity_access.User"` (`config/settings.py:52`).
- Visible user identifier follows `USR-NNNNNN` after save (`apps/identity_access/models.py:171`-`177`), covered by test (`apps/identity_access/tests.py:246`-`247`).
- Owner protection for the tested primary-role owner path blocks admin management, status change, delete, and direct denies (`apps/identity_access/services.py:161`-`179`, `apps/identity_access/models.py:161`-`181`, `apps/identity_access/models.py:265`-`272`).
- Direct deny precedence over allow is implemented for permissions, section access, and store access (`apps/identity_access/services.py:77`-`124`, `apps/identity_access/services.py:127`-`158`, `apps/identity_access/services.py:39`-`52`).
- ADR-0007 seed roles exist: Owner, Global admin, Local admin, Manager, Observer (`apps/identity_access/seeds.py:17`-`29`).
- TASK-003 overreach not found: stores are minimal `BusinessGroup` / `StoreAccount` stubs used for object access only (`apps/stores/models.py:1`-`74`).
- Seed idempotency is implemented with `update_or_create` / `get_or_create` (`apps/identity_access/seeds.py:236`-`296`) and passed repeat-run checks.
- WB/Ozon business logic was not implemented; only permission codes and placeholder apps were found.

## environment limitations

- Repository is not a Git worktree from this directory: `git status --short` failed with `fatal: not a git repository`.
- Default PostgreSQL connection is configured in `config/settings.py:86`-`96`, but local credentials for `promo_v2` were not usable during tests: password authentication failed for `promo_v2` on `127.0.0.1:5432`.
- SQLite override was used only for audit tests and seed idempotency checks. It did not modify project settings or product code.

## decision

TASK-002 is not accepted. Return to developer for fixes before moving to TASK-003.

## next handoff

- Fix system dictionary/admin immutability for system roles, permissions, section access, and role-permission/role-section composition according to TASK-002, ADR-0007, and deletion policy.
- Enforce user/access deletion vs archive/block/deactivate policy so used non-owner users and their assignments/history are not physically deleted through regular admin/UI.
- Align owner detection across model and service layers or constrain owner assignment to the single approved representation.
- Keep TASK-003 work blocked until the major TASK-002 findings are corrected and re-audited.
