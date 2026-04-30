# TASK-025-ozon-elastic-upload-deactivate.md

ID: TASK-025  
Тип задачи: реализация Stage 2.2 upload  
Агент: разработчик Codex CLI  
Цель: implement Ozon Elastic add/update/deactivate upload with confirmations, drift-check, row-level results and duplicate protection. Active/candidate_and_active + not_upload_ready rows are mandatory `deactivate_from_action` per customer decision 2026-04-30.

Входные документы:
- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-2/TASK-025-ozon-elastic-upload-deactivate.md`
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

Связанные GAP/ADR:
- ADR-0023, ADR-0025, ADR-0026, ADR-0028, ADR-0029, ADR-0030, ADR-0031, ADR-0033, ADR-0034.
- `GAP-0018` resolved 2026-04-30: live write-side `activate/deactivate` uses current official Ozon actions schema and is not mock/stub-only.
- `GAP-0019` resolved 2026-04-30 by technical/orchestrator decision: write batch size default `100`, minimum interval `500 ms`, read-only transient retry with bounded backoff, no automatic retry for sent/uncertain `activate/deactivate`, explicit new write operation only after drift-check, row-level partial failures persisted/reported.

Разрешённые файлы / области изменения:
- future `apps/discounts/ozon_api/upload*`, drift check, batching, upload reports, audit/techlog tests, UI confirmation block.

Запрещённые файлы / области изменения:
- `/v1/product/import/prices`.
- Any upload without accepted result, explicit confirmation and drift-check.
- Deactivate without one group confirmation for all `deactivate_from_action` rows and mandatory row-level reasons.
- Upload add/update proceeding while mandatory deactivate rows remain unconfirmed.
- Real secrets/raw sensitive responses.

Ожидаемый результат:
- `ozon_api_elastic_upload` operation.
- Add/update uses the Ozon actions activate endpoint with `action_id`, Ozon-required product identifiers and `action_price`; exact field names follow current official Ozon docs and tests/fixtures cover the mapping.
- Deactivate uses the Ozon actions deactivate endpoint with `action_id` and Ozon-required product identifiers; exact field names follow current official Ozon docs and tests/fixtures cover the mapping.
- Batch/rate/retry follows ADR-0034: write batches <= `100`, minimum Ozon request interval `500 ms`, defaults configurable via settings/env later.
- Sent or response-uncertain activate/deactivate requests are not automatically retried; any retry is a separate explicit new operation after drift-check.
- Drift-check verifies saved `action_id` still exists and still has `action_type = MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT` plus title marker `Эластичный бустинг`.
- Drift-check compares J against `/v3/product/info/list` `min_price` per ADR-0030; absent/non-numeric current `min_price` invalidates J and blocks/updates status according to drift handling.
- Drift-check compares R against `/v4/product/info/stocks` summed `present` per ADR-0031, including FBO + FBS and without subtracting `reserved`; absent current stock info or summed `present <= 0` invalidates R and blocks/updates status according to drift handling.
- Partial success/rejection persists row-level details and safe report.
- `candidate_and_active` rows never create duplicate add rows: upload_ready rows update action price, not_upload_ready rows deactivate from action.

Обязательные проверки:
- confirmation gates;
- deactivate group confirmation absent -> upload not started and result remains `review_pending_deactivate_confirmation`;
- deactivate group confirmation is one group action and UI/service receives the full row list with row-level reasons;
- drift blocks upload;
- action identity drift blocks upload;
- duplicate protection;
- candidate_and_active duplicate-source protection and visible collision details in upload/report basis;
- partial success/rejection;
- write batch size <= `100`, minimum interval `500 ms`, no automatic retry after sent/uncertain write, explicit new operation after drift-check for retry;
- activate/deactivate request and response mapping contract tests;
- no `/v1/product/import/prices`;
- secret redaction.

Получатель результата:
- orchestrator Stage 2.2 and auditor.
