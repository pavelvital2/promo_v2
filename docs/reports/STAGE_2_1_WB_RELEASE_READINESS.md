# STAGE_2_1_WB_RELEASE_READINESS

Date: 2026-04-26 17:40 MSK  
Release area: Stage 2.1 WB API  
Verdict: READY

## Summary

Stage 2.1 WB API release gates are satisfied on the current workspace:

- TASK-011..TASK-016 implementation evidence and audits are PASS after rechecks.
- Stage 2.1 documentation audit recheck is PASS.
- No open Stage 2.1 GAP is registered.
- Current `.env.runtime` checks passed: system check, migration check, impacted Stage 2.1 suite, Stage 1 WB Excel regression and full suite.
- Real WB token files and real `test_files/secrets` were not read or printed.
- WB API verification remained mock/stub-based.
- Ozon API / Stage 2.2 was not touched.

## Release Gate Results

| Gate | Result |
| --- | --- |
| Documentation audit gate | PASS |
| TASK-011 connection prerequisite | PASS |
| TASK-012 prices download | PASS |
| TASK-013 promotions download | PASS |
| TASK-014 calculation/result Excel | PASS |
| TASK-015 discount upload | PASS |
| TASK-016 UI/master/confirmation | PASS |
| Stage 1 WB Excel regression | PASS, 11 tests |
| Full Django suite | PASS, 160 tests |
| Stage 2.1 impacted suite | PASS, 139 tests |
| Migration drift | PASS, no changes detected |
| Secret redaction safety | PASS |
| Discount-only upload/no stale price fallback | PASS |
| Operation `step_code` / non-check-process contract | PASS |

## Release Commands

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api apps.operations apps.files apps.stores apps.audit apps.techlog apps.identity_access apps.marketplace_products apps.web --verbosity 1 --noinput
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_excel --verbosity 2 --noinput
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test --verbosity 1 --noinput
```

Results:

- `manage.py check`: PASS.
- `makemigrations --check --dry-run`: PASS.
- Stage 2.1 impacted suite: PASS, 139 tests.
- Stage 1 WB Excel regression: PASS, 11 tests.
- Full suite: PASS, 160 tests.

## Readiness Rationale

Stage 2.1 WB API preserves Stage 1 Excel availability and classification semantics. API operations are classified by `Operation.step_code`, with `Operation.type` left as non-check/process for WB API steps. Upload is gated by explicit confirmation, successful calculation, active connection, permissions/object access, pre-upload drift check and WB status polling. The normal upload payload is discount-only (`nmID` + `discount`), and tests prove there is no stale `price` fallback if WB rejects discount-only payload.

Secret handling is covered by connection, prices, promotions, calculation, upload and UI tests. The TASK-015 A1 recheck specifically verifies redaction of WB goods-level `errorText` / `error` before row persistence, report generation, audit and techlog.

## Residual Notes

- `apps/discounts/wb_api/calculation/test_settings.py` remains a non-blocking housekeeping note from TASK-014 audit; acceptance evidence uses `.env.runtime`, not that helper.
- Dedicated upload batch/detail models are not implemented as physical models. TASK-015 audit recheck accepted the current operation summary, report and detail-row persistence as sufficient for TASK-015 acceptance. Treat this only as a future model-compliance consideration unless the orchestrator opens a separate task.

## Release Decision

Ready for release handoff to orchestrator, auditor and release owner.

No blockers. No open questions for customer escalation through the orchestrator.

