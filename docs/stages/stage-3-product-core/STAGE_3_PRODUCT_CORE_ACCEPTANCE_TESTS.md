# STAGE_3_PRODUCT_CORE_ACCEPTANCE_TESTS.md

Трассировка: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md` §14, §22.

## Назначение

Документ задаёт high-level acceptance scenarios для Stage 3.0 / CORE-1. Detailed protocol and checklists are in:

- `docs/testing/STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md`
- `docs/testing/STAGE_3_PRODUCT_CORE_ACCEPTANCE_CHECKLISTS.md`

## Acceptance Scenarios

| ID | Scenario | Pass Criteria |
| --- | --- | --- |
| PC-ACC-001 | Internal product and variant exist | User with rights can create/view/update/archive internal product and variant; fixed dictionaries are enforced |
| PC-ACC-002 | Marketplace listings exist separately | WB and Ozon listings are store-specific and can exist without internal variant |
| PC-ACC-003 | One variant to many listings | One `ProductVariant` can be linked to multiple listings across stores/marketplaces |
| PC-ACC-004 | Manual mapping | User with `marketplace_listing.map` links listing to variant; audit and mapping history are created |
| PC-ACC-005 | Manual unmapping | User with `marketplace_listing.unmap` removes wrong link; audit/history preserve old link |
| PC-ACC-006 | No automatic merge | WB/Ozon are not auto-linked by title/barcode/article without user confirmation |
| PC-ACC-006A | Exact candidate suggestions | Non-authoritative candidates are shown only for exact `seller_article`, `barcode` or external identifier matches; multiple/conflicting candidates remain `needs_review` or `conflict` until user confirmation |
| PC-ACC-007 | MarketplaceProduct migration | Each legacy marketplace product becomes or is represented by a `MarketplaceListing`; legacy data remains available |
| PC-ACC-008 | Stage 1 regression | WB/Ozon Excel check/process continue to pass accepted tests |
| PC-ACC-009 | Stage 2.1 regression | WB API prices/promotions/calculation/upload contracts remain passable |
| PC-ACC-010 | Stage 2.2 regression | Ozon Elastic contracts remain passable |
| PC-ACC-011 | Snapshot foundation | Sync run and snapshot rows store source/time/run/listing safely and never store secrets |
| PC-ACC-012 | Object access | User without store access cannot see listings/snapshots/files/operations for that store |
| PC-ACC-013 | Export access | Exports do not reveal inaccessible store/listing data |
| PC-ACC-014 | Excel boundary | Existing Excel uploads do not automatically create internal products or confirmed mappings |
| PC-ACC-015 | Secret redaction | API tokens, keys, Client-Id and authorization-like values do not appear in UI/logs/audit/techlog/snapshots/files/reports |
| PC-ACC-016 | Audit gate | Implementation begins only after documentation audit pass |

## Formal Stage Exit

Stage 3.0 can be accepted only when:

- all mandatory tests in `docs/testing/STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md` pass or are explicitly blocked by a registered non-CORE artifact gate;
- all acceptance checklist items are marked pass;
- `docs/traceability/STAGE_3_PRODUCT_CORE_TRACEABILITY_MATRIX.md` has no uncovered mandatory requirements;
- there are no open spec-blocking GAP entries for the implemented slice;
- auditor report for implementation tasks is pass.
