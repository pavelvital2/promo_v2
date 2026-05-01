# TASK-PC-004-ui-internal-products.md

ID: TASK-PC-004  
Тип задачи: реализация Stage 3.0 / UI internal products  
Агент: разработчик Codex CLI  
Цель: implement access-aware internal products and variants UI.

## Источник Истины

- `docs/product/PRODUCT_CORE_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`

## Входные Документы

- package TASK-PC-004 from `STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- existing UI conventions in `docs/product/UI_SPEC.md`

## Разделы ТЗ Для Чтения

- task source §§5.1.6, §9.1-§9.3

## Связанные ADR/GAP

- ADR-0036
- ADR-0041

## Разрешённые Файлы / Области Изменения

- product core views/forms/templates/urls/tests
- navigation entries for implemented product core screens
- minimal service/query helpers for internal product UI

## Запрещённые Файлы / Области Изменения

- marketplace listing mapping writes
- future warehouse/production/supplier/label modules
- Stage 1/2 Excel/API screens except navigation link consistency

## Ожидаемый Результат

- Internal product list/card.
- Variant list/card blocks under product card.
- Access-aware linked listing counts/details.
- Create/update/archive flows according to permissions.

## Критерии Завершённости

- User without rights cannot view/edit.
- Hidden store listing data is not leaked via counts/details.
- Future hooks do not look implemented.

## Обязательные Проверки

- UI tests for list/card/forms
- permission tests
- responsive/readability smoke where project UI tests support it

## Формат Отчёта

Report screens, routes, permissions, tests, screenshots if used, gaps.

## Получатель Результата

Оркестратор -> аудитор.

Нужен аудит: да.  
Нужны тесты: да.  
Нужен техрайтер: нет.

