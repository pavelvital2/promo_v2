# API_CONNECTIONS_SPEC.md

Трассировка: `tz_stage_2.1.txt` §10-§11; ADR-0017, ADR-0019.

## Назначение

Документ описывает рабочий контур API-подключений Stage 2.1. В Stage 1 `ConnectionBlock` был подготовительным блоком с `is_stage1_used=false`; в Stage 2.1 он становится рабочим для WB API.

## Scope Stage 2.1

Только WB API:

- Prices and Discounts API;
- Promotions Calendar API;
- read-only connection check;
- upload скидок через `POST /api/v2/upload/task` только в 2.1.4.

Ozon API Stage 2.2 не входит.

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
