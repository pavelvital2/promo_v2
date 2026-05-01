# TASK-PC-003-listings-sync-foundation.md

ID: TASK-PC-003  
Тип задачи: реализация Stage 3.0 / sync foundation  
Агент: разработчик Codex CLI  
Цель: implement safe sync run and snapshot foundation for marketplace listings.

## Источник Истины

- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`

## Входные Документы

- package TASK-PC-003 from `STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- Stage 2.1/2.2 API specs only for integration points already implemented

## Разделы ТЗ Для Чтения

- task source §§5.1.4, §7.7-§7.12, §8

## Связанные ADR/GAP

- ADR-0039
- ADR-0040

## Разрешённые Файлы / Области Изменения

- sync/snapshot models/services created in TASK-PC-001 area
- adapters from already approved Stage 2.1/2.2 operations to snapshots
- tests and safe fixtures/mocks

## Запрещённые Файлы / Области Изменения

- adding new marketplace API business flows outside approved scope
- changing WB/Ozon calculation/upload rules
- storing secrets in snapshots
- scheduling automatic background sync as mandatory production feature

## Ожидаемый Результат

- Manual sync foundation and future scheduling contract.
- Snapshots linked to listing, sync run and operation where available.
- Latest listing cache updated from successful syncs only.

## Критерии Завершённости

- Failed sync keeps last successful values visible with clear status.
- Same store/marketplace/sync type duplicate launch is guarded.
- Raw-safe policy is tested.

## Обязательные Проверки

- unit tests for sync status transitions
- secret redaction tests
- integration test linking snapshots to operations/listings

## Формат Отчёта

List source adapters, snapshot entities, tests, secret-safety evidence and gaps.

## Получатель Результата

Оркестратор -> аудитор.

Нужен аудит: да.  
Нужны тесты: да.  
Нужен техрайтер: нет.

