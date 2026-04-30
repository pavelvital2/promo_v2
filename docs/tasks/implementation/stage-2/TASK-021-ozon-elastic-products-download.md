# TASK-021-ozon-elastic-products-download.md

ID: TASK-021  
Тип задачи: реализация Stage 2.2 products  
Агент: разработчик Codex CLI  
Цель: реализовать separate read-only downloads for active/participating products and candidates of selected Elastic Boosting action.

Входные документы:
- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-2/TASK-021-ozon-elastic-products-download.md`
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
- ADR-0023, ADR-0025, ADR-0028, ADR-0029, ADR-0033, ADR-0034.
- `GAP-0018` resolved 2026-04-30: use observed/approved fields from `/v1/actions/products` and `/v1/actions/candidates`, verify exact official field names at implementation time and cover mappings with contract tests/sanitized fixtures.
- `GAP-0021` resolved 2026-04-30: active/candidate collision rows are merged as `candidate_and_active`, with collision fact persisted in source details for reports/downstream planning.
- `GAP-0019` resolved 2026-04-30 by technical/orchestrator decision: read page size default `100`, minimum interval `500 ms`, read-only transient retry with bounded backoff.

Разрешённые файлы / области изменения:
- future `apps/discounts/ozon_api/products*`, snapshot persistence, operation detail rows, tests and UI step states for buttons 3-4.

Запрещённые файлы / области изменения:
- Product info/stocks join, calculation, review, upload/deactivate.
- Any Ozon write endpoint.
- Real secrets/raw sensitive responses.

Ожидаемый результат:
- `ozon_api_elastic_active_products_download` and `ozon_api_elastic_candidate_products_download` operations.
- Both operations use saved selected `action_id` from TASK-020 store/account context; no global Elastic Boosting `action_id` constant.
- Pagination, empty groups, missing elastic fields and duplicate product source handling covered.
- Read pagination/rate/retry uses ADR-0034 defaults and is configurable via settings/env later.
- Read-side field normalizers follow the official current Ozon schema when field names differ from project examples.
- `source_group` persisted as `active`, `candidate`, or `candidate_and_active`; `candidate_and_active` keeps visible collision details and no duplicate downstream basis.

Обязательные проверки:
- active pagination;
- candidates pagination;
- page size default `100`, minimum interval `500 ms`, and read retry only for `429`, `5xx`, timeout/network with bounded backoff;
- empty active/candidate groups;
- product in both sources has no duplicate downstream basis;
- missing elastic fields safe error/code;
- read-only endpoints only.
- saved `action_id` from selected action context is used for both active and candidate downloads.

Получатель результата:
- orchestrator Stage 2.2 and auditor.
