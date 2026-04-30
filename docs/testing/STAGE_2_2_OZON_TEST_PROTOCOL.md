# STAGE_2_2_OZON_TEST_PROTOCOL.md

Трассировка: `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`; `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`.

## Назначение

Протокол задаёт обязательные проверки Stage 2.2 Ozon API. Реальные Ozon secrets, raw sensitive API responses and `test_files/secrets` не читать, не печатать и не сохранять. По умолчанию использовать mocks/stubs and sanitized fixtures.

## Test layers

| Layer | Проверки |
| --- | --- |
| Unit | Ozon Excel decision engine reuse, API row normalizers, J/O/P/R mapping, source-group merge, reason/result codes |
| Integration | Ozon API client pagination/rate/retry with mocks, safe snapshots, product info/stocks join, immutable calculation snapshot |
| UI | Ozon Elastic master page, button order/gates, rights/object access, review, confirmations, stale/drift states |
| Acceptance | end-to-end actions -> active/candidates -> product data -> calculation -> review -> report -> confirmed upload with mocks |
| Security | no Client-Id/Api-Key/header/bearer/secret-like values in metadata, snapshots, audit, techlog, UI, files, reports or test output |

## Required mock scenarios

### Connection

- configured connection cannot run operations until check makes it `active`;
- production connection check uses read-only `GET /v1/actions`;
- no write endpoint is used for connection check;
- HTTP 200 with valid JSON containing `result` -> connection `active`;
- 401/403 auth failure -> `check_failed/auth_failed` and safe techlog;
- 429 rate limit -> `check_failed/rate_limited` after bounded read retry policy is exhausted;
- 5xx/timeout/network -> `check_failed/temporary`;
- invalid JSON/schema -> `check_failed/invalid_response`;
- saved secret cannot be read back.

### API client policy

- read page size default is `100` for Ozon read clients;
- write batch size default is `100` for activate/deactivate;
- minimum interval between Ozon API requests default is `500 ms`;
- only read operations retry transient failures (`429`, `5xx`, timeout/network) with bounded backoff;
- sent or response-uncertain write `activate/deactivate` is not automatically retried;
- write retry is modeled as explicit new operation after drift-check;
- defaults are configurable via settings/env later, but tests use the documented defaults.

### Actions

- `/v1/actions` returns multiple action types and only approved Elastic Boosting action is selectable;
- approved Elastic Boosting candidates require `action_type = MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT` and title marker `Эластичный бустинг`;
- selected `action_id` is saved per selected Ozon store/account and used by downstream steps;
- no hard-coded global Elastic Boosting `action_id` is used;
- no Elastic Boosting action -> workflow blocked with safe message;
- multiple Elastic Boosting candidates require explicit user selection;
- action disappears before upload -> drift block;
- saved action changes action type or loses title marker before upload -> drift block.

### Active/candidates

- active products paginate;
- candidates paginate;
- active/candidate normalizers use observed/approved fields from `/v1/actions/products` and `/v1/actions/candidates`, with exact field names verified against current official Ozon schema;
- empty active group;
- empty candidate group;
- product appears in both groups -> merged `candidate_and_active`, collision visible in details/report basis, no duplicate result row;
- missing elastic fields -> `ozon_api_missing_elastic_fields`, calculation blocked for affected row or operation per spec.

### Product info/stocks join

- product info provides `offer_id`, name and `min_price`;
- absent/non-numeric `min_price` leaves canonical J absent and produces existing Ozon reason `missing_min_price`;
- missing product info -> `ozon_api_missing_product_info`;
- stocks provide multiple stock rows;
- `R` aggregation follows ADR-0031: sum `present` across all `/v4/product/info/stocks` rows, including FBO + FBS, and do not subtract `reserved`;
- action-row stock differs from stocks endpoint -> stocks endpoint is used per approved rule;
- missing stock info or summed `present <= 0` -> existing Ozon reason `no_stock`; missing stock info may also expose API-level status `ozon_api_missing_stock_info` for diagnostics.

### Calculation

- API canonical fixture produces same decisions as equivalent Ozon Excel fixture;
- all 7 Ozon Excel rules covered;
- `use_max_boost_price` and `use_min_price` produce upload_ready rows;
- not_upload_ready active rows become `deactivate_from_action` with mandatory reason;
- upload_ready `candidate_and_active` rows become `update_action_price`, not duplicate add;
- not_upload_ready `candidate_and_active` rows become `deactivate_from_action` with mandatory reason;
- not_upload_ready candidates become `skip_candidate`;
- calculation result is immutable and review state starts as `not_reviewed`.

### Review and files

- upload blocked before `Принять результат`;
- `Не принять результат` blocks upload and audits the decision;
- repeated source download makes accepted result stale or forces drift-check;
- result report contains required columns and no sensitive values;
- manual upload Excel is generated only after result acceptance from accepted snapshot;
- manual upload Excel is labeled as Stage 1-compatible manual upload artifact;
- manual upload Excel add/update rows have K=`Да` and L=`calculated_action_price`;
- deactivate rows are present in `Снять с акции` sheet/section with reasons if the Stage 1-compatible template cannot directly encode deactivate.

### Upload/deactivate

- upload requires active connection, object access, rights, accepted result and confirmations;
- add/update confirmation absent -> upload not started;
- deactivate group confirmation absent -> upload not started and accepted result remains `review_pending_deactivate_confirmation`;
- deactivate confirmation is one group action for all `deactivate_from_action` rows;
- deactivate preview shows all rows and row-level reasons before confirmation;
- add/update request contract uses the Ozon actions activate endpoint with `action_id`, Ozon-required product identifiers and `action_price`;
- deactivate request contract uses the Ozon actions deactivate endpoint with `action_id` and Ozon-required product identifiers;
- activate/deactivate batches contain at most `100` rows and observe the `500 ms` minimum request interval;
- if official Ozon field names differ from project-level examples, tests cover the official field names actually used by implementation;
- release readiness must not replace live activate/deactivate with mock/stub-only behavior;
- drift in action membership or J/O/P/R blocks upload;
- partial success preserves row-level details;
- rejected rows store safe Ozon reason without raw sensitive payload;
- repeated send is protected from accidental duplicate; sent/uncertain writes are not automatically retried and require explicit new operation after drift-check;
- `/v1/product/import/prices` is never called.

## Required assertions

- All Stage 2.2 operations have `mode=api`, `marketplace=ozon` and documented `step_code`.
- Stage 2.2 API operations do not store `Operation.type=check/process`.
- Read-only steps never call Ozon write endpoints.
- Upload never starts without accepted result, explicit add/update confirmation, required deactivate group confirmation and drift-check.
- Deactivate never starts without one group confirmation for all `deactivate_from_action` rows.
- Deactivate rows always have row-level reason.
- Stage 1 Ozon Excel tests remain unchanged and passing.
- Stage 2.1 WB API regression remains passing.
- Safe snapshots contain no Client-Id, Api-Key, authorization header, bearer/API key or secret-like values.
- Audit/techlog use documented codes and object access.

## Acceptance evidence

Each TASK-019..TASK-026 report must include:

- executed test commands;
- mock/sanitized fixtures used;
- changed files;
- Stage 2.2 checklist items covered;
- current GAP status;
- confirmation that no secret-like values or raw sensitive API responses were printed or persisted.
