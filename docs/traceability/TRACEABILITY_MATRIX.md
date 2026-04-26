# TRACEABILITY_MATRIX.md

Трассировка: ТЗ §25.1-§25.2.

## Назначение

Матрица связывает обязательные требования этапа 1 с исполнительными документами, gaps и ADR. Статус `accepted_with_registered_artifacts` означает, что проектное правило отражено, gap закрыт, а фактические customer artifacts зарегистрированы и приняты.

| ТЗ | Требование этапа 1 | Документы покрытия | Статус | GAP/ADR |
| --- | --- | --- | --- | --- |
| §1 | Источник истины, запрет домысливания, эскалация пробелов | `AGENTS.md`, `docs/orchestration/ORCHESTRATION.md`, `docs/gaps/GAP_REGISTER.md`, `docs/adr/ADR_LOG.md`, `docs/audit/AUDIT_PROTOCOL.md` | covered | ADR-0001, ADR-0005 |
| §2.4-§2.5 | Бизнес-функция как модульность, Excel штатный/резервный режим | `docs/architecture/ARCHITECTURE.md`, `docs/architecture/PROJECT_STRUCTURE.md`, `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`, `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md` | covered | ADR-0003 |
| §3.1 | Обязательный объём этапа 1 | `docs/stages/stage-1/PROJECT_DOCUMENTATION_PLAN.md`, `docs/product/modules/README.md`, профильные спецификации, `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`, `docs/tasks/implementation/stage-1/` | covered | ADR-0006, ADR-0007, ADR-0008 |
| §3.2-§3.4 | Будущие этапы только архитектурно | `docs/architecture/ARCHITECTURE.md`, `docs/architecture/DATA_MODEL.md`, `docs/architecture/PROJECT_STRUCTURE.md` | covered | ADR-0002, ADR-0003 |
| §4 | Модульный монолит, единая БД, deployment baseline | `docs/architecture/ARCHITECTURE.md`, `docs/architecture/PROJECT_STRUCTURE.md`, `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md` | covered | ADR-0002, ADR-0006 |
| §5 | Обязательные разделы и навигация | `docs/product/UI_SPEC.md`, `docs/stages/stage-1/PROJECT_DOCUMENTATION_PLAN.md` | covered | - |
| §6 | Формат экранов и обязательный перечень экранов | `docs/product/UI_SPEC.md` | covered | - |
| §7 | Обязательные сущности и будущие сущности | `docs/architecture/DATA_MODEL.md` | covered | - |
| §8 | Магазины/кабинеты/подключения | `docs/architecture/DATA_MODEL.md`, `docs/product/UI_SPEC.md`, `docs/product/PERMISSIONS_MATRIX.md`, `docs/architecture/DELETION_ARCHIVAL_POLICY.md` | covered | - |
| §9 | Marketplace products и будущая номенклатура | `docs/architecture/DATA_MODEL.md`, `docs/product/UI_SPEC.md`, `docs/product/modules/README.md` | covered | - |
| §10 | Производство/склад как будущие направления | `docs/architecture/ARCHITECTURE.md`, `docs/architecture/DATA_MODEL.md` | covered | - |
| §11 | Пользователи, роли, права, object access, owner | `docs/product/PERMISSIONS_MATRIX.md`, `docs/architecture/DATA_MODEL.md`, `docs/product/UI_SPEC.md`, `docs/architecture/DELETION_ARCHIVAL_POLICY.md` | covered | ADR-0007 |
| §12 | Operations, run, check/process, statuses | `docs/product/OPERATIONS_SPEC.md`, `docs/architecture/DATA_MODEL.md`, `docs/product/UI_SPEC.md` | covered | ADR-0004 |
| §13 | Files, versions, retention | `docs/architecture/FILE_CONTOUR.md`, `docs/architecture/DATA_MODEL.md`, `docs/product/UI_SPEC.md`, `docs/architecture/DELETION_ARCHIVAL_POLICY.md` | covered | - |
| §14 | Parameters/settings calculation | `docs/architecture/DATA_MODEL.md`, `docs/product/UI_SPEC.md`, `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md` | covered | ADR-0009 |
| §15 | WB Discounts Excel logic | `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`, `docs/product/OPERATIONS_SPEC.md`, `docs/architecture/FILE_CONTOUR.md`, `docs/stages/stage-1/ACCEPTANCE_TESTS.md` | covered | ADR-0009, ADR-0010, ADR-0011 |
| §16 | Ozon Discounts Excel logic | `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md`, `docs/product/OPERATIONS_SPEC.md`, `docs/architecture/FILE_CONTOUR.md`, `docs/stages/stage-1/ACCEPTANCE_TESTS.md` | covered | - |
| §17 | Explainability, operation card, detail audit/export | `docs/product/UI_SPEC.md`, `docs/product/OPERATIONS_SPEC.md`, `docs/architecture/DATA_MODEL.md`, `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`, `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md` | covered | ADR-0010 |
| §18 | Lists, filters, search, sorting, pagination, exports | `docs/product/UI_SPEC.md`, `docs/stages/stage-1/ACCEPTANCE_TESTS.md`, `docs/product/modules/README.md` | covered | - |
| §19 | Desktop-first UX | `docs/product/UI_SPEC.md` | covered | - |
| §20 | Audit, techlog, cards, filters, separation | `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`, `docs/architecture/DATA_MODEL.md`, `docs/product/UI_SPEC.md`, `docs/audit/AUDIT_PROTOCOL.md` | covered | ADR-0014 |
| §21 | Deletion, blocking, archiving | `docs/architecture/DELETION_ARCHIVAL_POLICY.md`, `docs/architecture/DATA_MODEL.md`, `docs/architecture/FILE_CONTOUR.md`, `docs/product/PERMISSIONS_MATRIX.md`, `docs/product/UI_SPEC.md` | covered | ADR-0014 |
| §22 | Execution, failures, restore, updates, backup, notifications | `docs/architecture/ARCHITECTURE.md`, `docs/product/OPERATIONS_SPEC.md`, `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md`, `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md` | covered | ADR-0006, ADR-0012 |
| §23.1 | Fixed system dictionaries and codes | `docs/architecture/DATA_MODEL.md`, `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`, `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`, `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md` | covered | ADR-0010 |
| §23.2 | Visible identifiers | `docs/architecture/DATA_MODEL.md`, `docs/gaps/GAP_REGISTER.md`, `docs/adr/ADR_LOG.md` | covered | ADR-0008 |
| §24 | Acceptance by control files | `docs/stages/stage-1/ACCEPTANCE_TESTS.md`, `docs/testing/TEST_PROTOCOL.md`, `docs/testing/CONTROL_FILE_REGISTRY.md`, `docs/testing/TEST_REPORT_STAGE_1_FORMAL_ACCEPTANCE.md` | accepted_with_registered_artifacts | ADR-0013; `WB-REAL-001` / `OZ-REAL-001` accepted 2026-04-26 |
| §25 | Executive documentation requirements | `docs/stages/stage-1/PROJECT_DOCUMENTATION_PLAN.md`, `docs/traceability/TRACEABILITY_MATRIX.md`, all профильные документы | covered | - |
| §26 | Codex CLI agent process, task-scoped context, handoff and escalation | `AGENTS.md`, `docs/orchestration/ORCHESTRATION.md`, `docs/roles/AGENT_ROLES_MATRIX.md`, `docs/orchestration/TASK_TEMPLATES.md`, `docs/orchestration/HANDOFF_TEMPLATES.md`, `docs/orchestration/PARALLEL_WORK_RULES.md`, `docs/audit/AUDIT_PROTOCOL.md`, `docs/testing/TEST_PROTOCOL.md`, `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`, `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`, `docs/tasks/implementation/stage-1/README.md` | covered | ADR-0005 |
| §27 | Non-functional: security, reliability, extensibility | `docs/architecture/ARCHITECTURE.md`, `docs/product/PERMISSIONS_MATRIX.md`, `docs/architecture/DATA_MODEL.md`, `docs/architecture/FILE_CONTOUR.md`, `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md`, `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md` | covered | ADR-0006, ADR-0007, ADR-0012, ADR-0014 |
| §28 | Final fixation and priority of stage 1 concerns | `AGENTS.md`, `docs/stages/stage-1/PROJECT_DOCUMENTATION_PLAN.md`, `docs/traceability/TRACEABILITY_MATRIX.md` | covered | ADR-0001 |

## Gates summary

| Phase gate | Blocking gaps | Что блокируется |
| --- | --- | --- |
| blocks_before_any_development | нет открытых | старт реализации, миграции, seed, UI skeleton разрешены после повторного аудита документации |
| blocks_before_module_implementation | нет открытых | WB settings/WB discounts slices, WB row-level dictionaries, WB acceptance details разрешены после audit pass |
| blocks_before_acceptance/production | нет открытых GAP | production readiness policy утверждена; real WB/Ozon comparison artifact gate закрыт для `WB-REAL-001` / `OZ-REAL-001`; дальнейший production sign-off зависит от deployment/ops checks |
