# STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md

Трассировка: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md` §14; итоговое ТЗ §24, §27.

## Назначение

Test protocol for Stage 3.0 / CORE-1 Product Core Foundation.

## Test Groups

| Group | Required Checks |
| --- | --- |
| Data model | entities, fixed dictionaries, constraints, indexes, deletion/archive rules |
| Migration | `MarketplaceProduct -> MarketplaceListing` backfill, count checks, rollback/re-run safety |
| Permissions | product core rights, store-scoped listing access, owner/global/local/manager/observer seed behavior |
| UI internal products | list/card/forms, filters, counts, future hooks hidden/disabled |
| UI listings | list/card, filters, snapshot blocks, related operations/files |
| Mapping workflow | manual map/unmap, create product/variant from workflow, audit/history, no auto-merge |
| Sync snapshots | sync run status, latest cache vs immutable snapshot, failed sync behavior |
| Excel boundary | old Excel unchanged, no auto catalog growth, explicit import gated if implemented |
| Exports | access-aware exports and secret-free files |
| Stage 1 regression | WB/Ozon Excel accepted tests still pass |
| Stage 2.1 regression | WB API contracts still pass |
| Stage 2.2 regression | Ozon Elastic contracts still pass |
| Audit/techlog | action/event creation, immutable records, safe messages |
| Secret redaction | no tokens/keys/Client-Id/auth headers in unsafe surfaces |

## Minimum Test IDs

| Test ID | Scenario |
| --- | --- |
| PC-DM-001 | Create product, variant, category, identifier with fixed dictionaries |
| PC-DM-002 | Listing uniqueness and store/marketplace constraints |
| PC-DM-003 | Mapping/listing statuses reject unsupported values |
| PC-MIG-001 | Backfill all legacy products into listings with `internal_variant_id=null` |
| PC-MIG-002 | Legacy operations remain visible by `product_ref` |
| PC-MIG-003 | Rollback leaves legacy `MarketplaceProduct` intact |
| PC-PERM-001 | User without store access cannot see listing/snapshot |
| PC-PERM-002 | Internal product list does not leak hidden store listing details |
| PC-UI-001 | Internal product list/card required columns and filters |
| PC-UI-002 | Listing list/card required columns and filters |
| PC-MAP-001 | Manual map creates audit and mapping history |
| PC-MAP-002 | Manual unmap preserves old mapping in history |
| PC-MAP-003 | Candidate suggestion cannot create confirmed mapping automatically |
| PC-MAP-004 | Candidate suggestions are exact `seller_article`/`barcode`/external identifier matches only |
| PC-MAP-005 | Multiple candidates or conflicting exact matches keep/set `needs_review` or `conflict` |
| PC-SYNC-001 | Successful sync stores snapshots and updates listing cache |
| PC-SYNC-002 | Failed sync records techlog and preserves last successful values |
| PC-XLS-001 | Stage 1 Excel upload does not create internal products |
| PC-EXP-001 | Mapping report export respects object access |
| PC-SEC-001 | Secret redaction across snapshots/audit/techlog/files/reports |
| PC-REG-001 | Stage 1 WB/Ozon regression |
| PC-REG-002 | Stage 2.1 WB API regression |
| PC-REG-003 | Stage 2.2 Ozon Elastic regression |

## Result Format

```md
Test ID:
Scenario:
Input data / fixtures:
Expected:
Actual:
Status: pass / fail / blocked
Defect/GAP link:
Notes:
```

## Blocking Rules

Fail is mandatory if:

- WB/Ozon listings are auto-merged without confirmation;
- Excel creates internal products automatically;
- legacy `MarketplaceProduct` data is deleted/truncated;
- user sees listings/snapshots for inaccessible stores;
- API secrets appear in any unsafe surface;
- Stage 1/2 regression breaks without approved design change.
