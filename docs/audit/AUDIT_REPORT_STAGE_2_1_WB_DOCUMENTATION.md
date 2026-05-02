# AUDIT_REPORT_STAGE_2_1_WB_DOCUMENTATION.md

Дата аудита: 2026-04-26

Проверенная область: исполнительная документация Stage 2.1 WB API до начала реализации.

Итог: PASS WITH REQUIRED FIXES

Implementation may start: no. Реализация TASK-011..TASK-017 должна ждать исправления blocking findings ниже и повторной точечной проверки.

## Проверенные источники

- `docs/source/stage-inputs/tz_stage_2.1.txt`
- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/orchestration/TASK_TEMPLATES.md`
- `docs/audit/AUDIT_PROTOCOL.md`
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`
- `docs/traceability/TRACEABILITY_MATRIX.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`
- `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/product/UI_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/testing/TEST_PROTOCOL.md`
- all new Stage 2.1 documents and TASK-011..TASK-017 listed in the audit request.

Official WB API sources checked:

- https://dev.wildberries.ru/docs/openapi/work-with-products
- https://dev.wildberries.ru/docs/openapi/promotion

## Findings

### BLOCKER-01: `Operation.type` contract is internally inconsistent for Stage 2.1 API steps

References:

- `docs/architecture/DATA_MODEL.md:33`
- `docs/product/OPERATIONS_SPEC.md:22`
- `docs/product/OPERATIONS_SPEC.md:29`
- `docs/architecture/DATA_MODEL.md:227`
- `docs/architecture/DATA_MODEL.md:238`
- `docs/product/OPERATIONS_SPEC.md:169`
- `docs/product/OPERATIONS_SPEC.md:175`
- `docs/product/UI_SPEC.md:316`
- `docs/product/UI_SPEC.md:333`
- `docs/source/stage-inputs/tz_stage_2.1.txt` §6.6

Problem:

The Stage 1 baseline still defines `Operation` as having mandatory `type: check/process`. Stage 2.1 then says API download/upload steps must not be masked as Stage 1 Excel check/process and should use `Operation.step_code` or an equivalent execution-context contract. It does not define what `Operation.type` contains for `wb_api_prices_download`, `wb_api_promotions_download`, `wb_api_discount_calculation`, and `wb_api_discount_upload`.

This leaves implementers with an unsafe choice: either misuse `check/process`, make `type` nullable without documentation, or invent a new enum. The UI operation list/card also still display and filter by `type` without Stage 2.1 semantics.

Required fix:

Define one explicit model:

- either extend `Operation.type` with approved Stage 2.1 values;
- or document that `Operation.type` is nullable/not used for non-check/process API steps and `Operation.step_code` is the primary classifier;
- or introduce a separate mandatory field with migration notes.

Then update `DATA_MODEL.md`, `OPERATIONS_SPEC.md`, `UI_SPEC.md`, tests/checklists, and TASK-011..TASK-017 migration guidance consistently.

### BLOCKER-02: TASK-011..TASK-017 are not fully task-scoped against `READING_PACKAGES.md` and the task template

References:

- `docs/roles/READING_PACKAGES.md:149`
- `docs/roles/READING_PACKAGES.md:156`
- `docs/roles/READING_PACKAGES.md:164`
- `docs/roles/READING_PACKAGES.md:167`
- `docs/roles/READING_PACKAGES.md:169`
- `docs/roles/READING_PACKAGES.md:171`
- `docs/orchestration/TASK_TEMPLATES.md:16`
- `docs/orchestration/TASK_TEMPLATES.md:25`
- `docs/orchestration/TASK_TEMPLATES.md:28`
- `docs/tasks/implementation/stage-2/TASK-012-wb-api-prices-download.md:11`
- `docs/tasks/implementation/stage-2/TASK-013-wb-api-current-promotions-download.md:11`
- `docs/tasks/implementation/stage-2/TASK-014-wb-api-discount-calculation-excel-output.md:11`
- `docs/tasks/implementation/stage-2/TASK-015-wb-api-discount-upload.md:11`

Problem:

The Stage 2.1 developer reading package requires the stage scope documents, `OPERATIONS_SPEC.md`, `DATA_MODEL.md`, `FILE_CONTOUR.md`, `AUDIT_AND_TECHLOG_SPEC.md`, `PERMISSIONS_MATRIX.md`, Stage 2.1 test protocol, Stage 2.1 acceptance checklists, `GAP_REGISTER.md`, and `ADR_LOG.md`. Several task files omit required context. For example, TASK-012..TASK-015 do not include `docs/stages/stage-2/STAGE_2_SCOPE.md` or `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`; TASK-012..TASK-015 omit `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`; TASK-012..TASK-015 omit `docs/gaps/GAP_REGISTER.md`; TASK-014 and TASK-015 omit some cross-cutting docs needed for permissions/file/audit consistency.

The task template also includes `Связанные требования ТЗ`, but the task files only list sections to read. Allowed/forbidden areas are broad module names rather than concrete repo paths or explicit future module boundaries, which is not implementation-ready enough for a multi-agent codebase.

Required fix:

Align every TASK-011..TASK-017 with `READING_PACKAGES.md` and `TASK_TEMPLATES.md`:

- add the missing mandatory Stage 2.1 scope, acceptance checklist, GAP, ADR, audit/techlog, file, operations and permissions documents where applicable;
- add explicit `Связанные требования ТЗ`;
- replace broad "backend modules" style allowed areas with concrete paths or exact future path boundaries from project structure;
- keep forbidden areas explicit enough to prevent accidental Stage 1 Excel or Ozon API changes.

### BLOCKER-03: Secret handling contains a conditional loophole for techlog sensitive details

References:

- `docs/architecture/API_CONNECTIONS_SPEC.md:34`
- `docs/architecture/API_CONNECTIONS_SPEC.md:36`
- `docs/architecture/API_CONNECTIONS_SPEC.md:38`
- `docs/architecture/API_CONNECTIONS_SPEC.md:44`
- `docs/architecture/DATA_MODEL.md:267`
- `docs/product/WB_DISCOUNTS_API_SPEC.md:257`
- `docs/source/stage-inputs/tz_stage_2.1.txt` §10.1

Problem:

The overall documents say API token is stored only through `protected_secret_ref`, but `API_CONNECTIONS_SPEC.md` forbids token in `sensitive_details_ref` only "if it can be shown to operator". That conditional is not allowed by the Stage 2.1 TЗ. `sensitive_details_ref` is part of the techlog contour, and the TЗ forbids token/api_key in metadata, audit, techlog, snapshots, UI and files.

Required fix:

Make the ban absolute: no token, authorization header, API key, bearer value or secret-like value may be stored in techlog `safe_message`, `sensitive_details_ref`, snapshots, audit, metadata, UI, files or reports. Add this explicitly to security tests for TASK-011..TASK-017.

### REQUIRED-01: Upload payload rule is specified but not fully covered by tests/checklists

References:

- `docs/product/WB_DISCOUNTS_API_SPEC.md:156`
- `docs/product/WB_DISCOUNTS_API_SPEC.md:160`
- `docs/product/WB_DISCOUNTS_API_SPEC.md:162`
- `docs/product/WB_DISCOUNTS_API_SPEC.md:175`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md:49`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md:46`
- `docs/source/stage-inputs/tz_stage_2.1.txt` §9.2

Problem:

The spec correctly chooses discount-only payload and forbids falling back to stale price if WB rejects it. However, Stage 2.1 test protocol and acceptance checklist do not require a direct assertion that:

- normal upload payload contains `nmID` and `discount`, not stale `price`;
- a WB rejection of discount-only payload stops upload safely;
- implementation does not silently add old price from the calculation Excel.

Official WB docs state `POST /api/v2/upload/task` accepts up to 1000 products and that price and discount cannot both be empty; the sample includes both price and discount, so this local safety decision must be locked down by tests.

Required fix:

Add explicit mock tests and checklist items for discount-only payload, no stale price fallback, and safe stop/escalation if discount-only is rejected.

## Confirmed Coverage

- Required Stage 2.1 documents exist and are listed in `docs/README.md` / `docs/DOCUMENTATION_MAP.md` where expected.
- Stage 2 split is documented: 2.1 WB API only, 2.2 Ozon API future/separate.
- 2.1.1, 2.1.2 and 2.1.3 are read-only toward WB; only 2.1.4 performs write upload.
- Stage 1 WB Excel logic remains the shared baseline and Excel mode is not replaced.
- Current promotion definition is strict: `startDateTime <= now_utc < endDateTime`.
- Prices API pagination/rate limit, size conflicts, snapshots and product-directory mapping are documented.
- Promotions API list/details/nomenclatures, regular/auto behavior, promo Excel files and DB entities are documented.
- Upload flow covers confirmation, drift check, batching <=1000, uploadID per batch, polling, statuses 3/4/5/6, partial errors, quarantine, 208 and 429/backoff.
- Stage 2.1 reason/result codes are closed and backed by ADR-0020.
- GAP/ADR set for Stage 2.1 exists; no customer question is required for the documented recommended decisions.

## Questions For Customer Via Orchestrator

None at this audit round. The findings above are project documentation defects, not customer business/UX decisions. If the designer cannot fix `Operation.type` without choosing a new user-visible operation taxonomy, then that specific taxonomy question must be escalated before implementation.

## Required Fixes Summary

1. Resolve the `Operation.type` / `step_code` model conflict and update all affected docs/tests/tasks.
2. Bring TASK-011..TASK-017 task-scoped packages into exact alignment with `READING_PACKAGES.md` and `TASK_TEMPLATES.md`.
3. Remove the conditional secret-storage loophole for `sensitive_details_ref`; make protected secret reference the only storage location.
4. Add upload payload tests/checklists for discount-only payload and no stale price fallback.

## Audit Result

Verdict: PASS WITH REQUIRED FIXES.

Implementation may start: no, not until required fixes are applied and the fixed documentation receives a targeted audit pass.

Changed files in this audit:

- `docs/audit/AUDIT_REPORT_STAGE_2_1_WB_DOCUMENTATION.md`
