# TEST_REPORT_TASK_015

Task: `TASK-015 Stage 2.1 WB API discount upload`  
Tester: Codex CLI, tester role  
Date: 2026-04-26  
Verdict: FAIL

## Scope

Checked TASK-015 behavior against:

- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/tasks/implementation/stage-2/TASK-015-wb-api-discount-upload.md`
- `docs/product/WB_DISCOUNTS_API_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/testing/TEST_REPORT_TASK_014.md`

Product code was not changed. Real WB calls and real secrets were not used. Tests used mocked WB clients and the normal `.env.runtime` PostgreSQL test database.

## Results

| Area | Result |
| --- | --- |
| Upload requires exact confirmation phrase before creating upload operation | PASS |
| Permissions `wb.api.discounts.upload` and `wb.api.discounts.upload.confirm`, object access and active connection | PASS |
| Upload requires successful 2.1.3 calculation without errors | PASS |
| Pre-upload drift check uses `POST /api/v2/list/goods/filter` with `nmList` batches <=1000 and blocks upload | PASS |
| Normal upload payload contains only `nmID` + `discount`; no `price` | PASS |
| Discount-only rejection stops safely; no stale price fallback | PASS |
| Batch size <=1000, uploadID per batch, payload checksum per batch | PASS |
| Status polling is required; HTTP 200 alone is not final success | PASS |
| WB statuses 3/4/5/6, 208, 429/auth/timeout safe handling covered by tests or client behavior | PASS |
| Operation classifier `mode=api`, `marketplace=wb`, `step_code=wb_api_discount_upload`, non-check/process type | PASS |
| Secret redaction in checked operation/audit/techlog/reports/test output | PASS |
| Quarantine rows are shown separately and do not hide applied rows | FAIL |
| Stage 1 WB/Ozon regression and full suite | PASS |

## Commands And Results

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check
```

Result: PASS. `System check identified no issues (0 silenced).`

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
```

Result: PASS. `No changes detected`.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api.upload --verbosity 2 --noinput
```

Result: PASS. Ran 7 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api apps.operations apps.files apps.stores apps.audit apps.techlog apps.identity_access --verbosity 2 --noinput
```

Result: PASS. Ran 111 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_excel apps.discounts.ozon_excel --verbosity 2 --noinput
```

Result: PASS. Ran 21 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test --verbosity 1 --noinput
```

Result: PASS. Ran 152 tests.

```bash
rg -n "urlopen\(|requests\.|WBApiClient\(|upload_discount_task\(|/api/v2/upload/task|test_files/secrets|Bearer|Authorization|api key|token" apps/discounts/wb_api apps/discounts/wb_excel apps/discounts/ozon_excel -g '*.py'
```

Result: PASS for no real WB calls in tests. Upload tests inject `FakeUploadClient`; scan found production client and synthetic test token strings only. No `test_files/secrets` usage.

## Test IDs

Test ID: TASK-015-CONFIRMATION-PERMISSIONS-CALCULATION  
Scenario: missing exact confirmation, missing rights/object access, failed calculation.  
Expected: upload is not started.  
Actual: focused test passed; wrong phrase leaves no upload operation; outsider and failed calculation are rejected.  
Status: pass.

Test ID: TASK-015-DRIFT  
Scenario: current WB price differs from calculation price.  
Expected: drift check blocks before upload POST and records `wb_api_upload_blocked_by_drift`.  
Actual: focused test passed; upload payload list remains empty.  
Status: pass.

Test ID: TASK-015-PAYLOAD-NO-STALE-PRICE  
Scenario: calculation detail and result Excel contain stale price-like values.  
Expected: POST payload contains only `nmID` and `discount`; no `price` or stale Excel/snapshot price.  
Actual: focused test passed; payload is `{"nmID": 101, "discount": 30}` only.  
Status: pass.

Test ID: TASK-015-DISCOUNT-ONLY-REJECTION  
Scenario: WB rejects discount-only payload.  
Expected: safe stop/escalation, no retry with old price.  
Actual: focused test passed; operation becomes `interrupted_failed`, one payload attempt, no `price`.  
Status: pass.

Test ID: TASK-015-BATCH-STATUS-208-PARTIAL-QUARANTINE  
Scenario: >1000 rows, second batch receives 208 with uploadID, partial status and quarantine row.  
Expected: batches <=1000, uploadID per batch, status polling drives result.  
Actual: focused test passed for batch split, uploadIDs, partial warning and quarantine event. Static review found missing mixed-quarantine coverage and a detail mapping defect below.  
Status: fail.

Test ID: TASK-015-CLASSIFIER-REDACTION  
Scenario: completed upload operation and safe outputs.  
Expected: `mode=api`, WB step code, non-check/process type; no secret-like values in checked operation/audit/techlog.  
Actual: focused test passed.  
Status: pass.

Test ID: TASK-015-STAGE1-REGRESSION-FULL-SUITE  
Scenario: Stage 1 WB/Ozon and full project suite after TASK-015 changes.  
Expected: no regressions.  
Actual: Stage 1 WB/Ozon 21 tests passed; full suite 152 tests passed.  
Status: pass.

## Findings / Defects

Defect TASK-015-D1 - quarantine code leaks from batch outcome to non-quarantined rows in the same batch.  
Severity: High for acceptance behavior, non-destructive for WB safety.

Evidence:

- `apps/discounts/wb_api/upload/services.py:623` computes batch `result_code` with `has_quarantine=bool(quarantine_rows)`, so any quarantine in the batch makes the batch result code `wb_api_upload_quarantine`.
- `apps/discounts/wb_api/upload/services.py:639` assigns `row_result_code = "wb_api_upload_quarantine" if quarantine else result_code`.
- Therefore, a non-quarantined row in a batch with `wb_status == 3` and at least one different quarantined nmID receives reason code `wb_api_upload_quarantine` while row status is `ok`.
- This conflicts with `WB_DISCOUNTS_API_SPEC.md` quarantine requirements: quarantine rows must be shown separately and applied rows must not be hidden behind quarantine rows.
- Existing test coverage at `apps/discounts/wb_api/upload/tests.py:338` uses a quarantine batch containing only one row, so it does not catch mixed applied/quarantine rows in the same batch.

No new GAP was opened; this is an implementation defect against existing spec, not a missing rule.

## Audit Readiness

Not ready for audit. The upload safety gates are mostly covered and the suites are green, but TASK-015 should be fixed and retested for mixed quarantine batches before audit.

## Changed Files

- `docs/testing/TEST_REPORT_TASK_015.md`

Existing implementation changes were already present in the worktree and were not modified by this tester check:

- `apps/discounts/wb_api/client.py`
- `apps/discounts/wb_api/upload/`
