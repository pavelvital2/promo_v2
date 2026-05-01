# TASK-PC-006-mapping-workflow.md

ID: TASK-PC-006  
Тип задачи: реализация Stage 3.0 / mapping workflow  
Агент: разработчик Codex CLI  
Цель: implement manual map/unmap workflow between `MarketplaceListing` and `ProductVariant`, including non-authoritative exact-match candidate suggestions.

## Источник Истины

- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`

## Входные Документы

- package TASK-PC-006 from `STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- resolved `docs/gaps/GAP_REGISTER.md` entry `GAP-0023`

## Разделы ТЗ Для Чтения

- task source §§5.1.3, §6.2, §9.6, §19.3

## Связанные ADR/GAP

- ADR-0038
- `GAP-0023` resolved/customer_decision 2026-05-01: Option B exact-match non-authoritative candidates are allowed

## Разрешённые Файлы / Области Изменения

- mapping views/forms/services/templates/tests
- mapping history/audit writes
- listing mapping fields/status updates
- non-authoritative candidate suggestions by exact `seller_article`, `barcode` or external identifier matches

## Запрещённые Файлы / Области Изменения

- automatic confirmed mapping
- WB/Ozon merge by title/barcode/article without explicit user confirmation
- fuzzy/title/partial-article candidate suggestion algorithm in CORE-1
- creating `matched` from any suggestion without explicit user confirmation, audit and history
- historical operation row rewrites

## Ожидаемый Результат

- User can manually link/unlink listings and variants.
- User can create product+variant or variant under existing product from mapping workflow.
- User can see non-authoritative exact-match candidates where present.
- Audit and `ProductMappingHistory` are written.

## Критерии Завершённости

- `matched` requires explicit user action.
- Unmap preserves previous mapping in history.
- Object access to listing store and mapping permission are both enforced.
- Candidate suggestions are exact-match only, visibly non-authoritative, and never create confirmed mapping automatically.
- Multiple candidates or conflicting exact matches produce/retain `needs_review` or `conflict` until the user resolves them.

## Обязательные Проверки

- mapping permission tests
- map/unmap history tests
- conflict/needs_review status tests
- exact-match candidate suggestion tests
- no auto-confirmed mapping from suggestion tests
- audit action tests

## Формат Отчёта

Report workflow behavior, resolved GAP-0023 rule handling, tests, changed files and audit handoff.

## Получатель Результата

Оркестратор -> аудитор.

Нужен аудит: да.  
Нужны тесты: да.  
Нужен техрайтер: нет.
