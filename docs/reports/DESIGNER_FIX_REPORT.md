# DESIGNER_FIX_REPORT.md

Дата: 2026-04-25

Роль: Проектировщик исполнительной проектной документации Codex CLI.

## Что исправлено

- F-001: открытые gaps разделены по phase gates в `docs/gaps/GAP_REGISTER.md`: `blocks_before_any_development`, `blocks_before_module_implementation`, `blocks_before_acceptance/production`. Gaps не закрывались предположениями.
- F-002: `docs/architecture/DATA_MODEL.md` дополнен обязательными полями `Operation`, связями operation -> files/parameters/audit/techlog и историями пользователя, блокировок, магазина/кабинета и marketplace product.
- F-003: добавлен `docs/architecture/DELETION_ARCHIVAL_POLICY.md`; профильные документы ссылаются на правила удаления, блокировки, деактивации и архивирования по ТЗ §21.
- F-004: `docs/product/UI_SPEC.md` расширен до экранной спецификации по формату ТЗ §6.2 для всех обязательных экранов/состояний §6.3.
- F-005: Ozon process синхронизирован с правилами актуальности check в `docs/product/OPERATIONS_SPEC.md`; `docs/product/modules/README.md` теперь требует `docs/product/OPERATIONS_SPEC.md` и `docs/architecture/FILE_CONTOUR.md` как обязательные входы Ozon-модуля.
- F-006: добавлен `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md` с каталогом audit actions, techlog events, обязательными полями, фильтрами, карточками, связями и правилами видимости sensitive details.
- F-007: `docs/stages/stage-1/ACCEPTANCE_TESTS.md` доработан так, чтобы отсутствие фактических контрольных файлов было явным acceptance gate; добавлены структура реестра будущих файлов, checksums и expected results. После закрытия `GAP-0008` проектным решением этот gate остаётся artifact gate.
- F-008: добавлен `docs/traceability/TRACEABILITY_MATRIX.md` с трассировкой обязательных требований этапа 1 к документам, gaps и ADR.
- F-009: агентные правила приведены к task-scoped context reading: итоговое ТЗ остаётся источником истины, но оркестратор выдаёт агенту минимальный набор документов и конкретных разделов ТЗ для задачи. Добавлено правило customer escalation: spec-blocking вопросы и аудиторские замечания, которые нельзя исправить без пробела в ТЗ или утверждённого решения, фиксируются как gap и передаются заказчику через оркестратора.

## Доработка F-009: task-scoped context и customer escalation

По указанию заказчика изменены агентные правила:

- итоговое ТЗ сохранено как источник истины и приоритетный документ;
- снято требование полного перечитывания итогового ТЗ каждым агентом на каждую задачу;
- оркестратор обязан выдавать минимальный достаточный входной контекст: документы, чек-листы, связанные GAP/ADR и конкретные разделы ТЗ;
- если аудиторское замечание нельзя исправить без пробела в ТЗ или утверждённого решения, проектировщик фиксирует blocking gap и передаёт вопрос заказчику через оркестратора;
- проектировщик не закрывает такие вопросы предположениями и не оставляет их без эскалации.

## Доработка после решений заказчика от 2026-04-25

Закрыты phase-gate gaps `blocks_before_any_development`:

- `GAP-0001`: стек этапа 1 утверждён как Django + PostgreSQL + server-rendered UI / Django templates; решение зафиксировано в ADR-0006.
- `GAP-0005`: seed-набор прав типовых ролей утверждён как conservative template; решение зафиксировано в ADR-0007 и детализировано в `docs/product/PERMISSIONS_MATRIX.md`.
- `GAP-0006`: visible identifiers утверждены в формате `OP-YYYY-NNNNNN`, `RUN-YYYY-NNNNNN`, `FILE-YYYY-NNNNNN`, `STORE-NNNNNN`, `USR-NNNNNN`; решение зафиксировано в ADR-0008 и `docs/architecture/DATA_MODEL.md`.

Создан практический комплект задач реализации этапа 1:

- `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md` - индекс, порядок, зависимости и phase gates.
- `docs/tasks/implementation/stage-1/README.md` - правила task-scoped чтения задач и handoff.
- `docs/tasks/implementation/stage-1/TASK-001-project-bootstrap.md` .. `TASK-010-acceptance-and-deployment.md` - конкретные задачи для будущих агентов реализации.

Комплект задач больше не содержит downstream blockers по `GAP-0002`, `GAP-0003`, `GAP-0004`, `GAP-0007`, `GAP-0008`, `GAP-0009`: эти gaps закрыты решениями заказчика. Для `GAP-0008` оставлен не gap-blocker, а acceptance artifact gate по фактическим контрольным файлам, checksums и expected results.

## Доработка после решений заказчика по GAP-0002..0004/0007..0009 от 2026-04-25

Закрыты решениями заказчика:

- `GAP-0002`: системные WB defaults = `wb_threshold_percent = 70`, `wb_fallback_over_threshold_percent = 55`, `wb_fallback_no_promo_percent = 55`; ADR-0009.
- `GAP-0003`: утверждён минимальный закрытый перечень WB reason/result codes; ADR-0010.
- `GAP-0004`: WB итоговая скидка вне 0..100 = row error `wb_discount_out_of_range`, check с ошибками, process запрещён, без обрезки и частичной обработки; ADR-0011.
- `GAP-0007`: backup policy = daily PostgreSQL backup + daily server file storage backup, retention 14 days, mandatory backup before production update, restore check by documented manual procedure after setup and before important releases; ADR-0012.
- `GAP-0008`: проектное решение закрыто: заказчик передаёт реальные контрольные WB/Ozon файлы и результаты старой программы, дополнительно нужны edge-case наборы; ADR-0013. Фактические files/checksums/expected results остаются acceptance artifact gate.
- `GAP-0009`: audit records и techlog records хранятся 90 дней; очистка только регламентной процедурой, не через обычный UI; ADR-0014.

Синхронизированы профильные документы: WB spec, data model, audit/techlog spec, deletion/retention policy, file contour, release/update runbook, acceptance tests, test/checklist docs, implementation tasks and traceability matrix.

## Доработка после решений заказчика по TASK-009 UI gaps от 2026-04-25

Закрыты решениями заказчика:

- `GAP-0010`: backend product model/list/card реализуется сейчас в рамках исправления TASK-009; status screen не считается покрытием.
- `GAP-0011`: WB store parameter write-flow реализуется сейчас с history/audit; read-only parameters screen не считается покрытием.
- `GAP-0012`: draft run context реализуется сейчас: upload/replace/delete files, version list, затем "Проверить" / "Обработать"; single-submit upload без draft context не считается покрытием.
- `GAP-0013`: admin write-flow зарегистрирован после аудита и закрыт customer decision: users create/edit/block/archive, role edit where allowed, permission assignment, store access assignment реализуются сейчас.

Решение зафиксировано в ADR-0015.

Синхронизированы профильные документы: `docs/gaps/GAP_REGISTER.md`, `docs/adr/ADR_LOG.md`, `docs/product/UI_SPEC.md`, `docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md`, `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`.

`docs/architecture/DATA_MODEL.md` не изменялся: минимальные сущности `MarketplaceProduct` / `MarketplaceProductHistory` уже описаны как обязательные сущности этапа 1, дополнительные поля не утверждались.

Файлы, изменённые в рамках F-009:

- `AGENTS.md`
- `docs/orchestration/ORCHESTRATION.md`
- `docs/orchestration/TASK_TEMPLATES.md`
- `docs/orchestration/HANDOFF_TEMPLATES.md`
- `docs/roles/AGENT_ROLES_MATRIX.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/audit/AUDIT_PROTOCOL.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`
- `docs/stages/stage-1/PROJECT_DOCUMENTATION_PLAN.md`
- `docs/traceability/TRACEABILITY_MATRIX.md`
- `docs/reports/DESIGNER_FIX_REPORT.md`

## Изменённые файлы

- `docs/gaps/GAP_REGISTER.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/UI_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md`
- `docs/product/modules/README.md`
- `docs/stages/stage-1/ACCEPTANCE_TESTS.md`
- `docs/audit/AUDIT_PROTOCOL.md`
- `docs/stages/stage-1/PROJECT_DOCUMENTATION_PLAN.md`
- `AGENTS.md`
- `docs/orchestration/ORCHESTRATION.md`
- `docs/orchestration/TASK_TEMPLATES.md`
- `docs/orchestration/HANDOFF_TEMPLATES.md`
- `docs/roles/AGENT_ROLES_MATRIX.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`
- `docs/traceability/TRACEABILITY_MATRIX.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/PROJECT_STRUCTURE.md`
- `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md`
- `docs/adr/ADR_LOG.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/reports/DESIGNER_FIX_REPORT.md`
- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`
- `docs/architecture/DELETION_ARCHIVAL_POLICY.md`
- `docs/product/UI_SPEC.md`
- `docs/tasks/implementation/stage-1/TASK-004-files-and-retention.md`
- `docs/tasks/implementation/stage-1/TASK-006-audit-techlog-notifications.md`
- `docs/tasks/implementation/stage-1/TASK-007-wb-discounts-excel.md`
- `docs/tasks/implementation/stage-1/TASK-008-ozon-discounts-excel.md`
- `docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md`
- `docs/tasks/implementation/stage-1/TASK-010-acceptance-and-deployment.md`

## Созданные файлы

- `docs/architecture/DELETION_ARCHIVAL_POLICY.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/traceability/TRACEABILITY_MATRIX.md`
- `docs/reports/DESIGNER_FIX_REPORT.md`
- `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`
- `docs/tasks/implementation/stage-1/README.md`
- `docs/tasks/implementation/stage-1/TASK-001-project-bootstrap.md`
- `docs/tasks/implementation/stage-1/TASK-002-auth-users-roles-permissions.md`
- `docs/tasks/implementation/stage-1/TASK-003-stores-cabinets-connections.md`
- `docs/tasks/implementation/stage-1/TASK-004-files-and-retention.md`
- `docs/tasks/implementation/stage-1/TASK-005-operations-run-execution.md`
- `docs/tasks/implementation/stage-1/TASK-006-audit-techlog-notifications.md`
- `docs/tasks/implementation/stage-1/TASK-007-wb-discounts-excel.md`
- `docs/tasks/implementation/stage-1/TASK-008-ozon-discounts-excel.md`
- `docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md`
- `docs/tasks/implementation/stage-1/TASK-010-acceptance-and-deployment.md`

## Findings

| Finding | Статус после исправления | Комментарий |
| --- | --- | --- |
| F-001 | closed_for_reaudit | Gaps сфазированы; после решений заказчика по TASK-009 открытых phase-gate gaps в `GAP_REGISTER.md` не осталось. |
| F-002 | closed_for_reaudit | Модель данных дополнена без утверждения новых бизнес-правил. |
| F-003 | closed_for_reaudit | Политика удаления/архивирования выделена и связана с профильными документами. |
| F-004 | closed_for_reaudit | UI спецификация приведена к формату §6.2. |
| F-005 | closed_for_reaudit | Ozon handoff и process rules синхронизированы. |
| F-006 | closed_for_reaudit | Audit/techlog catalog формализован. |
| F-007 | closed_for_reaudit | Acceptance gate зафиксирован; контрольные файлы не выдуманы. |
| F-008 | closed_for_reaudit | Добавлена матрица трассировки. |
| F-009 | closed_for_reaudit | Полное чтение ТЗ заменено task-scoped входным контекстом; customer escalation для spec-blocking вопросов зафиксирована. |

## Оставшиеся artifact gates

- Фактические контрольные WB/Ozon файлы не переданы.
- Checksums исходных файлов не зафиксированы.
- Результаты старой программы не переданы.
- Expected summary и expected row-level results по контрольным наборам не заполнены.
- Edge-case наборы должны быть подготовлены, но не заменяют реальные customer files.

Открытых gaps из `GAP-0002`, `GAP-0003`, `GAP-0004`, `GAP-0007`, `GAP-0008`, `GAP-0009`, `GAP-0010`, `GAP-0011`, `GAP-0012`, `GAP-0013` не осталось. TASK-009 остаётся blocked до реализации закрытых customer decisions `GAP-0010`..`GAP-0013` в текущем исправлении.

## Закрытые gaps после решений заказчика

- `GAP-0001`: closed/resolved, ADR-0006.
- `GAP-0005`: closed/resolved, ADR-0007.
- `GAP-0006`: closed/resolved, ADR-0008.
- `GAP-0002`: closed/resolved, ADR-0009.
- `GAP-0003`: closed/resolved, ADR-0010.
- `GAP-0004`: closed/resolved, ADR-0011.
- `GAP-0007`: closed/resolved, ADR-0012.
- `GAP-0008`: closed/resolved as project decision, ADR-0013; acceptance artifact gate remains.
- `GAP-0009`: closed/resolved, ADR-0014.
- `GAP-0010`: closed/resolved/customer_decision, ADR-0015.
- `GAP-0011`: closed/resolved/customer_decision, ADR-0015.
- `GAP-0012`: closed/resolved/customer_decision, ADR-0015.
- `GAP-0013`: closed/resolved/customer_decision, ADR-0015.

## Выполненные проверки

- Проверена связность новых ссылок на `docs/architecture/DELETION_ARCHIVAL_POLICY.md`, `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`, `docs/traceability/TRACEABILITY_MATRIX.md`.
- Проверено наличие Ozon rules по актуальности check и обязательных module inputs.
- Проверено наличие новых data model entities/sвязей для histories, operation files, parameter snapshots, audit/techlog links.
- Проверено отсутствие требования полного перечитывания итогового ТЗ каждым агентом на каждую задачу.
- Проверено наличие маршрута `проектировщик -> оркестратор -> заказчик` для spec-blocking вопросов после аудита.
- Проверено, что `blocks_before_any_development` больше не содержит открытых gaps.
- Проверено наличие task-scoped implementation tasks и explicit blockers для downstream gaps.
- Проверено закрытие `GAP-0002`, `GAP-0003`, `GAP-0004`, `GAP-0007`, `GAP-0008`, `GAP-0009` в GAP register и ADR.
- Проверено, что WB implementation blockers сняты, а formal acceptance оставляет только artifact gate по фактическим контрольным файлам.
- Проверено закрытие `GAP-0010`, `GAP-0011`, `GAP-0012`, `GAP-0013` в GAP register и ADR-0015.
- Проверено, что TASK-009 остаётся blocked до реализации этих customer decisions и что deferral в TASK-010 запрещён.

## Следующий рекомендуемый шаг

Передать обновлённый комплект на повторный аудит документации. После audit pass оркестратор может ставить задачи реализации платформенного каркаса и WB/Ozon modules по `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`. Formal acceptance завершается только после закрытия artifact gate: передачи и фиксации реальных customer files, checksums, результатов старой программы и expected results.
