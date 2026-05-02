# API_CONNECTIONS_SPEC.md

Трассировка: `docs/source/stage-inputs/tz_stage_2.1.txt` §10-§11; `docs/tasks/implementation/stage-2/TASK-018-DESIGN-STAGE-2-2-OZON-API.md`; ADR-0017, ADR-0019, ADR-0024, ADR-0035.

## Назначение

Документ описывает рабочий контур API-подключений Stage 2.1 and Stage 2.2. В Stage 1 `ConnectionBlock` был подготовительным блоком с `is_stage1_used=false`; в Stage 2 он становится рабочим для API-сценариев marketplace.

## Scope Stage 2.1

Только WB API:

- Prices and Discounts API;
- Promotions Calendar API;
- read-only connection check;
- upload скидок через `POST /api/v2/upload/task` только в 2.1.4.

Ozon API Stage 2.2 описан ниже отдельным контуром и не смешивается с WB connection.

## ConnectionBlock usage

`ConnectionBlock` связан с `StoreAccount` и должен покрывать:

| Поле | Правило Stage 2.1 |
| --- | --- |
| `store_id` | конкретный WB store/account |
| `module` | `wb_api` или более точный системный code |
| `connection_type` | `wb_header_api_key` |
| `status` | один из статусов ниже |
| `protected_secret_ref` | единственная ссылка на token/API key/authorization secret |
| `metadata` | только безопасные настройки без secret-like значений |
| `is_stage1_used` | остаётся false для Stage 1; Stage 2.1 использует отдельный признак/контекст `is_stage2_1_used=true` или equivalent migration |

## Secret handling

API token хранится только через `protected_secret_ref`. Это единственное разрешённое место хранения token, authorization header, API key, bearer value and secret-like value.

Запрещено сохранять:

- token/api_key/password/secret-like values в `metadata`;
- authorization headers в snapshots;
- token, authorization header, API key, bearer value or secret-like value в audit records, including `safe_message`, before/after snapshots and metadata;
- token, authorization header, API key, bearer value or secret-like value в techlog `safe_message`;
- token, authorization header, API key, bearer value or secret-like value в techlog `sensitive_details_ref`;
- token, authorization header, API key, bearer value or secret-like value в UI, exports, Excel, files, reports, test output.

При сохранении connection metadata реализация должна отклонять ключи и значения, похожие на секреты: `token`, `api_key`, `authorization`, `password`, `secret`, bearer-like strings.

## Status catalog

| Status | Значение |
| --- | --- |
| `not_configured` | подключение отсутствует или не имеет secret ref |
| `configured` | secret ref сохранён, проверка ещё не пройдена |
| `active` | последняя проверка успешна, подключение можно использовать |
| `check_failed` | последняя проверка упала |
| `disabled` | подключение отключено пользователем/администратором |
| `archived` | подключение архивировано по policy |

Only `active` allows Stage 2.1 operations.

## Connection check

Проверка WB API connection:

- read-only;
- не меняет данные WB;
- использует `GET /api/v2/list/goods/filter?limit=1&offset=0`;
- выполняется с WB Prices and Discounts rate limiter;
- сохраняет `last_checked_at`, `last_check_status`, safe message;
- создаёт audit `wb_api_connection_checked`;
- создаёт techlog при ошибке;
- не сохраняет response headers/token.

Если выбранный endpoint меняется, это требует документационного изменения.

## External API policies

### Rate limits

| API category | Baseline |
| --- | --- |
| Prices and Discounts | 10 requests / 6 seconds, interval 600 ms, burst 5 |
| Promotions Calendar | 10 requests / 6 seconds, interval 600 ms, burst 5 |

Rate limiter должен быть scoped как минимум по store/account и API category. При 429 применяется backoff и retry policy; после исчерпания retries operation получает safe failure.

### Timeout and retry

Implementation task must define concrete numeric timeout/retry values before code. Baseline policy:

- finite connect/read timeout;
- retry only idempotent read calls and status polling;
- upload POST retry запрещён без idempotency/duplicate handling через WB 208/status;
- exponential or fixed backoff respecting WB interval.

### Snapshots

Safe API snapshots may include:

- endpoint code, method, query/body without secrets;
- response status;
- safe response body fields;
- pagination/batch metadata;
- request/response checksums.

Snapshots must exclude:

- `Authorization`;
- API key/token;
- raw headers with secrets;
- internal storage paths if sensitive;
- stack traces with secrets.

## Audit and techlog

Connection changes use audit actions:

- `wb_api_connection_created`;
- `wb_api_connection_updated`;
- `wb_api_connection_checked`.

Connection/API errors use techlog events:

- `wb_api_auth_failed`;
- `wb_api_rate_limited`;
- `wb_api_timeout`;
- `wb_api_response_invalid`;
- `wb_api_secret_redaction_violation`.

## Permissions

- View connection state: `wb.api.connection.view` + object access.
- Manage token/connection: `wb.api.connection.manage` + object access.
- Sensitive technical details still require `techlog.sensitive.view`; connection manage does not grant secret readback. `sensitive_details_ref` may contain only redacted diagnostics and never contains token, authorization header, API key, bearer value or secret-like values.

## Запреты

- Нельзя показывать сохранённый token после ввода.
- Нельзя считать `configured` достаточным для API operations.
- Нельзя использовать WB connection для Ozon.
- Нельзя bypass object access через global connection screens.

## Scope Stage 2.2 Ozon API

Stage 2.2 uses a separate `ConnectionBlock` for Ozon API:

- module: `ozon_api` or more exact `ozon_actions_api`;
- connection_type: `ozon_client_id_api_key`;
- marketplace/store: only Ozon store/account;
- `protected_secret_ref`: only allowed storage for `Client-Id` and `Api-Key`;
- metadata: safe settings without secret-like values;
- only `active` status allows operations.

WB token and Ozon Client-Id/Api-Key must not share a connection record or secret reference semantics.

### Ozon connection check

Connection check:

- read-only;
- does not change Ozon data;
- uses read-only `GET /v1/actions` per ADR-0035;
- stores `last_checked_at`, `last_check_status`, safe message;
- creates audit `ozon_api_connection_checked`;
- creates techlog on failure;
- does not store response headers, Client-Id, Api-Key or raw sensitive body.

ADR-0035 resolves `GAP-0022`: production connection check is allowed through `GET /v1/actions`, which was verified against test credentials as read-only and relevant for the Ozon actions API. No write endpoint may be used for connection check.

Status mapping:

| Response | Connection status/result |
| --- | --- |
| HTTP 200 with valid JSON containing `result` | `active` |
| 401/403 | `check_failed/auth_failed` |
| 429 | `check_failed/rate_limited` |
| 5xx, timeout or network failure | `check_failed/temporary` |
| invalid JSON/schema | `check_failed/invalid_response` |

### Ozon rate limits

Stage 2.2 Ozon API uses ADR-0034 conservative configurable defaults:

- read page size default: `100`;
- write batch size default: `100`;
- minimum interval between Ozon API requests default: `500 ms`;
- retry only read operations on transient failures (`429`, `5xx`, timeout/network) with bounded backoff;
- no automatic retry for write `activate/deactivate` after request was sent or response is uncertain;
- write retry only as an explicit new operation after drift-check;
- defaults configurable via settings/env later, with documented defaults used for implementation/tests.

The limiter is scoped at least by store/account and API category. 429 handling on reads uses bounded backoff and ends with safe operation failure after retries are exhausted. Row-level partial failures from write responses are persisted and reported.

### Ozon snapshots

Safe Ozon snapshots may include:

- endpoint code, method, query/body without secrets;
- response status;
- selected safe response fields;
- pagination/batch metadata;
- request/response checksums.

Snapshots must exclude:

- `Client-Id`;
- `Api-Key`;
- authorization headers;
- raw headers with secrets;
- raw sensitive API responses;
- stack traces with secrets.

### Ozon audit and techlog

Connection changes use audit actions:

- `ozon_api_connection_created`;
- `ozon_api_connection_updated`;
- `ozon_api_connection_checked`.

Connection/API errors use techlog events:

- `ozon_api_auth_failed`;
- `ozon_api_rate_limited`;
- `ozon_api_timeout`;
- `ozon_api_response_invalid`;
- `ozon_api_secret_redaction_violation`.

### Ozon permissions

- View connection state: `ozon.api.connection.view` + object access.
- Manage connection: `ozon.api.connection.manage` + object access.
- Connection manage never grants secret readback.
