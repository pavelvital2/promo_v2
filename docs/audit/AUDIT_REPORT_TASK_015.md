# AUDIT_REPORT_TASK_015

Task: `TASK-015 Stage 2.1 WB API discount upload`  
Auditor: Codex CLI, audit role  
Date: 2026-04-26  
Verdict: PASS WITH REQUIRED FIXES

## Проверенная область

- Stage 2.1 / 2.1.4 WB API discount upload.
- Upload gates: calculation basis, exact confirmation, rights, object access, active connection.
- Drift check, discount-only payload, batching, `uploadID`, status polling, 208/429/auth/timeout behavior.
- Partial/quarantine row mapping, including recheck closure for `TASK-015-D1`.
- Secret handling in operation/audit/techlog/snapshots/files/reports/test output.
- Regression boundaries: no Ozon API changes and no Stage 1 WB Excel behavior change.

## Проверенные файлы

- `docs/tasks/implementation/stage-2/TASK-015-wb-api-discount-upload.md`
- `docs/product/WB_DISCOUNTS_API_SPEC.md`
- `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/testing/TEST_REPORT_TASK_015.md`
- `docs/testing/TEST_REPORT_TASK_015_RECHECK.md`
- `apps/discounts/wb_api/client.py`
- `apps/discounts/wb_api/upload/services.py`
- `apps/discounts/wb_api/upload/tests.py`
- `apps/discounts/wb_api/calculation/services.py`
- `apps/discounts/wb_api/calculation/tests.py`
- `apps/operations/models.py`
- `apps/operations/services.py`

## Findings

### TASK-015-A1 - Raw WB `errorText` can be persisted as `errorText_safe`

Severity: High.  
Status: REQUIRED FIX.

`apps/discounts/wb_api/upload/services.py:319` builds a redacted `safe_snapshot` from polling details, but the function returns the original unredacted `details`. Later `apps/discounts/wb_api/upload/services.py:655` selects `item_detail` from those raw details and `apps/discounts/wb_api/upload/services.py:682` stores `item_detail.get("errorText")` / `item_detail.get("error")` directly into `OperationDetailRow.final_value["errorText_safe"]`.

This violates the Stage 2.1 secret invariant if WB ever echoes a token-like/header-like value in a goods-level error. `docs/architecture/API_CONNECTIONS_SPEC.md:36-45` forbids token/header/API key/bearer/secret-like values outside `protected_secret_ref`, including audit, techlog, UI, exports, files, reports and test output. `docs/product/WB_DISCOUNTS_API_SPEC.md:199` requires status details to be saved as safe snapshot data, and `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md:73-74` requires safe snapshots and safe outputs to contain no secret-like values.

The existing secret test covers operation summary/audit/techlog for a safe mocked error string, but it does not exercise a secret-like `errorText` from `history_goods_task` / `buffer_goods_task`.

Required fix:

- Redact and validate goods-level `errorText` / `error` before persisting row `final_value`.
- Add a regression test where mocked WB goods detail returns a bearer/token-like value in `errorText`; assert operation detail rows, operation summary/report, audit and techlog do not contain it.
- Keep row-level partial/quarantine mapping from the D1 fix unchanged.

## TASK-015-D1

Status: CLOSED.

Evidence:

- `apps/discounts/wb_api/upload/services.py:335-350` now resolves row-level reason/status independently for quarantine, partial error and success rows.
- `apps/discounts/wb_api/upload/tests.py:375-399` covers status 3 mixed success/quarantine rows.
- `apps/discounts/wb_api/upload/tests.py:401-428` covers status 5 mixed partial/quarantine/success rows.
- Focused upload suite passed: 9 tests.

## Positive audit notes

- Upload gates are present before upload operation creation: rights/object access and confirmation at `apps/discounts/wb_api/upload/services.py:486-490`, successful WB API calculation at `apps/discounts/wb_api/upload/services.py:126-138`, result file at `apps/discounts/wb_api/upload/services.py:114-123`, active Stage 2.1 WB connection at `apps/discounts/wb_api/upload/services.py:97-111`.
- Drift check uses `list_goods_filter_by_nm_list` with `_chunks(..., 1000)` before POST upload and blocks on drift at `apps/discounts/wb_api/upload/services.py:184-239` and `apps/discounts/wb_api/upload/services.py:540-551`.
- Normal upload payload is discount-only and enforces exactly `nmID` + `discount` at `apps/discounts/wb_api/upload/services.py:242-247`.
- Upload POST is not retried blindly: `apps/discounts/wb_api/client.py:127-133` calls `post_json(..., retry=False)`.
- HTTP 200 alone is not treated as final success: upload extracts `uploadID` and polls history/buffer task endpoints at `apps/discounts/wb_api/upload/services.py:570-625`.
- Batch summary includes `payload_checksum`, `uploadID`, WB status and quarantine count at `apps/discounts/wb_api/upload/services.py:714-724`.
- 208 is handled through existing `uploadID` if available, otherwise safe failure at `apps/discounts/wb_api/upload/services.py:572-597`; client maps 401/403, 429 and timeout to safe exception classes at `apps/discounts/wb_api/client.py:290-307`.
- Operation classifier is enforced by model constraints and validation in `apps/operations/models.py:91-95`, `apps/operations/models.py:184-205`, and `apps/operations/models.py:229-250`.
- Static scan found no test usage of real `test_files/secrets`; upload tests inject `FakeUploadClient`.
- No Ozon API implementation or Stage 1 WB Excel code changes were required for this audit.

## Commands/tests run

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api.upload --verbosity 2 --noinput
```

Result: PASS. Ran 9 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check
```

Result: PASS. `System check identified no issues (0 silenced).`

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
```

Result: PASS. `No changes detected`.

```bash
rg -n "urlopen\(|requests\.|httpx\.|aiohttp|WBApiClient\(|upload_discount_task\(|/api/v2/upload/task|test_files/secrets|Bearer|Authorization|api key|token" apps/discounts/wb_api apps/discounts/wb_excel apps/discounts/ozon_excel -g '*.py'
```

Result: PASS for no real WB calls in tests and no `test_files/secrets` usage. Matches are production client code and synthetic test token strings.

Project `__pycache__` directories under `apps/` and `config/` were removed after test execution.

## Риски

- Current code has no dedicated `WBApiUploadBatch` / `WBApiUploadDetail` models from `docs/architecture/DATA_MODEL.md:263-264`; TASK-015 evidence persists batch data in operation summary and row data in `OperationDetailRow`. This audit does not mark it as an additional blocker because TASK-015 acceptance checks focus on batch checksum/`uploadID`, operation summary aggregation and row-level visibility, all of which are present. If the orchestrator requires physical upload batch/detail entities before Stage 2.1 release, track it as a separate model-compliance task before TASK-017.

## Обязательные исправления

1. Fix `TASK-015-A1` by redacting/validating goods-level polling detail text before any operation detail/report persistence.
2. Add focused redaction regression for secret-like WB `errorText` / `error`.
3. Rerun focused upload tests and safe-output scan.

## Открытые gaps

No new GAP opened. `TASK-015-A1` is an implementation defect against existing secret-handling specs, not a missing business rule.

## Spec-blocking вопросы

None.

## Требуется эскалация заказчику через оркестратора

No customer escalation required for the required fix.

## Может ли стартовать TASK-016

No. TASK-016 should wait for the `TASK-015-A1` required fix and recheck, because UI work would otherwise expose an upload detail field named `errorText_safe` that may contain unredacted WB text.

## Changed files

- `docs/audit/AUDIT_REPORT_TASK_015.md`

Итог: pass with required fixes.
