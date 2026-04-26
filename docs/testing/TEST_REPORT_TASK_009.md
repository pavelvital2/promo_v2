# TEST_REPORT_TASK_009

Дата проверки: 2026-04-25.

Роль проверки: тестировщик Codex CLI TASK-009 UI stage 1 screens. Проверка выполнена через Django HTTP client/view tests, template smoke and route checks. Архитектурный аудит не выполнялся.

## status

FAIL

Причина: обязательные PostgreSQL checks прошли, но сценарий UI visibility для скачивания detail report в карточке операции не соответствует правам: пользователь с `download_detail_report` и без `download_output` может скачать файл прямым маршрутом, но UI скрывает ссылку.

## scenario matrix

| # | Scenario | Status | Evidence / notes |
| --- | --- | --- | --- |
| 1 | Main navigation and home/dashboard visible according to permissions | PASS | `apps.web` smoke tests: owner screens render, anonymous home redirects, home template shell renders. Views build nav by section access. |
| 2 | WB draft upload/replace/delete/version list, then check/process actions | PASS WITH REMARKS | Covered by `test_draft_replace_preserves_file_chain_and_creates_audit`, launch denial before creating files, WB template route smoke. Delete action exists in draft context. Formal Excel acceptance remains artifact-gated. |
| 3 | Ozon draft upload/replace/delete/version list, then check/process actions | PASS WITH REMARKS | Route/template smoke and shared draft handler path reviewed. Ozon screen has upload/replace/delete, version chain and check/process controls. Formal Excel acceptance remains artifact-gated. |
| 4 | Operation list/card/result/confirmation action visibility: download/confirm only with rights | FAIL | Defect T009-UI-001: detail report download link is hidden when only `download_detail_report` is granted, while direct download succeeds. Confirmation action is gated by `confirm_warnings` + `run_process`. |
| 5 | Product list/card store-aware visibility and related operations scope | PASS | Existing tests cover product list/card and related operation scoping by store and marketplace. |
| 6 | WB parameter write-flow: set/clear, history, audit, permissions; Ozon has no params | PASS WITH REMARKS | Existing tests cover set/history/audit; settings template has clear controls and disabled state by edit right; Ozon template explicitly has no WB params. |
| 7 | Admin write-flow: users create/edit/block/archive, role edit, permission assignment, store access assignment; owner/system protections visible behavior | PASS WITH REMARKS | Existing tests cover create user and distinct status/edit/archive permissions. Templates expose role/permission/store access forms and hide protected role edit for owner/system roles. No product code changes were made. |
| 8 | Reference/admin/log index section gating for local/store-scoped users | PASS | Round 4 audit context plus `test_reference_index_allows_store_scoped_store_list_access`: local admin with store-scoped access can open references, sees allowed store link only, and inaccessible store is absent. |
| 9 | Audit/techlog filters and sensitive details behavior | PASS WITH REMARKS | Audit and techlog list/card routes are smoke-tested for owner; templates include filters. Techlog card hides `sensitive_details_ref` unless `techlog.sensitive.view`. |
| 10 | System notifications view access | PASS | Owner route smoke covers notification list; `notification_list` requires audit or techlog section access and filters notifications by visible stores/global records. |
| 11 | No API mode UI appears for WB/Ozon Excel | PASS | WB/Ozon Excel templates are Excel-only and show no API launch mode. Store API stage-2 notices are outside WB/Ozon Excel mode. |

## commands run/results

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check
```

Result: PASS.

```text
System check identified no issues (0 silenced).
```

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.web apps.marketplace_products apps.platform_settings apps.identity_access apps.files apps.operations apps.discounts.wb_excel apps.discounts.ozon_excel
```

Result: PASS.

```text
Found 74 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
..........................................................................
----------------------------------------------------------------------
Ran 74 tests in 79.370s

OK
Destroying test database for alias 'default'...
```

Temporary HTTP scenario runner:

```text
SCENARIO detail_report_link_visibility status= 200
SCENARIO detail_report_direct_download status= 200
SCENARIO contains_download_link= False
SCENARIO contains_hidden_by_rights= True
```

Interpretation: direct download route grants access to detail report by `download_detail_report`, but the operation card renders "Скрыто правами доступа" and no download link.

## defects found

### T009-UI-001

Severity: MAJOR.

Scenario: Operation list/card/result action visibility.

Actual: `templates/web/operation_card.html` renders all output file links using only `can_download_output`. The view calculates both `can_download_output` and `can_download_detail`, but the template does not use `can_download_detail`.

Expected: output workbook visibility must be gated by `*_download_output`; detail report visibility must be gated by `*_download_detail_report`.

Evidence:

- `apps/web/views.py` computes `can_download_detail`.
- `templates/web/operation_card.html` line 45 checks only `can_download_output` for every `output_kind`.
- Temporary scenario: detail report direct download returns HTTP 200, operation card returns HTTP 200 but hides the link.

Impact: users with detail report download rights cannot discover/download detail reports from the UI; users with output-only rights may see detail report links depending on file availability.

## environment limitations

- PostgreSQL was available with user `postgres`, password `postgres`; required commands ran against PostgreSQL test database successfully.
- No real customer WB/Ozon control Excel files, checksums, old-program expected summaries or row-level expected results were provided. Formal Excel acceptance remains `blocked_by_artifact_gate` per `docs/testing/TEST_PROTOCOL.md`.
- Manual browser sanity check/dev server was not run; verification used Django test client, route smoke tests, templates and an optional temporary scenario runner.
- Working directory is not a git repository, so no git diff/status evidence is available.

## recommendation

Do not move to TASK-010 yet.

Fix T009-UI-001 and rerun at minimum:

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.web apps.marketplace_products apps.platform_settings apps.identity_access apps.files apps.operations apps.discounts.wb_excel apps.discounts.ozon_excel
```

After the fix, repeat the detail-report visibility scenario for users with only `download_detail_report`, only `download_output`, both rights, and neither right.
