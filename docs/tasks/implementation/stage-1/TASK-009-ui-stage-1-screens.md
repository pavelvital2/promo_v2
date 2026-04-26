# TASK-009: UI Stage 1 Screens

## ID

TASK-009-ui-stage-1-screens

## Роль агента

Разработчик Codex CLI, server-rendered UI.

## Цель

Реализовать обязательные server-rendered Django templates screens and workflows этапа 1 по `docs/product/UI_SPEC.md`, включая backend/service pieces, без которых обязательные UI workflows TASK-009 не могут быть приняты.

Customer decisions от 2026-04-25 по `GAP-0010`, `GAP-0011`, `GAP-0012` и `GAP-0013` входят в текущий scope TASK-009. Перенос этих решений в TASK-010 или замена status/read-only screens не допускаются.

## Task-scoped входные документы

- `AGENTS.md`
- `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`
- `docs/product/UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/adr/ADR_LOG.md` ADR-0006, ADR-0007, ADR-0008, ADR-0009, ADR-0010, ADR-0011, ADR-0013, ADR-0014, ADR-0015
- `docs/gaps/GAP_REGISTER.md`
- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`

## Релевантные разделы ТЗ

- §5
- §6
- §11
- §12
- §17-§20
- §27

## Разрешённые файлы / области изменения

- Django templates, views, forms, URL routes and static assets for stage 1 UI.
- Backend models/services/migrations required only to fulfill the approved TASK-009 customer decisions:
  - backend product model/list/card for `MarketplaceProduct` according to `docs/architecture/DATA_MODEL.md`;
  - WB store parameter write-flow with history/audit;
  - draft run context for upload/replace/delete files, version list, then Check/Process;
  - admin write-flow for users/roles/permission assignment/store access assignment.
- UI tests.
- Documentation updates for actual routes/screens if needed.

## Запрещённые области

- SPA rewrite or frontend framework baseline that contradicts ADR-0006.
- In-app text that changes business rules.
- Showing inaccessible stores/files/operations/logs.
- Changing approved WB defaults, reason/result codes or out-of-range behavior in UI text/actions.
- Resolving UX/functionality gaps по веб-панели without customer escalation through orchestrator.
- Deferring `GAP-0010`, `GAP-0011`, `GAP-0012` or `GAP-0013` decisions to TASK-010.
- Accepting status screens/read-only substitutes for product directory, WB store parameters, draft file context or administration write-flow.

## Зависимости

- TASK-002 for auth/access.
- TASK-003 through TASK-006 for core screens.
- TASK-007/TASK-008 for complete WB/Ozon screens, subject to gaps.

## Expected output

- Home/dashboard.
- WB/Ozon Excel scenario screens with draft run context: upload/replace/delete files, version list, then "Проверить" / "Обработать".
- Operation list/card.
- Store/cabinet list/card.
- Product backend model/list/card for current stage-1 marketplace products.
- Settings screens including WB store parameter write-flow with history/audit.
- Users/roles/access screens including create/edit/block/archive, role edit where allowed, permission assignment and store access assignment.
- Audit/techlog screens.
- System notifications view.

## Acceptance criteria

- Screens follow `docs/product/UI_SPEC.md` roles, actions, messages, filters and transitions.
- All object access restrictions are applied server-side.
- Desktop-first layout is usable and does not hide required actions.
- Observer has view-only behavior and no default output/detail download.
- UI shows registered acceptance states explicitly; artifact-gated states are used only for future customer artifacts that are actually pending.
- `GAP-0010` is implemented now: product list/card work against backend `MarketplaceProduct` data and related operations/files/history.
- `GAP-0011` is implemented now: WB store parameters can be set/cleared/saved where allowed, with immutable history and audit.
- `GAP-0012` is implemented now: WB/Ozon upload screens have draft run context with file upload/replace/delete, version list and Check/Process after draft validation.
- `GAP-0013` is implemented now: administration write-flow covers users, role editing where allowed, permission assignment and store access assignment.

## Required checks

- Django template/view tests for permissions and object access.
- Smoke tests for mandatory screens.
- UI workflow tests for check/process where implemented.
- Tests for product list/card, WB store parameter write/history/audit, draft file upload/replace/delete context, and admin write-flow permissions/object access.
- Manual browser sanity check if dev server is available.

## Handoff format

Использовать формат из `docs/tasks/implementation/stage-1/README.md`; include route map and list of screens not completed because of new open gaps or future pending artifacts.

## Gaps/blockers

No open WB UI implementation blocker remains for GAP-0002, GAP-0003 or GAP-0004. Formal real WB/Ozon comparison artifacts are accepted for `WB-REAL-001` / `OZ-REAL-001`; pending artifact states apply only to future new customer artifacts.

`GAP-0010`, `GAP-0011`, `GAP-0012` and `GAP-0013` are closed as `resolved/customer_decision`, but TASK-009 remains blocked until those decisions are implemented in this task. They must not be deferred to TASK-010.

Any missing or ambiguous web-panel UX/functionality rule must be routed to orchestrator for customer decision and recorded in `docs/gaps/GAP_REGISTER.md`.
