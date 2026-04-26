# AUDIT_REPORT_TASK_009

## status

FAIL

## checked scope

- Task: `docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md`
- Specs: `docs/product/UI_SPEC.md`, `docs/product/PERMISSIONS_MATRIX.md`, `docs/product/OPERATIONS_SPEC.md`, `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`, `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md`
- Architecture: `docs/architecture/FILE_CONTOUR.md`, `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- Gaps: `docs/gaps/GAP_REGISTER.md`, especially `GAP-0010`, `GAP-0011`, `GAP-0012`
- Implementation: `apps/web/views.py`, `apps/web/urls.py`, `apps/web/tests.py`, `templates/base.html`, `templates/web/**`, `templates/stores/**`, `apps/stores/**` for route/template integration

Audit method: static implementation audit against UI_SPEC/TASK-009/permissions/object access/file and operation rules, plus required PostgreSQL sanity commands. This report does not replace tester acceptance testing.

## route/screen coverage summary

| Area | Coverage | Audit result |
| --- | --- | --- |
| Home/dashboard | `web:home` implemented with accessible sections, quick actions, operations, notifications, file retention state. | Partial pass; data is filtered, but notification access has no explicit permission gate. |
| Marketplace index | `web:marketplaces` implemented. | Partial pass; scenario links depend on available stores, not explicit section route denial. |
| WB Excel launch/result/process | `web:wb_excel`, `web:operation_result`, `web:warning_confirmation` implemented. | Partial pass; no WB API overreach and WB defaults/codes not changed. Draft replace/delete is absent under valid `GAP-0012`; action permission side effects need fix. |
| Ozon Excel launch/result/process | `web:ozon_excel`, `web:operation_result`, `web:warning_confirmation` implemented. | Partial pass; no WB params shown on Ozon, no API replacement. Draft replace/delete is absent under valid `GAP-0012`; action permission side effects need fix. |
| Operations list/card | `web:operation_list`, `web:operation_card` implemented. | Partial pass; object filtering exists, but download/confirm controls are not visibility-gated by action rights. |
| Stores list/card/history/connection | `stores:*` routes implemented. | Pass with remarks; object checks use store services and API block remains stage-2 notice. |
| Product list/card | `web:product_list` is a status page; no product card route. | Blocked by valid `GAP-0010`; cannot be accepted as full UI_SPEC coverage before customer/orchestrator decision or backend task. |
| Settings | `web:settings_index` read-only system/store params. | Blocked by valid `GAP-0011`; no store parameter write-flow or parameter history screen. |
| Users/roles/access administration | list/card/dictionary/access list routes implemented read-only. | Major gap not registered: UI_SPEC requires create/edit/assign flows and controls; current UI silently downgrades to read-only. |
| Audit/techlog | list/card routes implemented. | Partial pass; no edit/delete UI found, sensitive techlog is gated, but index visibility and card object checks need correction. |
| System notifications | `web:notification_list` implemented. | Partial pass; object filtering exists, but no explicit section/permission gate. |

No implementation overreach into TASK-010/deployment acceptance was found.

## GAP-0010..0012 validation

| GAP | Validation | Must go to customer before TASK-009 acceptance? | Notes |
| --- | --- | --- | --- |
| `GAP-0010` Product directory UI without backend product model | Valid. UI_SPEC requires product list/card and related operations/files/history (`docs/product/UI_SPEC.md:291`-`323`), while the app has only a placeholder `apps/marketplace_products` config and `templates/web/product_list.html:4`-`8`; no product card route exists in `apps/web/urls.py:19`-`20`. | Yes. | Customer/orchestrator must decide whether to add a backend product task or explicitly accept a stage-1 status screen instead of product list/card. |
| `GAP-0011` Store parameter write-flow without approved audit/history service | Valid. UI_SPEC requires store parameter edits, history and audit (`docs/product/UI_SPEC.md:344`-`376`), but models only store values (`apps/platform_settings/models.py:63`-`93`) and TASK-009 renders read-only with a note (`templates/web/settings_index.html:17`-`25`). | Yes. | Customer/orchestrator must decide whether write-flow is required before UI acceptance or split into backend/service task. |
| `GAP-0012` Draft pre-run upload/replace/delete context | Valid. OPERATIONS_SPEC requires an active draft scenario context for upload/replace/delete before operation start (`docs/product/OPERATIONS_SPEC.md:46`-`57`); current UI is single-submit upload/check/process (`templates/web/wb_excel.html:6`-`44`, `templates/web/ozon_excel.html:6`-`29`). | Yes. | Customer/orchestrator must approve the single-submit limitation or create a backend/UI task for draft run context. |

Additional missing customer/orchestrator question: whether stage-1 administration must include user/role/object-access write flows now, as UI_SPEC specifies, or whether a separate backend/service gap/task should be opened. This was not recorded as a developer gap.

## findings

### Blocker

1. Mandatory product card/list coverage is not implemented; only a status page exists.
   - Spec/task: `docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md:64`-`70`, `docs/product/UI_SPEC.md:291`-`323`.
   - Implementation: route list has `references/products/` only (`apps/web/urls.py:19`-`20`), and template is a placeholder (`templates/web/product_list.html:4`-`8`).
   - Assessment: this is covered by valid `GAP-0010`, but TASK-009 cannot be accepted without customer/orchestrator decision or a separate backend/product implementation task.

### Major

1. Administration write/action screens required by UI_SPEC are absent and not covered by a registered gap.
   - Spec: user create/edit/block/assign flows (`docs/product/UI_SPEC.md:380`-`412`), role create/edit/archive flows (`docs/product/UI_SPEC.md:414`-`446`), store access assignment write flow (`docs/product/UI_SPEC.md:465`-`480`).
   - Implementation: URL map has read-only list/card routes only for users/roles/permissions/store access (`apps/web/urls.py:22`-`28`); templates show read-only tables/cards (`templates/web/user_list.html:4`-`12`, `templates/web/user_card.html:4`-`20`, `templates/web/role_card.html:4`-`10`, `templates/web/store_access_list.html:4`-`10`).
   - Risk: TASK-009 silently reduces mandatory admin UX/functionality instead of routing the missing write-flow as a gap.

2. Access-aware visibility is incomplete on section/index screens.
   - Spec: unavailable sections must not be shown as working (`docs/product/UI_SPEC.md:36`-`43`, `docs/product/UI_SPEC.md:45`-`60`).
   - Implementation: `reference_index`, `admin_index`, and `logs_index` render without route-level section/permission checks (`apps/web/views.py:549`-`551`, `apps/web/views.py:587`-`589`, `apps/web/views.py:685`-`687`) and their templates show all child links unconditionally (`templates/web/reference_index.html:5`-`14`, `templates/web/admin_index.html:5`-`9`, `templates/web/logs_index.html:5`-`8`).
   - Risk: target routes may still deny, but direct access to index screens presents inaccessible functions as working UI.

3. Operation card exposes action links without checking download/confirmation rights.
   - Spec: observer is view-only and has no default output/detail download (`docs/product/PERMISSIONS_MATRIX.md:19`-`28`, `docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md:72`-`79`); output download requires explicit scenario download rights and retention/object checks (`docs/architecture/FILE_CONTOUR.md:56`-`64`).
   - Implementation: operation card always renders warning confirmation when warnings exist (`templates/web/operation_card.html:5`-`9`) and renders output download link whenever the file is physically available (`templates/web/operation_card.html:38`-`46`). The view computes `can_view_details` only, not `can_download_output` or `can_confirm_warnings` (`apps/web/views.py:438`-`458`).
   - Risk: server-side download and confirmation checks exist, but UI violates access-aware visibility and the observer no-default-download requirement.

4. Excel launch POST can create input file versions before run action permission is denied.
   - Spec: UI must enforce action/object restrictions server-side and file/run boundaries (`docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md:72`-`79`, `docs/architecture/FILE_CONTOUR.md:89`-`97`).
   - Implementation: WB/Ozon POST handlers check only `upload_input` before creating file versions (`apps/web/views.py:273`-`301`, `apps/web/views.py:324`-`341`), then call services that enforce `run_check`/`run_process` later (`apps/operations/services.py:356`-`364`, `apps/operations/services.py:627`-`635`).
   - Risk: a user with upload rights but without run_check/run_process can cause pre-operation file metadata/physical files to be created through a tampered launch POST before the action is rejected.

5. Audit/techlog card object checks do not fully match list visibility for operation-linked records.
   - Spec: limited logs can be visible through related store or operation object access (`docs/product/PERMISSIONS_MATRIX.md:108`-`114`, `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md:110`-`117`).
   - Implementation: list query allows records by `operation__store_id` (`apps/web/views.py:694`-`711`), but card permission checks pass only `record.store` to `has_permission` (`apps/web/views.py:736`-`741`, `apps/web/views.py:756`-`765`).
   - Risk: operation-linked records with `store` null but accessible `operation.store` can appear in list and then be denied on card; this breaks route consistency and object-access semantics.

### Minor

1. Audit/techlog filters are materially thinner than UI_SPEC.
   - Spec requires period, user, action/event type, related store, related operation, severity where applicable, and visible_id/entity search (`docs/architecture/AUDIT_AND_TECHLOG_SPEC.md:118`-`130`; `docs/product/UI_SPEC.md:484`-`550`).
   - Implementation has audit `q/action` and techlog `q/severity` only (`apps/web/views.py:724`-`753`, `templates/web/audit_list.html:5`-`8`, `templates/web/techlog_list.html:5`-`8`).

2. TASK-009 route smoke tests exist, but permission/object-access coverage is not present in `apps/web/tests.py`.
   - Task required template/view tests for permissions and object access (`docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md:80`-`85`).
   - Current web tests are health/home/smoke routes only (`apps/web/tests.py:10`-`80`).

## WB/Ozon business logic and boundaries

- No UI-side change to WB defaults was found; defaults remain in service/spec as `70/55/55` (`apps/discounts/wb_excel/services.py:52`-`56`, `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md:119`-`127`).
- No new WB reason/result codes were found in the UI; detail rows display stored codes (`templates/web/operation_card.html:81`-`84`).
- Ozon UI explicitly states that WB parameters are not used and that only K/L are changed (`templates/web/ozon_excel.html:18`-`24`).
- No API mode was implemented as a replacement for Excel in TASK-009. Store connection UI keeps the stage-2 notice (`templates/stores/store_card.html:19`-`29`).

## PostgreSQL commands/results

Command:

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check
```

Result: passed. Output: `System check identified no issues (0 silenced).`

Command:

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.web apps.stores
```

Result: passed. Output summary: `Ran 16 tests in 7.046s`, `OK`, `System check identified no issues (0 silenced).`

## decision

Return to developer.

TASK-009 is not accepted. `GAP-0010`, `GAP-0011`, and `GAP-0012` are valid and must be routed to orchestrator/customer before formal TASK-009 acceptance or stage-1 acceptance. In addition, the unregistered administration write-flow gap and access-aware visibility issues require developer action or explicit orchestration/customer decisions.

## recommendation

Customer/orchestrator questions before acceptance:

1. Is `GAP-0010` acceptable as a stage-1 product directory status screen, or must backend product model/list/card be implemented before TASK-009 acceptance?
2. For `GAP-0011`, should store-level WB parameter edit/history/audit service be implemented now, or is read-only parameter UI accepted for stage 1?
3. For `GAP-0012`, is single-submit upload/check/process acceptable, or must a draft run context with replace/delete/version list be implemented before acceptance?
4. Should UI_SPEC administration write flows for users, roles and store access assignments be implemented in TASK-009, or should a new gap/backend task be opened and routed to customer?

Separate tester next: not yet. First return to developer/orchestrator for the major coverage/access issues and customer questions; tester acceptance would otherwise validate a known incomplete screen set.
