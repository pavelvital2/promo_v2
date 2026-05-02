# TEST_REPORT_TASK_PC2_003_API_ARTICLE_LINKAGE

Date: 2026-05-02
Role: tester
Task: TASK-PC2-003 narrowed API exact valid article linkage + auto-create/imported_draft
Retest scope: final retest after techlog cleanup
Verdict: PASS

Product code was not changed by this tester pass. Only this test report was updated.

## Retest Context

Final retest after cleanup of the TASK-PC2-003 audit finding for duplicate external article techlog:

- `TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR` was added with value `marketplace_sync.data_integrity_error`.
- `TECHLOG_EVENT_SEVERITY_BASELINE` maps this event type to `TechLogSeverity.ERROR`.
- Migration `apps/techlog/migrations/0010_alter_techlogrecord_event_type.py` is present for the `TechLogRecord.event_type` choices update.
- Product Core duplicate source data integrity logging uses `create_techlog_record`, not direct `TechLogRecord` construction.

Final retest verdict: PASS.

## Documents Read

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md`
- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/TEST_REPORT_TASK_PC2_003_API_ARTICLE_LINKAGE.md`

## Files Reviewed

- `apps/product_core/services.py`
- `apps/product_core/tests.py`
- `apps/techlog/models.py`
- `apps/techlog/tests.py`
- `apps/techlog/migrations/0010_alter_techlogrecord_event_type.py`

## Command Results

| Check | Result | Evidence |
| --- | --- | --- |
| `git diff --check` | PASS | No whitespace errors reported. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` | PASS | `System check identified no issues (0 silenced).` |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run` | PASS | `No changes detected`. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.product_core apps.techlog --verbosity 1 --noinput` | PASS | `Ran 59 tests in 8.446s`, `OK`. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api.prices apps.discounts.wb_api.promotions apps.discounts.ozon_api --verbosity 1 --noinput` | PASS | `Ran 60 tests in 82.881s`, `OK`. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.web apps.operations apps.marketplace_products --verbosity 1 --noinput` | PASS | `Ran 71 tests in 90.195s`, `OK`. |

## Static Evidence

| Requirement | Result | Evidence |
| --- | --- | --- |
| `marketplace_sync.data_integrity_error` is represented in `TechLogEventType` | PASS | `TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR` has value `marketplace_sync.data_integrity_error` in `apps/techlog/models.py:152`. |
| Data integrity event baseline severity is ERROR | PASS | `TECHLOG_EVENT_SEVERITY_BASELINE` maps `TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR` to `TechLogSeverity.ERROR` in `apps/techlog/models.py:217`. |
| Migration exists for updated `TechLogRecord.event_type` choices | PASS | `apps/techlog/migrations/0010_alter_techlogrecord_event_type.py` alters `TechLogRecord.event_type` and includes `marketplace_sync.data_integrity_error`. |
| Product Core duplicate techlog uses techlog service helper | PASS | `_record_source_data_integrity_warning()` calls `create_techlog_record(...)` with `severity="error"` and `event_type=TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR` in `apps/product_core/services.py:1097`. |
| Product Core duplicate techlog does not directly construct `TechLogRecord` | PASS | Static search found `TechLogRecord` usage in `apps/product_core/tests.py` only; `apps/product_core/services.py` imports and uses `create_techlog_record`. |
| No UI/mapping-table/`visual_external` changes in this slice | PASS | Static search found no `visual_external` in checked Product Core/web/discounts paths and no TASK-PC2-003 mapping-table preview/apply/upload implementation. |
| No marketplace card-field write changes in this slice | PASS | Static review found no Product Core WB/Ozon card-field mutation, `vendorCode` rewrite, or `offer_id` rewrite behavior added by TASK-PC2-003 cleanup. Existing API discount upload code is outside this slice. |

## Behavior Evidence

| Requirement | Result | Evidence |
| --- | --- | --- |
| Duplicate external article techlog severity/event type | PASS | Focused product_core tests assert WB price, WB promotion and Ozon duplicate paths use `TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR` with `TechLogSeverity.ERROR`; covered by `apps.product_core apps.techlog` test run. |
| Techlog enum/baseline cleanup does not break techlog module | PASS | Combined `apps.product_core apps.techlog` test run passed 59 tests. |
| WB/Ozon API regressions remain green | PASS | WB prices/promotions and Ozon API regression run passed 60 tests. |
| Optional web/operations/marketplace_products regression was possible and green | PASS | Additional regression run passed 71 tests. |

## Defects

None found.

## Gaps

No new gaps opened. `GAP-CORE2-007` remains deferred/future and was not implemented in this slice.

## Changed Files

- `docs/testing/TEST_REPORT_TASK_PC2_003_API_ARTICLE_LINKAGE.md`
