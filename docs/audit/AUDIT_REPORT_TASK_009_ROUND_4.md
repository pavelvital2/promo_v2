# AUDIT_REPORT_TASK_009_ROUND_4

## status

PASS

## checked scope

Narrow round 4 audit only: closure of the single major finding from `docs/audit/AUDIT_REPORT_TASK_009_ROUND_3.md` and absence of regression in the references/store-scope permission path.

Checked task-scoped inputs:

- `docs/audit/AUDIT_REPORT_TASK_009_ROUND_3.md`
- `apps/web/views.py`
- `apps/web/tests.py`
- `docs/product/PERMISSIONS_MATRIX.md`
- `apps/identity_access/services.py`

Related implementation read for "inaccessible stores are not exposed":

- `apps/stores/services.py`
- `apps/stores/views.py`
- `templates/web/reference_index.html`
- `templates/stores/store_list.html`

This is an audit pass for the narrow TASK-009 round 4 scope, not a separate tester acceptance pass.

## previous major closure

Closed.

The round 3 major was: store-scoped users with `stores.list.view` could be denied from the references index because `reference_index` used `has_permission(request.user, "stores.list.view")` without store context.

Round 4 result:

- `reference_index` now computes `can_stores` through `_has_permission_in_scope(request.user, "stores.list.view")` while still requiring `stores.view` section access (`apps/web/views.py:847`-`860`).
- `_has_permission_in_scope` checks global permission first, then checks whether any visible store grants the permission in object scope (`apps/web/views.py:136`-`146`).
- For store/global-store permissions, `has_permission` requires both the action permission and store/object access unless the user has full object scope; direct deny remains prioritary (`apps/identity_access/services.py:97`-`130`).
- A focused regression test was added: a local admin with `stores.list.view` and one allowed store can open `reference_index`, sees the store-list link, does not see product-list link, and the store list excludes an inaccessible store (`apps/web/tests.py:111`-`145`).

## findings blocker/major/minor

### Blocker

None.

### Major

None.

### Minor

None.

## regression checks

1. `reference_index` uses store-scoped permission logic so local/store-scoped users with `stores.list.view` and at least one store can access references.
   - Passed. The route uses `_has_permission_in_scope`, and the focused test covers a local admin with one allowed store.

2. Inaccessible stores are not exposed.
   - Passed. `store_list` renders `visible_stores_queryset(request.user)` only (`apps/stores/views.py:26`-`65`).
   - `visible_stores_queryset` checks `has_permission(user, "stores.list.view", store)` per store and returns only allowed ids (`apps/stores/services.py:134`-`148`).
   - The focused test verifies that the allowed store is present and the denied/unassigned store is absent.

3. No new permission bypass for users without store/object access.
   - Passed in the checked scope. A user with `stores.view` / `stores.list.view` but no full scope and no accessible store does not satisfy `_has_permission_in_scope` for stores; object rows are still filtered through `visible_stores_queryset`.
   - Product list/card paths remain store-filtered by `products_visible_to` / `visible_stores_queryset` in the checked view path, and no store rows are exposed through the references index template.

## PostgreSQL commands/results

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check
```

Result: passed.

Output summary:

```text
System check identified no issues (0 silenced).
```

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.web
```

Result: passed.

Output summary:

```text
Found 12 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
............
----------------------------------------------------------------------
Ran 12 tests in 13.886s

OK
Destroying test database for alias 'default'...
```

## decision

TASK-009 accepted for the narrow round 4 audit scope.

The single round 3 major is closed, and no blocker/major/minor regressions were found in the checked permission path.

## recommendation

Separate tester next: yes.

Proceed to an independent tester pass for TASK-009 acceptance scenarios. Formal acceptance remains subject to the project's normal tester protocol and any external acceptance artifact gates outside this narrow audit.
