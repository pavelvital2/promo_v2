# READING_PACKAGES.md

Трассировка: ТЗ §25-§26.

Назначение: минимальные пакеты чтения для ролей и типовых задач. Пакеты дополняют, но не заменяют конкретную постановку оркестратора.

Общее правило для всех пакетов: итоговое ТЗ `itogovoe_tz_platforma_marketplace_codex.txt` не читается целиком по умолчанию. Оркестратор указывает только релевантные разделы ТЗ. При спорном или критичном требовании аудитор сверяет исходное ТЗ.

## Оркестратор

Обязательно:

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/orchestration/ORCHESTRATION.md`
- `docs/orchestration/TASK_TEMPLATES.md`
- `docs/orchestration/HANDOFF_TEMPLATES.md`
- `docs/orchestration/PARALLEL_WORK_RULES.md`
- `docs/roles/AGENT_ROLES_MATRIX.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`
- `docs/traceability/TRACEABILITY_MATRIX.md`

Условно: профильные specs из `docs/architecture/`, `docs/product/`, `docs/testing/`, `docs/audit/` по задаче.

ТЗ: §25-§26; дополнительные разделы только под конкретную задачу.

## Проектировщик документации

Обязательно:

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`
- `docs/stages/stage-1/PROJECT_DOCUMENTATION_PLAN.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`
- профильные документы области изменения

Условно: `docs/audit/AUDIT_REPORT_ROUND_2.md`, `docs/reports/DESIGNER_FIX_REPORT.md`, `docs/traceability/TRACEABILITY_MATRIX.md`.

ТЗ: только разделы, указанные оркестратором для области изменения. Нельзя менять закрытые решения `GAP-0002`, `GAP-0003`, `GAP-0004`, `GAP-0007`, `GAP-0008`, `GAP-0009` предположениями.

## Аудитор документации

Обязательно:

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/audit/AUDIT_PROTOCOL.md`
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`
- `docs/traceability/TRACEABILITY_MATRIX.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`
- все документы, входящие в проверяемую область

Условно: прошлые отчёты `docs/audit/AUDIT_REPORT.md`, `docs/audit/AUDIT_REPORT_ROUND_2.md`, `docs/reports/DESIGNER_FIX_REPORT.md`.

ТЗ: аудитор читает релевантные разделы исходного ТЗ для проверяемой области и спорных/критичных требований; полное чтение ТЗ не является default для каждой проверки.

## Разработчик платформенного каркаса

Обязательно:

- `AGENTS.md`
- `docs/orchestration/AGENTS.md`
- `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`
- `docs/tasks/implementation/stage-1/TASK-001-project-bootstrap.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/PROJECT_STRUCTURE.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`
- `docs/testing/TEST_PROTOCOL.md`

Условно: `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md`, `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`.

ТЗ: §3, §7, §11, §22, §27 только если указаны оркестратором.

## Разработчик WB Excel

Обязательно:

- `AGENTS.md`
- `docs/orchestration/AGENTS.md`
- `docs/tasks/implementation/stage-1/TASK-007-wb-discounts-excel.md`
- `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/stages/stage-1/ACCEPTANCE_TESTS.md`
- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`
- `docs/gaps/GAP_REGISTER.md` entries `GAP-0002`, `GAP-0003`, `GAP-0004`, `GAP-0008`

Условно: `docs/product/UI_SPEC.md`, `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`, `docs/adr/ADR_LOG.md`.

ТЗ: §12, §14, §15, §17, §23, §24 только по указанию оркестратора. Нельзя закрывать WB gaps предположениями.

## Разработчик Ozon Excel

Обязательно:

- `AGENTS.md`
- `docs/orchestration/AGENTS.md`
- `docs/tasks/implementation/stage-1/TASK-008-ozon-discounts-excel.md`
- `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/stages/stage-1/ACCEPTANCE_TESTS.md`
- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`
- `docs/gaps/GAP_REGISTER.md` entry `GAP-0008`

Условно: `docs/product/UI_SPEC.md`, `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`, `docs/adr/ADR_LOG.md`.

ТЗ: §12, §16, §17, §24 только по указанию оркестратора.

## Frontend/UI Агент

Обязательно:

- `AGENTS.md`
- `docs/orchestration/AGENTS.md`
- `docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md`
- `docs/product/UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/testing/TEST_PROTOCOL.md`

Условно: WB/Ozon specs, acceptance checklists, ADR entries tied to routes/permissions.

ТЗ: §5, §6, §11, §12, §17-§20, §27 только по указанию оркестратора. Любой UX/functionality gap веб-панели передаётся оркестратору для заказчика, не закрывается предположением.

## Тестировщик

Обязательно:

- `AGENTS.md`
- `docs/orchestration/AGENTS.md`
- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`
- `docs/stages/stage-1/ACCEPTANCE_TESTS.md`
- спецификация проверяемой области
- связанная implementation task
- `docs/gaps/GAP_REGISTER.md`

Условно: `docs/audit/AUDIT_PROTOCOL.md`, `docs/product/UI_SPEC.md`, module specs, operations/file contour.

ТЗ: §24 и профильные разделы сценария только по указанию оркестратора. Отсутствие контрольных файлов не заменяется синтетическими expected results; см. `GAP-0008` / ADR-0013 и `docs/stages/stage-1/ACCEPTANCE_TESTS.md`.

## Техрайтер

Обязательно:

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`
- handoff от исполнителя
- документы, которые изменяются или должны отражать изменение
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Условно: `docs/traceability/TRACEABILITY_MATRIX.md`, `docs/reports/`, audit/test outputs.

ТЗ: только разделы, указанные оркестратором для проверки формулировок. Техрайтер не добавляет бизнес-логику и не закрывает gaps.
