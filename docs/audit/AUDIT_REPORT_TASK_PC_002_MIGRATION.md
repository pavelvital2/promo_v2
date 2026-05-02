# AUDIT_REPORT_TASK_PC_002_MIGRATION.md

Дата аудита: 2026-05-01

Задача: TASK-PC-002 MarketplaceProduct Migration

Статус: AUDIT PASS

## Scope

Проверены документы и task-scoped пакет:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-002-migration.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/DELETION_ARCHIVAL_POLICY.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Проверены фактические изменения в зоне аудита:

- `apps/product_core/migrations/0002_backfill_legacy_marketplace_products.py`
- `apps/marketplace_products/services.py`
- `apps/marketplace_products/tests.py`
- `apps/discounts/wb_api/prices/services.py`
- related Product Core model context in `apps/product_core/models.py`
- related `OperationDetailRow.product_ref` model context in `apps/operations/models.py`

## Blocking Findings

Блокирующих замечаний нет.

## Passed Checks

- Backfill migration uses option B from ADR-0037: copies legacy `MarketplaceProduct` data into `MarketplaceListing` and does not delete, truncate or rename legacy product rows.
- Migration reverse is explicit noop: `migrations.RunPython(_forward_backfill, migrations.RunPython.noop)`. Legacy `MarketplaceProduct` remains authoritative for rollback of old Stage 1/2 flows.
- Backfilled listings keep `internal_variant_id = NULL` and `mapping_status = unmatched`; no `InternalProduct` or `ProductVariant` is created from legacy products.
- `OperationDetailRow.product_ref` model remains raw `CharField`; TASK-PC-002 changes do not add a FK rewrite migration and the compatibility service test verifies `product_ref` remains unchanged.
- Stage 1/2 calculation logic is not changed by this task. The WB API prices touchpoint only calls `sync_listing_from_legacy_product(product)` after the existing legacy product sync.
- Compatibility helper maps legacy fields to listing fields, writes `ListingHistory`, is rerunnable through `get_or_create`, and keeps listing mapping unconfirmed.
- Validation helper reports legacy count, missing listing product ids and products whose matched/internal mapping would violate the migration contract.
- No audit/techlog/API secret storage changes were found in TASK-PC-002 scope.

## Verification

Переданные интегратором результаты учтены:

- `check` OK.
- `makemigrations --check --dry-run` OK.
- `git diff --check` OK.
- 89 tests OK for `apps.product_core apps.marketplace_products apps.identity_access apps.audit apps.techlog apps.operations apps.discounts.wb_excel apps.discounts.ozon_excel apps.discounts.wb_api.prices`.

Дополнительно аудитор запустил:

- `.venv/bin/python manage.py check` - OK.
- `.venv/bin/python manage.py makemigrations --check --dry-run` - OK, no changes detected; команда вывела warning о невозможности проверки migration history из-за PostgreSQL authentication failure for user `promo_v2`.
- `git diff --check` - OK.
- `.venv/bin/python manage.py test apps.marketplace_products apps.product_core` - не выполнено до тестов из-за PostgreSQL authentication failure for user `promo_v2` при создании test database. Поэтому тестовый статус принят по переданному интегратором прогону.

## Gaps

Новых GAP не зарегистрировано. Спорных участков, требующих эскалации оркестратору/заказчику, в TASK-PC-002 scope не найдено.

## Audit Decision

TASK-PC-002 получает `AUDIT PASS`.
