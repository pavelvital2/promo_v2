# TASK-013-wb-api-current-promotions-download.md

ID: TASK-013
Тип задачи: реализация Stage 2.1 / 2.1.2
Агент: разработчик Codex CLI
Цель: скачать текущие WB акции, сохранить акции/товары и сформировать Excel promo files.

Источник истины:
- `docs/source/stage-inputs/tz_stage_2.1.txt`, без полного перечитывания вне указанных разделов.

Входные документы:
- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/orchestration/TASK_TEMPLATES.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-2/TASK-013-wb-api-current-promotions-download.md`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`
- `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`
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
- `docs/source/stage-inputs/tz_stage_2.1.txt` §5.5, §6.6, §10.1, §11, §15.2, §16.

Связанные GAP/ADR:
- ADR-0016, ADR-0018, ADR-0020.
- Новых open GAP нет.

Связанные требования ТЗ:
- §6.6: API operation classification must not be left to developer.
- §10.1: secrets not stored outside protected secret reference.
- §11: operation/audit/techlog invariants.
- §16: no WB write in 2.1.2, no Ozon 2.2 mixing.

Разрешённые файлы / области изменения:
- Future path `apps/discounts/wb_api/promotions/` or `apps/discounts/wb_api/promotion_*.py` - Promotions Calendar API client/use case/normalizers.
- Future path `apps/discounts/wb_api/client.py`, `apps/discounts/wb_api/rate_limit*.py`, `apps/discounts/wb_api/snapshots*.py` - shared safe read client helpers.
- `apps/files/`, `apps/operations/`, `apps/audit/`, `apps/techlog/` - file/version, operation, audit and techlog integration for 2.1.2.
- `apps/exports/` - promo Excel export writer if export code belongs there.
- Future promotion persistence paths under `apps/discounts/wb_api/promotions/`.
- Tests in the same app paths and safe mock fixtures without real secrets.

Запрещённые файлы / области изменения:
- `itogovoe_tz_platforma_marketplace_codex.txt`, `docs/source/stage-inputs/tz_stage_2.1.txt`.
- `docs/audit/AUDIT_REPORT_STAGE_2_1_WB_DOCUMENTATION.md`.
- `apps/discounts/wb_excel/` calculation formula/order/outcome.
- Future `apps/discounts/wb_api/upload/` or upload execution code except shared read-only client helpers.
- `apps/discounts/ozon_excel/` and any future `apps/discounts/ozon_api/`.
- Real `test_files/secrets/`, real WB tokens, or generated files containing secrets.

Ожидаемый результат:
- 2.1.2 operation has `mode=api`, `marketplace=wb`, `step_code=wb_api_promotions_download`.
- `Operation.type` for this API step is `NULL` / blank / `not_applicable`, not `check/process`.
- Current promotions selected by `startDateTime <= now_utc < endDateTime`.
- Regular promotions have nomenclatures and Excel files.
- Auto promotions saved without invented rows.

Критерии завершённости:
- 2.1.2 checklist passed.
- No WB write endpoints called.
- `allPromo=true`, API window, current timestamp saved.
- Tokens absent from metadata, snapshots, audit, techlog, UI, files, reports and test output.

Обязательные проверки:
- current filter tests;
- details batch <=100 tests;
- nomenclatures pagination tests;
- auto promotion tests;
- Excel schema tests;
- operation classifier test for mandatory `step_code` and non-check/process `type`;
- secret redaction tests across safe and sensitive diagnostics.

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
