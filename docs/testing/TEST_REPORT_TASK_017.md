# TEST_REPORT_TASK_017

Task: `TASK-017 Stage 2.1 WB API acceptance and release`  
Tester: Codex CLI, acceptance/release role  
Date: 2026-04-26 17:40 MSK  
Verdict: PASS / READY

## Scope

Checked Stage 2.1 WB API release readiness against:

- `docs/tasks/implementation/stage-2/TASK-017-wb-api-acceptance-and-release.md`
- `docs/tasks/implementation/stage-2/IMPLEMENTATION_TASKS.md`
- TASK-011..TASK-016 task files and existing test/audit reports
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_1_WB_ACCEPTANCE_TESTS.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/traceability/STAGE_2_1_WB_TRACEABILITY_MATRIX.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`, ADR-0016..ADR-0020 only
- `tz_stage_2.1.txt` scoped sections: §5.5, §6.6, §9.2, §10.1, §11, §15.4, §16, §18

Product logic was not changed. Real WB token files and real `test_files/secrets` were not read or printed. WB API checks remained mock/stub-based. Ozon API / Stage 2.2 was not touched.

## Evidence Reviewed

| Area | Evidence | Status |
| --- | --- | --- |
| Documentation audit gate | `docs/audit/AUDIT_REPORT_STAGE_2_1_WB_DOCUMENTATION_RECHECK.md` | PASS |
| TASK-011 connection contour | `TEST_REPORT_TASK_011_RECHECK.md`, `AUDIT_REPORT_TASK_011_RECHECK.md` | PASS |
| TASK-012 prices download | `TEST_REPORT_TASK_012.md`, `AUDIT_REPORT_TASK_012.md` | PASS |
| TASK-013 current promotions | `TEST_REPORT_TASK_013_RECHECK.md`, `AUDIT_REPORT_TASK_013.md` | PASS |
| TASK-014 calculation/result Excel | `TEST_REPORT_TASK_014.md`, `AUDIT_REPORT_TASK_014.md` | PASS WITH HOUSEKEEPING REMARK |
| TASK-015 upload | `TEST_REPORT_TASK_015_A1_RECHECK.md`, `AUDIT_REPORT_TASK_015_RECHECK.md` | PASS |
| TASK-016 UI | `TEST_REPORT_TASK_016_RECHECK.md`, `AUDIT_REPORT_TASK_016.md` | PASS |
| GAP state | `docs/gaps/GAP_REGISTER.md` | No open Stage 2.1 GAP |
| Traceability | `docs/traceability/STAGE_2_1_WB_TRACEABILITY_MATRIX.md` plus passing test/audit evidence | Covered |

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
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api apps.operations apps.files apps.stores apps.audit apps.techlog apps.identity_access apps.marketplace_products apps.web --verbosity 1 --noinput
```

Result: PASS. Ran 139 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_excel --verbosity 2 --noinput
```

Result: PASS. Ran 11 tests. Stage 1 WB Excel regression remains passable.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test --verbosity 1 --noinput
```

Result: PASS. Ran 160 tests.

```bash
rg -n "calendar/promotions/upload|api/v1/calendar/promotions/upload|/api/v2/upload/task/size|/api/v2/upload/task/club|club-discount|clubDiscountUpload" apps/discounts/wb_api apps/web -g '*.py' -g '*.html'
```

Result: PASS. No forbidden WB Promotions upload, size upload or WB Club upload references in Stage 2.1 WB API/UI paths.

```bash
rg -n "test_files/secrets|secrets/|WB_REAL|real WB|real token" apps/discounts/wb_api apps/web apps/stores -g '*.py' -g '*.html'
```

Result: PASS. No real secret/test secret file usage found in checked Stage 2.1 code paths.

```bash
find apps config -type d -name __pycache__ -prune -exec rm -rf {} + && find apps config -type f -name '*.pyc' -delete && find apps config -type d -name __pycache__ -o -name '*.pyc'
```

Result: PASS. Test-generated Python cache artifacts were removed; final check printed no entries.

## Acceptance Checklist Execution

| Checklist area | Result | Evidence |
| --- | --- | --- |
| Documentation audit passed before implementation | PASS | Stage 2.1 documentation recheck PASS |
| WB Excel Stage 1 remains available and tests pass | PASS | `apps.discounts.wb_excel`, 11 tests PASS; full suite PASS |
| Ozon API Stage 2.2 not touched | PASS | Scope docs/audits; no Ozon API paths involved |
| WB API token only via `protected_secret_ref` | PASS | TASK-011 recheck/audit and redaction tests |
| No secret-like values in metadata/audit/techlog/snapshots/UI/files/reports/test output | PASS | TASK-011..016 redaction tests; TASK-015 A1 recheck; current static safety scan |
| Object access for stores, operations, files, products, promotions, connection | PASS | TASK-011, TASK-012, TASK-013, TASK-016 tests/audits |
| Stage 2.1 operations have mandatory `step_code`; non-check/process `Operation.type` | PASS | TASK-012..016 classifier tests and DB/model constraints |
| 2.1.1 prices download, pagination, rate, Excel, products/history, size conflict | PASS | TASK-012 test/audit report |
| 2.1.2 current promotions, details batches, nomenclatures, auto promotions, promo files | PASS | TASK-013 recheck/audit report |
| 2.1.3 calculation reuses Stage 1 WB logic, decimal+ceil, result Excel only `Новая скидка` | PASS | TASK-014 test/audit report |
| 2.1.4 upload gates, confirmation, drift, batching, uploadID, polling, statuses, quarantine | PASS | TASK-015 A1 recheck/audit report |
| Discount-only payload and no stale price fallback | PASS | `test_normal_payload_has_only_nmid_discount_and_never_uses_excel_or_old_price`; `test_discount_only_rejection_stops_safely_without_fallback_price` |
| Manual/UI confirmation flow coverage | PASS | `test_wb_api_upload_confirmation_posts_exact_phrase_to_service`; confirmation template renders read-only phrase field and POST path calls upload service |
| Traceability rows covered | PASS | Matrix rows have corresponding test/audit evidence from TASK-011..016 and current TASK-017 run |
| Backup/restore policy still valid for new DB/file entities | PASS BY DOCUMENTATION | No Stage 2.1-specific open blocker; Stage 1 policy remains the documented baseline |

## Acceptance Mock Scenarios

Covered by existing focused tests and rerun as part of the impacted/full suites:

- Prices API mocks: pagination to empty page, equal/missing/conflicting size prices, 401/403, 429, timeout/invalid response.
- Promotions API mocks: strict current filter, details batching, nomenclatures pagination, regular/auto behavior, invalid product rows.
- Calculation mocks/golden comparison: API-generated inputs produce Stage 1-equivalent WB calculation output with decimal + ceil and upload-blocking errors.
- Upload mocks: confirmation absent, drift, discount-only payload, discount-only rejection without fallback, batch split, statuses 3/4/5/6, 208, 429/auth/timeout, partial/quarantine rows, redacted WB goods error text.

## Findings

No blocking TASK-017 acceptance defects found.

Residual non-blocking notes:

- TASK-014 audit kept a housekeeping remark about `apps/discounts/wb_api/calculation/test_settings.py`, an isolated SQLite settings helper. It is not used by `.env.runtime` acceptance runs and does not block release readiness.
- TASK-015 audit noted that dedicated physical `WBApiUploadBatch` / `WBApiUploadDetail` models are not present; the recheck accepted operation summary, output report and `OperationDetailRow` persistence as sufficient for TASK-015 acceptance. This remains a release-planning consideration only unless the orchestrator raises a separate model-compliance task.

## GAP / Escalation

No new GAP was opened. No customer escalation question is required for TASK-017 acceptance.

## Changed Files

- `docs/testing/TEST_REPORT_TASK_017.md`
- `docs/reports/STAGE_2_1_WB_RELEASE_READINESS.md`

## Final Verdict

Stage 2.1 WB API is ready for release handoff from the acceptance/release testing perspective.

