# TASK-016 DESIGN HANDOFF

ID: TASK-016
Role: проектировщик Stage 2.1 UI
Status: READY_FOR_AUDIT
Date: 2026-04-26

## Scope Source

Handoff covers only WB API Stage 2.1 UI for:

- 2.1.1 `wb_api_prices_download`
- 2.1.2 `wb_api_promotions_download`
- 2.1.3 `wb_api_discount_calculation`
- 2.1.4 `wb_api_discount_upload`

Implementation must use task-scoped docs and existing backend services. Product code is not changed by this handoff.

Documentation is sufficient for implementation without UX/functional assumptions. No new blocking GAP is required.

## Current Code Surface

Existing relevant code:

- `apps/web/urls.py` has Excel routes only: `marketplaces/wb/discounts/excel/`, no WB API route yet.
- `apps/web/views.py` has Excel scenario views, operation list/card, file download and product references.
- `templates/web/marketplaces.html` links only `WB -> Скидки -> Excel` and `Ozon -> Скидки -> Excel`.
- `templates/web/operation_list.html` and `templates/web/_operation_table.html` filter/show operation `type`, not API `step_code`.
- `templates/web/operation_card.html` shows `operation_type` and check basis, not Stage 2.1 `step_code` as primary classifier.
- `apps/stores/views.py`, `apps/stores/urls.py`, `templates/stores/store_card.html`, `templates/stores/connection_form.html` already expose WB API connection status/actions with redacted secret reference.
- `apps/files/services.py` already maps WB API file scenarios to Stage 2.1 download rights.
- `apps/discounts/wb_api/*/services.py` provides callable backend services for prices, promotions, calculation and upload.

Implementation must preserve existing Excel UI and tests.

## Required Routes

Add under `apps/web/urls.py` unless implementer chooses a domain URL include with the same public route semantics:

| Route | Name | Purpose |
| --- | --- | --- |
| `marketplaces/wb/discounts/api/` | `web:wb_api` | Single WB API master screen and POST action dispatcher. |
| `marketplaces/wb/discounts/api/upload/confirm/` or same route with action | `web:wb_api_upload_confirm` if separate | Confirmation screen for 2.1.4 upload. |

The master route must support `GET ?store=<id>` and preserve selected store in redirects. POST actions may be handled by the master route if the confirmation screen remains separate and explicit.

Do not add Ozon API routes.

## Required Views And Services

Add UI controller code in `apps/web/views.py` or `apps/discounts/wb_api/views.py` if implementation keeps domain-specific controllers there. If added outside `apps/web`, include URLs from `apps/web/urls.py` or root URL config without changing public route semantics.

Required view/helper responsibilities:

- Select only WB stores visible to the user and accessible for WB API rights.
- Render connection status for selected store using existing `ConnectionBlock` fields and redacted display only.
- Query latest Stage 2.1 operations by `store`, `marketplace=wb`, `mode=api`, `module=wb_api`, `step_code`.
- Provide explicit basis selectors for successful price export operation and successful current promotions export operation.
- Provide explicit calculation basis/result selection for upload.
- Dispatch POST actions to existing backend services:
  - `apps.discounts.wb_api.prices.services.download_wb_prices(actor=request.user, store=store)`
  - `apps.discounts.wb_api.promotions.services.download_wb_current_promotions(actor=request.user, store=store)`
  - `apps.discounts.wb_api.calculation.services.calculate_wb_api_discounts(actor=request.user, store=store, price_operation=..., promotion_operation=...)`
  - `apps.discounts.wb_api.upload.services.upload_wb_api_discounts(actor=request.user, store=store, calculation_operation=..., confirmation_phrase=...)`
- Catch `PermissionDenied` and `ValidationError` like the existing Excel screens and show safe messages only.
- Redirect after each successful action to the master with `store` and resulting `operation` visible ID.

Required templates:

- `templates/web/wb_api.html` or equivalent domain template for master.
- `templates/web/wb_api_upload_confirm.html` if upload confirmation is a separate page.
- Reusable includes are allowed for step cards, operation links, file links and detail/status tables.

Required forms:

- Store selector form.
- Basis selection form for 2.1.3:
  - `price_operation_id`
  - `promotion_operation_id`
- Upload confirmation form for 2.1.4:
  - `calculation_operation_id`
  - exact confirmation phrase value: `Я понимаю, что скидки будут отправлены в WB по API.`

The UI may present the confirmation as a checkbox/button, but the POST to the upload service must supply the exact phrase expected by the backend. Upload action stays disabled or unavailable until all documented preconditions are met.

## Master Screen Content

The `WB -> Скидки -> API` master must show:

- Store selector with search-compatible existing pattern.
- Connection status block:
  - status catalog: `not_configured`, `configured`, `active`, `check_failed`, `disabled`, `archived`;
  - only `active` permits Stage 2.1 actions;
  - link to store card / connection screen when user has connection rights;
  - no token, API key, bearer value, authorization header or raw protected secret ref.
- Four step cards in this order:
  - Step 1: `Скачать цены`
  - Step 2: `Скачать текущие акции`
  - Step 3: `Рассчитать итоговый Excel`
  - Step 4: `Загрузить по API`
- For each step:
  - latest operation link and status;
  - result summary counts from `Operation.summary`;
  - warning/error panel from summary/details;
  - file links gated by file download rights;
  - operation card link gated by `wb.api.operation.view`.
- Visual text/label indicating:
  - 2.1.1, 2.1.2 and 2.1.3 do not change WB;
  - 2.1.4 is the only WB write step and requires confirmation plus drift check;
  - result Excel from 2.1.3 is available for manual WB cabinet upload.

## Workflow States And Buttons

### Shared State Gates

For all four steps:

- No selected store: show no action buttons.
- No object access: store and all related operations/files/products/promotions/connection must be hidden.
- No `wb.api.operation.view`: master route must not expose operations for that store.
- Connection not `active`: read/download/calculate/upload actions are blocked with status text.
- Any service exception message shown in UI must be safe; never render secrets.

### Step 1: Prices

Button:

- `Скачать цены` posts action `download_prices`.

Enabled only when:

- selected store is WB;
- object access exists;
- connection is `active`;
- user has `wb.api.prices.download`.

Display:

- fetched timestamp;
- goods count / Excel rows count;
- valid count;
- size conflict count;
- checksum if present;
- price Excel download link only with `wb.api.prices.file.download`;
- operation link.

States/messages:

- no active connection;
- API auth/rate/timeout error;
- size conflicts found;
- file expired/unavailable.

### Step 2: Current Promotions

Button:

- `Скачать текущие акции` posts action `download_promotions`.

Enabled only when:

- selected store is WB;
- object access exists;
- connection is `active`;
- user has `wb.api.promotions.download`.

Display:

- `current_filter_timestamp`;
- current/regular/auto counts;
- products count;
- action without nomenclatures count;
- separate promo Excel file links per regular current promotion only with `wb.api.promotions.file.download`;
- operation link.

States/messages:

- no current promotions;
- auto promotion without nomenclatures;
- invalid promo rows;
- API failures.

Do not offer future/all/nearest promotions as an alternative.

### Step 3: Calculation

Button:

- `Рассчитать итоговый Excel` posts action `calculate`.

Enabled only when:

- selected store is WB;
- object access exists;
- user has `wb.api.discounts.calculate`;
- successful price export basis exists;
- successful current promotions export basis exists.

Display:

- selected price export operation/file;
- selected promotion export operation/files;
- applied WB parameters snapshot;
- calculation logic version;
- row/error/warning counts;
- result Excel and detail report download links only with `wb.api.discounts.result.download`;
- `upload_blocked` state when calculation has errors.

States/messages:

- no price export;
- no promo export;
- source mismatch;
- outdated basis;
- errors block upload.

Calculation does not change WB.

### Step 4: API Upload

Button flow:

- `Открыть подтверждение` opens confirmation screen for selected successful calculation.
- Confirmation screen posts `confirm_upload` with exact phrase.
- No direct upload POST from the master without confirmation.

Enabled only when:

- selected store is WB;
- object access exists;
- user has both `wb.api.discounts.upload` and `wb.api.discounts.upload.confirm`;
- connection is `active`;
- selected calculation operation has `step_code=wb_api_discount_calculation`;
- calculation status is successful and has no errors;
- upload-ready rows exist;
- result file exists.

Confirmation screen must show:

- store;
- calculation operation;
- result file;
- calculation date;
- count of products to send;
- count of excluded products;
- warning that discounts will be sent to WB by API;
- exact phrase: `Я понимаю, что скидки будут отправлены в WB по API.`

Display after upload:

- upload operation link;
- drift check status;
- batch uploadIDs;
- success/error counts;
- partial errors as `completed_with_warnings`;
- quarantine rows separately;
- upload report link only with `wb.api.discounts.result.download`.

States/messages:

- upload blocked by drift;
- size conflict;
- invalid rows;
- status polling pending/failed;
- partial errors;
- quarantine errors;
- WB canceled upload.

Do not show success until WB status polling resolves final result.

## Permissions And Gates

All Stage 2.1 WB API rights require object access to the selected WB store.

Master route:

- Requires authenticated user.
- Requires `wb.api.operation.view` for the selected store to see Stage 2.1 operations.
- Store selector must include only WB stores visible through object access and relevant rights.

Action rights:

| UI Action | Required permission |
| --- | --- |
| View connection state | `wb.api.connection.view` |
| Open/manage connection | `wb.api.connection.manage` |
| Start prices download | `wb.api.prices.download` |
| Download price Excel | `wb.api.prices.file.download` |
| Start current promotions download | `wb.api.promotions.download` |
| Download promo Excel files | `wb.api.promotions.file.download` |
| Start calculation | `wb.api.discounts.calculate` |
| Download result Excel/detail/upload report | `wb.api.discounts.result.download` |
| Open upload confirmation | `wb.api.discounts.upload` and `wb.api.discounts.upload.confirm` |
| Execute upload | `wb.api.discounts.upload` and `wb.api.discounts.upload.confirm` |
| View WB API operation card/list row | `wb.api.operation.view` |

Secret rules:

- Do not render `protected_secret_ref`.
- Do not render token/API key/authorization/bearer values.
- Do not print secret-like values in tests, screenshots, logs or failure output.
- Connection blocks may show only `[ref-set]` / `[empty]`, safe status and safe metadata display.

## Operation List Changes

Update operation list query/classification so Stage 2.1 API operations are visible to users with `wb.api.operation.view` and object access.

Required behavior:

- Stage 1 Excel check/process operations remain classified by `Operation.operation_type`.
- Stage 2.1 WB API operations are classified by `Operation.step_code`.
- API operations must not be shown as `check` or `process`.
- Filters must support:
  - marketplace;
  - store;
  - mode;
  - `type` for check/process;
  - `step_code` for WB API Stage 2.1;
  - status;
  - visible_id search.
- Table must show classifier as:
  - `check` / `process` for Excel operations;
  - documented step code or user-facing step label for WB API operations.
- Object access must hide inaccessible stores and operations.

Current code to adjust:

- `_visible_operations_queryset()` in `apps/web/views.py`
- `_require_operation_view()` in `apps/web/views.py`
- `operation_list()` in `apps/web/views.py`
- `templates/web/operation_list.html`
- `templates/web/_operation_table.html`

## Operation Card Changes

Update operation card so Stage 2.1 API operation cards use `step_code` as the primary classifier.

Required behavior:

- For API operations show:
  - marketplace/module/mode;
  - `step_code`;
  - status;
  - store;
  - initiator;
  - start/finish;
  - logic version;
  - summary;
  - input/output file links;
  - parameter snapshots for calculation;
  - detail rows;
  - audit/techlog links.
- Do not show warning confirmation action for API operations.
- Do not force API operations into check/process wording.
- For upload operation, show batch/uploadID summary and quarantine/drift details from summary/detail rows.
- Existing check/process card behavior remains unchanged.

Current code to adjust:

- `operation_card()` in `apps/web/views.py`
- `templates/web/operation_card.html`
- `templates/web/_inline_operation_result.html` if API result inline display is reused on the master.

## Marketplace And Store Entry Points

Update `templates/web/marketplaces.html` and related context so `WB -> Скидки -> API` is a separate entry point next to `WB -> Скидки -> Excel`.

Required behavior:

- Excel remains visible and available as штатный/резервный route.
- WB API entry is shown only when user has object-accessible WB stores and Stage 2.1 view/action rights.
- Ozon API is not shown.

Store card:

- Keep existing connection block entry points.
- Add optional link from WB store card to WB API master for that store when user has `wb.api.operation.view` or any WB API action right for the store.
- Keep secret display redacted.

## Testing Checklist For Tester

Tester should cover at least:

- Route smoke for `web:wb_api` and optional `web:wb_api_upload_confirm`.
- Master hidden/forbidden for user without object access.
- Master does not show stores outside object access.
- User with `wb.api.operation.view` sees only accessible Stage 2.1 operations.
- User without `wb.api.prices.download` cannot start prices download.
- User without `wb.api.promotions.download` cannot start promotions download.
- User without `wb.api.discounts.calculate` cannot calculate.
- User without both upload rights cannot open/execute upload confirmation.
- Connection `configured`, `check_failed`, `disabled`, `archived`, `not_configured` blocks actions.
- Connection `active` allows actions when rights and basis are present.
- Step 1 displays size conflict and blocks upload readiness where present.
- Step 2 displays current filter timestamp and auto-promotion no-nomenclatures limitation.
- Step 3 displays selected basis and parameter snapshot; calculation errors block upload.
- Step 4 confirmation is required and exact phrase is posted.
- Drift rows block upload and are visible.
- Partial errors map/display as `completed_with_warnings`.
- Quarantine rows display separately.
- Operation list filters by `step_code` for API operations and by `type` for check/process operations.
- Operation card shows API `step_code`, not check/process type.
- File links are gated by Stage 2.1 file permissions.
- No token/header/API key/bearer/secret-like value appears in rendered HTML, screenshots, test output, audit/techlog snippets or file links.
- Existing Stage 1 WB Excel route and tests remain available.
- Ozon API route/UI is absent.

## Explicit Non-Goals

- Do not implement backend business logic for prices/promotions/calculation/upload beyond invoking existing services.
- Do not change Stage 1 WB/Ozon Excel semantics, routes, permissions or calculation behavior.
- Do not add Ozon API Stage 2.2 UI.
- Do not add new reason/result codes.
- Do not create new file scenarios or zip/package promo exports.
- Do not expose or read real WB token files or `test_files/secrets`.
- Do not render token/API key/authorization/bearer/protected secret values.
- Do not auto-release quarantine goods.
- Do not use size upload endpoints or WB Club discount endpoints.
- Do not add fallback upload payload with `price`.
- Do not treat HTTP 200 from upload POST as final success.
- Do not add API mode as replacement for Excel mode.

## Read Documents And Files

Documents:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/tasks/implementation/stage-2/TASK-016-wb-api-ui-stage-2-1.md`
- `docs/tasks/implementation/stage-2/IMPLEMENTATION_TASKS.md`
- `docs/roles/READING_PACKAGES.md` section `Frontend/UI Агент WB API Stage 2.1`
- `docs/product/UI_SPEC.md` relevant WB API, operations list/card sections
- `docs/product/WB_DISCOUNTS_API_SPEC.md` relevant calculation/upload/confirmation/drift/status/quarantine sections
- `docs/product/WB_API_PRICE_EXPORT_SPEC.md`
- `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md` relevant Stage 2.1 operation classifier section
- `docs/product/PERMISSIONS_MATRIX.md` relevant WB API Stage 2.1 rights
- `docs/architecture/API_CONNECTIONS_SPEC.md` relevant active connection/secret sections
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md` relevant UI/security checks
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md` relevant Stage 2.1 checks
- `docs/gaps/GAP_REGISTER.md` current open gaps and Stage 2.1 evaluation
- `docs/adr/ADR_LOG.md` ADR-0016..ADR-0020

Code/files inspected:

- `apps/web/urls.py`
- `apps/web/views.py`
- `apps/web/tests.py`
- `templates/web/marketplaces.html`
- `templates/web/operation_list.html`
- `templates/web/_operation_table.html`
- `templates/web/operation_card.html`
- `templates/web/_inline_operation_result.html`
- `apps/discounts/wb_api/prices/services.py`
- `apps/discounts/wb_api/promotions/services.py`
- `apps/discounts/wb_api/calculation/services.py`
- `apps/discounts/wb_api/upload/services.py`
- `apps/operations/models.py`
- `apps/operations/services.py`
- `apps/stores/urls.py`
- `apps/stores/views.py`
- `apps/stores/forms.py`
- `apps/stores/services.py`
- `apps/stores/tests.py`
- `templates/stores/store_card.html`
- `templates/stores/connection_form.html`
- `apps/stores/templates/stores/store_card.html`
- `apps/stores/templates/stores/connection_form.html`
- `apps/files/models.py`
- `apps/files/services.py`
- `apps/identity_access/seeds.py`
- `config/urls.py`
