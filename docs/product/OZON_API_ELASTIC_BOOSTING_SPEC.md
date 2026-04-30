# OZON_API_ELASTIC_BOOSTING_SPEC.md

Трассировка: `docs/tasks/implementation/stage-2/TASK-018-DESIGN-STAGE-2-2-OZON-API.md`; `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md`; ADR-0022..ADR-0035; GAP-0014..GAP-0022.

## Назначение

Документ задаёт исполнимую спецификацию Stage 2.2 Ozon API для акции `Эластичный бустинг`.

API-контур обязан переиспользовать Ozon Excel calculation core. Дублировать формулы в `ozon_api` запрещено. `GAP-0020` resolved by ADR-0027: review is calculation result state, not a separate Operation.
`GAP-0021` resolved by customer decision 2026-04-30 and ADR-0028: candidate/active source collisions are merged as `candidate_and_active` and treated as active for write planning.
`GAP-0014` resolved by customer decision 2026-04-30 and ADR-0029: Elastic Boosting candidates are detected by `action_type = MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT` plus title marker `Эластичный бустинг`; the user-selected/saved `action_id` is the workflow basis.
`GAP-0015` resolved by customer decision 2026-04-30 and ADR-0030: canonical Excel J (`минимально допустимая цена`) is `/v3/product/info/list` field `min_price`; absent/non-numeric `min_price` is treated as missing J and uses existing reason `missing_min_price`.
`GAP-0016` resolved by customer decision 2026-04-30 and ADR-0031: canonical Excel R (`остаток`) is the sum of `present` across all stock rows from `/v4/product/info/stocks`, including FBO + FBS; `reserved` is not subtracted; absent stock info or summed `present <= 0` uses existing reason `no_stock`.
`GAP-0017` resolved by customer decision 2026-04-30 and ADR-0032: manual upload Excel uses the current Stage 1 Ozon Excel template/format as a Stage 1-compatible manual upload file, with accepted compatibility risk.
`GAP-0018` resolved by customer decision 2026-04-30 and ADR-0033: read-side uses observed/approved fields from `/v1/actions/products` and `/v1/actions/candidates`; write-side is live Ozon actions activate/deactivate by current official schema, not mock/stub-only, and never uses `/v1/product/import/prices`.
`GAP-0022` resolved by technical decision 2026-04-30 and ADR-0035: Ozon API connection check uses read-only `GET /v1/actions` with documented status mapping; no write endpoint may be used for connection check.

## Каноническое правило расчёта

Используется порядок из `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md`:

| # | Reason | Условие | Planned action |
| --- | --- | --- | --- |
| 1 | `missing_min_price` | J отсутствует | not_upload_ready |
| 2 | `no_stock` | R отсутствует или `R <= 0` | not_upload_ready |
| 3 | `no_boost_prices` | O и P одновременно отсутствуют | not_upload_ready |
| 4 | `use_max_boost_price` | P присутствует и `P >= J` | upload_ready, L = P |
| 5 | `use_min_price` | P присутствует, O присутствует, `P < J`, `O >= J` | upload_ready, L = J |
| 6 | `below_min_price_threshold` | O присутствует и `O < J` | not_upload_ready |
| 7 | `insufficient_ozon_input_data` | остальные случаи | not_upload_ready |

API-level codes не заменяют эти business reason codes.

## API source mapping

| Canonical | Excel | API source | Статус |
| --- | --- | --- | --- |
| `min_allowed_price` | J | `/v3/product/info/list` field `min_price` | approved by customer decision 2026-04-30 / ADR-0030; absent or non-numeric `min_price` means J absent and reason `missing_min_price` |
| `price_min_elastic` | O | observed/approved elastic minimum price field from `/v1/actions/products` and `/v1/actions/candidates` | approved by customer decision 2026-04-30 / ADR-0033; exact official field name/schema must be verified at implementation time and covered by fixtures/tests |
| `price_max_elastic` | P | observed/approved elastic maximum price field from `/v1/actions/products` and `/v1/actions/candidates` | approved by customer decision 2026-04-30 / ADR-0033; exact official field name/schema must be verified at implementation time and covered by fixtures/tests |
| `stock_present` | R | `/v4/product/info/stocks` sum of `present` across all stock rows, including FBO + FBS; do not subtract `reserved` | approved by customer decision 2026-04-30 / ADR-0031; absent stock info or summed `present <= 0` means reason `no_stock` |
| `participate` | K | calculation result | output |
| `calculated_action_price` | L | calculation result; upload as Ozon action price after confirmation | output |

Action-row `stock` from `/v1/actions/*` must not be the only source of `R` unless a future approved GAP resolution changes this rule.

## Product identity and source groups

Required row identifiers:

- `action_id`;
- `product_id`;
- `offer_id`, if available from product info;
- product name/title, if available;
- `source_group`: `active`, `candidate`, `candidate_and_active`;
- `source_snapshot_id`.

Customer decision 2026-04-30: if the same `product_id` appears in both active and candidate sources for the selected action, source rows are merged as one canonical `candidate_and_active` row. For write planning the row is treated as already participating in the action (`active`):

- do not create a duplicate `add_to_action` row;
- `upload_ready` plans `update_action_price`;
- `not_upload_ready` plans `deactivate_from_action`.

The collision fact must remain visible in persisted source row details/details metadata and in result reports, not only implied by deduplication.

## Step codes

| Step code | UI button | Write to Ozon |
| --- | --- | --- |
| `ozon_api_connection_check` | connection check | no |
| `ozon_api_actions_download` | Скачать доступные акции | no |
| `ozon_api_elastic_active_products_download` | Скачать товары участвующие в акции | no |
| `ozon_api_elastic_candidate_products_download` | Скачать товары кандидаты в акцию | no |
| `ozon_api_elastic_product_data_download` | Скачать данные по полученным товарам | no |
| `ozon_api_elastic_calculation` | Обработать | no |
| `ozon_api_elastic_upload` | Загрузить в Ozon | yes |

`Принять результат` / `Не принять результат` фиксируются как immutable review state calculation result, not a separate Operation. Audit actions record the review decision.

## Workflow

### 1. Скачать доступные акции

Operation: `ozon_api_actions_download`.

Requirements:

- read-only;
- use Ozon actions endpoint after official schema confirmation;
- save safe snapshot without Client-Id, Api-Key, headers or raw secret-like values;
- display only actions available for selected Ozon store/account;
- identify Elastic Boosting candidates by `action_type = MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT` and title contains `Эластичный бустинг`;
- never use a hard-coded global Elastic Boosting `action_id` constant.

### 2. Выбрать акцию

Selection is a master-page state based on the latest actions snapshot:

- user selects exact `action_id`;
- UI shows action name, status/type, dates if available, active/candidate counters if available;
- selected/saved `action_id` is persisted as the basis for this Ozon store/account workflow context;
- all following steps use saved `action_id`;
- selection is blocked if action is not recognized as Elastic Boosting.

### 3. Скачать товары участвующие в акции

Operation: `ozon_api_elastic_active_products_download`.

Requirements:

- read-only;
- use `/v1/actions/products` with observed/approved fields per ADR-0033 and official current schema verification;
- paginate until source exhaustion;
- persist safe action-row snapshot with elastic fields;
- set `source_group=active`;
- no activate/deactivate/update calls.

### 4. Скачать товары кандидаты в акцию

Operation: `ozon_api_elastic_candidate_products_download`.

Requirements:

- read-only;
- use `/v1/actions/candidates` with observed/approved fields per ADR-0033 and official current schema verification;
- paginate until source exhaustion;
- persist safe action-row snapshot with elastic fields;
- set `source_group=candidate`;
- no activate calls.

Calculation is normally allowed only after both active and candidate downloads exist for the selected action. If one group is unavailable or empty, user must see the missing group state; any UX exception must be confirmed through GAP resolution, not guessed by implementation.

### 5. Скачать данные по полученным товарам

Operation: `ozon_api_elastic_product_data_download`.

Requirements:

- read-only;
- union product ids from active and candidates;
- fetch `/v3/product/info/list`;
- fetch `/v4/product/info/stocks`;
- build joined safe snapshot;
- map J from `/v3/product/info/list` `min_price`; if `min_price` is absent or non-numeric, J is absent and the existing Ozon reason `missing_min_price` applies;
- map R as the sum of `present` across all `/v4/product/info/stocks` stock rows, including FBO + FBS; `reserved` is not subtracted; if stock info is absent or summed `present <= 0`, R is treated as unavailable/non-positive and existing reason `no_stock` applies;
- show missing `J/O/P/R` source fields per row;
- do not use action-row `stock` as the source of R.

### 6. Обработать

Operation: `ozon_api_elastic_calculation`.

Requirements:

- use shared Ozon decision engine with the same 7 rules as Excel;
- calculate active, candidate and `candidate_and_active` rows;
- for `candidate_and_active`, preserve collision details and apply active write-planning semantics;
- create immutable calculation snapshot and detail rows;
- create result report file `ozon_api_elastic_result_report`;
- do not create `ozon_api_elastic_manual_upload_excel` in the calculation step; that file is generated only after result acceptance in step 7/9;
- produce summary groups below.

| Planned action | Rows |
| --- | --- |
| `add_to_action` | candidate + upload_ready |
| `update_action_price` | active/candidate_and_active + upload_ready |
| `deactivate_from_action` | active/candidate_and_active + not_upload_ready |
| `skip_candidate` | candidate + not_upload_ready |
| `blocked` | technical invalid/missing state not covered by business reason |

For every `deactivate_from_action` row, `deactivate_reason_code` and human-readable reason are mandatory. Without them the row is `blocked`, not silently uploaded or deactivated.

Customer decision 2026-04-30: active/candidate_and_active rows that are already in the action but are `not_upload_ready` must be removed from the action. They are not optional skips.

### 7. Принять / Не принять результат

Customer decision 2026-04-30: review is stored on the calculation result, not as a separate Operation:

- `not_reviewed`;
- `accepted`;
- `declined`;
- `stale`;
- `review_pending_deactivate_confirmation`.

`Принять результат` freezes accepted basis for upload. Upload is allowed only from accepted result state. `Не принять результат` fixes `declined` state and audit and blocks upload. If source data is downloaded again after acceptance, the accepted basis becomes stale for upload unless drift-check explicitly confirms it.

When an accepted result contains `deactivate_from_action` rows and the group deactivate confirmation has not yet been given, UI/backend must expose `review_pending_deactivate_confirmation` and must not start upload until one group deactivate confirmation is provided.

After `Принять результат`, the system generates `ozon_api_elastic_manual_upload_excel` from the immutable accepted calculation snapshot according to step 9. This generation is tied to the accepted result state, not to the earlier calculation operation.

### 8. Скачать Excel результата

File scenario: `ozon_api_elastic_result_report`.

Minimum columns:

- marketplace;
- store/cabinet;
- action_id;
- action name;
- source_group;
- source_details/collision note, if `candidate_and_active`;
- product_id;
- offer_id;
- name;
- current action_price;
- J/min_price;
- O/price_min_elastic;
- P/price_max_elastic;
- R/stock_present;
- current_boost;
- min_boost;
- max_boost;
- reason_code;
- human-readable reason;
- planned action;
- calculated action_price;
- upload_ready;
- deactivate_required;
- deactivate_reason_code;
- deactivate_reason.

This file is a control/report artifact. Source of truth for upload is immutable accepted calculation snapshot, not the downloaded Excel.

### 9. Скачать Excel для ручной загрузки

File scenario: `ozon_api_elastic_manual_upload_excel`.

Customer decision 2026-04-30 / ADR-0032: Stage 2.2 v1 uses the current Stage 1 Ozon Excel template/format as a Stage 1-compatible manual upload Excel. This is an accepted compatibility risk: if Ozon ЛК does not accept the file, that is a future compatibility issue, not a v1 blocker.

Rules:

- generated only from immutable accepted Stage 2.2 calculation snapshot;
- API upload remains the primary write path; manual Excel is secondary artifact for ручная загрузка/контроль;
- workbook metadata/title/visible note must explicitly mark the file as manual upload Excel по Stage 1-compatible template;
- Stage 1 Ozon Excel business rules, workbook template behavior and 7-rule calculation order are not changed by this file scenario;
- add/update rows are written in Stage 1-compatible columns with K=`Да` and L=`calculated_action_price`;
- deactivate rows must not be silently omitted;
- if Stage 1-compatible template cannot directly represent deactivate action, workbook/report includes separate sheet/section `Снять с акции` with product identifiers and row-level deactivate reasons;
- file must not contain secrets/raw API responses.

### 10. Загрузить в Ozon

Operation: `ozon_api_elastic_upload`.

Preconditions:

- active Ozon API connection;
- selected/saved action still exists and is Elastic Boosting by the approved `action_type` plus title marker rule;
- accepted non-stale calculation result;
- upload rights and object access;
- if add/update rows exist, explicit confirmation for add/update group;
- if `deactivate_from_action` rows exist, one explicit group confirmation for all deactivate rows;
- drift-check passed;
- at least one confirmed add/update row or confirmed deactivate row.

Drift-check must re-read action membership and critical fields:

- action still exists;
- saved `action_id` still has `action_type = MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT`;
- saved `action_id` title still contains `Эластичный бустинг`;
- product source membership still relevant;
- J/O/P/R critical values still match accepted basis by approved tolerance;
- product eligibility did not change.

Add/update rows use the current official Ozon actions activate endpoint, expected as `/v1/actions/products/activate`, with:

- `action_id`;
- product rows containing Ozon-required product identifiers;
- `action_price`.

Deactivate rows use the current official Ozon actions deactivate endpoint, expected as `/v1/actions/products/deactivate`, with:

- `action_id`;
- product identifiers required by Ozon for removing products from the action.

If exact field names in official Ozon docs differ from these project-level names, implementation follows the official schema and tests must cover the actual mapping.

### API rate, batch and retry policy

Stage 2.2 uses the conservative configurable API policy from ADR-0034:

- read page size default: `100`;
- write batch size default: `100`;
- minimum interval between Ozon API requests default: `500 ms`;
- retry is allowed only for read operations and transient failures (`429`, `5xx`, timeout/network) with bounded backoff;
- write `activate/deactivate` must not be automatically retried after request was sent or response is uncertain;
- write retry is allowed only as an explicit new operation after drift-check;
- defaults must be configurable via settings/env later, but these documented defaults are used for implementation and tests;
- row-level partial failures are persisted and reported.

Deactivate rows are sent only after the user confirms the entire `deactivate_from_action` group once. UI must show every deactivate row and row-level reason before the group confirmation. If the group is not confirmed, upload is blocked with `ozon_api_upload_blocked_deactivate_unconfirmed` / `review_pending_deactivate_confirmation`; add/update does not proceed as a normal final scenario and no destructive Ozon API call is sent.

The upload implementation must not use `/v1/product/import/prices` for this flow.

### Closed Stage 2.2 planning/status catalogs

`source_group` values:

- `active`;
- `candidate`;
- `candidate_and_active`.

`planned_action` values:

- `add_to_action`;
- `update_action_price`;
- `deactivate_from_action`;
- `skip_candidate`;
- `blocked`.

`review_state` values:

- `not_reviewed`;
- `accepted`;
- `declined`;
- `stale`;
- `review_pending_deactivate_confirmation` - accepted result contains `deactivate_from_action` rows but group confirmation is not yet given.

Deactivate group confirmation status:

- `not_required`;
- `pending`;
- `confirmed`.

Allowed `deactivate_reason_code` values are the not-upload-ready business reason codes:

- `missing_min_price`;
- `no_stock`;
- `no_boost_prices`;
- `below_min_price_threshold`;
- `insufficient_ozon_input_data`.

## API-level reason/result codes

Closed Stage 2.2 API catalog:

- `ozon_api_action_not_elastic`;
- `ozon_api_action_not_found`;
- `ozon_api_missing_elastic_fields`;
- `ozon_api_missing_product_info`;
- `ozon_api_missing_stock_info`;
- `ozon_api_product_not_eligible`;
- `ozon_api_upload_blocked_by_drift`;
- `ozon_api_upload_blocked_deactivate_unconfirmed`;
- `ozon_api_upload_ready`;
- `ozon_api_upload_rejected`;
- `ozon_api_upload_partial_rejected`;
- `ozon_api_upload_success`;
- `ozon_api_deactivate_required`;
- `ozon_api_deactivate_group_confirmed`;
- `ozon_api_auth_failed`;
- `ozon_api_rate_limited`;
- `ozon_api_timeout`;
- `ozon_api_response_invalid`;
- `ozon_api_secret_redaction_violation`.

`ozon_api_missing_stock_info` is diagnostic/API-level status only. It does not replace the business reason: absent stock info maps canonical R to existing reason `no_stock` per ADR-0031.

Adding or renaming codes requires documentation update and ADR.

## Secret and snapshot safety

Snapshots, files, audit, techlog, UI and test output must not contain:

- Client-Id;
- Api-Key;
- authorization headers;
- bearer/API key values;
- protected secret references if they can reveal secret backend details;
- raw API responses with sensitive data.

Safe snapshots may contain endpoint code, method, safe request body without secrets, response status, selected safe body fields, pagination metadata and checksum.
