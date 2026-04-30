# TASK-019-ozon-api-connection.md

ID: TASK-019  
Тип задачи: реализация Stage 2.2 prerequisite  
Агент: разработчик Codex CLI  
Цель: реализовать Ozon API connection contour with protected Client-Id/Api-Key, production read-only `GET /v1/actions` connection check, safe client baseline and audit/techlog.

Источник истины:
- `itogovoe_tz_platforma_marketplace_codex.txt`, only sections explicitly issued by orchestrator.

Входные документы:
- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-2/TASK-019-ozon-api-connection.md`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`
- `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`
- `docs/product/OZON_API_ELASTIC_UI_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/testing/STAGE_2_2_OZON_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_2_OZON_ACCEPTANCE_CHECKLISTS.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Разделы ТЗ для чтения:
- Только разделы, выданные оркестратором для Stage 2.2 connection.

Связанные GAP/ADR:
- ADR-0024.
- ADR-0034 resolves `GAP-0019` with conservative configurable API defaults: read page size `100`, write batch size `100`, minimum interval `500 ms`, read-only transient retry with bounded backoff, and no automatic retry for sent/uncertain writes.
- ADR-0035 resolves `GAP-0022`: Ozon production connection check uses read-only `GET /v1/actions`; no write endpoint may be used for connection check.

Разрешённые файлы / области изменения:
- `apps/stores/`, `apps/identity_access/`, `apps/audit/`, `apps/techlog/`, future `apps/discounts/ozon_api/`, tests in same areas.

Запрещённые файлы / области изменения:
- Stage 1 Ozon Excel calculation behavior.
- Stage 2.1 WB API behavior.
- Real secrets, raw sensitive API responses, `test_files/secrets`.
- Ozon write endpoints.

Ожидаемый результат:
- Ozon API connection can be configured/disabled by rights.
- Production connection check calls read-only `GET /v1/actions`.
- Check result mapping is implemented: HTTP 200 with valid JSON containing `result` -> `active`; 401/403 -> `check_failed/auth_failed`; 429 -> `check_failed/rate_limited`; 5xx/timeout/network -> `check_failed/temporary`; invalid JSON/schema -> `check_failed/invalid_response`.
- Client-Id and Api-Key stored only via `protected_secret_ref`.
- No secret-like values in metadata/snapshots/audit/techlog/UI/files/reports/tests.
- Statuses `not_configured/configured/active/check_failed/disabled/archived` supported.

Обязательные проверки:
- secret redaction tests;
- permission/object access tests;
- connection check tests with mocks/sanitized fixtures for success/auth/rate/timeout/network/5xx/schema failure and verification that only `GET /v1/actions` is used;
- operation classifier test for `ozon_api_connection_check`.

Получатель результата:
- orchestrator Stage 2.2 and auditor.
