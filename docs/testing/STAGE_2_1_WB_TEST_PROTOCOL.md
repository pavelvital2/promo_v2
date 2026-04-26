# STAGE_2_1_WB_TEST_PROTOCOL.md

Трассировка: `tz_stage_2.1.txt` §15; `docs/stages/stage-2/STAGE_2_1_WB_ACCEPTANCE_TESTS.md`.

## Назначение

Протокол задаёт обязательные проверки Stage 2.1 WB API. Реальные WB tokens/secrets и реальные `test_files/secrets` не трогать. По умолчанию использовать mocks/stubs официальных WB API.

## Test layers

| Layer | Проверки |
| --- | --- |
| Unit | normalizers, size conflict detection, current promotion filter, WB calculation core reuse, reason codes |
| Integration | API client pagination/rate/retry with mocks, file generation, DB snapshots, product/promotions persistence |
| UI | мастер WB API, rights/object access, confirmation, drift/partial/quarantine display |
| Acceptance | end-to-end 2.1.1-2.1.4 with WB API mocks and golden Excel comparison |
| Security | absolute secret redaction in metadata/snapshots/audit/techlog `safe_message`/techlog `sensitive_details_ref`/UI/files/reports |

## Required mock scenarios

### Prices API

- multiple pages with `limit=1000`, empty final page;
- equal prices across sizes;
- different prices across sizes -> `wb_api_price_row_size_conflict`;
- invalid/missing price -> `wb_api_price_row_invalid`;
- 401/403 auth failure;
- 429 rate limit with backoff;
- timeout and invalid schema.

### Promotions API

- past/current/future promotions in one API window;
- `allPromo=true` and local strict filter;
- details batches >100 IDs;
- regular promotion with `inAction=true/false` pages;
- auto promotion where nomenclatures are not called;
- missing `planPrice`/`planDiscount`;
- 429/timeout/invalid schema.

### Calculation

- API-generated price/promo data produces same final discounts as Stage 1 WB Excel on equivalent workbook data;
- decimal + ceil edge cases;
- threshold/fallback order;
- `wb_discount_out_of_range` blocks result and upload;
- size-conflict rows not upload-ready.

### Upload

- explicit confirmation absent -> upload not started;
- drift check detects changed price -> upload blocked;
- normal upload payload contains `nmID` and `discount` only, without `price`;
- WB rejection of discount-only payload stops upload safely and records a safe error/escalation note;
- implementation does not silently add old/stale price from calculation Excel or price snapshot;
- batch split <=1000;
- WB status 3 -> `completed_success`;
- WB status 5 -> `completed_with_warnings`;
- WB status 6 -> `completed_with_error`;
- WB status 4 -> `completed_with_error`;
- quarantine detail -> separate UI/detail code;
- 208 already exists -> no blind resend;
- 429/status poll timeout -> safe failure;
- HTTP 200 before polling -> operation not final success yet.

## Required assertions

- 2.1.1/2.1.2/2.1.3 never call WB write endpoints.
- 2.1.4 never starts without successful 2.1.3, confirmation and drift check.
- All Stage 2.1 operations have `mode=api` and WB step code.
- Stage 2.1 API operations use `Operation.step_code` as primary classifier and do not store `Operation.type=check/process`.
- File versions are immutable and linked to operations.
- API safe snapshots contain no token/header/API key/bearer/secret-like values.
- Metadata, audit, techlog `safe_message`, techlog `sensitive_details_ref`, UI, files, reports and test outputs contain no token/header/API key/bearer/secret-like values.
- Audit and techlog records use documented codes.
- Object access restricts all store-linked data.
- Stage 1 WB Excel tests remain unchanged and passing.

## Acceptance evidence

Each TASK-011..TASK-017 report must include:

- executed test command(s);
- mock fixtures used;
- changed files;
- Stage 2.1 checklist items covered;
- any GAP/escalation;
- confirmation that token/header/API key/bearer/secret-like values were not printed or persisted outside `protected_secret_ref`.
