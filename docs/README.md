# Документация проекта

Точка входа в исполнительную проектную документацию платформы marketplace-операций WB/Ozon.

Источник истины: `itogovoe_tz_platforma_marketplace_codex.txt`, редакция от 25.04.2026. Исполнительная документация в `docs/` перерабатывает ТЗ в рабочие спецификации, но не заменяет его. Полное чтение ТЗ агентами по умолчанию запрещено; оркестратор выдаёт task-scoped пакет и конкретные разделы ТЗ.

## Быстрый маршрут чтения

1. Прочитать корневой `AGENTS.md`.
2. Прочитать `docs/PROJECT_NAVIGATOR.md`.
3. Прочитать `docs/orchestration/AGENTS.md`.
4. Найти свой пакет в `docs/roles/READING_PACKAGES.md`.
5. Читать только документы из задачи/пакета и связанные записи `docs/gaps/GAP_REGISTER.md` / `docs/adr/ADR_LOG.md`.
6. При споре или критичном требовании аудитор сверяет с исходным ТЗ.

## Каталоги

| Каталог | Назначение | Владелец |
| --- | --- | --- |
| `docs/source/` | Ссылки на исходное ТЗ и стартовый prompt | Оркестратор, аудитор |
| `docs/project/` | Текущий статус, глоссарий и project-level навигация | Оркестратор, техрайтер |
| `docs/orchestration/` | Правила агентов, оркестрация, шаблоны, handoff, parallel rules, documentation protocol | Оркестратор |
| `docs/roles/` | Матрица ролей и пакеты чтения | Оркестратор |
| `docs/architecture/` | Архитектура, модель данных, файловый контур, audit/techlog, структура проекта, удаление/архивация | Проектировщик архитектуры |
| `docs/product/` | UI, права, операции, WB/Ozon Excel specs, модульные спецификации | Проектировщик продукта |
| `docs/stages/stage-1/` | План документации и приёмочные тесты этапа 1 | Оркестратор этапа 1 |
| `docs/stages/stage-2/` | Scope и приёмочные документы Stage 2.1 WB API | Оркестратор этапа 2 |
| `docs/stages/stage-3-product-core/` | Scope, migration, audit gate and reading packages CORE-1 Product Core Foundation | Оркестратор этапа 3 |
| `docs/tasks/implementation/stage-1/` | Задачи реализации этапа 1 | Оркестратор реализации |
| `docs/tasks/implementation/stage-2/` | Task-scoped задачи реализации Stage 2.1 WB API | Оркестратор реализации |
| `docs/tasks/implementation/stage-0/` | Task-scoped пакеты будущей UI-реализации Stage 0 | Оркестратор реализации |
| `docs/tasks/implementation/stage-3-product-core/` | Task-scoped задачи реализации CORE-1 Product Core Foundation | Оркестратор реализации |
| `docs/tasks/implementation/documentation/` | Документационные задачи по навигации, структуре и handoff | Оркестратор, техрайтер |
| `docs/gaps/` | Реестр gaps | Оркестратор, проектировщик |
| `docs/adr/` | Журнал архитектурных решений | Проектировщик архитектуры |
| `docs/audit/` | Audit protocol и отчёты аудита | Аудитор |
| `docs/reports/` | Отчёты проектировщиков и служебные отчёты | Автор отчёта, оркестратор |
| `docs/testing/` | Test protocol и acceptance checklists | Тестировщик |
| `docs/operations/` | Release/update/deployment runbooks | DevOps/эксплуатационный агент |
| `docs/traceability/` | Матрица трассировки требований | Аудитор, проектировщик |

Подробная карта документов: `docs/DOCUMENTATION_MAP.md`.

## Правила эскалации

- UX/functionality gaps веб-панели: агент -> оркестратор -> заказчик.
- Spec-blocking gaps: агент -> оркестратор -> заказчик.
- Аудитор сверяет проектную документацию с исходным ТЗ.
- Исполнители работают по утверждённой исполнительной документации и task-scoped пакетам.
- Закрытые решения по `GAP-0002`, `GAP-0003`, `GAP-0004`, `GAP-0007`, `GAP-0008`, `GAP-0009` не изменяются предположениями; для `GAP-0008` real WB/Ozon comparison artifact gate закрыт 2026-04-26 в `docs/testing/CONTROL_FILE_REGISTRY.md`.
- Stage 2.1 WB API исполняется только по task-scoped пакету Stage 2.1; Ozon API Stage 2.2 не смешивается с этими задачами.
- Stage 0 UI Ozon Elastic исполняется только после аудита проектной документации и по пакету `docs/tasks/implementation/stage-0/OZON_ELASTIC_UI_READING_PACKAGE.md`.
- Stage 3.0 CORE-1 Product Core исполняется только после audit pass документации по `docs/audit/HANDOFF_STAGE_3_PRODUCT_CORE_DOCUMENTATION_TO_AUDITOR.md` and task-scoped packages in `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`.
- На 2026-05-02 Stage 3.0 CORE-1 Product Core release validation accepted as PASS WITH NOTES in `docs/reports/CORE_1_RELEASE_VALIDATION_REPORT.md`; CORE-2 design documentation has audit/recheck PASS and post-audit customer decisions for `GAP-CORE2-001`..`GAP-CORE2-005` are recorded. CORE-2 implementation still requires follow-up audit/recheck of the updated docs and a separate task-scoped implementation assignment.
