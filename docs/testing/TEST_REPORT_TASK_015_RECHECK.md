# TEST_REPORT_TASK_015_RECHECK

Task: `TASK-015 Stage 2.1 WB API discount upload`  
Recheck target: `TASK-015-D1` plus upload safety regression  
Tester: Codex CLI, tester role  
Date: 2026-04-26  
Verdict: PASS

## Scope

Rechecked the defect from `docs/testing/TEST_REPORT_TASK_015.md`:

- quarantine result code leaked from a batch outcome to non-quarantined rows in the same batch.

Also reran the TASK-015 upload safety coverage:

- confirmation, permissions, successful calculation precondition;
- pre-upload drift check;
- discount-only payload without `price`;
- no stale price fallback;
- batching, uploadID per batch, polling, 208 handling;
- WB status mapping, partial errors, quarantine rows;
- 429/auth/timeout classifier coverage through related WB API client tests;
- operation classifier and secret redaction;
- Stage 1 WB/Ozon regression and full suite.

Product code was not changed by this recheck. Real WB calls and real secrets were not used.

## Results

| Area | Result |
| --- | --- |
| Mixed status 3 batch: success row remains `ok` / `wb_api_upload_success`; quarantine row is `warning` / `wb_api_upload_quarantine` | PASS |
| Mixed status 5 batch: partial error row, quarantine row and successful row keep separate row-level statuses/codes | PASS |
| Upload requires exact confirmation phrase, rights, object access, active connection and successful 2.1.3 calculation | PASS |
| Pre-upload drift check blocks before upload POST and records drift code | PASS |
| Normal upload payload contains only `nmID` + `discount`; no `price` | PASS |
| Discount-only rejection stops safely; no stale price fallback | PASS |
| Batch size <=1000, uploadID per batch, payload checksum per batch | PASS |
| Status polling is required; HTTP 200 alone is not final success | PASS |
| WB statuses 3/4/5/6, 208, 429/auth/timeout safe handling | PASS |
| Operation classifier `mode=api`, `marketplace=wb`, `step_code=wb_api_discount_upload`, non-check/process type | PASS |
| Secret redaction in checked operation/audit/techlog/snapshots/test output | PASS |
| Stage 1 WB/Ozon regression and full suite | PASS |

## Commands And Results

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api.upload --verbosity 2 --noinput
```

Result: PASS. Ran 9 tests. Includes:

- `test_mixed_status_3_quarantine_does_not_leak_to_success_rows`
- `test_mixed_status_5_partial_and_quarantine_keep_row_level_codes`

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check
```

Result: PASS. `System check identified no issues (0 silenced).`

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
```

Result: PASS. `No changes detected`.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api apps.operations apps.files apps.stores apps.audit apps.techlog apps.identity_access --verbosity 2 --noinput
```

Result: PASS. Ran 113 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_excel apps.discounts.ozon_excel --verbosity 2 --noinput
```

Result: PASS. Ran 21 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test --verbosity 1 --noinput
```

First parallel attempt result: infrastructure collision only. It overlapped with the Stage 1 regression command and failed to create `test_promo_v2` because another test session was using it.

Sequential rerun result: PASS. Ran 154 tests.

```bash
rg -n "urlopen\(|requests\.|WBApiClient\(|upload_discount_task\(|/api/v2/upload/task|test_files/secrets|Bearer|Authorization|api key|token" apps/discounts/wb_api apps/discounts/wb_excel apps/discounts/ozon_excel -g '*.py'
```

Result: PASS for no real WB calls in tests. Scan found production client endpoints and synthetic test token strings only; no `test_files/secrets` usage.

## TASK-015-D1 Recheck

Status: CLOSED.

Evidence:

- In status 3 mixed quarantine batch, product `501` remains `row_status=ok`, `reason_code=wb_api_upload_success`; product `502` is `row_status=warning`, `reason_code=wb_api_upload_quarantine`.
- In status 5 mixed partial/quarantine batch, product `601` is `warning` / `wb_api_upload_partial_error`; product `602` is `warning` / `wb_api_upload_quarantine`; product `603` is `ok` / `wb_api_upload_success`.
- Focused upload suite and broader regression suites passed.

## Findings

No recheck findings.

No new GAP was opened.

## Audit Readiness

Ready for audit for TASK-015 / `TASK-015-D1`.

## Changed Files

Changed by this tester recheck:

- `docs/testing/TEST_REPORT_TASK_015_RECHECK.md`

Existing worktree changes were not modified by this tester recheck:

- `apps/discounts/wb_api/client.py`
- `apps/discounts/wb_api/upload/`
- `docs/testing/TEST_REPORT_TASK_015.md`
