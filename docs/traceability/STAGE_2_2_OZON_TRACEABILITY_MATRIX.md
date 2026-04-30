# STAGE_2_2_OZON_TRACEABILITY_MATRIX.md

Трассировка: `docs/tasks/implementation/stage-2/TASK-018-DESIGN-STAGE-2-2-OZON-API.md`.

| Requirement | Документ | Tests/Acceptance | ADR/GAP |
| --- | --- | --- | --- |
| Stage 2 split 2.1 WB / 2.2 Ozon | `docs/stages/stage-2/STAGE_2_SCOPE.md`, `STAGE_2_2_OZON_SCOPE.md` | General checklist | ADR-0016 |
| Ozon API adapts existing Ozon Excel logic | `OZON_API_ELASTIC_BOOSTING_SPEC.md`, `OZON_DISCOUNTS_EXCEL_SPEC.md` | Calculation golden fixtures | ADR-0022 |
| Stage 1 Ozon Excel remains штатный | `STAGE_2_2_OZON_SCOPE.md` | Stage 1 Ozon regression | ADR-0022 |
| UI hierarchy marketplace/domain/source/workflow | `OZON_API_ELASTIC_UI_SPEC.md`, `UI_SPEC.md` | UI acceptance | ADR-0023 |
| Fixed 10-button workflow | `OZON_API_ELASTIC_UI_SPEC.md` | UI button order tests | ADR-0023 |
| Ozon API connection secret safety | `API_CONNECTIONS_SPEC.md` | Connection/security tests | ADR-0024 |
| Ozon API production connection check endpoint | `API_CONNECTIONS_SPEC.md`, `TASK-019` | `GET /v1/actions` status mapping tests with mocks/sanitized fixtures | ADR-0035; GAP-0022 resolved |
| Actions download and Elastic action selection | `OZON_API_ELASTIC_BOOSTING_SPEC.md` | Actions mocks | ADR-0029; GAP-0014 resolved |
| Active products download | `OZON_API_ELASTIC_BOOSTING_SPEC.md` | Active pagination mocks and field mapping contract tests | ADR-0033; GAP-0018 resolved |
| Candidate products download | `OZON_API_ELASTIC_BOOSTING_SPEC.md` | Candidate pagination mocks and field mapping contract tests | ADR-0033; GAP-0018 resolved |
| Product info/stocks join | `OZON_API_ELASTIC_BOOSTING_SPEC.md` | Join tests | ADR-0030 for J; ADR-0031 for R |
| J/O/P/R mapping | `OZON_API_ELASTIC_BOOSTING_SPEC.md` | Sanitized fixture tests | ADR-0030 for J; ADR-0031 for R |
| Product in active and candidate sources | `OZON_API_ELASTIC_BOOSTING_SPEC.md` | Merge/update/deactivate/report visibility tests | ADR-0028; GAP-0021 resolved |
| Result review state | `OZON_API_ELASTIC_BOOSTING_SPEC.md`, `OPERATIONS_SPEC.md` | Review tests | ADR-0027 |
| Result report Excel | `FILE_CONTOUR.md`, `OZON_API_ELASTIC_BOOSTING_SPEC.md` | File generation tests | ADR-0025 |
| Manual upload Excel after accepted result | `OZON_API_ELASTIC_BOOSTING_SPEC.md`, `FILE_CONTOUR.md`, `TASK-024` | Post-acceptance generation tests, Stage 1-compatible template tests, K/L mapping, `Снять с акции` visibility | ADR-0032; GAP-0017 resolved |
| Ozon API rate/batch/retry/idempotency policy | `OZON_API_ELASTIC_BOOSTING_SPEC.md`, `API_CONNECTIONS_SPEC.md` | API client policy tests: read page `100`, write batch `100`, `500 ms`, read transient retry, no automatic sent/uncertain write retry | ADR-0034; GAP-0019 resolved |
| API upload add/update | `OZON_API_ELASTIC_BOOSTING_SPEC.md` | Activate payload contract tests, upload mocks/live-safe evidence | ADR-0033, ADR-0034; GAP-0018 resolved; GAP-0019 resolved |
| Deactivate group confirmation and row-level reasons | `OZON_API_ELASTIC_BOOSTING_SPEC.md`, `OZON_API_ELASTIC_UI_SPEC.md` | Deactivate group confirmation and payload contract tests | ADR-0026, ADR-0033; GAP-0018 resolved |
| Drift-check before write | `OZON_API_ELASTIC_BOOSTING_SPEC.md` | Drift tests | ADR-0023 |
| Ozon API reason/result codes | `OZON_API_ELASTIC_BOOSTING_SPEC.md`, `DATA_MODEL.md` | Code catalog tests | ADR-0025, ADR-0026 |
| Operations step_code contract | `OPERATIONS_SPEC.md`, `DATA_MODEL.md` | Operation classifier tests | ADR-0025 |
| Permissions | `PERMISSIONS_MATRIX.md` | Rights/object access tests | ADR-0024 |
| Audit/techlog events | `AUDIT_AND_TECHLOG_SPEC.md` | Audit/techlog tests | ADR-0024 |
| Implementation task-scoped docs | `docs/tasks/implementation/stage-2/*` | Audit of task files | none |

## GAP status

Stage 2.2 has no open spec-blocking GAP entries in this matrix as of 2026-04-30. `GAP-0014` is resolved by customer decision 2026-04-30 and ADR-0029. `GAP-0015` is resolved by customer decision 2026-04-30 and ADR-0030. `GAP-0016` is resolved by customer decision 2026-04-30 and ADR-0031. `GAP-0017` is resolved by customer decision 2026-04-30 and ADR-0032. `GAP-0018` is resolved by customer decision 2026-04-30 and ADR-0033. `GAP-0019` is resolved by technical/orchestrator decision 2026-04-30 and ADR-0034. `GAP-0020` is resolved by customer decision and ADR-0027. `GAP-0021` is resolved by customer decision 2026-04-30 and ADR-0028. `GAP-0022` is resolved by technical decision 2026-04-30 and ADR-0035. Implementation may not code blocked areas until each affected GAP is resolved in `docs/gaps/GAP_REGISTER.md` and, where needed, `docs/adr/ADR_LOG.md`.
