# TASK-PC-008-excel-export-boundary.md

ID: TASK-PC-008  
Тип задачи: реализация Stage 3.0 / Excel export boundary  
Агент: разработчик Codex CLI  
Цель: implement Product Core exports and enforce that Excel does not auto-create internal products/variants or confirmed mappings/history; legacy compatibility sync may mirror operation refs into unmatched listing records.

## Источник Истины

- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/product/PRODUCT_CORE_SPEC.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/FILE_CONTOUR.md`

## Входные Документы

- package TASK-PC-008 from `STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`

## Разделы ТЗ Для Чтения

- task source §§5.1.9, §12

## Связанные ADR/GAP

- ADR-0041

## Разрешённые Файлы / Области Изменения

- export services/views/templates/tests for Product Core/listings/mapping reports
- UI messages for Excel boundary
- optional explicit import scaffolding only if already audited and included by orchestrator

## Запрещённые Файлы / Области Изменения

- changing existing Stage 1 Excel behavior
- auto-importing internal products/listings from Excel
- saving hidden marketplace secrets in files
- adding new Excel import workflow without diff/confirmation/audit design

## Ожидаемый Результат

- Exports for internal products, listings, unmatched listings, listing latest values and mapping report.
- Exports enforce object access.
- Existing Excel screens explicitly do not imply automatic catalog updates.

## Критерии Завершённости

- Export files reveal only permitted rows/columns.
- Internal product export does not leak hidden store data through linked listing details.
- No Excel upload path creates internal products/mappings automatically.

## Обязательные Проверки

- export access tests
- secret/redaction tests
- Stage 1 Excel regression
- UI copy/smoke check for boundary messaging

## Формат Отчёта

Report export formats, access behavior, tests, changed files and gaps.

## Получатель Результата

Оркестратор -> аудитор.

Нужен аудит: да.  
Нужны тесты: да.  
Нужен техрайтер: нет.
