# TASK-PC-007-permissions-audit-techlog.md

ID: TASK-PC-007  
Тип задачи: реализация Stage 3.0 / permissions audit techlog  
Агент: разработчик Codex CLI  
Цель: implement Product Core permissions, audit actions, techlog events and history enforcement.

## Источник Истины

- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/architecture/DATA_MODEL.md`

## Входные Документы

- package TASK-PC-007 from `STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- `docs/product/OPERATIONS_SPEC.md`

## Разделы ТЗ Для Чтения

- task source §§5.1.7-5.1.8, §10-§11

## Связанные ADR/GAP

- ADR-0036..ADR-0041

## Разрешённые Файлы / Области Изменения

- permission seed/catalog changes
- access service checks
- audit/techlog catalogs and creation helpers
- tests

## Запрещённые Файлы / Области Изменения

- owner/admin protections weakening
- bypassing store object access for listings/snapshots
- adding sensitive data to audit/techlog
- changing Stage 1/2 permission semantics except additive Product Core rights

## Ожидаемый Результат

- Product Core permissions are seeded/documented.
- Manual changes and mapping emit audit/history.
- Sync/migration failures emit safe techlog events.
- Snapshot technical view permission is enforced.

## Критерии Завершённости

- Owner has full rights.
- Global/local admin/manager/observer seed behavior follows matrix.
- Direct user deny still wins.
- Store access blocks listings/snapshots.

## Обязательные Проверки

- permission matrix tests
- audit/techlog creation tests
- secret redaction tests
- object access tests

## Формат Отчёта

Report permission codes, seed changes, audit/techlog evidence, tests and gaps.

## Получатель Результата

Оркестратор -> аудитор.

Нужен аудит: да.  
Нужны тесты: да.  
Нужен техрайтер: нет.

