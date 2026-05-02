# TASK_PC2_004_OPERATION_ROW_FK_ENRICHMENT_REPORT

Date: 2026-05-02
Role: Codex CLI, technical writer closeout
Task: `TASK-PC2-004 Operation Row FK Enrichment`
Status: CLOSED / READY FOR COMMIT

## Scope

This closeout covers only `TASK-PC2-004`: deterministic nullable `OperationDetailRow.marketplace_listing` FK enrichment.

The closed slice includes:

- same-store/same-marketplace resolver using exact approved listing keys only;
- writer hooks for approved Stage 1 WB/Ozon Excel, Stage 2.1 WB API and Stage 2.2 Ozon Elastic operation detail product rows;
- bounded idempotent backfill command `backfill_operation_detail_listing_fk` with dry-run default, `--write`, `--limit`, `--start-id` and `--end-id`;
- narrow terminal-row guard that permits only `marketplace_listing_id` updates inside the explicit enrichment context;
- pre/post row count and `(id, product_ref)` checksum evidence, with expected `product_ref` changes equal to `0`;
- summary/action rows intentionally left unlinked, including Ozon actions and WB promotion summary/current-filter rows.

Out of scope and not closed by this report:

- any mutation of `OperationDetailRow.product_ref`;
- operation summary/status/files/reason/result/message/problem/final_value or calculation/upload behavior changes;
- UI/report listing-link display;
- marketplace write endpoints or marketplace card-field updates;
- full CORE-2 release completion.

Full CORE-2 remains in progress.

## Inputs

- `docs/reports/TASK_PC2_004_DESIGN_HANDOFF.md`
- `docs/testing/TEST_REPORT_TASK_PC2_004_OPERATION_ROW_FK_ENRICHMENT.md`
- `docs/audit/AUDIT_REPORT_TASK_PC2_004_OPERATION_ROW_FK_ENRICHMENT.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_ACCEPTANCE_CHECKLIST.md`

No additional final TZ sections were issued for this closeout task.

## Changed Files

Implementation files recorded by tester/auditor evidence:

- `apps/operations/models.py`
- `apps/operations/listing_enrichment.py`
- `apps/operations/management/commands/backfill_operation_detail_listing_fk.py`
- `apps/operations/management/__init__.py`
- `apps/operations/management/commands/__init__.py`
- `apps/operations/tests.py`
- `apps/discounts/wb_excel/services.py`
- `apps/discounts/wb_excel/tests.py`
- `apps/discounts/ozon_excel/services.py`
- `apps/discounts/wb_api/prices/services.py`
- `apps/discounts/wb_api/prices/tests.py`
- `apps/discounts/wb_api/promotions/services.py`
- `apps/discounts/wb_api/promotions/tests.py`
- `apps/discounts/wb_api/calculation/services.py`
- `apps/discounts/wb_api/upload/services.py`
- `apps/discounts/ozon_api/products.py`
- `apps/discounts/ozon_api/product_data.py`
- `apps/discounts/ozon_api/calculation.py`
- `apps/discounts/ozon_api/upload.py`
- `apps/discounts/ozon_api/tests.py`

Task evidence and closeout documentation:

- `docs/reports/TASK_PC2_004_DESIGN_HANDOFF.md`
- `docs/testing/TEST_REPORT_TASK_PC2_004_OPERATION_ROW_FK_ENRICHMENT.md`
- `docs/audit/AUDIT_REPORT_TASK_PC2_004_OPERATION_ROW_FK_ENRICHMENT.md`
- `docs/reports/TASK_PC2_004_OPERATION_ROW_FK_ENRICHMENT_REPORT.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_ACCEPTANCE_CHECKLIST.md`

No product code was changed by this closeout task.

## Test Evidence

Tester report: `docs/testing/TEST_REPORT_TASK_PC2_004_OPERATION_ROW_FK_ENRICHMENT.md`

Final tester verdict: PASS.

Recorded passing commands:

| Command | Result |
| --- | --- |
| `git diff --check` | PASS. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` | PASS, no system check issues. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run` | PASS, no changes detected. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.operations apps.product_core --verbosity 1 --noinput` | PASS, 75 tests. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts --verbosity 1 --noinput` | PASS, 102 tests. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py help backfill_operation_detail_listing_fk` | PASS, command options exposed. |

Tester confirmed the previous writer-hook blocker is closed. Direct FK assertions are representative rather than exhaustive for every discount writer, but this residual risk is accepted because all approved hooks call the common tested enrichment service and the full discounts regression suite passed.

## Audit Evidence

Audit report: `docs/audit/AUDIT_REPORT_TASK_PC2_004_OPERATION_ROW_FK_ENRICHMENT.md`

Final audit verdict: PASS.

Auditor confirmed:

- `product_ref` is preserved byte-for-byte and enrichment writes only `marketplace_listing_id`;
- resolver is deterministic, exact-key only, same-store and same-marketplace scoped;
- action/promotion summary rows remain unlinked while product rows link when a safe unique listing exists;
- terminal immutability remains intact except for the explicit FK enrichment path;
- backfill is dry-run by default, bounded/resumable/idempotent and records row count, `(id, product_ref)` checksum, conflict counts, family counts, same-scope violation evidence and changed `product_ref` count;
- existing different FK values are not overwritten;
- no UI/report leak path and no marketplace write behavior were added;
- tester residual risk is acceptable and not a release blocker for this task.

Auditor reran:

| Command | Result |
| --- | --- |
| `git diff --check` | PASS. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` | PASS, no system check issues. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.operations apps.product_core --verbosity 1 --noinput` | PASS, 75 tests. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts --verbosity 1 --noinput` | PASS, 102 tests. |

## Residual Risk

The public enrichment context manager can be misused by future code to update `marketplace_listing_id` directly. Current production callers use the common enrichment service, and tests prove protected fields remain blocked. This risk is accepted for TASK-PC2-004.

Several writer hooks have static placement plus full-suite regression evidence rather than direct FK assertions in every individual flow. This is accepted because the common resolver/backfill/guard service is covered and representative writer tests passed.

No new gaps were opened by closeout.

## Final Decision

`TASK-PC2-004 Operation Row FK Enrichment` is closed and ready for commit.

Only this deterministic operation-row FK enrichment slice is closed by this report. Full CORE-2 remains in progress and must not be treated as release-complete.
