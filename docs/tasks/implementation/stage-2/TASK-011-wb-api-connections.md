# TASK-011-wb-api-connections.md

ID: TASK-011
Тип задачи: реализация Stage 2.1 prerequisite
Агент: разработчик Codex CLI
Цель: реализовать рабочий WB API connection contour с protected secrets, status/check flow, safe API client policies and audit/techlog.

Источник истины:
- `docs/source/stage-inputs/tz_stage_2.1.txt`, без полного перечитывания вне указанных разделов.

Входные документы:
- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/orchestration/TASK_TEMPLATES.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-2/TASK-011-wb-api-connections.md`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`
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
- `docs/source/stage-inputs/tz_stage_2.1.txt` §5.5, §10.1, §11, §15.4, §16.

Связанные GAP/ADR:
- ADR-0016, ADR-0017, ADR-0019.
- Новых open GAP нет.

Связанные требования ТЗ:
- §5.5: TASK-011 как инфраструктурная предпосылка.
- §10.1: token хранится только через protected secret reference.
- §11: audit/techlog separated, secrets not exposed.
- §16: запрет на хранение token outside protected secret reference and mixing WB 2.1 with Ozon 2.2.

Разрешённые файлы / области изменения:
- `apps/stores/models.py`, `apps/stores/services.py`, `apps/stores/forms.py`, `apps/stores/views.py`, `apps/stores/urls.py`, `apps/stores/templates/stores/connection_form.html`, `templates/stores/connection_form.html`, `apps/stores/migrations/` - WB connection fields/status UI.
- `apps/identity_access/` - permission seeds/checks for WB API connection rights.
- `apps/audit/`, `apps/techlog/` - Stage 2.1 action/event codes, safe messages and tests.
- Future path `apps/discounts/wb_api/` - WB API client, rate limiter, redaction helpers and mocks.
- `apps/stores/tests.py`, `apps/audit/tests.py`, `apps/techlog/tests.py`, future `apps/discounts/wb_api/tests.py`.
- `docs/testing/` or `docs/reports/` only for executor evidence/report files if the task process requires them.

Запрещённые файлы / области изменения:
- `itogovoe_tz_platforma_marketplace_codex.txt`, `docs/source/stage-inputs/tz_stage_2.1.txt`.
- `docs/audit/AUDIT_REPORT_STAGE_2_1_WB_DOCUMENTATION.md`.
- `apps/discounts/wb_excel/` and Stage 1 WB Excel calculation behavior.
- `apps/discounts/ozon_excel/` and any future `apps/discounts/ozon_api/`.
- TASK-012..TASK-015 business flows except shared safe client helpers inside `apps/discounts/wb_api/`.
- Real `test_files/secrets/`, real WB tokens, or code paths that print/store tokens.

Ожидаемый результат:
- WB API connection can be configured, checked, disabled/archived by rights.
- Token, authorization header, API key, bearer value and secret-like values are stored only through `protected_secret_ref`.
- Safe read-only check uses `GET /api/v2/list/goods/filter?limit=1&offset=0`.
- Safe snapshots/audit/techlog/UI/files/reports contain no secret-like values.

Критерии завершённости:
- Statuses `not_configured/configured/active/check_failed/disabled/archived` supported.
- Audit/techlog codes implemented.
- Secret redaction tests pass for metadata, audit, techlog `safe_message`, techlog `sensitive_details_ref`, snapshots, UI, files, reports and test output.
- Object access and connection permissions enforced.

Обязательные проверки:
- unit/integration tests for metadata secret rejection;
- permission/object access tests;
- connection check mock tests for success, 401/403, 429, timeout;
- security test proving no token/header/API key/bearer/secret-like value is persisted outside `protected_secret_ref`.

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
