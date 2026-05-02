# STAGE_3_PRODUCT_CORE_SCOPE.md

Трассировка: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md` §1-§6, §14-§18; итоговое ТЗ §2.4-§2.5, §7.2, §9-§12, §18, §20-§23, §25-§27.

## Назначение

Stage 3.0 / CORE-1 Product Core Foundation закладывает минимальное товарное ядро компании:

```text
InternalProduct
  -> ProductVariant
      -> MarketplaceListing для WB/Ozon в конкретном StoreAccount
      -> будущие склад, производство, поставщики, упаковка, этикетки
```

Этап не реализует ERP целиком. Его задача - отделить внутреннюю идентичность товара от внешних WB/Ozon карточек и подготовить безопасную миграцию текущего `MarketplaceProduct` в слой внешних листингов.

## Входит в CORE-1

| Блок | Обязательный результат |
| --- | --- |
| Внутренний каталог | `InternalProduct`, `ProductVariant`, `ProductCategory`, `ProductIdentifier` как минимальная модель внутренней номенклатуры |
| Внешние листинги | `MarketplaceListing` для конкретного marketplace + store/account + external identifiers |
| Связь | nullable связь `MarketplaceListing.internal_variant_id`; подтверждённая связь только вручную пользователем с правом mapping; candidate suggestions are non-authoritative exact matches only |
| Mapping statuses | `unmatched`, `matched`, `needs_review`, `conflict`, `archived` |
| Listing statuses | `active`, `not_seen_last_sync`, `inactive`, `archived`, `sync_error` |
| API sync foundation | `MarketplaceSyncRun` and snapshots for listings/prices/stocks/sales/promotions as immutable/queryable contract |
| Migration | безопасный план `MarketplaceProduct -> MarketplaceListing` без удаления legacy data and without breaking Stage 1/2 |
| UI | lists/cards for internal products, variants, listings, unmatched listings and manual mapping workflow |
| Rights | product core permissions, store-scoped listing access, separate map/unmap/export/snapshot permissions |
| Audit/techlog | audit actions for manual changes/mapping and techlog events for sync/migration failures |
| Excel boundary | existing Excel scenarios stay operational; Excel does not create internal products/variants or confirmed mappings/history; legacy compatibility sync may mirror operation refs into unmatched listing records |
| Agent readiness | task-scoped implementation tasks, reading packages, testing, traceability and audit handoff |

## Не входит в CORE-1

В CORE-1 не реализуются:

- полный складской ledger;
- закупки и supplier directory as operational module;
- production jobs, operator journals, packaging shifts;
- BOM в промышленном виде;
- label printing;
- automatic demand planning;
- margin/financial accounting;
- новые WB/Ozon API flows outside approved Stage 2.1/2.2;
- replacement of Stage 1 WB/Ozon Excel scenarios.

Будущие склад, производство, поставщики, BOM, упаковка and labels могут быть упомянуты только как architectural hooks or clearly disabled/future entry points.

## Stage Naming

Выбранное именование:

```text
docs/stages/stage-3-product-core/
docs/tasks/implementation/stage-3-product-core/
```

Конфликта с существующей stage-нумерацией нет: в репозитории есть Stage 0, Stage 1, Stage 2.1 and Stage 2.2; отдельного Stage 3 scope до этой задачи не обнаружено.

## Dependencies And Protected Invariants

- Stage 1 Excel WB/Ozon остаётся штатным режимом.
- Stage 2.1 WB API release-ready flow не меняется.
- Stage 2.2 Ozon Elastic Boosting flow не меняется.
- `Operation.type=check/process` semantics не меняются.
- `Operation.step_code` remains primary classifier for API/non-check-process steps.
- Completed operations, files, detail rows, audit and techlog remain immutable.
- `OperationDetailRow.product_ref` remains raw historical reference even after nullable FK enrichment.
- `MarketplaceProduct` cannot be deleted, truncated or silently replaced without audited migration/backup/rollback/regression plan.

## Acceptance Overview

CORE-1 documentation is acceptable only if:

- internal product/variant is the company core;
- marketplace listing is an external store-specific representation;
- WB/Ozon listings are not automatically merged;
- manual map/unmap has audit/history;
- existing Stage 1/2 workflows remain backward-compatible;
- API snapshots are source/time/run aware and secret-safe;
- Excel import into the core is explicit, confirmed and audited, or out of scope;
- implementation tasks are task-scoped and blocked until documentation audit result `AUDIT PASS`.
