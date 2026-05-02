# TASK_PC2_003_API_ARTICLE_LINKAGE_REPORT

Date: 2026-05-02
Role: Codex CLI, technical writer closeout
Task: `TASK-PC2-003 Normalized Article Linkage And Auto-Create`
Status: CLOSED / READY FOR COMMIT

## Scope

This closeout covers only the narrowed `TASK-PC2-003` API linkage slice:

- exact trimmed valid API article linkage to an existing active/non-archived `ProductVariant`;
- API auto-create of `InternalProduct` plus `ProductVariant` with `review_state=imported_draft` when a valid article has no safe existing variant and no conflict;
- reuse of the same `internal_sku` across stores/marketplaces;
- later title mismatch handling that preserves first product/variant names, keeps the listing `matched`, and marks the variant `needs_review`;
- audit/history/source-context recording for the API/service path;
- conflict/listing-only behavior for unsafe, blank, invalid, duplicate or non-unified article cases.

Deferred and not closed by this report:

- external mapping table preview/apply workflow;
- `visual_external` table workflow;
- upload/apply UI, file/table contract, mapping-table permissions and mapping-table tests;
- full CORE-2 release completion.

`GAP-CORE2-007` remains deferred/future for the mapping-table workflow. Full CORE-2 remains in progress.

## Inputs

- `docs/reports/TASK_PC2_003_DESIGN_HANDOFF.md`
- `docs/testing/TEST_REPORT_TASK_PC2_003_API_ARTICLE_LINKAGE.md`
- `docs/audit/AUDIT_REPORT_TASK_PC2_003_API_ARTICLE_LINKAGE.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_ACCEPTANCE_CHECKLIST.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md`

No additional final TZ sections were issued for this closeout task.

## Changed Files

Implementation files recorded by tester/auditor evidence:

- `apps/product_core/services.py`
- `apps/product_core/tests.py`
- `apps/techlog/models.py`
- `apps/techlog/tests.py`

Migration:

- `apps/techlog/migrations/0010_alter_techlogrecord_event_type.py`

Task evidence and closeout documentation:

- `docs/reports/TASK_PC2_003_DESIGN_HANDOFF.md`
- `docs/testing/TEST_REPORT_TASK_PC2_003_API_ARTICLE_LINKAGE.md`
- `docs/audit/AUDIT_REPORT_TASK_PC2_003_API_ARTICLE_LINKAGE.md`
- `docs/reports/TASK_PC2_003_API_ARTICLE_LINKAGE_REPORT.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_ACCEPTANCE_CHECKLIST.md`

No product code was changed by this closeout task.

## Migration

Migration `apps/techlog/migrations/0010_alter_techlogrecord_event_type.py` is accepted as limited and justified. It updates `TechLogRecord.event_type` choices to include `marketplace_sync.data_integrity_error`, matching the CORE-2 techlog catalog and closing the duplicate external article techlog finding.

The migration does not introduce Product Core model changes, UI changes, permission changes or marketplace write behavior.

## Test Evidence

Tester report: `docs/testing/TEST_REPORT_TASK_PC2_003_API_ARTICLE_LINKAGE.md`

Final tester verdict: PASS.

Recorded passing commands:

| Command | Result |
| --- | --- |
| `git diff --check` | PASS, no whitespace errors reported. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` | PASS, no system check issues. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run` | PASS, no changes detected. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.product_core apps.techlog --verbosity 1 --noinput` | PASS, 59 tests OK. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api.prices apps.discounts.wb_api.promotions apps.discounts.ozon_api --verbosity 1 --noinput` | PASS, 60 tests OK. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.web apps.operations apps.marketplace_products --verbosity 1 --noinput` | PASS, 71 tests OK. |

Tester confirmed no new gaps and no `visual_external`/mapping-table implementation in this slice.

## Audit Evidence

Audit report: `docs/audit/AUDIT_REPORT_TASK_PC2_003_API_ARTICLE_LINKAGE.md`

Final audit verdict: PASS.

Auditor confirmed:

- scope is exactly the narrowed TASK-PC2-003 API slice;
- exact trim-only matching follows the approved policy;
- API auto-create follows the resolved `GAP-CORE2-006` field policy and creates imported/draft variants;
- repeated same SKU reuses one variant;
- unsafe, archived, pre-linked or impossible `internal_sku` states do not auto-link, overwrite or auto-create;
- duplicate external article rows are skipped before auto-link/auto-create and logged with the approved techlog event/severity;
- no UI/mapping-table/`visual_external` workflow and no marketplace card-field writes were implemented;
- documentation does not mark full CORE-2 or deferred mapping-table scope complete.

Auditor reran:

| Command | Result |
| --- | --- |
| `git diff --check` | PASS |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` | PASS, no system check issues. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.product_core apps.techlog --verbosity 1 --noinput` | PASS, 59 tests OK. |

## Previous Findings

| Previous finding | Closeout result |
| --- | --- |
| MAJOR-1 inactive product/variant can be selected for automatic API mapping. | CLOSED by active product/variant safe-selection fixes and focused tests. |
| MAJOR-2 duplicate external article techlog does not match the CORE-2 techlog catalog. | CLOSED by `marketplace_sync.data_integrity_error`, ERROR severity baseline, service-helper logging and tests. |

No remaining blocker, major or minor audit findings are recorded for this task.

## ADR/GAP Context

- `GAP-CORE2-006` is reflected as the accepted imported/draft auto-create policy for this narrowed API slice.
- `GAP-CORE2-007` remains deferred/future and is not closed by this report.
- No new gaps were opened by closeout.

## Final Decision

`TASK-PC2-003 Normalized Article Linkage And Auto-Create` is closed and ready for commit.

Only the narrowed API exact valid article linkage plus auto-create/imported_draft slice is closed here. External mapping table / `visual_external` and full CORE-2 release completion remain outside this closeout.
