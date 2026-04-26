# IMPLEMENTATION_TASKS.md

Трассировка: ТЗ §3, §25-§27.

## Назначение

Индекс фиксирует практический порядок задач реализации этапа 1 для будущих агентов Codex CLI. Реализация стартует только после повторного аудита документации и при соблюдении phase gates из `docs/gaps/GAP_REGISTER.md`.

Задачи не требуют от агента полного перечитывания итогового ТЗ. Оркестратор выдаёт task-scoped context: файл задачи, `AGENTS.md`, указанные документы, связанные ADR/GAP и только перечисленные разделы ТЗ.

## Утверждённые решения перед реализацией

- Стек этапа 1: Django + PostgreSQL + server-rendered UI / Django templates. См. ADR-0006.
- Seed-набор ролей: консервативный набор из `docs/product/PERMISSIONS_MATRIX.md`. См. ADR-0007.
- Visible identifiers: `OP-YYYY-NNNNNN`, `RUN-YYYY-NNNNNN`, `FILE-YYYY-NNNNNN`, `STORE-NNNNNN`, `USR-NNNNNN`. См. ADR-0008.
- WB system defaults: `wb_threshold_percent = 70`, `wb_fallback_over_threshold_percent = 55`, `wb_fallback_no_promo_percent = 55`. См. ADR-0009.
- WB reason/result codes: минимальный закрытый перечень из `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`. См. ADR-0010.
- WB out-of-range final discount: row error `wb_discount_out_of_range`, check с ошибками, process запрещён. См. ADR-0011.
- Backup policy: daily PostgreSQL + daily server file storage backup, retention 14 days, mandatory backup before production update, manual restore check after setup and before important releases. См. ADR-0012.
- Acceptance control files: проектное решение закрыто, но фактические customer files/checksums/expected results остаются artifact gate. См. ADR-0013.
- Audit/techlog retention: 90 days, cleanup only by regulated non-UI procedure. См. ADR-0014.
- TASK-009 customer decisions from 2026-04-25: `GAP-0010` product backend/list/card, `GAP-0011` WB store parameter write-flow with history/audit, `GAP-0012` draft run context, `GAP-0013` admin write-flow. См. ADR-0015 и `docs/gaps/GAP_REGISTER.md`.

## Открытые gates

| Gate | Gaps | Влияние |
| --- | --- | --- |
| blocks_before_module_implementation | нет открытых | WB settings/WB discounts implementation разрешена после audit pass документации |
| blocks_before_acceptance/production | нет открытых GAP | production readiness policy утверждена; formal acceptance остаётся заблокированной artifact gate до передачи customer контрольных файлов, checksums и expected results; TASK-009 дополнительно blocked до реализации customer decisions `GAP-0010`..`GAP-0013` в самом TASK-009 |

## Порядок задач

| Порядок | Задача | Назначение | Зависимости | Blockers |
| --- | --- | --- | --- | --- |
| 1 | `docs/tasks/implementation/stage-1/TASK-001-project-bootstrap.md` | Django bootstrap, базовая структура, test/deploy skeleton | повторный аудит документации | нет |
| 2 | `docs/tasks/implementation/stage-1/TASK-002-auth-users-roles-permissions.md` | auth, пользователи, роли, права, object access, seed | TASK-001 | нет |
| 3 | `docs/tasks/implementation/stage-1/TASK-003-stores-cabinets-connections.md` | магазины/кабинеты, группы, API-блок этапа 2, история | TASK-002 | нет |
| 4 | `docs/tasks/implementation/stage-1/TASK-004-files-and-retention.md` | file metadata, versions, storage, retention and download rights | TASK-002, TASK-003 | нет |
| 5 | `docs/tasks/implementation/stage-1/TASK-005-operations-run-execution.md` | operation/run, statuses, check/process orchestration shell | TASK-002, TASK-003, TASK-004 | нет |
| 6 | `docs/tasks/implementation/stage-1/TASK-006-audit-techlog-notifications.md` | audit, techlog, notifications, sensitive visibility | TASK-002, TASK-005 | нет |
| 7 | `docs/tasks/implementation/stage-1/TASK-007-wb-discounts-excel.md` | WB Excel check/process | TASK-002..TASK-006 | нет |
| 8 | `docs/tasks/implementation/stage-1/TASK-008-ozon-discounts-excel.md` | Ozon Excel check/process | TASK-002..TASK-006 | artifact gate только для formal acceptance |
| 9 | `docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md` | server-rendered screens and workflows, including approved TASK-009 backend/service pieces | TASK-002..TASK-008 as available | blocked until `GAP-0010` product backend/list/card, `GAP-0011` WB store parameter write-flow with history/audit, `GAP-0012` draft run context and `GAP-0013` admin write-flow are implemented; no deferral to TASK-010 |
| 10 | `docs/tasks/implementation/stage-1/TASK-010-acceptance-and-deployment.md` | acceptance, release, backup/restore, deployment readiness | TASK-001..TASK-009 | artifact gate для customer control files |

## Общие правила для всех задач

- Не писать API-режим скидок вместо Excel-режима этапа 1.
- Не менять WB/Ozon бизнес-логику, порядок правил, check/process split, файловую версионность, модель прав, audit/techlog separation.
- Не менять решения `GAP-0002`, `GAP-0003`, `GAP-0004`, `GAP-0007`, `GAP-0008`, `GAP-0009` без нового утверждённого ADR/документационного изменения.
- Не переносить customer decisions `GAP-0010`, `GAP-0011`, `GAP-0012`, `GAP-0013` из TASK-009 в TASK-010; status/read-only substitutes для этих решений не считаются выполнением TASK-009.
- Если задача упирается в новый открытый gap или отсутствующий artifact, агент останавливает спорный участок, фиксирует blocked handoff и передаёт вопрос оркестратору.
- Связанная документация обновляется по `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`.
- Результат передаётся аудитору по `docs/audit/AUDIT_PROTOCOL.md` и проверяется по `docs/testing/TEST_PROTOCOL.md` / `docs/testing/ACCEPTANCE_CHECKLISTS.md`.
