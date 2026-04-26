# TASK-014-wb-api-discount-calculation-excel-output.md

ID: TASK-014
Тип задачи: реализация Stage 2.1 / 2.1.3
Агент: разработчик Codex CLI
Цель: рассчитать скидки по API-источникам через Stage 1 WB logic и сформировать итоговый Excel для ручной загрузки.

Источник истины:
- `tz_stage_2.1.txt`, без полного перечитывания вне указанных разделов.

Входные документы:
- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/orchestration/TASK_TEMPLATES.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-2/TASK-014-wb-api-discount-calculation-excel-output.md`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`
- `docs/product/WB_DISCOUNTS_API_SPEC.md`
- `docs/product/WB_API_PRICE_EXPORT_SPEC.md`
- `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`
- `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Разделы ТЗ для чтения:
- `tz_stage_2.1.txt` §5.5, §6.6, §10.1, §11, §15.3, §16.

Связанные GAP/ADR:
- ADR-0016, ADR-0017, ADR-0020.
- Новых open GAP нет.

Связанные требования ТЗ:
- §6.6: 2.1.3 operation must have explicit API step classification.
- §10.1: secrets not stored outside protected secret reference.
- §11: operation/file/audit/techlog invariants.
- §16: no WB API upload in 2.1.3 and no Stage 1 WB Excel behavior change.

Разрешённые файлы / области изменения:
- Future path `apps/discounts/wb_api/calculation/` or `apps/discounts/wb_api/calculation_*.py` - API-source calculation adapter and orchestration.
- Future path `apps/discounts/wb_shared/` - extracted shared WB calculation core only if needed to preserve Stage 1 behavior.
- `apps/discounts/wb_excel/` - only minimal extraction/reuse needed for shared core; changing Stage 1 outputs is forbidden.
- `apps/files/`, `apps/operations/`, `apps/audit/`, `apps/techlog/` - file/version, operation, audit and techlog integration for 2.1.3.
- `apps/exports/` - result Excel/detail writer if export code belongs there.
- Tests in the same app paths and safe mock/golden fixtures without real secrets.

Запрещённые файлы / области изменения:
- `itogovoe_tz_platforma_marketplace_codex.txt`, `tz_stage_2.1.txt`.
- `docs/audit/AUDIT_REPORT_STAGE_2_1_WB_DOCUMENTATION.md`.
- Stage 1 WB Excel calculation outcome, formula order, parameter defaults or accepted control outputs.
- Future `apps/discounts/wb_api/upload/` or WB write endpoint calls.
- `apps/discounts/ozon_excel/` and any future `apps/discounts/ozon_api/`.
- Real `test_files/secrets/`, real WB tokens, or generated files containing secrets.

Ожидаемый результат:
- 2.1.3 operation has `mode=api`, `marketplace=wb`, `step_code=wb_api_discount_calculation`.
- `Operation.type` for this API step is `NULL` / blank / `not_applicable`, not `check/process`.
- Selected price/promo basis and parameter snapshot are stored.
- Result Excel writes only `Новая скидка`.
- Golden comparison with Stage 1 equivalent data passes.

Критерии завершённости:
- Same formula/order/decimal+ceil as Stage 1.
- Errors block upload.
- Recalculation creates new operation/file version.
- Tokens absent from metadata, snapshots, audit, techlog, UI, files, reports and test output.

Обязательные проверки:
- WB calculation regression tests;
- API adapter tests;
- result Excel tests;
- basis actuality tests;
- no float tests if supported by codebase;
- operation classifier test for mandatory `step_code` and non-check/process `type`;
- security tests proving result Excel/detail/audit/techlog contain no secret-like values.

Формат отчёта:
- что сделано;
- изменённые файлы;
- закрытые требования;
- проверки;
- использованные входные документы / разделы ТЗ;
- gaps;
- вопросы для эскалации заказчику через оркестратора;
- следующий шаг.

Получатель результата:
- оркестратор Stage 2.1 и аудитор.
