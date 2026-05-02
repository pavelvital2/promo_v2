# CORE_2_ACCEPTANCE_CHECKLIST.md

Статус: исполнительная проектная документация CORE-2, обновлена после AUDIT PASS по решениям заказчика; `TASK-PC2-002` closed / ready for commit after test and audit PASS. Full CORE-2 remains in progress and is not release-complete.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§14-16, §11.13.

## Documentation Audit Checklist

| Criterion | PASS/FAIL |
| --- | --- |
| All TZ §3.2 CORE-2 documents exist. |  |
| Scope and non-scope protect Stage 1/2 and future ERP boundary. |  |
| ADR-0042..ADR-0046 are recorded. |  |
| GAP-CORE2-001..005 decisions and remaining implementation constraints are recorded and not hidden as assumptions. |  |
| API endpoints are limited to approved current sources or endpoint-specific official read-only docs evidence; no marketplace writes in CORE-2. |  |
| ProductVariant auto-create follows customer-approved imported/draft policy and fixed internal SKU validator. |  |
| `product_ref` immutability is explicit. |  |
| Nullable FK enrichment is reversible and non-destructive. |  |
| Snapshot semantics and future-only sales/buyouts/returns/demand/in-work/production/shipments hooks are explicit. |  |
| UI spec excludes warehouse/production/suppliers/BOM/packaging/labels/machine vision. |  |
| Permissions/object access/redaction are specified. |  |
| Test plan includes Stage 1/2 and Product Core regression. |  |
| Agent tasks include reading packages, prohibited changes, tests and audit criteria. |  |
| Rollout runbook includes backup/validation/rollback/post-deploy checks. |  |

## Implementation Acceptance Checklist

### Task Closeout Status

| Task | Status | Evidence |
| --- | --- | --- |
| `TASK-PC2-002 Marketplace Listing Sync Integration` | CLOSED / READY FOR COMMIT | Test PASS in `docs/testing/TEST_REPORT_TASK_PC2_002_MARKETPLACE_LISTING_SYNC.md`; audit PASS in `docs/audit/AUDIT_REPORT_TASK_PC2_002_MARKETPLACE_LISTING_SYNC.md`; closeout report in `docs/reports/TASK_PC2_002_MARKETPLACE_LISTING_SYNC_REPORT.md`. |

Only `TASK-PC2-002` is marked closed here. Full CORE-2 remains in progress and is not marked release-complete.

| Area | PASS/FAIL |
| --- | --- |
| Updated documentation follow-up audit/recheck accepted after post-audit customer decisions. |  |
| Resolved GAP constraints and endpoint/artifact gates are satisfied for implemented slice. |  |
| No product code was implemented outside allowed task files. |  |
| No WB/Ozon endpoint is called without current docs/code approval or endpoint-specific official read-only evidence and tests. |  |
| No WB/Ozon write endpoint/card-field update is implemented in CORE-2. |  |
| WB/Ozon API secrets are redacted everywhere. |  |
| `MarketplaceProduct` rows are preserved. |  |
| Existing Stage 1/2 operation results remain unchanged. |  |
| `OperationDetailRow.product_ref` remains unchanged in all migrations/backfills. |  |
| Nullable listing FK is correct, optional and reversible. |  |
| Listing sync is idempotent and access-safe. |  |
| Mapping conflicts never auto-confirm. |  |
| Auto-created variants follow approved imported/draft customer decision, fixed SKU validator and audit/history. |  |
| External mapping table workflow requires preview/diff/conflicts and explicit apply confirmation. |  |
| Snapshot writes are source-aware, run-aware and nullable where required. |  |
| Exports apply object access and redaction. |  |
| UI pages do not show future ERP modules as working functions. |  |
| Stage 1 WB Excel regression passed. |  |
| Stage 1 Ozon Excel regression passed. |  |
| Stage 2.1 WB API regression passed. |  |
| Stage 2.2 Ozon Elastic regression passed. |  |
| Product Core UI/permissions/export regression passed. |  |
| Release report and handoff are complete. |  |

## Blocking Failure Examples

- New read endpoint added without official-docs evidence, pagination/rate/retry/redaction contract and mocks.
- Marketplace write/card-field update endpoint added to CORE-2.
- Excel operation creates internal product/variant or confirmed mapping.
- `product_ref` rewritten or old operation outcome changed.
- Hidden store listing visible through operation row link/export/count.
- Secret-like value appears in UI/export/audit/techlog/snapshot/report.
- Future warehouse/production/BOM/labels UI appears operational.
- Invalid/non-unified external article auto-creates ProductVariant without mapping table/manual confirmation.
