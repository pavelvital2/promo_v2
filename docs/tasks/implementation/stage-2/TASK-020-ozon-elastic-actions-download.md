# TASK-020-ozon-elastic-actions-download.md

ID: TASK-020  
Тип задачи: реализация Stage 2.2 actions  
Агент: разработчик Codex CLI  
Цель: реализовать read-only скачивание Ozon actions and selection of one approved Elastic Boosting action.

Источник истины:
- `itogovoe_tz_platforma_marketplace_codex.txt`, only sections explicitly issued by orchestrator.

Входные документы:
- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-2/TASK-020-ozon-elastic-actions-download.md`
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
- ADR-0023, ADR-0025, ADR-0029, ADR-0034.
- `GAP-0014` resolved by customer decision 2026-04-30: identify candidates by `action_type = MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT` plus title marker `Эластичный бустинг`; user-selected/saved `action_id` is the workflow basis.
- `GAP-0019` resolved by technical/orchestrator decision 2026-04-30: read page size default `100`, minimum interval `500 ms`, read-only transient retry with bounded backoff.

Разрешённые файлы / области изменения:
- future `apps/discounts/ozon_api/actions*`, safe client/snapshot helpers, operations/files/audit tests, UI selector if needed for this slice.

Запрещённые файлы / области изменения:
- Ozon write endpoints.
- Product downloads/calculation/upload.
- WB Stage 2.1 and Stage 1 Excel logic.
- Real secrets/raw sensitive responses.

Ожидаемый результат:
- `ozon_api_actions_download` operation downloads actions with mocks/sanitized fixtures.
- Read pagination/rate policy follows ADR-0034 defaults and remains configurable via settings/env later.
- UI/state lets user select only approved Elastic Boosting action.
- Selected `action_id` is persisted in selected store/account context and reused by downstream steps; no hard-coded global `action_id`.
- Safe snapshots and action counters are persisted.

Обязательные проверки:
- Elastic/non-Elastic/ambiguous actions by approved action type/title marker;
- saved `action_id` basis and no hard-coded global constant;
- no active connection/no rights/object access;
- safe snapshot redaction;
- page size default `100`, minimum interval `500 ms`, and read retry only for `429`, `5xx`, timeout/network with bounded backoff;
- operation has `mode=api`, `marketplace=ozon`, `step_code=ozon_api_actions_download`, no `type=check/process`.

Получатель результата:
- orchestrator Stage 2.2 and auditor.
