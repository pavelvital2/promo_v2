# TASK-PC-001-data-model.md

ID: TASK-PC-001  
Тип задачи: реализация Stage 3.0 / data model foundation  
Агент: разработчик Codex CLI  
Цель: create Product Core and Marketplace Listing data model foundation.

## Источник Истины

- `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md`
- `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/PRODUCT_CORE_SPEC.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`

## Входные Документы

- common package from `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/adr/ADR_LOG.md`
- `docs/gaps/GAP_REGISTER.md`

## Разделы ТЗ Для Чтения

- task source §§5.1.1-5.1.4, §7, §10
- final TZ §9 only if orchestrator asks for source verification

## Связанные ADR/GAP

- ADR-0036..ADR-0041 after documentation audit
- `GAP-0023` resolved/customer_decision 2026-05-01; candidate suggestion behavior is not implemented in this base model task

## Разрешённые Файлы / Области Изменения

- new/updated product core app models, migrations, admin minimal registration if project convention requires
- `apps/marketplace_products/` only for adding new listing models or compatibility references
- model tests for new entities
- documentation if implementation reveals non-behavioral naming correction

## Запрещённые Файлы / Области Изменения

- Stage 1/2 business calculation services
- Excel workbook writers/parsers
- API upload behavior
- UI mapping workflow
- deletion of legacy `MarketplaceProduct`

## Ожидаемый Результат

- Models/dictionaries for internal products, variants, identifiers, listings, sync runs, snapshots and histories.
- Constraints/indexes matching `docs/architecture/DATA_MODEL.md`.
- No automatic mapping or data backfill in this task.

## Критерии Завершённости

- `manage.py makemigrations --check` is clean after committed migrations.
- New model tests pass.
- System dictionaries are fixed and not user-editable.
- No existing Stage 1/2 tests fail because of model import changes.

## Обязательные Проверки

- `python manage.py check`
- focused model tests
- relevant existing tests for operations/marketplace products if imports changed

## Формат Отчёта

Report changed files, migrations, tests, used docs, covered requirements, gaps/questions, and next audit target.

## Получатель Результата

Оркестратор -> аудитор.

Нужен аудит: да.  
Нужны тесты: да.  
Нужен техрайтер: нет.
