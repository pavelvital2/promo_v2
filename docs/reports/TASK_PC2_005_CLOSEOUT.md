# TASK_PC2_005_CLOSEOUT

Date: 2026-05-02
Role: TASK-PC2-005 technical writer
Task: TASK-PC2-005 Snapshot Filling
Status: DONE
Audit: PASS

## Basis

- `docs/reports/TASK_PC2_005_DESIGN_HANDOFF.md`
- `docs/reports/TASK_PC2_005_DESIGN_AUDIT.md`
- `docs/reports/TASK_PC2_005_IMPLEMENTATION_AUDIT.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-005`

## Implemented

- WB price snapshots wiring from the approved Stage 2.1 WB prices flow.
- WB regular promotion snapshots wiring for deterministic product-row/listing matches.
- Ozon Elastic action promotion snapshots wiring for selected active/candidate product sets.
- Ozon stock snapshots adapter and wiring from selected Elastic product data based on `/v4/product/info/stocks`.

## Intentionally Not Implemented

- Sales, buyouts, returns, demand, production, in-work and shipments active filling.
- UI, workflow, exports or formulas for future hooks.
- WB stock snapshots.
- Fake WB auto-promotion product rows, listings or promotion snapshots.
- New marketplace source endpoints.

## Verification

- Focused suite with PostgreSQL env: `113 tests`, `OK`.
- `manage.py check`: `OK`.
- `makemigrations --check`: `OK`.
- `git diff --check`: `OK`.

## Residual Risks

- Product Core failure isolation has a dedicated mocked adapter-failure integration test for WB prices. Ozon and WB promotion call-sites use the same post-success `try/except` isolation pattern, but do not each have a dedicated mocked adapter-failure integration test in the audited diff.
- Secret guard coverage relies on shared `assert_no_secret_like_values` behavior and representative redaction tests. This is adequate for TASK-PC2-005, but future endpoints must add endpoint-specific redaction tests before snapshot filling.
- `MarketplaceListing.last_values` still has generic support for sales snapshots from the foundation model. This is acceptable because TASK-PC2-005 adds no active sales snapshot creation path.

## Closeout Verdict

TASK-PC2-005 Snapshot Filling is closed as `DONE` after implementation audit `PASS`. The implemented scope matches the approved CORE-2 snapshot scope and keeps future hooks inactive.
