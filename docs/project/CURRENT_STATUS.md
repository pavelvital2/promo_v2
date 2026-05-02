# CURRENT_STATUS.md

Дата актуализации: 2026-05-02.

Назначение: короткий статус проекта для входа в работу перед постановкой следующего этапа.

## Реализовано

- Stage 1 Excel workflows WB/Ozon.
- Stage 2.1 WB API flow.
- Stage 2.2 Ozon Elastic API flow.
- Stage 3.0 / CORE-1 Product Core Foundation, accepted for release validation as `PASS WITH NOTES`.
- Пользователи, роли, права и object access.
- Магазины, кабинеты, API connection records.
- Операции, файлы, audit trail, techlog.
- Product Core:
  - internal products;
  - variants;
  - marketplace listings;
  - snapshot foundation;
  - manual mapping workflow;
  - CSV exports.

## Документация подготовлена

- Stage 3 / CORE-2 Product Core Integration design documentation prepared in `docs/stages/stage-3-product-core/core-2/`; CORE-2 product implementation is not started and remains blocked until documentation audit.

## Принятые ограничения

- WB auto promotions по текущему WB API не дают product rows через `promotions/nomenclatures`; система не должна выдумывать состав автоакций.
- Excel остаётся операционным входом/выходом и не создаёт автоматически `InternalProduct`, `ProductVariant` или confirmed mappings.
- Legacy `MarketplaceProduct` сохраняется для совместимости.
- Полная складская, производственная, закупочная и этикеточная логика ещё не реализована.
- CORE-1 release validation notes: local env was not independently certified as staging/production-like; live destructive WB/Ozon uploads were not executed; manual Playwright/browser smoke was not performed; the single `pre_update_backup.sh` wrapper was not run, while underlying backup/restore scripts were verified.

## Ключевые документы статуса

- `README.md`
- `docs/reports/STAGE_2_1_WB_RELEASE_READINESS.md`
- `docs/testing/TASK-026_STAGE_2_2_ACCEPTANCE_REPORT.md`
- `docs/testing/TEST_REPORT_TASK_PC_009_STAGE_3_ACCEPTANCE.md`
- `docs/audit/AUDIT_REPORT_TASK_PC_010_DOCS_RUNBOOK.md`
- `docs/reports/STAGE_3_PRODUCT_CORE_IMPLEMENTATION_REPORT.md`
- `docs/testing/TEST_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md`
- `docs/audit/AUDIT_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md`
- `docs/reports/CORE_1_RELEASE_VALIDATION_REPORT.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_DESIGN_HANDOFF.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_ACCEPTANCE_CHECKLIST.md`
- `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md`

## Следующий этап

CORE-2 design package is prepared from `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` and is ready for documentation audit.

CORE-2 implementation remains prohibited until this design documentation is accepted by audit-gate as `AUDIT PASS` and the affected `GAP-CORE2-001`..`GAP-CORE2-005` decisions are resolved or explicitly excluded from task scope.

Рабочее направление после Stage 3: перевод дальнейших операций вокруг справочника товаров/Product Core. Склад, производство, поставщики, упаковка, этикетки и расширенная аналитика должны вводиться отдельными этапами, без расширения scope по умолчанию.

## Правило для новых задач

Перед реализацией:

1. оркестратор формирует task-scoped пакет;
2. проектировщик готовит/обновляет исполнительную документацию;
3. аудитор даёт `AUDIT PASS`;
4. разработчики получают только профильные документы и конкретные задачи.
