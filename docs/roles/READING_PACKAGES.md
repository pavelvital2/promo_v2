# READING_PACKAGES.md

Трассировка: ТЗ §25-§26.

Назначение: минимальные пакеты чтения для ролей и типовых задач. Пакеты дополняют, но не заменяют конкретную постановку оркестратора.

Общее правило для всех пакетов: итоговое ТЗ `itogovoe_tz_platforma_marketplace_codex.txt` не читается целиком по умолчанию. Оркестратор указывает только релевантные разделы ТЗ. При спорном или критичном требовании аудитор сверяет исходное ТЗ.

Для быстрого входа в проект перед профильным пакетом читать `docs/PROJECT_NAVIGATOR.md`, если задача не ограничена уже выданным task-scoped контекстом.

## Оркестратор

Обязательно:

- `AGENTS.md`
- `docs/README.md`
- `docs/PROJECT_NAVIGATOR.md`
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
- `docs/PROJECT_NAVIGATOR.md`
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
- `docs/PROJECT_NAVIGATOR.md`
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

## Разработчик WB API Stage 2.1

Обязательно:

- `AGENTS.md`
- `docs/orchestration/AGENTS.md`
- конкретный task file из `docs/tasks/implementation/stage-2/`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`
- профильная спецификация:
  - TASK-011: `docs/architecture/API_CONNECTIONS_SPEC.md`
  - TASK-012: `docs/product/WB_API_PRICE_EXPORT_SPEC.md`
  - TASK-013: `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`
  - TASK-014/TASK-015: `docs/product/WB_DISCOUNTS_API_SPEC.md`
- `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md` только для задач с shared WB calculation
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Условно: `docs/product/UI_SPEC.md` для UI-facing задач, `docs/traceability/STAGE_2_1_WB_TRACEABILITY_MATRIX.md` для audit/release задач.

ТЗ: только разделы `docs/source/stage-inputs/tz_stage_2.1.txt`, указанные в конкретном TASK-011..TASK-017. Не читать всё итоговое ТЗ целиком. WB Stage 2.1 не смешивается с Ozon Stage 2.2.

## Разработчик Ozon API Stage 2.2

Обязательно:

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- concrete task file `docs/tasks/implementation/stage-2/TASK-019..TASK-026`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`
- `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`
- `docs/product/OZON_API_ELASTIC_UI_SPEC.md`
- `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md` for shared calculation tasks
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

Условно: `docs/product/UI_SPEC.md` for UI-facing tasks, `docs/traceability/STAGE_2_2_OZON_TRACEABILITY_MATRIX.md` for audit/release tasks.

ТЗ: only task-scoped sections explicitly issued by orchestrator. Do not read whole final TZ by default. Do not implement blocked slices while `GAP-0014`..`GAP-0022` remain open for that slice. WB Stage 2.1 не смешивается с Ozon Stage 2.2.

## Frontend/UI Агент WB API Stage 2.1

Обязательно:

- `AGENTS.md`
- `docs/orchestration/AGENTS.md`
- `docs/tasks/implementation/stage-2/TASK-016-wb-api-ui-stage-2-1.md`
- `docs/product/UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/product/WB_DISCOUNTS_API_SPEC.md`
- `docs/product/WB_API_PRICE_EXPORT_SPEC.md`
- `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

ТЗ: `docs/source/stage-inputs/tz_stage_2.1.txt` §13, §15-§16 только по указанию task. Любой новый UX/functionality gap веб-панели фиксируется в `docs/gaps/GAP_REGISTER.md` и передаётся оркестратору.

## Разработчик Product Core Stage 3.0

Обязательно:

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- конкретный task file `docs/tasks/implementation/stage-3-product-core/TASK-PC-001..TASK-PC-010`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- documents listed for the concrete task package in that file
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

ТЗ: only task source sections listed in the concrete TASK-PC file. Do not read the full final TZ by default. Implementation is prohibited until `docs/audit/AUDIT_REPORT_STAGE_3_PRODUCT_CORE_DOCUMENTATION.md` has `AUDIT PASS`. `GAP-0023` is resolved/customer_decision 2026-05-01: CORE-1 candidate suggestions are non-authoritative exact `seller_article`/`barcode`/external identifier matches only, and confirmed mapping still requires explicit user confirmation with audit/history.

## Разработчик Product Core CORE-2

Обязательно:

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- concrete CORE-2 task section from `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md`
- documents listed for the concrete task package in that file
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

ТЗ: only task source sections listed in the CORE-2 task package. Do not read the full final TZ by default. CORE-2 documentation audit/recheck passed on 2026-05-02, and `GAP-CORE2-001`..`GAP-CORE2-005` are resolved customer decisions with implementation constraints. Implementation is still prohibited until the updated post-audit design docs pass follow-up audit/recheck and a separate task-scoped implementation assignment is issued; UX/functionality and spec-blocking gaps go through orchestrator to customer.

## Аудитор Product Core CORE-2

Обязательно:

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md`
- all files in `docs/stages/stage-3-product-core/core-2/`
- updated shared docs listed in `docs/stages/stage-3-product-core/core-2/CORE_2_DESIGN_HANDOFF.md`
- `docs/reports/CORE_1_RELEASE_VALIDATION_REPORT.md`
- `docs/audit/AUDIT_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

ТЗ: auditor verifies CORE-2 against the input design TZ and relevant final TZ sections for critical requirements. Open CORE-2 GAP entries may be accepted as documented blockers only if they are not hidden assumptions and affected implementation slices remain blocked.

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

Для Stage 2.1 WB API тестировщик читает вместо Stage 1 acceptance:

- `docs/stages/stage-2/STAGE_2_1_WB_ACCEPTANCE_TESTS.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/traceability/STAGE_2_1_WB_TRACEABILITY_MATRIX.md`
- проверяемый TASK-011..TASK-017

ТЗ Stage 2.1: только разделы, указанные в task.

Для Stage 2.2 Ozon API тестировщик читает:

- `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`
- `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`
- `docs/product/OZON_API_ELASTIC_UI_SPEC.md`
- `docs/testing/STAGE_2_2_OZON_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_2_OZON_ACCEPTANCE_CHECKLISTS.md`
- `docs/traceability/STAGE_2_2_OZON_TRACEABILITY_MATRIX.md`
- проверяемый TASK-019..TASK-026

ТЗ Stage 2.2: только разделы, указанные task/orchestrator. Open Stage 2.2 GAP не закрываются тестировщиком предположениями.

Для Stage 3.0 Product Core тестировщик читает:

- `docs/testing/STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md`
- `docs/testing/STAGE_3_PRODUCT_CORE_ACCEPTANCE_CHECKLISTS.md`
- `docs/traceability/STAGE_3_PRODUCT_CORE_TRACEABILITY_MATRIX.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_ACCEPTANCE_TESTS.md`
- проверяемый `docs/tasks/implementation/stage-3-product-core/TASK-PC-009-tests-and-acceptance.md`

ТЗ Stage 3.0: только task source §14, §22 and sections explicitly issued by orchestrator. Open Product Core GAP are not closed by tester assumptions.

## Аудитор Product Core Stage 3.0

Обязательно:

- `docs/audit/AUDIT_PROTOCOL.md`
- `docs/audit/HANDOFF_STAGE_3_PRODUCT_CORE_DOCUMENTATION_TO_AUDITOR.md`
- `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md`
- all files listed in the handoff
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

ТЗ: relevant final TZ sections listed in the handoff for critical verification; full final TZ reread is not a default requirement for implementation agents.

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
