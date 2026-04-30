# TASK-024-ozon-elastic-result-review.md

ID: TASK-024  
Тип задачи: реализация Stage 2.2 review  
Агент: разработчик Codex CLI  
Цель: implement accept/decline review workflow and immutable accepted basis for Ozon Elastic calculation result.

Входные документы:
- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-2/TASK-024-ozon-elastic-result-review.md`
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
- ADR-0023, ADR-0025, ADR-0027, ADR-0029, ADR-0032.
- `GAP-0020` resolved by customer decision 2026-04-30; review is calculation result state, not a separate Operation.
- `GAP-0017` resolved by customer decision 2026-04-30; manual upload Excel can be generated only from accepted calculation result.

Разрешённые файлы / области изменения:
- future `apps/discounts/ozon_api/review*`, web views/templates for review block, audit tests.

Запрещённые файлы / области изменения:
- Upload/deactivate calls.
- Calculation rule changes.
- Manual upload Excel generation before result acceptance.

Ожидаемый результат:
- Result review states `not_reviewed`, `accepted`, `declined`, `stale`, `review_pending_deactivate_confirmation`.
- `Принять результат` freezes accepted basis checksum.
- Accepted basis includes saved selected `action_id`.
- `Не принять результат` fixes declined state, writes audit and blocks upload.
- Accepted result with unconfirmed `deactivate_from_action` group is displayed as `review_pending_deactivate_confirmation` and blocks upload.
- New source downloads mark previous accepted result stale or force documented drift-check state.
- After result acceptance, generate manual upload Excel scenario `ozon_api_elastic_manual_upload_excel` from the immutable accepted calculation snapshot using ADR-0032 Stage 1-compatible template decision: add/update rows have K=`Да` and L=`calculated_action_price`; deactivate rows are visible in a separate `Снять с акции` sheet/section with reasons if not directly supported by the template.
- No `Operation` and no `Operation.step_code` is created for review; audit records the review decision.

Обязательные проверки:
- rights/object access;
- accepted result required for upload precondition;
- decline blocks upload;
- audit `ozon_api_elastic_result_reviewed`;
- stale state after source refresh.
- manual upload Excel generated only after acceptance, labeled as Stage 1-compatible manual upload artifact, and does not silently omit deactivate rows.

Получатель результата:
- orchestrator Stage 2.2 and auditor.
