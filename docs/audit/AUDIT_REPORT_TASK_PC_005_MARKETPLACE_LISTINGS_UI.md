# AUDIT_REPORT_TASK_PC_005_MARKETPLACE_LISTINGS_UI.md

Дата аудита: 2026-05-02

Задача: TASK-PC-005 Marketplace Listings UI

Статус: AUDIT PASS

## Scope

Проверены обязательные документы:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- package TASK-PC-005 from `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-005-ui-marketplace-listings.md`
- `docs/product/MARKETPLACE_LISTINGS_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/product/OPERATIONS_SPEC.md`
- related GAP/ADR context from `docs/gaps/GAP_REGISTER.md` and `docs/adr/ADR_LOG.md`

Проверены фактические изменения в указанном re-audit scope:

- `apps/web/urls.py`
- `apps/web/views.py`
- `apps/web/tests.py`
- `templates/web/legacy_product_list.html`
- `templates/web/legacy_product_card.html`
- `templates/web/marketplace_listing_list.html`
- `templates/web/marketplace_listing_card.html`
- `templates/web/product_list.html`
- `templates/web/product_card.html`
- `templates/web/product_form.html`
- `templates/web/variant_form.html`
- `templates/web/reference_index.html`

Дополнительно read-only проверены связанные helpers/models для оценки object access и legacy compatibility:

- `apps/marketplace_products/services.py`
- `apps/product_core/services.py`

## Re-audit Notes

Повторная проверка выполнена после исправления BLOCKER-01 из первого аудита.

BLOCKER-01 закрыт:

- `apps/web/urls.py:31`-`32` сохраняет legacy route names `web:product_list` и `web:product_card` на `references/products/` and `references/products/<int:pk>/`.
- `apps/web/views.py:2359`-`2388` снова реализует `product_list` поверх legacy `MarketplaceProduct` через `products_visible_to(request.user)`.
- `apps/web/views.py:2392`-`2412` снова реализует `product_card` через `get_object_or_404(products_visible_to(request.user), pk=pk)`, то есть collision with `InternalProduct.pk` no longer returns an internal product card.
- `templates/web/legacy_product_list.html` and `templates/web/legacy_product_card.html` render the legacy product list/card and keep legacy links through `web:product_card`.
- `apps/web/tests.py:808`-`836` adds a regression where `MarketplaceProduct.pk` collides with `InternalProduct.pk`; the test asserts that legacy list/card show `MarketplaceProduct` data and do not show the colliding `InternalProduct`.

Product Core UI remains reachable on explicit new routes:

- `apps/web/urls.py:33`-`45` exposes `web:internal_product_list/create/card/update/archive` under `references/product-core/products/`.
- `apps/web/urls.py:58`-`70` exposes variant create/update/archive under the same Product Core route prefix.
- Product Core templates link to `web:internal_product_*`, not to legacy `web:product_*`.
- `templates/web/reference_index.html` links implemented Product Core navigation to `web:internal_product_list`.

Marketplace Listings UI remains within TASK-PC-005 boundaries:

- List/card access is store-scoped through `marketplace_listings_visible_to(request.user)` and concrete `marketplace_listing.view` checks.
- Hidden listing card access is blocked through `get_object_or_404(marketplace_listings_visible_to(...), pk=pk)`.
- Snapshot summary/list price-stock visibility remains guarded by `marketplace_snapshot.view`; raw-safe details remain guarded by `marketplace_snapshot.technical_view` and rendered in collapsed `<details>`.
- Listing list/card templates still include required columns/blocks: marketplace, store/account, external identifiers, article, barcode, title, brand, category, listing status, mapping status, linked internal variant, latest price/stock/sync/source, snapshot tables, listing history, mapping history, related operations and files.

Forbidden scope checks:

- No manual map/unmap writes were found in the checked TASK-PC-005 views/forms/templates. Mapping is represented as filter/status display and TASK-PC-006 placeholder badges/links only.
- No new marketplace listings API sync flow or sync POST route was found in the checked listing UI. Sync is represented as a separate workflow placeholder/badge.
- Legacy `MarketplaceProduct` model/table remains in use for compatibility and is not deleted/truncated by the checked changes.

## Verification

Переданные исполнителем результаты учтены:

- `check` OK.
- `makemigrations --check --dry-run` OK.
- `git diff --check` OK.
- `tests apps.web apps.product_core apps.marketplace_products apps.identity_access apps.operations` - 94 tests OK.

Аудитор дополнительно выполнил:

- `sed`, `nl`, `rg`, `git status`, `git diff` inspection по re-audit scope.
- `.venv/bin/python manage.py check` - OK, `System check identified no issues`.
- Targeted `rg` checks for mapping writes, sync/API flow additions, Product Core route names and legacy route compatibility.

Аудитор попытался выполнить targeted Django tests:

```text
.venv/bin/python manage.py test apps.web.tests.HomeSmokeTests.test_legacy_product_list_and_card_keep_stage_1_route_compatibility apps.web.tests.HomeSmokeTests.test_internal_product_list_and_card_are_store_access_aware apps.web.tests.HomeSmokeTests.test_marketplace_listing_list_filters_and_enforces_store_access apps.web.tests.HomeSmokeTests.test_marketplace_listing_card_hides_raw_safe_without_technical_permission
```

Локальный запуск тестов не стартовал из-за инфраструктурной ошибки PostgreSQL authentication failure for user `promo_v2` при создании test database. Поэтому тестовый статус принят по переданному исполнителем полному прогону и подтверждён read-only inspection.

## Gaps

Новых GAP не зарегистрировано. Исправление использует уже утверждённое требование TASK-PC-005 о legacy route compatibility and does not require a new business/UX decision.

## Audit Decision

TASK-PC-005 Marketplace Listings UI passes re-audit. BLOCKER-01 is closed, and no new blockers were found in the checked scope.
