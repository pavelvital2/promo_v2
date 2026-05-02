# TASK-015-wb-api-discount-upload.md

ID: TASK-015
Тип задачи: реализация Stage 2.1 / 2.1.4
Агент: разработчик Codex CLI
Цель: реализовать безопасную API-загрузку рассчитанных скидок WB с confirmation, drift check, batching, uploadID и status polling.

Источник истины:
- `docs/source/stage-inputs/tz_stage_2.1.txt`, без полного перечитывания вне указанных разделов.

Входные документы:
- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/orchestration/TASK_TEMPLATES.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-2/TASK-015-wb-api-discount-upload.md`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`
- `docs/product/WB_DISCOUNTS_API_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/product/UI_SPEC.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Разделы ТЗ для чтения:
- `docs/source/stage-inputs/tz_stage_2.1.txt` §5.5, §6.6, §9.2, §10.1, §11, §15.4, §16.

Связанные GAP/ADR:
- ADR-0016, ADR-0019, ADR-0020.
- Новых open GAP нет.

Связанные требования ТЗ:
- §6.6: 2.1.4 operation must have explicit API step classification.
- §9.2: upload uses `POST /api/v2/upload/task`, batch <=1000, safe payload handling.
- §10.1: secrets not stored outside protected secret reference.
- §11: operation/audit/techlog invariants.
- §15.4: confirmation, drift check, uploadID, status polling, errors/quarantine acceptance.
- §16: no stale price, no HTTP 200 as final success, no Ozon 2.2 mixing.

Разрешённые файлы / области изменения:
- Future path `apps/discounts/wb_api/upload/` or `apps/discounts/wb_api/upload_*.py` - upload, drift check, batching, status polling and result mapping.
- Future path `apps/discounts/wb_api/client.py`, `apps/discounts/wb_api/rate_limit*.py`, `apps/discounts/wb_api/snapshots*.py` - shared safe API client helpers.
- `apps/files/`, `apps/operations/`, `apps/audit/`, `apps/techlog/` - upload operation, batch/detail persistence, reports and diagnostics.
- `apps/exports/` - upload report writer if export code belongs there.
- Tests in the same app paths and safe mock fixtures without real secrets.

Запрещённые файлы / области изменения:
- `itogovoe_tz_platforma_marketplace_codex.txt`, `docs/source/stage-inputs/tz_stage_2.1.txt`.
- `docs/audit/AUDIT_REPORT_STAGE_2_1_WB_DOCUMENTATION.md`.
- Upload from 2.1.1/2.1.2/2.1.3.
- Adding `price` to normal upload payload or silently using price from calculation Excel/old snapshot.
- Stage 1 WB Excel calculation behavior and accepted control outputs.
- Size upload endpoints, WB Club discount endpoints.
- `apps/discounts/ozon_excel/` and any future `apps/discounts/ozon_api/`.
- Real `test_files/secrets/`, real WB tokens, or generated files containing secrets.

Ожидаемый результат:
- 2.1.4 operation has `mode=api`, `marketplace=wb`, `step_code=wb_api_discount_upload`.
- `Operation.type` for this API step is `NULL` / blank / `not_applicable`, not `check/process`.
- Upload starts only after successful 2.1.3 and explicit confirmation.
- Drift blocks upload.
- Normal upload payload contains `nmID` + `discount` only; no `price`.
- WB rejection of discount-only payload stops upload safely and does not retry with old price.
- Batch <=1000, uploadID per batch.
- Status polling maps WB statuses 3/4/5/6.
- Partial/quarantine errors visible.

Критерии завершённости:
- HTTP 200 alone never marks success.
- 208/429/auth/timeout handled safely.
- No stale price fallback exists.
- Secrets absent from all safe outputs and sensitive diagnostics.

Обязательные проверки:
- confirmation tests;
- drift tests;
- normal payload assertion: only `nmID` and `discount`, no `price`;
- discount-only rejection test: safe stop/escalation, no fallback to old price;
- test proving implementation does not add price from calculation Excel or old price snapshot;
- batch/status polling tests;
- partial/quarantine tests;
- operation classifier test for mandatory `step_code` and non-check/process `type`;
- secret redaction tests.

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
