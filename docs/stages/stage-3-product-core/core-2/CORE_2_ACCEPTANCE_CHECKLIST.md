# CORE_2_ACCEPTANCE_CHECKLIST.md

Статус: исполнительная проектная документация CORE-2, подготовлена для audit-gate.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§14-16, §11.13.

## Documentation Audit Checklist

| Criterion | PASS/FAIL |
| --- | --- |
| All TZ §3.2 CORE-2 documents exist. |  |
| Scope and non-scope protect Stage 1/2 and future ERP boundary. |  |
| ADR-0042..ADR-0046 are recorded. |  |
| GAP-CORE2-001..005 are recorded and not hidden as assumptions. |  |
| API endpoints are limited to current approved docs/code or blocked by GAP. |  |
| ProductVariant auto-create does not proceed without customer decision. |  |
| `product_ref` immutability is explicit. |  |
| Nullable FK enrichment is reversible and non-destructive. |  |
| Snapshot semantics and foundation-only types are explicit. |  |
| UI spec excludes warehouse/production/suppliers/BOM/packaging/labels/machine vision. |  |
| Permissions/object access/redaction are specified. |  |
| Test plan includes Stage 1/2 and Product Core regression. |  |
| Agent tasks include reading packages, prohibited changes, tests and audit criteria. |  |
| Rollout runbook includes backup/validation/rollback/post-deploy checks. |  |

## Implementation Acceptance Checklist

| Area | PASS/FAIL |
| --- | --- |
| Documentation audit result is `AUDIT PASS`. |  |
| No blocking GAP remains for implemented slice. |  |
| No product code was implemented outside allowed task files. |  |
| No new unapproved WB/Ozon endpoint is called. |  |
| WB/Ozon API secrets are redacted everywhere. |  |
| `MarketplaceProduct` rows are preserved. |  |
| Existing Stage 1/2 operation results remain unchanged. |  |
| `OperationDetailRow.product_ref` remains unchanged in all migrations/backfills. |  |
| Nullable listing FK is correct, optional and reversible. |  |
| Listing sync is idempotent and access-safe. |  |
| Mapping conflicts never auto-confirm. |  |
| Auto-created variants, if implemented, follow approved customer decision and audit. |  |
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

- New endpoint added without `GAP-CORE2-002` resolution.
- Excel operation creates internal product/variant or confirmed mapping.
- `product_ref` rewritten or old operation outcome changed.
- Hidden store listing visible through operation row link/export/count.
- Secret-like value appears in UI/export/audit/techlog/snapshot/report.
- Future warehouse/production/BOM/labels UI appears operational.
- Auto-created active confirmed mapping implemented under Option C without customer decision.
