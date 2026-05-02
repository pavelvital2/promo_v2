# AUDIT_REPORT_STAGE_2_1_WB_DOCUMENTATION_RECHECK.md

Дата повторной проверки: 2026-04-26

Проверенная область: исправления Stage 2.1 WB API после `docs/audit/AUDIT_REPORT_STAGE_2_1_WB_DOCUMENTATION.md`.

Фокус проверки: четыре previous findings из первичного аудита и возможные регрессии в связанных документах.

Итог: PASS

Implementation may start: yes, после commit текущего комплекта документации и orchestration выдачи TASK-011..TASK-017. Код продукта в рамках этого аудита не запускался и не изменялся.

## Findings

Новых blocking или required findings не обнаружено.

## Статус previous findings

### BLOCKER-01: Operation contract is internally consistent

Статус: closed.

Подтверждение:

- `docs/architecture/DATA_MODEL.md:136` фиксирует `Operation.type=check/process` только для check/process-сценариев, а `docs/architecture/DATA_MODEL.md:137` вводит обязательный `step_code` для Stage 2.1 API steps.
- `docs/architecture/DATA_MODEL.md:231`-`docs/architecture/DATA_MODEL.md:250` задаёт явный Stage 2.1 contract: `Operation.step_code` is the primary classifier; `Operation.type` не расширяется API-значениями и не должен быть `check/process` для `wb_api_prices_download`, `wb_api_promotions_download`, `wb_api_discount_calculation`, `wb_api_discount_upload`.
- `docs/product/OPERATIONS_SPEC.md:176`-`docs/product/OPERATIONS_SPEC.md:190` синхронизирует operation/list/card/report serializer semantics.
- `docs/product/UI_SPEC.md:316`-`docs/product/UI_SPEC.md:323` и `docs/product/UI_SPEC.md:333`-`docs/product/UI_SPEC.md:340` документируют list/card/filter semantics: check/process classified by `type`, Stage 2.1 API steps by `step_code`.
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md:70`-`docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md:71` и `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md:13` требуют проверки контракта.
- TASK-012..TASK-015 требуют `mode=api`, WB `step_code` и non-check/process `Operation.type`; TASK-016/TASK-017 проверяют UI/list/card and acceptance contract.

Риск из первичного аудита устранён: разработчик не оставлен выбирать semantics для `Operation.type`.

### BLOCKER-02: TASK-011..TASK-017 aligned with task-scoped rules

Статус: closed.

Подтверждение:

- Все TASK-011..TASK-017 содержат блоки из `docs/orchestration/TASK_TEMPLATES.md`: source of truth, input docs, ТЗ sections, related GAP/ADR, related ТЗ requirements, allowed/forbidden files, expected result, criteria, checks, report format and recipient.
- `docs/tasks/implementation/stage-2/TASK-011-wb-api-connections.md:11`-`docs/tasks/implementation/stage-2/TASK-011-wb-api-connections.md:30` включает mandatory Stage 2.1 package: scope docs, profile spec, data/file/audit/operations/permissions/UI/test/checklist/GAP/ADR docs.
- TASK-012..TASK-015 include stage scope docs, profile specs, `DATA_MODEL.md`, `FILE_CONTOUR.md`, `AUDIT_AND_TECHLOG_SPEC.md`, `OPERATIONS_SPEC.md`, `PERMISSIONS_MATRIX.md`, Stage 2.1 protocol/checklists, `GAP_REGISTER.md`, `ADR_LOG.md`.
- TASK-014 includes `WB_DISCOUNTS_EXCEL_SPEC.md` for shared WB calculation.
- TASK-016 includes UI-facing package and TASK-017 includes implementation task index, all task files, acceptance tests, traceability matrix and release evidence docs.
- Allowed/forbidden scopes are concrete repo paths or future path boundaries, with explicit bans on Stage 1 Excel behavior changes, Ozon API mixing, real secrets, and editing the previous audit report.

Риск из первичного аудита устранён: implementation tasks are now orchestration-ready and do not require developers to infer missing task scope.

### BLOCKER-03: Absolute secret ban has no conditional loophole

Статус: closed.

Подтверждение:

- `docs/architecture/API_CONNECTIONS_SPEC.md:36` states that `protected_secret_ref` is the only allowed storage location for token, authorization header, API key, bearer value and secret-like values.
- `docs/architecture/API_CONNECTIONS_SPEC.md:38`-`docs/architecture/API_CONNECTIONS_SPEC.md:47` bans those values in metadata, audit records, snapshots, techlog `safe_message`, techlog `sensitive_details_ref`, UI, exports, Excel, files, reports and test output.
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md:112`-`docs/architecture/AUDIT_AND_TECHLOG_SPEC.md:113` keeps `safe_message` UI-safe and prohibits secrets even in `sensitive_details_ref`, despite `techlog.sensitive.view`.
- `docs/architecture/DATA_MODEL.md:279` repeats the same storage boundary for `ConnectionBlock`.
- `docs/product/WB_DISCOUNTS_API_SPEC.md:260`, `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md:17`, `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md:73`-`docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md:74`, and `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md:10`-`docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md:11` cover security specs/tests/checklists.
- TASK-011..TASK-017 include either direct secret redaction checks or task-specific prohibitions against real tokens and secret-like outputs.

Риск из первичного аудита устранён: conditional wording around `sensitive_details_ref` is removed.

### REQUIRED-01: Upload payload tests/checklists/spec/tasks lock discount-only behavior

Статус: closed.

Подтверждение:

- `docs/product/WB_DISCOUNTS_API_SPEC.md:156`-`docs/product/WB_DISCOUNTS_API_SPEC.md:177` defines `POST /api/v2/upload/task` as discount-only in Stage 2.1, with normal payload containing only `nmID` and `discount`; `price` from calculation Excel, old snapshot or stale internal value is forbidden.
- The same section requires safe stop and orchestrator escalation note if WB rejects discount-only payload; automatic fallback to payload with `price` is forbidden without documentation change/audit.
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md:53`-`docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md:55` adds explicit tests for payload without `price`, safe stop on discount-only rejection, and no old/stale price from Excel or snapshot.
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md:54`-`docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md:56` adds matching checklist items.
- `docs/tasks/implementation/stage-2/TASK-015-wb-api-discount-upload.md:55`-`docs/tasks/implementation/stage-2/TASK-015-wb-api-discount-upload.md:63`, `docs/tasks/implementation/stage-2/TASK-015-wb-api-discount-upload.md:70`-`docs/tasks/implementation/stage-2/TASK-015-wb-api-discount-upload.md:87`, and `docs/tasks/implementation/stage-2/TASK-017-wb-api-acceptance-and-release.md:79`-`docs/tasks/implementation/stage-2/TASK-017-wb-api-acceptance-and-release.md:95` make the rule implementation and acceptance evidence requirements.

Риск из первичного аудита устранён: silent fallback to calculation Excel price is explicitly banned and testable.

## Regression Check

No new blocking regressions found in:

- Stage split and Stage 1 invariants: `docs/stages/stage-2/STAGE_2_SCOPE.md`.
- Stage 2.1 WB scope: `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`.
- API connection, operation, audit/techlog, UI and WB discount API specs.
- Stage 2.1 testing protocol and acceptance checklists.
- TASK-011..TASK-017 and `docs/tasks/implementation/stage-2/IMPLEMENTATION_TASKS.md`.
- GAP/ADR state: `docs/gaps/GAP_REGISTER.md` reports no open Stage 2.1 GAP; ADR-0016..ADR-0020 cover current Stage 2.1 decisions.

## Проверенные источники

- `docs/audit/AUDIT_REPORT_STAGE_2_1_WB_DOCUMENTATION.md`
- `docs/source/stage-inputs/tz_stage_2.1.txt` §5.5, §6.6, §9.2, §10.1, §11, §15.4, §16, §19
- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/orchestration/TASK_TEMPLATES.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/product/UI_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/product/WB_DISCOUNTS_API_SPEC.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/tasks/implementation/stage-2/IMPLEMENTATION_TASKS.md`
- `docs/tasks/implementation/stage-2/TASK-011-wb-api-connections.md`
- `docs/tasks/implementation/stage-2/TASK-012-wb-api-prices-download.md`
- `docs/tasks/implementation/stage-2/TASK-013-wb-api-current-promotions-download.md`
- `docs/tasks/implementation/stage-2/TASK-014-wb-api-discount-calculation-excel-output.md`
- `docs/tasks/implementation/stage-2/TASK-015-wb-api-discount-upload.md`
- `docs/tasks/implementation/stage-2/TASK-016-wb-api-ui-stage-2-1.md`
- `docs/tasks/implementation/stage-2/TASK-017-wb-api-acceptance-and-release.md`
- linked Stage 2.1 scope/acceptance/traceability docs for regression check.

## Required Fixes

None.

## Questions For Customer Via Orchestrator

None.

## Audit Result

Verdict: PASS.

Stage 2.1 documentation is ready for commit and implementation task orchestration.

Implementation may start: yes, after the documentation changes are committed and the orchestrator issues implementation tasks. Do not start implementation from this audit task.

Changed files in this audit:

- `docs/audit/AUDIT_REPORT_STAGE_2_1_WB_DOCUMENTATION_RECHECK.md`
