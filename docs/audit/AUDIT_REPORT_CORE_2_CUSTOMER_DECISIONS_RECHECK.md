# AUDIT_REPORT_CORE_2_CUSTOMER_DECISIONS_RECHECK.md

Date: 2026-05-02
Role: documentation auditor
Scope: follow-up recheck of CORE-2 design documentation after post-audit customer decisions for `GAP-CORE2-001`..`GAP-CORE2-005`
Verdict: PASS

Product code was not changed during this audit. This report audits documentation only.

## Checked Files

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/PROJECT_NAVIGATOR.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/audit/AUDIT_PROTOCOL.md`
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`
- `docs/audit/AUDIT_REPORT_CORE_2_DESIGN_DOCUMENTATION.md`
- `docs/audit/AUDIT_REPORT_CORE_2_DESIGN_DOCUMENTATION_RECHECK.md`
- `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md`
- all files in `docs/stages/stage-3-product-core/core-2/`
- `docs/adr/ADR_LOG.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/project/CURRENT_STATUS.md`

## Method

Static documentation audit against:

- prior CORE-2 audit PASS / recheck PASS;
- CORE-2 design TZ boundaries;
- customer decisions listed in the task;
- GAP/ADR consistency;
- forbidden CORE-2 scope checks;
- git scope and whitespace checks.

## Findings

### BLOCKER

None.

### MAJOR

None.

### MINOR

None.

## Decision Recheck

| Decision | Result | Evidence |
| --- | --- | --- |
| Fixed structured `internal_sku` format for `nash`/`chev` etc.; fixed docs/code dictionary, editable UI future | PASS | `CORE_2_MAPPING_RULES_SPEC.md` defines fixed format and dictionary, examples, and says editable UI dictionaries are future scope. `CORE_2_UI_UX_SPEC.md` also prohibits CORE-2 UI dictionary editing. |
| Valid API article links existing active `ProductVariant` or auto-creates imported/draft `InternalProduct` + `ProductVariant` with matched mapping and audit/history | PASS | `CORE_2_SCOPE.md`, `CORE_2_MAPPING_RULES_SPEC.md`, `GAP-CORE2-001`, ADR-0045. |
| Invalid/non-unified articles stay `MarketplaceListing` only, with `visual_external`, mapping table, manual mapping actions | PASS | `CORE_2_MAPPING_RULES_SPEC.md`, `CORE_2_UI_UX_SPEC.md`, `GAP-CORE2-001`, `GAP-CORE2-005`. |
| Multiple stores/marketplaces may share one `ProductVariant`; impossible duplicate external articles are API data integrity errors | PASS | `CORE_2_MAPPING_RULES_SPEC.md`, `CORE_2_API_SYNC_SPEC.md`, tests/tasks include duplicate guards. |
| Operation enrichment applies to new and old deterministic rows; `product_ref` immutability has row-count/checksum evidence | PASS | `CORE_2_OPERATION_LINKING_SPEC.md`, `CORE_2_MODEL_AND_MIGRATION_PLAN.md`, `GAP-CORE2-003`, ADR-0044. |
| CORE-2 fills only prices/stocks/promotions-actions; sales/buyouts/returns/demand/in-work/production/shipments are future hooks | PASS | `CORE_2_SCOPE.md`, `CORE_2_SNAPSHOT_FILLING_SPEC.md`, ADR-0046. |
| Official read-only catalog/listing APIs allowed with endpoint docs evidence/tests; no writes in CORE-2 | PASS | `CORE_2_API_SYNC_SPEC.md`, `CORE_2_SCOPE.md`, `GAP-CORE2-002`, ADR-0042/0046. |
| External normalization supports API auto-match, mapping table preview/apply with confirmation, manual fallback | PASS | `CORE_2_MAPPING_RULES_SPEC.md`, `CORE_2_UI_UX_SPEC.md`, `GAP-CORE2-005`, ADR-0043. |
| Marketplace card field updates by API are out of CORE-2 only, not out of promo_v2 forever | PASS | `CORE_2_SCOPE.md`, `CORE_2_API_SYNC_SPEC.md`, `CORE_2_UI_UX_SPEC.md`, ADR-0042, `CURRENT_STATUS.md`. |

## GAP Status

`GAP-CORE2-001`..`GAP-CORE2-005` are justified as `resolved/customer_decision` or `resolved/customer_decision_with_endpoint_artifact_gate`.

Remaining constraints are explicit and implementation-facing:

- `GAP-CORE2-001`: fixed SKU validator, imported/draft lifecycle, audit/history, tests; no active confirmed auto-created product.
- `GAP-CORE2-002`: every new concrete read-only endpoint still needs official docs evidence, pagination/rate/retry/redaction contract and mocks; no marketplace writes.
- `GAP-CORE2-003`: deterministic same-store/same-marketplace matching only, no summary rows, chunked/idempotent backfill, `(id, product_ref)` evidence and Stage 1/2 regression.
- `GAP-CORE2-004`: filled snapshots require approved source semantics and tests; future metric formulas require separate design.
- `GAP-CORE2-005`: mapping table apply requires preview, explicit confirmation, object access, permissions, audit/history, redaction and conflict handling.

These are not open customer-decision blockers.

## ADR Check

ADR-0042..ADR-0046 reflect the customer decisions and do not claim implemented product functionality:

- ADR-0042 keeps CORE-2 marketplace writes out of scope while allowing future audited promo_v2 card updates.
- ADR-0043 fixes `internal_sku` as business key, records the SKU dictionary and matching modes, and prohibits fuzzy/title/image matching.
- ADR-0044 preserves `product_ref` and requires row-count/checksum evidence for old rows.
- ADR-0045 records approved Option B without overstating imported/draft variants as manually confirmed products.
- ADR-0046 limits active snapshot filling and leaves future metrics as hooks only.

## Scope And Assumption Check

No new product/UX/business assumption was found beyond the recorded customer decisions.

No forbidden CORE-2 active functionality slipped into scope:

- warehouse, production, suppliers, purchases, BOM, packaging, labels, demand planning and machine vision remain out of CORE-2;
- sales/buyouts/returns/demand/in-work/production/shipments remain future hooks without active UI/workflow/formulas;
- WB/Ozon write endpoints and card-field updates are prohibited in CORE-2;
- Excel discount workflows still do not create Product Core records or confirmed mappings;
- fuzzy/title/image matching remains prohibited.

Historical wording in `AUDIT_REPORT_CORE_2_DESIGN_DOCUMENTATION.md` still describes the pre-decision state, but current `CORE_2_READING_PACKAGES.md` explicitly tells agents to treat `GAP-CORE2-001`..`005` as resolved decision records and not use old open-gap wording as current scope. This is acceptable and does not contradict the prior PASS.

## Customer Decisions Still Required

None for this follow-up audit/recheck.

Implementation still requires endpoint-specific official documentation artifacts and tests for any newly added read-only catalog/listing endpoint, but that is an implementation artifact gate, not a remaining customer decision.

## Checks

- `git diff --check`: PASS after creating this report.
- New untracked report whitespace check: PASS via `git diff --no-index --check /dev/null docs/audit/AUDIT_REPORT_CORE_2_CUSTOMER_DECISIONS_RECHECK.md`.
- Product code unchanged: PASS. `git status --short --untracked-files=all` shows only documentation paths under `docs/`, plus this new audit report. `git status --short --untracked-files=all -- apps config templates static manage.py` and `git diff --name-only -- apps config templates static manage.py` returned no product-code changes.

## Conclusion

PASS. The updated CORE-2 design docs can proceed to orchestrator acceptance for task-scoped implementation assignment. Implementation remains prohibited until that separate assignment is issued.

## Changed Files

- `docs/audit/AUDIT_REPORT_CORE_2_CUSTOMER_DECISIONS_RECHECK.md`
