# AUDIT_REPORT_TASK_PC2_003_API_ARTICLE_LINKAGE

Date: 2026-05-02
Role: implementation auditor
Task: TASK-PC2-003 narrowed API exact valid article linkage + auto-create/imported_draft
Re-audit scope: after MAJOR bugfix + duplicate techlog cleanup
Verdict: PASS

Product code was not changed during this re-audit. This report is the only file updated by the auditor.

## Scope

Re-audited the narrowed TASK-PC2-003 implementation only:

- API exact valid article linkage;
- API auto-create of `InternalProduct` + imported/draft `ProductVariant`;
- conflict/listing-only behavior;
- audit/history/source context;
- duplicate external article techlog cleanup;
- TASK-PC2-003 documentation and test evidence.

Out of scope for this audit and not accepted here: mapping-table preview/apply, `visual_external`, UI upload/apply flow, marketplace card-field writes, full CORE-2 completion.

## Documents Read

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/reports/TASK_PC2_003_DESIGN_HANDOFF.md`
- `docs/audit/AUDIT_REPORT_TASK_PC2_003_DESIGN_HANDOFF.md`
- `docs/testing/TEST_REPORT_TASK_PC2_003_API_ARTICLE_LINKAGE.md`
- `docs/gaps/GAP_REGISTER.md` entries `GAP-CORE2-006` and `GAP-CORE2-007`
- `docs/stages/stage-3-product-core/core-2/CORE_2_MAPPING_RULES_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md` section `TASK-PC2-003`
- `docs/stages/stage-3-product-core/core-2/CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md`

## Files Audited

- `apps/product_core/services.py`
- `apps/product_core/tests.py`
- `apps/techlog/models.py`
- `apps/techlog/tests.py`
- `apps/techlog/migrations/0010_alter_techlogrecord_event_type.py`
- changed TASK-PC2-003 docs:
  - `docs/README.md`
  - `docs/gaps/GAP_REGISTER.md`
  - `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md`
  - `docs/stages/stage-3-product-core/core-2/CORE_2_MAPPING_RULES_SPEC.md`
  - `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md`
  - `docs/reports/TASK_PC2_003_DESIGN_HANDOFF.md`
  - `docs/testing/TEST_REPORT_TASK_PC2_003_API_ARTICLE_LINKAGE.md`

## Findings

### BLOCKER

None.

### MAJOR

None.

### MINOR

None.

## Previous Findings Recheck

| Previous finding | Result | Evidence |
| --- | --- | --- |
| MAJOR-1 inactive product/variant can be selected for automatic API mapping. | CLOSED | `_safe_existing_api_variant()` now selects only variants where both variant and parent product have `ProductStatus.ACTIVE`, and treats any non-active variant/product as conflict: `apps/product_core/services.py:745`-`774`. `_safe_parent_for_api_auto_create()` reuses only active parents and treats inactive/archived parents as conflict: `apps/product_core/services.py:777`-`797`. Tests cover inactive variant, inactive product with active variant, and inactive parent without variant at `apps/product_core/tests.py:1273`-`1351`. |
| MAJOR-2 duplicate external article techlog does not match the CORE-2 techlog catalog. | CLOSED | `TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR` exists with value `marketplace_sync.data_integrity_error`: `apps/techlog/models.py:152`-`155`. Baseline severity is ERROR: `apps/techlog/models.py:217`. Product Core writes via `create_techlog_record` with that event and error severity: `apps/product_core/services.py:1091`-`1110`. Tests assert event/severity in WB price, WB promotion and Ozon duplicate paths: `apps/product_core/tests.py:1533`-`1647`, plus baseline normalization in `apps/techlog/tests.py:108`-`129`. |

## Criteria Review

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1. Scope exactly narrowed TASK-PC2-003. | PASS | Code changes are limited to Product Core services/tests and justified techlog enum/migration cleanup; no web/UI mapping-table implementation is present in the changed code. |
| 2. Exact trim-only matching. | PASS | `_valid_api_internal_sku()` strips only outer whitespace and calls `validate_core2_internal_sku`: `apps/product_core/services.py:589`-`597`; tests cover trim/case/hyphen/partial/title-only rejection. |
| 3. GAP-CORE2-006 field policy. | PASS | Auto-created `InternalProduct` uses `internal_code=internal_sku`, first title/fallback name, finished_good, active, null category, computed attributes and empty comments: `apps/product_core/services.py:798`-`828`. Auto-created `ProductVariant` uses same name policy, active status and `review_state=imported_draft`: `apps/product_core/services.py:831`-`880`. Tests verify the field policy at `apps/product_core/tests.py:1093`-`1134`. |
| 4. Same SKU across stores/marketplaces reuses one variant. | PASS | Existing exact variant is resolved before auto-create: `apps/product_core/services.py:961`; test coverage at `apps/product_core/tests.py:1154`-`1208`. |
| 5. Later title mismatch preserves first names and marks review. | PASS | `apps/product_core/services.py:883`-`920`; test coverage at `apps/product_core/tests.py:1154`-`1208`. |
| 6. Invalid/blank/non-unified article listing-only. | PASS | Invalid helper returns no SKU and no linkage: `apps/product_core/services.py:948`-`950`; test coverage at `apps/product_core/tests.py:1210`-`1246`. |
| 7. Duplicate source rows excluded before auto-link/auto-create. | PASS | Duplicate article rows are skipped before listing upsert/linking in WB prices, WB promotions and Ozon paths: `apps/product_core/services.py:1265`-`1268`, `1408`-`1416`, `1572`-`1580`. Tests verify no auto-link/auto-create and no snapshots for duplicate affected rows: `apps/product_core/tests.py:1385`-`1399`, `1533`-`1647`. |
| 8. Unsafe/archived/pre-linked conflicts do not auto-create/overwrite. | PASS | Non-active variant/product/parent states are conflicts, and pre-linked different variant is not overwritten: `apps/product_core/services.py:745`-`797`, `952`-`959`, `1000`-`1013`; tests at `apps/product_core/tests.py:1247`-`1383`. |
| 9. History/audit source_context safe and API/service source. | PASS | API path writes `ProductMappingHistory`, redaction checks, `AuditSourceContext.API`: `apps/product_core/services.py:625`-`705`. |
| 10. Migration justified and limited. | PASS | The only new migration is `apps/techlog/migrations/0010_alter_techlogrecord_event_type.py`; it only alters `TechLogRecord.event_type` choices and adds `marketplace_sync.data_integrity_error` to match the approved CORE-2 techlog catalog. |
| 11. No UI/mapping-table/visual_external/marketplace writes. | PASS | No `apps/web` diff; no `visual_external` implementation; Product Core code only reads/stores source article values and does not add WB/Ozon card-field mutation. |
| 12. Test report evidence sufficient. | PASS | Test report records `git diff --check`, `manage.py check`, `makemigrations --check --dry-run`, focused `apps.product_core apps.techlog` tests and additional regression suites as PASS. The focused test evidence covers inactive safe-selection and duplicate techlog event/severity. |
| 13. Docs do not mark full CORE-2 or `visual_external` complete. | PASS | `docs/README.md` keeps CORE-2 implementation behind follow-up audit/recheck and separate task assignment; `GAP-CORE2-007` remains deferred/future for mapping-table/`visual_external`. |

## Migration Review

PASS. The migration is justified by the approved CORE-2 techlog catalog and previous MAJOR-2 fix. It is limited to the `TechLogRecord.event_type` choices update and does not introduce product model, UI, permission or marketplace write changes.

## Test Evidence Review

PASS. `docs/testing/TEST_REPORT_TASK_PC2_003_API_ARTICLE_LINKAGE.md` is sufficient for this re-audit:

- focused `apps.product_core apps.techlog` run covers the changed Product Core linkage and techlog catalog;
- tests prove inactive/archived/non-active candidates do not auto-link or auto-create;
- tests prove duplicate external article rows are skipped and logged as `marketplace_sync.data_integrity_error` with `error` severity;
- additional WB/Ozon API and web/operations regression runs are recorded green by the tester;
- no test/report claims full CORE-2 completion.

## Checks Run

| Command | Result |
| --- | --- |
| `git diff --check` | PASS |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.product_core apps.techlog --verbosity 1 --noinput` | PASS: `Ran 59 tests in 9.740s`, `OK`. |

## Conclusion

PASS. The re-audit criteria are satisfied. Previous MAJOR-1 and MAJOR-2 are closed, the original TASK-PC2-003 criteria remain passing, the techlog migration is justified and limited, test evidence is sufficient, and the documentation does not mark full CORE-2 or the deferred mapping-table/`visual_external` workflow complete.

## Changed Files

- `docs/audit/AUDIT_REPORT_TASK_PC2_003_API_ARTICLE_LINKAGE.md`
