# AUDIT_REPORT_TASK_PC_004_INTERNAL_PRODUCTS_UI.md

Дата аудита: 2026-05-01

Задача: TASK-PC-004 Internal Products UI

Статус: AUDIT PASS

## Scope

Проверены документы и task-scoped пакет:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- package TASK-PC-004 from `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-004-ui-internal-products.md`
- `docs/product/PRODUCT_CORE_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/UI_SPEC.md`
- related ADR/GAP context for ADR-0036, ADR-0041 and Stage 3 Product Core gaps

Проверены фактические изменения в зоне аудита:

- `apps/web/views.py`
- `apps/web/urls.py`
- `apps/web/forms.py`
- `apps/web/tests.py`
- `templates/web/product_list.html`
- `templates/web/product_card.html`
- `templates/web/product_form.html`
- `templates/web/variant_form.html`
- `templates/web/reference_index.html`

Related context used for access and model checks:

- `apps/product_core/models.py`
- `apps/product_core/services.py`
- `apps/identity_access/services.py`
- `apps/audit/services.py`

## Blocking Findings

Блокирующих замечаний нет.

## Passed Checks

- Internal product list is gated by `product_core.view` plus section access and shows CORE-1 required working columns: internal code, name, product type, category, variant count, visible WB/Ozon listing counts, status and updated timestamp.
- List search/filtering covers internal code/name, variant SKU/barcode/identifiers, product type, category, status and visible linked/unlinked listing state.
- Product card shows main data, variant block, access-filtered linked WB/Ozon listings, audit records where visible, and planned future blocks as explicitly non-implemented CORE-1 notes.
- Create/update/archive product flows require `product_core.create`, `product_core.update` and `product_core.archive`; successful writes create Product Core audit records.
- Variant create/update/archive flows require `product_variant.create`, `product_variant.update` and `product_variant.archive`; variant display is hidden without `product_variant.view`.
- Linked listing counts and details use `marketplace_listings_visible_to(user)`, which requires `marketplace_listing.view` on the concrete store. Hidden store listings are excluded from both counts and details.
- No hidden store listing details were found in product list/card templates. The linked/unlinked filter is based on visible links and UI wording says visible links.
- No mapping writes were found in the checked web UI scope: no `MarketplaceListing.internal_variant`, `mapping_status`, `ProductMappingHistory`, map or unmap writes are performed by PC-004 views/forms/templates.
- Future stock, production, suppliers, BOM, packaging and labels are not presented as working modules.
- Stage 1/2 Excel/API routes and operation/file/settings/admin URL entries remain present; no Product Core UI change was found that rewrites completed operations, files or legacy operation detail truth.

## Verification

Переданные интегратором результаты учтены:

- `check` OK.
- `makemigrations --check --dry-run` OK.
- `git diff --check` OK.
- общий test run по `product_core/marketplace_products/identity_access/audit/techlog/operations/web/discounts wb/ozon` - 132 tests OK.

Дополнительно аудитор запустил:

- `.venv/bin/python manage.py check` - OK.
- `git diff --check` - OK.
- `.venv/bin/python manage.py test apps.web.tests.HomeSmokeTests.test_product_list_and_card_are_store_access_aware apps.web.tests.HomeSmokeTests.test_product_card_hides_inaccessible_listing_counts_and_details apps.web.tests.HomeSmokeTests.test_internal_product_and_variant_create_update_archive_flows apps.web.tests.HomeSmokeTests.test_product_core_write_requires_permissions` - не выполнено до тестов из-за PostgreSQL authentication failure for user `promo_v2` при создании test database. Поэтому тестовый статус принят по переданному интегратором полному прогону.

## Gaps

Новых GAP не зарегистрировано. Спорных участков, требующих эскалации оркестратору/заказчику, в TASK-PC-004 scope не найдено.

## Audit Decision

TASK-PC-004 получает `AUDIT PASS`.
