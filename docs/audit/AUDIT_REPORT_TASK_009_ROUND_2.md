# AUDIT_REPORT_TASK_009_ROUND_2

## status

FAIL

## checked scope

- Task/customer decisions: `docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md`, `docs/gaps/GAP_REGISTER.md` `GAP-0010`..`GAP-0013`, `docs/adr/ADR_LOG.md` `ADR-0015`.
- Previous audit inputs: `docs/audit/AUDIT_REPORT_TASK_009.md`, `docs/audit/AUDIT_REPORT_TASK_009_DOC_DECISIONS.md`.
- Specs: `docs/product/UI_SPEC.md`, `docs/product/PERMISSIONS_MATRIX.md`, `docs/product/OPERATIONS_SPEC.md`.
- Architecture: `docs/architecture/FILE_CONTOUR.md`, `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`.
- Implementation: `apps/web/**`, `templates/web/**`, `templates/stores/**`, `templates/base.html`, `apps/marketplace_products/**`, `apps/platform_settings/**`.
- Boundary review only: `apps/identity_access/**`, `apps/files/**`, `apps/operations/**`, `apps/discounts/wb_excel/**`, `apps/discounts/ozon_excel/**`.

Method: static implementation audit against TASK-009/UI_SPEC/customer decisions/access boundaries, plus PostgreSQL sanity commands and relevant test rerun. This is not a tester acceptance pass.

## customer decisions closure table

| GAP | Decision requirement | Round 2 audit result |
| --- | --- | --- |
| `GAP-0010` | Backend `MarketplaceProduct` list/card with store-aware visibility, related operations/files/history. | Partial pass. Model, list/card routes and templates exist (`apps/marketplace_products/models.py:8`, `apps/web/urls.py:20`-`21`, `apps/web/views.py:752`-`802`). Store-aware product visibility exists (`apps/marketplace_products/services.py:100`-`109`). Remark: product card related operations are matched by `product_ref` only, not by product store/marketplace (`apps/web/views.py:788`). |
| `GAP-0011` | WB store parameter write-flow with history/audit, permissions/object access, no Ozon params. | Pass with remarks. Write-flow and immutable history exist (`apps/platform_settings/services.py:77`-`135`, `apps/platform_settings/models.py:98`-`140`); audit `settings.wb_parameter_changed` is created (`apps/platform_settings/services.py:113`-`134`). Ozon screen states WB params are not used (`templates/web/ozon_excel.html:103`). |
| `GAP-0012` | Draft run context upload/replace/delete/version list before Check/Process; run action permissions before operation start. | Fail. Draft upload/delete and run permission checks exist (`apps/web/views.py:381`-`457`, `apps/web/views.py:463`-`517`), but replace deletes the old pre-operation version and creates a new `FileObject`/`v1` instead of preserving replacement as a new version of the same file (`apps/web/views.py:220`-`237`, `apps/files/services.py:144`-`201`). Required `file.input_uploaded` / `file.input_replaced` audit is also absent from the draft upload flow (`apps/web/views.py:523`-`534`; audit catalog in `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`). |
| `GAP-0013` | Admin write-flow for users/roles/permissions/store access with owner/system protections. | Partial pass. Write forms and owner/system protections exist for main flows (`apps/web/views.py:900`-`1229`, `apps/identity_access/models.py:327`-`347`, `apps/identity_access/models.py:492`-`497`, `apps/identity_access/models.py:590`-`597`). Failures remain in scoped/local-admin access and action-specific permission checks, listed below. |

## previous findings closure table

| Previous finding | Round 2 status |
| --- | --- |
| Product list/card missing. | Fixed with remarks. Backend model/list/card implemented, but product card related operations are not constrained by product store/marketplace. |
| Administration write/action screens absent. | Partially fixed. Write UI exists, but local admin scoped access and action-specific permission separation are not correct. |
| Section/index screens render inaccessible links. | Fixed for reference/admin/logs indexes (`apps/web/views.py:738`-`749`, `apps/web/views.py:882`-`896`, `apps/web/views.py:1234`-`1243`). |
| Operation card exposes warning/download actions without rights. | Fixed. `can_confirm_warnings`, `can_download_output`, `can_download_detail` are computed and used (`apps/web/views.py:599`-`647`, `templates/web/operation_card.html:171`-`173`, `templates/web/operation_card.html:202`-`210`). |
| Launch POST creates file versions before run permission denial. | Fixed for Check/Process POST. Current Check/Process actions use existing draft versions and check run permissions before operation start (`apps/web/views.py:431`-`457`, `apps/web/views.py:495`-`517`). |
| Audit/techlog card consistency for operation-linked records. | Fixed. Card checks use `record.store or record.operation.store` (`apps/web/views.py:1293`-`1298`, `apps/web/views.py:1313`-`1323`). |
| Audit/techlog filters thinner than spec. | Not fixed; remains minor. |

## new findings

### Blocker

1. `GAP-0012` is not fully implemented because draft replacement does not preserve version history.
   - Spec/customer decision: UI_SPEC requires draft context and says replacement creates a new version (`docs/product/UI_SPEC.md:77`-`88`); FILE_CONTOUR requires repeated upload to create a new file version, not overwrite/delete history.
   - Implementation: `_replace_single_draft_file` deletes the old pre-operation version first (`apps/web/views.py:229`-`235`) and `_create_input_version` calls `create_file_version` without passing the previous `FileObject` (`apps/web/views.py:523`-`534`), so the new upload becomes a new file object with `version_no = 1` (`apps/files/services.py:162`-`189`).
   - Impact: the visible version list cannot show a replacement chain as `v1 -> v2`; required `file.input_replaced` audit/history semantics are lost before operation start.

### Major

1. Store-scoped/global-store permissions are checked without a store, so local/scoped admin and limited log users lose required flows.
   - Permission resolver requires object access for `STORE`/`GLOBAL_STORE` permissions (`apps/identity_access/services.py:120`-`130`), but many views call `has_permission(..., store=None)`.
   - Admin examples: user list/create and store access assignment gate on global calls (`apps/web/views.py:900`-`905`, `apps/web/views.py:1182`-`1188`), so local admins cannot use required scoped TASK-009 admin workflows despite `PERMISSIONS_MATRIX.md` local-admin scope.
   - Logs examples: audit/techlog index/list gates also use global calls (`apps/web/views.py:1236`-`1239`, `apps/web/views.py:1250`-`1267`), so limited-scope audit/techlog access required by `PERMISSIONS_MATRIX.md` is not available as specified.

2. Admin user actions do not consistently enforce the distinct action permissions from `PERMISSIONS_MATRIX.md`.
   - Spec separates `users.edit`, `users.status.change`, `users.archive`, and `permissions.assign`.
   - Implementation uses `can_manage_user()` for edit/status/archive (`apps/web/views.py:950`-`984`) while `can_manage_user()` returns true for either `users.edit` or `users.status.change` (`apps/identity_access/services.py:177`-`210`).
   - Impact: a user with status-change rights can edit display name/primary role, a user with edit/status rights can archive without `users.archive`, and primary role assignment is not gated by `permissions.assign`.

3. Draft file upload/replacement does not create the audit records required by the approved audit catalog.
   - Spec: `file.input_uploaded` and `file.input_replaced` are stage-1 audit actions in `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`.
   - Implementation: upload paths create only `FileVersion` metadata (`apps/web/views.py:398`-`428`, `apps/web/views.py:480`-`493`, `apps/web/views.py:523`-`534`); no `create_audit_record` call exists for file upload/replace in `apps/web`, `apps/files`, or discount services.
   - Impact: draft run context side effects are not traceable in audit, unlike settings/admin write-flows.

### Minor

1. Audit/techlog filters remain materially thinner than UI_SPEC/AUDIT_AND_TECHLOG_SPEC.
   - Required filters include period, user, action/event type, related store, related operation and severity where applicable.
   - Current audit list supports only `q` and `action` (`apps/web/views.py:1281`-`1289`, `templates/web/audit_list.html:5`-`8`); techlog supports only `q` and `severity` (`apps/web/views.py:1301`-`1310`, `templates/web/techlog_list.html:48`-`51`).

2. Product card related operations can include unrelated operations with the same product reference in another accessible store.
   - Implementation filters related operations by `detail_rows__product_ref=product.sku` only (`apps/web/views.py:788`), without `store=product.store` and `marketplace=product.marketplace`.
   - Impact: no object-access leak was found, but product explainability can show unrelated operations/files when SKU/article values collide across stores.

3. Direct test coverage for product/settings modules is thin.
   - `apps/marketplace_products/tests.py` and `apps/platform_settings/tests.py` contain only placeholders; coverage exists mainly through `apps/web/tests.py`.
   - The rerun test suite passed, but TASK-009 requested focused tests for product list/card, WB parameter write/history/audit, draft upload/replace/delete context, and admin write-flow permissions/object access.

## WB/Ozon business logic and boundaries

- No WB default value change found; defaults remain `70/55/55` in `apps/discounts/wb_excel/services.py:53`-`57`.
- No WB/Ozon API mode replacement found; Ozon UI does not expose WB parameters (`templates/web/ozon_excel.html:103`).
- No approved WB/Ozon calculation order or output-column change was found in this audit pass.
- Product sync was added around operation detail rows (`apps/discounts/wb_excel/services.py:700`-`718`, `apps/discounts/ozon_excel/services.py:366`-`381`); no calculation-output regression was found statically.
- No TASK-010 overreach found.

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

Result: passed. Output summary: `Ran 70 tests in 71.658s`, `OK`.

## decision

Return to developer.

TASK-009 is not accepted in round 2. The remaining blocker is implementation-level, not a new customer decision: draft replacement/version/audit semantics do not satisfy `GAP-0012`/UI_SPEC/FILE_CONTOUR. The major admin/log permission issues also need correction before acceptance.

## recommendation

- Separate tester next: not yet. Send back to developer first for the blocker and major permission defects.
- Customer questions: none required from this audit. The issues are covered by existing UI_SPEC, customer decisions, PERMISSIONS_MATRIX, FILE_CONTOUR and AUDIT_AND_TECHLOG_SPEC.
