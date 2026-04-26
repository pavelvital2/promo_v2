# TEST_REPORT_TASK_013

Task: `TASK-013 Stage 2.1 WB API current promotions download`
Tester: Codex CLI, tester role
Date: 2026-04-26
Verdict: FAIL

## Scope

Checked implementation against:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/tasks/implementation/stage-2/TASK-013-wb-api-current-promotions-download.md`
- `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/testing/TEST_REPORT_TASK_012.md`

Product code was not changed. Real WB calls and real secrets were not used.

## Results

| Area | Result |
| --- | --- |
| Current filter `startDateTime <= now_utc < endDateTime` with boundary cases | PASS |
| API window `now_utc -24h/+24h`, `allPromo=true`, timestamp saved | PASS |
| Promotions list pagination until empty page | PASS |
| Details batching <=100 unique IDs | PASS |
| Nomenclatures pagination for regular promotions with `inAction=true` and `inAction=false`, `limit=1000`, offset until empty page | PASS |
| Auto promotions without invented product rows and without fake Excel rows | PASS |
| Promo Excel schema per regular current promotion | PASS |
| Missing `planPrice`/`planDiscount` invalid row | PASS |
| Operation classifier: `mode=api`, `marketplace=wb`, `step_code=wb_api_promotions_download`, type not check/process | PASS |
| Output file links support multiple promo files | PASS |
| Permission/object access and active WB connection prerequisite | PASS |
| Secret redaction in snapshots/audit/techlog/files/test output | PASS |
| No WB write endpoint scan, especially no `calendar/promotions/upload` | PASS |
| Stage 1 WB/Ozon Excel regression | PASS |
| `manage.py check`, `makemigrations --check --dry-run`, focused tests, full suite | PASS |
| Required DB persistence entities for promotions/snapshot/products/export links | FAIL |

## Commands And Results

```bash
git status --short
```

Result: existing implementation changes were present before testing and were not modified:

- `apps/discounts/wb_api/client.py`
- `apps/operations/models.py`
- `apps/discounts/wb_api/promotions/`
- `apps/operations/migrations/0004_allow_multiple_operation_outputs_per_kind.py`

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check
```

Result: PASS. `System check identified no issues (0 silenced).`

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
```

Result: PASS. `No changes detected`.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api.promotions --verbosity 2 --noinput
```

Result: PASS. Ran 8 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api apps.operations apps.files apps.stores apps.audit apps.techlog apps.identity_access --verbosity 2 --noinput
```

Result: PASS. Ran 99 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_excel apps.discounts.ozon_excel --verbosity 2 --noinput
```

Result: PASS. Ran 21 tests.

Note: one earlier parallel attempt of this same command failed before tests because another Django test command had already created `test_promo_v2`; it was rerun sequentially and passed.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test --verbosity 1 --noinput
```

Result: PASS. Ran 140 tests.

```bash
rg -n "calendar/promotions/upload|promotions/upload|api/v1/calendar/promotions/upload|method=\"POST\"|method='POST'|\\.post\\(" apps/discounts/wb_api apps -g '*.py'
```

Result: PASS for WB write endpoint scan. No `calendar/promotions/upload` reference found; `.post(` hits were unrelated Django view tests outside WB API client/use case code.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py shell -c "from django.apps import apps; names=sorted(m.__name__ for m in apps.get_models() if 'Promotion' in m.__name__ or 'WB' in m.__name__); print(names)"
```

Result: FAIL evidence for persistence requirement. Output was `[]`; no `WBPromotion`, `WBPromotionSnapshot`, `WBPromotionProduct`, or `WBPromotionExportFile` model exists.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py shell -c "from apps.operations.models import OperationDetailRow; f=[fld.name for fld in OperationDetailRow._meta.fields]; print(f)"
```

Result: supporting evidence. Output fields were generic operation detail fields only: `id`, `operation`, `row_no`, `product_ref`, `row_status`, `reason_code`, `message_level`, `message`, `problem_field`, `final_value`, `created_at`.

## Test IDs

Test ID: TASK-013-CURRENT-FILTER
Scenario: promotion starts exactly at `now_utc`; promotion ends exactly at `now_utc`.
Expected: start boundary included, end boundary excluded.
Actual: focused test passed; implementation uses `start_datetime <= now_utc < end_datetime`.
Status: pass.

Test ID: TASK-013-API-WINDOW
Scenario: mocked list request at `2026-04-26T09:00:00Z`.
Expected: `startDateTime=2026-04-25T09:00:00Z`, `endDateTime=2026-04-27T09:00:00Z`, `allPromo=true`, timestamp persisted.
Actual: focused test passed; operation summary stores window and `current_filter_timestamp`.
Status: pass.

Test ID: TASK-013-DETAIL-BATCHING
Scenario: 102 unique current auto promotion IDs plus duplicate.
Expected: details calls split as 100 and 2 unique IDs.
Actual: focused test passed.
Status: pass.

Test ID: TASK-013-NOMENCLATURES-PAGINATION
Scenario: regular current promotion with true/false pages and empty terminal pages.
Expected: both `inAction` values fetched with `limit=1000`, offsets until empty page.
Actual: focused test passed.
Status: pass.

Test ID: TASK-013-AUTO-PROMOTIONS
Scenario: current auto promotions.
Expected: no nomenclatures call, no invented product rows, no promo Excel output.
Actual: focused test passed.
Status: pass.

Test ID: TASK-013-EXCEL-SCHEMA
Scenario: regular current promotion with valid and invalid product rows.
Expected: Excel columns `Артикул WB`, `Плановая цена для акции`, `Загружаемая скидка для участия в акции`.
Actual: focused test passed.
Status: pass.

Test ID: TASK-013-INVALID-PRODUCT
Scenario: missing `planPrice`.
Expected: row is invalid with `wb_api_promotion_product_invalid`.
Actual: focused test passed; detail row problem field is `planPrice/planDiscount`.
Status: pass.

Test ID: TASK-013-CLASSIFIER
Scenario: API operation for promotions download.
Expected: `mode=api`, `marketplace=wb`, `step_code=wb_api_promotions_download`, type not `check/process`.
Actual: focused test passed; model validation rejects `operation_type=process`.
Status: pass.

Test ID: TASK-013-MULTIPLE-FILES
Scenario: operation may create more than one promotion export.
Expected: multiple `OperationOutputFile` links of `promotion_export` kind are supported.
Actual: model/migration now remove the old unique `(operation, output_kind)` constraint and keep unique `file_version`; no dry-run migrations pending.
Status: pass.

Test ID: TASK-013-ACCESS-CONNECTION
Scenario: outsider, inactive connection, direct deny.
Expected: denied before API execution.
Actual: focused test passed.
Status: pass.

Test ID: TASK-013-SECRET-REDACTION
Scenario: token resolved at runtime and operation/audit/techlog/file metadata inspected.
Expected: no token/header/API key/bearer/secret-like values in safe contours.
Actual: focused test passed; no sentinel token or `Authorization` was present.
Status: pass.

Test ID: TASK-013-NO-WB-WRITE
Scenario: static scan for WB promotions upload endpoint.
Expected: no `POST /api/v1/calendar/promotions/upload` reference.
Actual: no forbidden endpoint found.
Status: pass.

Test ID: TASK-013-PERSISTENCE-ENTITIES
Scenario: verify required Stage 2.1 promotion persistence model from `DATA_MODEL.md` and task expected result.
Expected: implementation has and writes dedicated entities equivalent to `WBPromotion`, `WBPromotionSnapshot`, `WBPromotionProduct`, `WBPromotionExportFile`.
Actual: no such Django models exist; implementation persists promotion/product facts only as generic `OperationDetailRow` JSON and file links. This does not satisfy the specified data model.
Status: fail.

## Findings / Defects

### DEF-TASK-013-001: Dedicated promotion persistence entities are missing

Severity: blocking.

Evidence:

- `docs/architecture/DATA_MODEL.md` Stage 2.1 defines `WBPromotion`, `WBPromotionSnapshot`, `WBPromotionProduct`, and `WBPromotionExportFile`.
- `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md` requires mapping for `WBPromotion`, `WBPromotionSnapshot`, `WBPromotionProduct`, and auto promotions saved as promotions without invented product rows.
- `docs/tasks/implementation/stage-2/TASK-013-wb-api-current-promotions-download.md` expected result says current WB promotions and products are saved.
- Runtime model introspection returned no promotion/WB-specific models.
- Code search found no persistence model for these entities; only generic `OperationDetailRow` JSON is used for promotion and product facts.

Impact:

- Stage 2.1 calculation cannot reliably consume normalized promotion products through the documented data model.
- Object access, future UI/detail views, traceability, and audit around promotions/products depend on operation detail JSON rather than first-class store-linked entities.
- `WBPromotionSnapshot.current_filter_timestamp` and file-to-promotion links are not represented as specified entities.

## Acceptance Checklist Coverage

- Current filter, API window, details batching, nomenclature pagination, auto promotion behavior, Excel schema, invalid row marking, classifier, multi-file output links, access prerequisites, redaction, and no-write scan were covered by passing tests.
- Stage 1 WB/Ozon Excel regression passed.
- Full Django suite passed.
- No real secrets were used or printed. Token/header/API key/bearer/secret-like values were not found in checked safe contours.

## GAP / Escalation

No new documentation GAP was opened. The requirement is already explicit in the task, product spec, and data model; this is an implementation defect.

## Audit Readiness

Not ready for audit as PASS. Ready for audit only as a failed TASK-013 report with blocking defect `DEF-TASK-013-001`.

## Changed Files

- `docs/testing/TEST_REPORT_TASK_013.md`

Existing implementation changes were already present in the worktree before this tester report and were not modified by this check.
