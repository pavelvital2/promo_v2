# TASK-017-wb-api-acceptance-and-release.md

ID: TASK-017
Тип задачи: acceptance/release Stage 2.1
Агент: тестировщик/релизный агент Codex CLI
Цель: выполнить Stage 2.1 acceptance checks, собрать evidence и подготовить release readiness без изменения бизнес-логики.

Источник истины:
- `tz_stage_2.1.txt`, без полного перечитывания вне указанных разделов.

Входные документы:
- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/orchestration/TASK_TEMPLATES.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-2/TASK-017-wb-api-acceptance-and-release.md`
- `docs/tasks/implementation/stage-2/IMPLEMENTATION_TASKS.md`
- `docs/tasks/implementation/stage-2/TASK-011-wb-api-connections.md`
- `docs/tasks/implementation/stage-2/TASK-012-wb-api-prices-download.md`
- `docs/tasks/implementation/stage-2/TASK-013-wb-api-current-promotions-download.md`
- `docs/tasks/implementation/stage-2/TASK-014-wb-api-discount-calculation-excel-output.md`
- `docs/tasks/implementation/stage-2/TASK-015-wb-api-discount-upload.md`
- `docs/tasks/implementation/stage-2/TASK-016-wb-api-ui-stage-2-1.md`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_1_WB_ACCEPTANCE_TESTS.md`
- `docs/product/WB_DISCOUNTS_API_SPEC.md`
- `docs/product/WB_API_PRICE_EXPORT_SPEC.md`
- `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`
- `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`
- `docs/product/UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/traceability/STAGE_2_1_WB_TRACEABILITY_MATRIX.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Разделы ТЗ для чтения:
- `tz_stage_2.1.txt` §5.5, §6.6, §9.2, §10.1, §11, §15.4, §16, §18.

Связанные GAP/ADR:
- ADR-0016, ADR-0017, ADR-0018, ADR-0019, ADR-0020.
- Новых open GAP нет.

Связанные требования ТЗ:
- §5.5: TASK-011..TASK-017 evidence complete.
- §6.6: operation/file model and `step_code` classification verified.
- §9.2: discount-only upload payload and no stale price fallback verified.
- §10.1: secret handling verified.
- §11: operation/audit/techlog invariants verified.
- §15.4: upload acceptance criteria verified.
- §16: mandatory prohibitions verified.
- §18: final readiness report format.

Разрешённые файлы / области изменения:
- `docs/testing/` - Stage 2.1 test reports, acceptance evidence, checklist execution results.
- `docs/reports/` - release readiness or handoff reports.
- `docs/traceability/STAGE_2_1_WB_TRACEABILITY_MATRIX.md` - coverage status updates only if the release process requires them.
- Test-only fixtures under `apps/**/tests*` or future `apps/discounts/wb_api/tests/`, without product logic changes and without real secrets.

Запрещённые файлы / области изменения:
- `itogovoe_tz_platforma_marketplace_codex.txt`, `tz_stage_2.1.txt`.
- `docs/audit/AUDIT_REPORT_STAGE_2_1_WB_DOCUMENTATION.md`.
- Product logic except explicitly assigned fixes from orchestrator.
- Stage 1 accepted comparison artifacts and expected results.
- Real `test_files/secrets/`, real WB tokens, or generated reports containing secrets.
- `apps/discounts/ozon_excel/` and any future `apps/discounts/ozon_api/`.

Ожидаемый результат:
- Completed Stage 2.1 acceptance checklist.
- Traceability coverage confirmed.
- Operation classifier contract verified: Stage 2.1 operations have `step_code`, not `type=check/process`.
- Upload payload contract verified: normal payload has `nmID` + `discount` only, no stale `price`; discount-only rejection stops safely.
- Blocking findings reported to orchestrator/auditor.

Критерии завершённости:
- TASK-011..TASK-016 evidence reviewed.
- Stage 1 WB Excel regression status recorded.
- Secret redaction confirmed across metadata, audit, techlog `safe_message`, techlog `sensitive_details_ref`, snapshots, UI, files, reports and test output.
- Ready/not ready decision documented.

Обязательные проверки:
- full automated test suite relevant to Stage 2.1;
- Stage 1 WB Excel regression;
- acceptance mock scenarios;
- operation `step_code` and `Operation.type` contract checks;
- upload payload checks for `nmID` + `discount` only, discount-only rejection safe stop and no old price fallback;
- secret redaction checks;
- manual UI confirmation flow if UI exists.

Формат отчёта:
- что сделано;
- изменённые файлы;
- закрытые требования;
- проверки;
- использованные входные документы / разделы ТЗ;
- gaps;
- вопросы для эскалации заказчику через оркестратора;
- release readiness: ready/not ready;
- следующий шаг.

Получатель результата:
- оркестратор Stage 2.1, аудитор, release owner.
