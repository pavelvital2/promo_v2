# AUDIT_REPORT_TASK_015_RECHECK

Task: `TASK-015 Stage 2.1 WB API discount upload`
Recheck target: `TASK-015-A1` after required fix
Auditor: Codex CLI, audit role
Date: 2026-04-26
Verdict: PASS

## Проверенная область

- Закрытие `TASK-015-A1`: goods-level WB `errorText` / `error` redacted and validated before persistence.
- Регрессия `TASK-015-D1`: row-level quarantine/partial/success mapping remains separated.
- TASK-015 / Stage 2.1 upload requirements: confirmation gate, rights/object access/active connection gates, successful calculation gate, discount-only payload, no stale price fallback, batching <=1000, `uploadID`, polling, 208 handling, partial/quarantine rows, audit/techlog without secrets.
- Safety boundary: no real WB token file was read or printed.

## Проверенные файлы

- `docs/tasks/implementation/stage-2/TASK-015-wb-api-discount-upload.md`
- `docs/product/WB_DISCOUNTS_API_SPEC.md`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`
- `docs/audit/AUDIT_REPORT_TASK_015.md`
- `docs/testing/TEST_REPORT_TASK_015.md`
- `docs/testing/TEST_REPORT_TASK_015_RECHECK.md`
- `docs/testing/TEST_REPORT_TASK_015_A1_RECHECK.md`
- `apps/discounts/wb_api/upload/services.py`
- `apps/discounts/wb_api/upload/tests.py`
- `apps/discounts/wb_api/redaction.py`
- `apps/discounts/wb_api/client.py`
- `apps/operations/models.py`
- `apps/operations/services.py`

## Метод проверки

- Сверка реализации с TASK-015, `WB_DISCOUNTS_API_SPEC.md`, Stage 2.1 scope, API connection secret rules, operations and permissions specs.
- Code-level audit of polling detail sanitization, row persistence, operation summary/report construction, audit/techlog writes, batching and status mapping.
- Использованы отчёты тестировщика как evidence, но вывод сделан по самостоятельному чтению кода.

## Findings

No blocking or functional findings.

### TASK-015-A1

Status: CLOSED.

Evidence:

- `apps/discounts/wb_api/upload/services.py:301-323` defines `_safe_goods_error_text()` and `_safe_goods_detail()`. `errorText` and `error` are redacted, checked by `assert_no_secret_like_values()`, and replaced with `[redacted]` when the value was redacted or still looks secret-like.
- `apps/discounts/wb_api/upload/services.py:348-365` converts polling `history_goods_task` / `buffer_goods_task` output into `safe_details`, builds a redacted safe snapshot, validates it, and returns `safe_details` downstream.
- `apps/discounts/wb_api/upload/services.py:699-730` maps `OperationDetailRow.final_value["errorText_safe"]` from the safe detail path and runs `_safe_goods_error_text()` again before persistence.
- `apps/discounts/wb_api/upload/tests.py:478-539` covers a mocked WB goods detail containing `Authorization: Bearer ...` and `token=...`, then asserts operation detail rows, summary, generated report, audit and techlog do not contain the original secret-like text.

### TASK-015-D1

Status: remains CLOSED.

Evidence:

- `apps/discounts/wb_api/upload/services.py:379-394` resolves row-level result/status separately for quarantine, partial row error and successful row.
- `apps/discounts/wb_api/upload/tests.py:376-429` covers both mixed status 3 success/quarantine and mixed status 5 partial/quarantine/success batches.

## Stage 2.1 TASK-015 Requirements

Status: PASS.

- Confirmation gate: exact phrase validated before operation start and audit confirmation is recorded.
- Rights/object/connection gates: `wb.api.discounts.upload`, `wb.api.discounts.upload.confirm`, object access via permission checks, WB store validation and active Stage 2.1 connection are required.
- Successful calculation gate: upload requires WB API 2.1.3 calculation, `OperationType.NOT_APPLICABLE`, `wb_api_discount_calculation`, `completed_success`, no errors, and result Excel.
- Payload: `_upload_payload()` creates only `nmID` + `discount`; no `price` fallback exists on discount-only rejection.
- Drift: pre-upload `POST /api/v2/list/goods/filter` by `nmList` runs in <=1000 batches and blocks upload on missing product, size conflict, invalid row or price change.
- Batching/polling: upload batches are <=1000, payload checksum and `uploadID` are stored per batch, HTTP 200 alone is not final success, and history/buffer task and goods endpoints are polled.
- Statuses/errors: WB statuses 3/4/5/6, 208 existing task, partial rows and quarantine rows are handled without hiding applied rows.
- Audit/techlog/files: checked paths use documented audit/techlog codes and safe messages/snapshots; no token/header/API key/bearer/secret-like values are persisted in checked outputs.

## Commands/tests run

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api.upload --verbosity 2 --noinput
```

Result: PASS. Ran 10 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check
```

Result: PASS. `System check identified no issues (0 silenced).`

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
```

Result: PASS. `No changes detected`.

```bash
rg -n "urlopen\(|requests\.|httpx\.|aiohttp|WBApiClient\(|upload_discount_task\(|/api/v2/upload/task|test_files/secrets|Bearer|Authorization|api key|token" apps/discounts/wb_api apps/discounts/wb_excel apps/discounts/ozon_excel -g '*.py'
```

Result: PASS for no real WB calls in upload tests and no `test_files/secrets` usage. Matches are production client references and synthetic test token/assertion strings.

## Риски

- No new TASK-015 blocker. The earlier model-compliance note from `AUDIT_REPORT_TASK_015.md` about no dedicated physical `WBApiUploadBatch` / `WBApiUploadDetail` models remains a release-planning consideration only; TASK-015 acceptance evidence persists required batch and row data through operation summary, output report and `OperationDetailRow`.

## Обязательные исправления

None.

## Рекомендации

- TASK-016 may start from the TASK-015 upload backend perspective.

## Открытые gaps

No new GAP opened.

## Spec-blocking вопросы

None.

## Требуется эскалация заказчику через оркестратора

No.

## Changed files

- `docs/audit/AUDIT_REPORT_TASK_015_RECHECK.md`

Итог: pass.
