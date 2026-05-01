# TASK-PC-005-ui-marketplace-listings.md

ID: TASK-PC-005  
Тип задачи: реализация Stage 3.0 / UI marketplace listings  
Агент: разработчик Codex CLI  
Цель: implement access-aware marketplace listings list/card UI.

## Источник Истины

- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`

## Входные Документы

- package TASK-PC-005 from `STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- `docs/product/OPERATIONS_SPEC.md`

## Разделы ТЗ Для Чтения

- task source §§5.1.6, §9.4-§9.5

## Связанные ADR/GAP

- ADR-0037
- ADR-0039

## Разрешённые Файлы / Области Изменения

- listing views/forms/templates/urls/tests
- product/listing navigation for implemented screens
- read-only snapshot summaries in listing card

## Запрещённые Файлы / Области Изменения

- manual mapping writes except links to mapping task
- new API synchronization flows
- legacy `MarketplaceProduct` deletion

## Ожидаемый Результат

- Listings table with required columns, filters, search and pagination.
- Listing card with identifiers, status, mapping status, snapshots, history, related operations/files.
- Object access enforced.

## Критерии Завершённости

- User sees only listings from accessible stores.
- Technical raw-safe details are hidden without technical view permission.
- Existing Stage 1/2 product card route either remains compatible or has documented redirect.

## Обязательные Проверки

- UI/access tests
- snapshot visibility tests
- Stage 1/2 web regression around old product references

## Формат Отчёта

Report screens, filters, access checks, changed files, tests and gaps.

## Получатель Результата

Оркестратор -> аудитор.

Нужен аудит: да.  
Нужны тесты: да.  
Нужен техрайтер: нет.

