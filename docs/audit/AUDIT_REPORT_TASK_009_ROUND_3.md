# AUDIT_REPORT_TASK_009_ROUND_3

## status

FAIL

## checked scope

- Previous audit inputs: `docs/audit/AUDIT_REPORT_TASK_009_ROUND_2.md`, `docs/audit/AUDIT_REPORT_TASK_009.md`.
- Specs: `docs/product/UI_SPEC.md`, `docs/product/PERMISSIONS_MATRIX.md`.
- Architecture: `docs/architecture/FILE_CONTOUR.md`, `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`.
- Implementation: `apps/web/views.py`, `apps/web/tests.py`, `templates/web/wb_excel.html`, `templates/web/ozon_excel.html`, `templates/web/audit_list.html`, `templates/web/techlog_list.html`, `apps/identity_access/services.py`, `apps/files/services.py`, `apps/marketplace_products/**`, `apps/platform_settings/**`.
- Boundary static review: WB/Ozon Excel services/templates for API/business-logic overreach.

Method: implementation audit against round 2 findings and task-scoped specs, plus requested PostgreSQL sanity commands. This is not a tester acceptance pass.

## previous findings closure table

| Round 2 finding | Round 3 result |
| --- | --- |
| Blocker: draft replace deletes old pre-operation version and creates a new `FileObject`/`v1` instead of preserving version chain. | Closed. `_replace_single_draft_file` now resolves the old draft `FileVersion` and passes `old_version.file` into `_create_input_version` (`apps/web/views.py:308`-`336`); `create_file_version` appends `version_no = current_max + 1` on an existing `FileObject` (`apps/files/services.py:162`-`201`). Explicit delete remains a separate action through `_delete_draft_version` and `delete_pre_operation_file_version` (`apps/web/views.py:339`-`353`, `apps/files/services.py:302`-`314`). |
| Major: missing `file.input_uploaded` / `file.input_replaced` audit records. | Closed. Draft upload/replace calls `_audit_input_version_upload` for WB price, WB promo and Ozon input uploads (`apps/web/views.py:258`-`305`, `apps/web/views.py:502`-`525`, `apps/web/views.py:584`-`591`). Metadata is safe for UI: file visible id, version ids/numbers, original/logical names, scenario, size and checksum; no `storage_path`, filesystem path or secret values are written (`apps/web/views.py:265`-`286`). |
| Major: store-scoped/global-store checks for local admin and log flows used global permission calls without store context. | Mostly closed for the reported admin/log flows. Admin indexes/lists now use `_has_permission_in_scope` and per-store checks (`apps/web/views.py:142`-`156`, `apps/web/views.py:997`-`1018`, `apps/web/views.py:1313`-`1320`); audit/techlog index and lists use store-aware scope helpers (`apps/web/views.py:1366`-`1403`, `apps/web/views.py:1417`-`1524`). A new related major remains in the reference index, listed below. |
| Major: admin user actions do not enforce distinct `users.edit` / `users.status.change` / `users.archive` / `permissions.assign`. | Closed. `user_card` checks `users.edit` for save, `permissions.assign` for primary role changes and overrides, `users.status.change` for block/unblock, and `users.archive` for archive (`apps/web/views.py:1066`-`1132`). `can_manage_user_action` preserves owner/full-scope protections and shared-store scope (`apps/identity_access/services.py:169`-`199`). |
| Minor: audit/techlog filters thinner than spec. | Closed for TASK-009 audit level. Audit list now supports period, user, action, store, operation and search (`apps/web/views.py:1417`-`1458`, `templates/web/audit_list.html:5`-`13`). Techlog list now supports period, user, event, store, operation, severity and search (`apps/web/views.py:1479`-`1524`, `templates/web/techlog_list.html:5`-`14`). |
| Minor: product related operations only matched `product_ref`, not store/marketplace. | Closed. Product card related operations are now constrained by `marketplace=product.marketplace`, `store=product.store` and `detail_rows__product_ref=product.sku` (`apps/web/views.py:895`-`904`). |
| Minor: focused tests thin. | Acceptable for audit. Focused tests were added for product related operation scope, WB parameter history/audit, draft replace chain/audit, distinct admin action permissions and launch permission denial before file creation (`apps/web/tests.py:111`-`163`, `apps/web/tests.py:165`-`189`, `apps/web/tests.py:210`-`246`, `apps/web/tests.py:248`-`305`, `apps/web/tests.py:307`-`345`). |

## new findings

### Blocker

None found in round 3.

### Major

1. Store-scoped users with `stores.list.view` can be denied from the references index before reaching the stores list.
   - Spec: store list access is `stores.list.view` with object access or global admin rights (`docs/product/UI_SPEC.md:266`-`281`); local admin/manager/observer store visibility is store-scoped in `PERMISSIONS_MATRIX.md` (`docs/product/PERMISSIONS_MATRIX.md:119`-`143`).
   - Permission model: `stores.list.view` is `GLOBAL_STORE` (`apps/identity_access/seeds.py:80`), and `has_permission()` for `STORE`/`GLOBAL_STORE` requires store/object context unless the user has full object scope (`apps/identity_access/services.py:120`-`130`).
   - Implementation: `reference_index` computes `can_stores` with `has_permission(request.user, "stores.list.view")` and no store context (`apps/web/views.py:847`-`858`). For a local/scoped user who has `stores.view` section access and `stores.list.view` only through assigned stores, this evaluates false; if the user also lacks `products.view` the route raises `PermissionDenied`.
   - Impact: the web panel can hide/deny the approved store directory entry point for local/scoped users even though object-scoped access exists. This reopens the store-scoped permission pattern for the references area and should be fixed by using the same in-scope/per-store pattern as admin/log flows.

### Minor

None found in round 3.

## boundary review

- No WB/Ozon API mode replacement found. Ozon UI still states WB parameters are not used and only K/L are changed (`templates/web/ozon_excel.html:42`-`45`).
- WB defaults remain `70/55/55` (`apps/discounts/wb_excel/services.py:53`-`56`).
- Product sync additions remain post-operation explainability updates and do not change WB/Ozon calculation branches in this static pass (`apps/discounts/wb_excel/services.py:705`-`718`, `apps/discounts/ozon_excel/services.py:369`-`381`).
- No TASK-010/deployment overreach found in the checked files.
- No hidden UX/business decision was needed to close the remaining issue; it is covered by the existing permissions/UI specs.

## PostgreSQL commands/results

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check
```

Result: passed. Output: `System check identified no issues (0 silenced).`

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py makemigrations --check --dry-run
```

Result: passed with environment warning. Output included `No changes detected`; Django also warned that database `promo_v2` does not exist while checking migration history.

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.web apps.marketplace_products apps.platform_settings apps.identity_access apps.files apps.operations apps.discounts.wb_excel apps.discounts.ozon_excel
```

Result: passed. Output summary: `Ran 73 tests in 73.123s`, `OK`.

## decision

Return to developer.

TASK-009 is not accepted in round 3 because one new major store-scoped permission defect remains in the references index. The round 2 blocker is closed and the previous major findings are closed for their original admin/log/file areas.

## recommendation

- Separate tester next: not yet. Fix the reference-index store-scope defect first, then run a focused developer sanity check for local admin/manager/observer access to references/stores.
- Customer questions: none required. The remaining issue is covered by `UI_SPEC` and `PERMISSIONS_MATRIX`.
