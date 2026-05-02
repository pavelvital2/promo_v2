# TASK_PC2_007_DESIGN_AUDIT

Date: 2026-05-02
Role: design documentation auditor
Task: TASK-PC2-007 Product Core UI Integration
Audited document: `docs/reports/TASK_PC2_007_DESIGN_HANDOFF.md`
Verdict: PASS

## Documents Read

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/reports/TASK_PC2_007_DESIGN_HANDOFF.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-007`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md` section `TASK-PC2-007`
- `docs/stages/stage-3-product-core/core-2/CORE_2_UI_UX_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_MAPPING_RULES_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_OPERATION_LINKING_SPEC.md`
- `docs/product/PRODUCT_CORE_UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/gaps/GAP_REGISTER.md`

Additional direct context checked because the handoff references export controls:

- `docs/stages/stage-3-product-core/core-2/CORE_2_EXCEL_EXPORT_SPEC.md`

## Audit Summary

| Check | Result | Notes |
| --- | --- | --- |
| Handoff does not guess UX/functionality. | PASS | The handoff narrows PC2-007 to concrete server-rendered UI surfaces and turns expanded mapping-table, `visual_external`, new sync route, new endpoint, new permission-code and future ERP behavior into explicit stop conditions. |
| Gaps requiring customer question are not hidden. | PASS | The only active customer-question boundary in this handoff is the deferred mapping-table / `visual_external` workflow. The handoff states that an expanded PC2-007 requiring active upload/preview/apply becomes `BLOCKED_BY_CUSTOMER_QUESTION`. |
| Mapping-table / `visual_external` handling is consistent with current GAP/docs. | PASS WITH RESIDUAL RISK | `GAP-CORE2-007` records the row/file contract as deferred/future and blocking for any future external mapping-table or `visual_external` workflow. The handoff keeps those controls hidden and prohibits routes, forms, parsers, permissions, persistence and exports for them. |
| Required PC2-007 UI scope is not silently dropped. | PASS | The handoff explicitly lists what remains in scope: navigation, listing sync/status display, exact-basis mapping review, imported/draft review queue, operation row links, snapshot/latest display and PC2-006 export controls. The deferred mapping-table scope is called out, not omitted. |
| Routes/templates/tests are concrete. | PASS | Existing routes/templates to extend and new variant review routes/templates are listed. Required tests cover permissions, object access, sync status rendering, redaction, review actions, mapping exactness, snapshot gates, export controls and prohibited UI. |
| Permissions are concrete enough for implementation. | PASS | The handoff maps each UI surface to existing `product_core`, `product_variant`, `marketplace_listing`, `marketplace_snapshot` and export gates, with direct deny/object access preserving current identity behavior. It correctly avoids identity/access seed changes unless PC2-008 or a separate assignment authorizes them. |
| Prohibited UI remains prohibited. | PASS | The handoff prohibits active ERP/warehouse/production/demand/suppliers/labels/card-field-write UI, WB `vendorCode` and Ozon `offer_id` edits, editable internal SKU dictionary UI, fuzzy/title/image matching and hidden auto-mapping. |
| Hidden store/internal identifier leakage is addressed. | PASS | The handoff requires access-filtered counts, links, operation FK display, export buttons, sync summaries and imported source context. Internal product/variant identifiers are shown on listing surfaces only when both `product_core.view` and `product_variant.view` are present. |
| Enough for developer. | PASS | The handoff is implementable as a scoped UI task without product model/service or identity/audit catalog changes. Stop conditions cover all places where a developer would otherwise need to guess. |

## Residual Risks

1. `CORE_2_AGENT_TASKS.md` still contains a broad PC2-007 step to add mapping-table preview/apply UI, while current `GAP-CORE2-007` and the audited handoff defer that workflow. This is acceptable only if the orchestrator assigns PC2-007 using the scoped handoff. If the broad step is reinstated, implementation is blocked until customer answers the retained mapping-table row/file/persistence questions.
2. `CORE_2_UI_UX_SPEC.md` and `CORE_2_EXCEL_EXPORT_SPEC.md` describe the future approved mapping-table workflow at CORE-2 level. Developers must treat those parts as future/deferred for this PC2-007 slice and must follow the handoff's prohibition on active upload/preview/apply UI.
3. The handoff reuses existing permissions for imported/draft review actions. If the orchestrator/customer requires a dedicated review-confirmation permission, that is outside PC2-007 and becomes a separate identity/access task.
4. Existing Product Core templates reportedly have leak paths and active sales/orders snapshot UI. The handoff identifies the required fixes and tests, but implementation audit must verify rendered HTML and access-filtered querysets, not only route presence.

## Customer Question Status

No customer question is needed for the scoped PC2-007 handoff.

Customer/orchestrator question is required before any implementation of active external mapping-table upload/preview/apply or `visual_external` table workflow. The questions are already preserved in the handoff and `GAP-CORE2-007`.

## Final Decision

PASS. `docs/reports/TASK_PC2_007_DESIGN_HANDOFF.md` is ready for scoped TASK-PC2-007 implementation, with the deferred mapping-table / `visual_external` boundary treated as a hard stop condition rather than active UI scope.
