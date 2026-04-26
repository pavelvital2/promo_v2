# TEST_REPORT_TASK_015_A1_RECHECK

Task: `TASK-015 Stage 2.1 WB API discount upload`  
Recheck target: `TASK-015-A1` after required audit fix  
Tester: Codex CLI, tester role  
Date: 2026-04-26  
Verdict: PASS

## Scope

Checked the audit finding from `docs/audit/AUDIT_REPORT_TASK_015.md`:

- raw WB goods-level `errorText` / `error` must not be persisted in `OperationDetailRow.final_value["errorText_safe"]`;
- operation summary, upload report, audit and techlog must not contain the original secret-like text;
- TASK-015-D1 row-level quarantine/partial mapping must remain closed.

Product code was not changed by this tester recheck. Real WB calls and real WB token files were not used or read. Tests use mocked WB clients and synthetic token-like strings only.

## Result

| Area | Result |
| --- | --- |
| Secret-like WB goods detail `errorText` / `error` redacted before row persistence | PASS |
| Operation summary and generated upload report do not contain original secret-like goods detail text | PASS |
| Audit records and techlog records do not contain original secret-like goods detail text | PASS |
| TASK-015-D1 mixed quarantine/partial/success row-level mapping remains closed | PASS |
| Focused upload tests | PASS |
| Impacted WB API / operations / files / stores / audit / techlog / access tests | PASS |
| Full suite | PASS |

## Evidence

- `apps/discounts/wb_api/upload/services.py` now sanitizes goods details with `_safe_goods_detail()` / `_safe_goods_error_text()` and `_poll_batch_status()` returns `safe_details` for downstream row persistence.
- `apps/discounts/wb_api/upload/tests.py` includes `test_goods_error_text_is_redacted_before_detail_summary_report_audit_and_techlog`.
- The A1 regression test sends mocked WB goods detail containing `Authorization: Bearer ...` and `token=...`, then checks `OperationDetailRow.final_value`, operation summary, generated report file, audit and techlog.
- D1 regression tests still pass:
  - `test_mixed_status_3_quarantine_does_not_leak_to_success_rows`
  - `test_mixed_status_5_partial_and_quarantine_keep_row_level_codes`

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

Result: PASS. Ran 10 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api apps.operations apps.files apps.stores apps.audit apps.techlog apps.identity_access --verbosity 2 --noinput
```

Result: PASS. Ran 114 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test --verbosity 1 --noinput
```

Result: PASS. Ran 155 tests.

```bash
rg -n "urlopen\(|requests\.|httpx\.|aiohttp|WBApiClient\(|upload_discount_task\(|/api/v2/upload/task|test_files/secrets|Bearer|Authorization|api key|token" apps/discounts/wb_api apps/discounts/wb_excel apps/discounts/ozon_excel -g '*.py'
```

Result: PASS for test safety. Matches are production WB API client references and synthetic test token/assertion strings; no `test_files/secrets` usage was found.

## Findings

No defects found in this recheck.

`TASK-015-A1`: CLOSED.  
`TASK-015-D1`: remains CLOSED.

No new GAP was opened.

## Changed Files

Changed by this tester recheck:

- `docs/testing/TEST_REPORT_TASK_015_A1_RECHECK.md`

Existing worktree changes were not modified by this tester recheck:

- `apps/discounts/wb_api/client.py`
- `apps/discounts/wb_api/redaction.py`
- `apps/discounts/wb_api/upload/`
- `docs/audit/AUDIT_REPORT_TASK_015.md`
- `docs/testing/TEST_REPORT_TASK_015.md`
- `docs/testing/TEST_REPORT_TASK_015_RECHECK.md`
