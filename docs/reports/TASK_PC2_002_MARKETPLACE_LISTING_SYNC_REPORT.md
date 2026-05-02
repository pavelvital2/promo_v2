# TASK_PC2_002_MARKETPLACE_LISTING_SYNC_REPORT

Date: 2026-05-02
Role: Codex CLI, technical writer closeout
Task: `TASK-PC2-002 Marketplace Listing Sync Integration`
Status: CLOSED / READY FOR COMMIT

## Scope

This closeout covers only `TASK-PC2-002`: approved-source WB/Ozon marketplace listing sync integration with `MarketplaceListing` and `MarketplaceSyncRun`.

The closed slice includes:

- WB prices listing adapter behavior;
- WB regular promotion product-row adapter behavior in the approved slice;
- Ozon Elastic scoped adapter behavior for the selected action set;
- sync run summaries, safe summaries, techlog failure/warning evidence;
- failed sync/latest cache safety;
- duplicate external article/data-integrity guard retest evidence;
- no marketplace write endpoints or card-field updates.

Full CORE-2 remains in progress. This report does not mark CORE-2 release-complete and does not close any CORE-2 task other than `TASK-PC2-002`.

## Changed Files

Implementation files recorded by tester/auditor evidence:

- `apps/product_core/services.py`
- `apps/product_core/tests.py`

Task evidence and closeout documentation:

- `docs/testing/TEST_REPORT_TASK_PC2_002_MARKETPLACE_LISTING_SYNC.md`
- `docs/audit/AUDIT_REPORT_TASK_PC2_002_MARKETPLACE_LISTING_SYNC.md`
- `docs/reports/TASK_PC2_002_MARKETPLACE_LISTING_SYNC_REPORT.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_ACCEPTANCE_CHECKLIST.md`

No product code was changed by this closeout task.

## Test Evidence

Tester report: `docs/testing/TEST_REPORT_TASK_PC2_002_MARKETPLACE_LISTING_SYNC.md`

Final tester result: PASS.

Recorded passing commands:

| Command | Result |
| --- | --- |
| `git diff --check` | PASS, no output. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` | PASS, no system check issues. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run` | PASS, no changes detected. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.product_core --verbosity 1 --noinput` | PASS, 38 tests OK. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api.prices apps.discounts.wb_api.promotions apps.discounts.ozon_api --verbosity 1 --noinput` | PASS, 60 tests OK. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.web apps.operations apps.marketplace_products --verbosity 1 --noinput` | PASS, 71 tests OK. |

Tester closed:

- `D-PC2-002`: WB regular promotion rows no longer fabricate missing `MarketplaceListing` rows.
- `D-PC2-002-001`: duplicate non-empty `seller_article` rows are treated as source data integrity warnings and affected rows are skipped.

## Audit Evidence

Audit report: `docs/audit/AUDIT_REPORT_TASK_PC2_002_MARKETPLACE_LISTING_SYNC.md`

Final audit verdict: PASS.

Auditor confirmed:

- `D-PC2-002` remains closed;
- `D-PC2-002-001` is closed;
- no endpoint/call-site/write/upload changes and no full catalog expansion;
- no model or migration changes;
- secret-like values are protected in summaries, external ids, raw safe payloads and techlog;
- tester evidence is sufficient.

Auditor reran:

| Command | Result |
| --- | --- |
| `git diff --check` | PASS, no output. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` | PASS, no system check issues. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.product_core --verbosity 1 --noinput` | PASS, 38 tests OK. |
| Static scans for HTTP/write/upload/endpoint patterns in changed Product Core files | PASS, no new call sites/write/upload behavior. |

## Non-blocking Notes

- The standalone implementation task file `docs/tasks/implementation/product-core/TASK_PC2_002_MARKETPLACE_LISTING_SYNC.md` is absent in this worktree. This is non-blocking for this closeout because the orchestrator supplied the mandatory `CORE_2_AGENT_TASKS.md` section `TASK-PC2-002` and the CORE-2 reading package; both tester and auditor recorded the same note.
- This closeout does not change `docs/README.md`.

## Final Decision

`TASK-PC2-002 Marketplace Listing Sync Integration` is closed and ready for commit.

Only `TASK-PC2-002` is closed by this report. Full CORE-2 remains in progress and must not be treated as release-complete.
