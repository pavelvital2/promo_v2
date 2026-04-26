# TASK-016-wb-api-ui-stage-2-1.md

ID: TASK-016
Тип задачи: реализация Stage 2.1 UI
Агент: frontend/fullstack Codex CLI
Цель: реализовать UI мастер `WB -> Скидки -> API` для 2.1.1-2.1.4.

Источник истины:
- `tz_stage_2.1.txt`, без полного перечитывания вне указанных разделов.

Входные документы:
- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/orchestration/TASK_TEMPLATES.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-2/TASK-016-wb-api-ui-stage-2-1.md`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`
- `docs/product/UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/product/WB_DISCOUNTS_API_SPEC.md`
- `docs/product/WB_API_PRICE_EXPORT_SPEC.md`
- `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Разделы ТЗ для чтения:
- `tz_stage_2.1.txt` §5.5, §6.6, §10.1, §11, §13, §15.4, §16.

Связанные GAP/ADR:
- ADR-0016, ADR-0017, ADR-0018, ADR-0019, ADR-0020.
- Новых open GAP нет.

Связанные требования ТЗ:
- §6.6: UI must classify API operations by explicit step, not by check/process type.
- §10.1: UI never exposes secrets.
- §13: WB API master screen and confirmation flow.
- §15.4: upload acceptance states visible.
- §16: Excel mode remains visible; Ozon 2.2 not mixed.

Разрешённые файлы / области изменения:
- `apps/web/`, `templates/web/` - WB API wizard, operation links, UI routes/views/templates/tests.
- `apps/stores/views.py`, `apps/stores/urls.py`, `apps/stores/templates/stores/connection_form.html`, `templates/stores/connection_form.html` - connection status entry points if needed.
- `apps/operations/` - read/query helpers for operation list/card classification only.
- Future path `apps/discounts/wb_api/ui/` or `apps/discounts/wb_api/views.py` - Stage 2.1 UI controllers if the project places them in the domain package.
- UI tests in the same paths.

Запрещённые файлы / области изменения:
- `itogovoe_tz_platforma_marketplace_codex.txt`, `tz_stage_2.1.txt`.
- `docs/audit/AUDIT_REPORT_STAGE_2_1_WB_DOCUMENTATION.md`.
- Stage 1 Excel UI semantics and availability for `WB -> Скидки -> Excel`.
- Backend business logic for calculation/upload except invoking already implemented services.
- Inventing unapproved UX/functionality beyond `docs/product/UI_SPEC.md`.
- `apps/discounts/ozon_excel/` and any future Ozon API UI.
- Rendering token, authorization header, API key, bearer value or secret-like values anywhere in UI.

Ожидаемый результат:
- Single WB API wizard with store, connection, four steps, latest operations, file links and errors/warnings.
- Operation list/card display Stage 2.1 classifier by `step_code`; API steps are not shown as check/process.
- Confirmation screen uses the required meaning and upload controls stay disabled until preconditions pass.
- Drift/partial/quarantine/size conflicts shown clearly.

Критерии завершённости:
- Users see only object-accessible stores/data.
- 2.1.1-2.1.3 read-only nature is visible.
- Upload controls disabled until preconditions pass.
- No secret-like value appears in DOM, templates, logs, screenshots or test output.

Обязательные проверки:
- UI permissions/object access tests;
- operation list/card classifier tests for `step_code` vs `type`;
- confirmation tests;
- screenshots/manual QA if project UI process requires;
- no token/header/API key/bearer/secret-like value rendered in UI.

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
