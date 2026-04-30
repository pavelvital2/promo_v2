# TASK-026-ozon-elastic-ui-acceptance-release.md

ID: TASK-026  
Тип задачи: реализация Stage 2.2 UI/acceptance/release readiness  
Агент: frontend/UI + тестировщик Codex CLI, then auditor handoff  
Цель: implement/verify Stage 2.2 master UI, execute acceptance, collect audit/release readiness evidence.

Входные документы:
- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-2/TASK-026-ozon-elastic-ui-acceptance-release.md`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`
- `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`
- `docs/product/OZON_API_ELASTIC_UI_SPEC.md`
- `docs/product/UI_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/testing/STAGE_2_2_OZON_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_2_OZON_ACCEPTANCE_CHECKLISTS.md`
- `docs/traceability/STAGE_2_2_OZON_TRACEABILITY_MATRIX.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Связанные GAP/ADR:
- ADR-0022..ADR-0035.
- No blocking Stage 2.2 GAP may remain for the release slice being accepted.

Разрешённые файлы / области изменения:
- web views/templates/navigation for Stage 2.2, tests, release/test reports in `docs/testing/` or `docs/reports/` if requested by orchestrator.

Запрещённые файлы / области изменения:
- Changing business calculation or upload behavior to satisfy UI tests.
- WB Stage 2.1 behavior.
- Real secrets/raw sensitive API responses.

Ожидаемый результат:
- Master page follows exact hierarchy and 10-button order.
- Action selector shows only approved Elastic Boosting candidates by ADR-0029 and saves selected `action_id` as downstream basis.
- Button enabled/disabled/processing states are implemented.
- Result review table, counters, files and confirmation panels match specs.
- Manual upload Excel file link/metadata identifies the file as Stage 1-compatible manual upload artifact, secondary to API upload.
- Deactivate confirmation UI shows all `deactivate_from_action` rows with row-level reasons and requests one group confirmation.
- Upload UI/acceptance evidence covers live activate/deactivate contract from ADR-0033 and confirms the flow is not mock/stub-only for release readiness.
- API client/upload acceptance evidence covers ADR-0034 defaults: read page size `100`, write batch size `100`, minimum interval `500 ms`, read-only transient retry with bounded backoff, no automatic retry for sent/uncertain writes.
- Acceptance checklist executed and release/audit handoff prepared.

## Sequential ownership gates

TASK-026 is one tracking task with three sequential gates. Work may not skip a gate or merge ownership:

1. UI implementation gate: frontend/UI agent implements navigation/master page, operation cards, button states, review table, files and confirmation panels. Output is a UI handoff with changed files and focused UI checks. No acceptance sign-off is issued by the UI agent.
2. Acceptance/testing gate: tester executes `STAGE_2_2_OZON_TEST_PROTOCOL.md` and `STAGE_2_2_OZON_ACCEPTANCE_CHECKLISTS.md` for the implemented release slice, including regressions. Output is a test report in `docs/testing/`.
3. Audit/release handoff gate: auditor/release owner verifies documentation/test evidence, open GAP status and release readiness. Output is audit/release handoff in `docs/audit/` or `docs/reports/`.

If a gate fails, ownership returns to the responsible preceding gate; later gates do not patch product behavior directly.

Обязательные проверки:
- UI permissions/object access;
- button order/gating;
- review and deactivate group confirmation UX;
- manual upload Excel file link, label and `Снять с акции` visibility when deactivate rows exist;
- operation card step_code display;
- Stage 1 Ozon Excel regression;
- Stage 2.1 WB API regression;
- full impacted suite.

Получатель результата:
- orchestrator Stage 2.2, tester, auditor and release owner.
