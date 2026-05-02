# TASK_PC2_006_DESIGN_AUDIT

Date: 2026-05-02
Role: TASK-PC2-006 documentation auditor
Audited handoff: `docs/reports/TASK_PC2_006_DESIGN_HANDOFF.md`
Verdict: BLOCKED

## Documents Read

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/reports/TASK_PC2_006_DESIGN_HANDOFF.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-006`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md` section `TASK-PC2-006`
- `docs/stages/stage-3-product-core/core-2/CORE_2_EXCEL_EXPORT_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Additional narrowly scoped checks:

- `docs/product/PERMISSIONS_MATRIX.md` for Product Core role interpretation.
- `docs/stages/stage-3-product-core/core-2/CORE_2_OPERATION_LINKING_SPEC.md` for operation-link export visibility.
- `docs/stages/stage-3-product-core/core-2/CORE_2_MAPPING_RULES_SPEC.md` and `CORE_2_UI_UX_SPEC.md` for the deferred mapping-table boundary.
- Read-only code spot-checks of current export/audit/file scenario facts named by the handoff.

## Blocking Findings

### B1. Operation-link export can leak linked variant identity without explicit Product Core/variant view guard

Owner: TASK-PC2-006 designer.

The handoff correctly protects listing identifiers in the operation-link report by operation visibility plus `marketplace_listing.export` / object access. It does not explicitly require `product_core.view` and `product_variant.view` before filling `linked_variant_internal_sku`.

This is inconsistent with the handoff's own marketplace-listing and mapping-report rules, where linked internal product/variant columns require Product Core/variant view access, and with the permissions model where local admins may have listing export scope without Product Core product/variant permissions. A developer could implement the operation-link CSV exactly as written and expose internal SKU values to an actor who is allowed to troubleshoot listing links but not view internal variants.

Required handoff fix:

- Add an explicit rule for operation-link report: `linked_variant_internal_sku` and any future internal product/variant fields are blank unless the actor has the required Product Core/variant view permissions in addition to operation visibility and listing export/object access.
- Add a required test for an actor with operation visibility plus listing export but without Product Core/variant view; the CSV must not expose internal SKU/name/code.

No customer escalation is required if this is corrected as a permission hardening rule already implied by existing Product Core export rules.

### B2. Export audit action is underspecified and leaves implementation dependent on auditor acceptance

Owner: TASK-PC2-006 designer, with implementation input from audit catalog owner if needed.

`CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md` names `product_core.export_generated` as the CORE-2 minimum audit action for product/listing/mapping/latest export generation. The handoff instead says implementation may add `product_core.export_generated`, otherwise use existing `marketplace_listing.exported` only where listing-specific and "the auditor accepts the equivalence".

This is not a concrete implementation contract. PC2-006 includes marketplace listing, latest values, mapping report and operation-link report exports; at least operation-link report is not cleanly covered by the existing listing-specific action name. Leaving the action code choice to later auditor acceptance makes the audit criteria insufficient for development.

Required handoff fix:

- Either mandate adding `product_core.export_generated` with migration/tests for all scoped PC2-006 export generation events, or provide a closed per-export audit-action mapping that conforms to the CORE-2 audit catalog.
- Remove the conditional "auditor accepts equivalence" language from the developer contract.
- Keep the existing safe audit snapshot limits: no row data, no raw JSON, no request headers, no stack traces, no secret-like values.

No customer escalation is required if the fix follows the already approved CORE-2 audit catalog.

## Checks Completed

- Scope boundary: the handoff does not expand PC2-006 into marketplace writes, Stage 1/2 Excel changes, external mapping-table preview/apply/export, or persisted Product Core file outputs. Operation-link CSV is within the assigned PC2-006 export slice.
- Excel boundary: the handoff explicitly prohibits Product Core export download/edit/re-upload side effects, Product Core import through existing WB/Ozon Excel workflows, and Stage 1/2 template/calculation/reason-code changes.
- Snapshot permission: latest-values export is specified to require `marketplace_listing.export` plus `marketplace_snapshot.view` per row store, with denial when no filtered row store has snapshot view. This is concrete enough.
- Secret/raw payload boundary: CSV, audit and techlog redaction requirements prohibit tokens, authorization headers, Ozon Client-Id/Api-Key, bearer/API key values, raw request/response headers, stack traces, raw snapshot payloads and row data in audit.
- FileVersion/persistence: streamed CSV as the default is consistent with current file contour and current lack of a Product Core export `FileObject.Scenario`. Persisted exports are correctly blocked unless a separate assignment updates the file contour and operation/file scenarios.
- External mapping table: deferral is consistent with `GAP-CORE2-007` and must stay out of PC2-006.
- Allowed/prohibited files and tests: mostly sufficient, but blocked by B1 and B2 before development can safely start.

## UX / Business Gaps

No new UX/functionality/business customer gap was found for the scoped PC2-006 exports. The blockers above are documentation-contract fixes against already approved permission and audit rules.

## Residual Risks After Fixes

- Header names must be kept stable in implementation tests because existing code currently uses older/latest-value header variants.
- Current code spot-check confirms the handoff's noted risk that latest-values export can currently materialize rows without snapshot permission; the implementation must tighten this before release.
- If the orchestrator later expands PC2-006 to product variant review exports or external mapping-table exports, that expansion needs a separate audited handoff because this audit covers only the scoped listing/latest/mapping/operation-link slice.
