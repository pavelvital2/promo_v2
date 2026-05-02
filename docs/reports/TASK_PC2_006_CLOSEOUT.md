# TASK_PC2_006_CLOSEOUT

Date: 2026-05-02
Role: TASK-PC2-006 technical writer
Task: TASK-PC2-006 Product Core Exports And Excel Boundary
Status: DONE
Implementation Recheck: PASS

## Basis

- `docs/reports/TASK_PC2_006_DESIGN_HANDOFF.md`
- `docs/reports/TASK_PC2_006_DESIGN_RECHECK.md`
- `docs/reports/TASK_PC2_006_IMPLEMENTATION_AUDIT.md`
- `docs/reports/TASK_PC2_006_IMPLEMENTATION_RECHECK.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-006`

## Implemented

- Streamed CSV marketplace listing exports.
- Unmatched, needs-review and conflict listing export behavior through the scoped listing export contract.
- Listings with latest values export, including snapshot permission gating and redacted latest JSON.
- Mapping report CSV for scoped mapping states and conflict diagnostics.
- Operation-link report CSV for visible operation detail rows and nullable listing FK enrichment state.
- Audit action `product_core.export_generated` for scoped Product Core export generation events.
- Permission gates, object access checks and redaction required for hidden stores, linked internal identifiers and latest-value payloads.

## Intentionally Not Implemented

- Product Core imports from any existing WB/Ozon Excel workflow.
- Stage 1 or Stage 2 Excel template, calculation, upload or reason/result-code changes.
- Persisted `FileVersion` Product Core exports or XLSX export generation.
- External mapping-table preview/apply/export workflow and `visual_external` table behavior.

## Verification

- `apps.web apps.product_core apps.audit`: `111 tests`, `OK`.
- `manage.py check`: `OK`.
- `makemigrations --check --dry-run`: `OK`.
- `git diff --check`: `OK`.

## Residual Risks

- Audit migration `apps/audit/migrations/0011_product_core_export_generated_action.py` must be included in the implementation commit/package.
- The reverse one-permission case for internal identifier access is covered by the shared `and` gate in code, not by a separate cross-export regression test.

## Closeout Verdict

TASK-PC2-006 Product Core Exports And Excel Boundary is closed as `DONE` after implementation recheck `PASS`. The implemented scope matches the approved CORE-2 export slice and preserves the Excel/file-contour boundaries for future tasks.
