# STAGE_3_PRODUCT_CORE_TRACEABILITY_MATRIX.md

Трассировка: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md` §22.

## Назначение

Traceability matrix for Stage 3.0 / CORE-1 Product Core Foundation documentation.

| Requirement | Documents | Status | ADR/GAP |
| --- | --- | --- | --- |
| Internal product/variant is company core | `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md`, `docs/product/PRODUCT_CORE_SPEC.md`, `docs/architecture/DATA_MODEL.md` | documented | ADR-0036 |
| MarketplaceListing is external store-specific layer | `docs/product/MARKETPLACE_LISTINGS_SPEC.md`, `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md` | documented | ADR-0037 |
| Manual confirmed mapping only | `docs/product/MARKETPLACE_LISTINGS_SPEC.md`, `docs/product/PRODUCT_CORE_UI_SPEC.md` | documented | ADR-0038 |
| Exact non-authoritative candidate suggestions | `docs/product/MARKETPLACE_LISTINGS_SPEC.md`, `docs/product/PRODUCT_CORE_UI_SPEC.md`, `docs/testing/STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md` | documented | ADR-0038, GAP-0023 resolved/customer_decision 2026-05-01 |
| No automatic WB/Ozon merge | `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_SCOPE.md`, `docs/product/MARKETPLACE_LISTINGS_SPEC.md` | documented | ADR-0038 |
| API sync/snapshot foundation | `docs/product/MARKETPLACE_LISTINGS_SPEC.md`, `docs/architecture/DATA_MODEL.md`, `docs/product/OPERATIONS_SPEC.md` | documented | ADR-0039 |
| Current values separated from snapshots | `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md`, `docs/product/MARKETPLACE_LISTINGS_SPEC.md` | documented | ADR-0039 |
| MarketplaceProduct migration plan | `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md` | documented | ADR-0037, ADR-0040 |
| Stage 1/2 backward compatibility | `STAGE_3_PRODUCT_CORE_SCOPE.md`, `STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md`, testing docs | documented | ADR-0040 |
| UI product/listing/mapping screens | `docs/product/PRODUCT_CORE_UI_SPEC.md` | documented | ADR-0038 |
| Permissions and object access | `docs/product/PERMISSIONS_MATRIX.md`, `docs/product/PRODUCT_CORE_UI_SPEC.md` | documented | ADR-0036..ADR-0038 |
| Audit/techlog events | `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md` | documented | ADR-0038..ADR-0040 |
| Excel boundary | `docs/product/PRODUCT_CORE_UI_SPEC.md`, `docs/product/OPERATIONS_SPEC.md` | documented | ADR-0041 |
| Task-scoped implementation packages | `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`, task files | documented | - |
| Tests and acceptance | `docs/testing/STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md`, `docs/testing/STAGE_3_PRODUCT_CORE_ACCEPTANCE_CHECKLISTS.md` | documented | - |
| Audit gate | `docs/audit/HANDOFF_STAGE_3_PRODUCT_CORE_DOCUMENTATION_TO_AUDITOR.md`, `STAGE_3_PRODUCT_CORE_DESIGN_PLAN.md` | documented | - |

## Resolved GAP Trace

`GAP-0023` is resolved by customer decision 2026-05-01, Option B. CORE-1 includes non-authoritative candidate suggestions by exact `seller_article`, `barcode` or external identifier matches only. Automatic confirmed mapping remains prohibited; user confirmation with mapping permission, audit and history is mandatory.
