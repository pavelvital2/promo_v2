# STAGE_2_2_OZON_ACCEPTANCE_CHECKLISTS.md

Трассировка: `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`; `docs/testing/STAGE_2_2_OZON_TEST_PROTOCOL.md`.

## Общий чек-лист

- [ ] Documentation audit passed before implementation.
- [ ] Open spec-blocking GAP status checked before each implementation task.
- [ ] Stage 1 Ozon Excel remains available and tests pass.
- [ ] Stage 2.1 WB API remains release-ready and regression tests pass.
- [ ] Ozon API secrets stored only via `protected_secret_ref`.
- [ ] No Client-Id/Api-Key/header/bearer/secret-like values in metadata, audit, techlog, snapshots, UI, Excel, files, reports or test output.
- [ ] Object access works for Ozon stores, operations, files, products, actions and connection.
- [ ] Stage 2.2 operations have mandatory `step_code`; `Operation.type=check/process` remains only for check/process scenarios.
- [ ] UI hierarchy is `Маркетплейсы -> Ozon -> Акции -> API -> Эластичный бустинг`.
- [ ] Future navigation entries do not expose unimplemented business actions.

## Connection

- [ ] User with `ozon.api.connection.manage` can create/replace/disable connection secret.
- [ ] Saved Client-Id/Api-Key are not shown after saving.
- [ ] Only `active` connection allows Ozon API operations.
- [ ] Connection check is read-only `GET /v1/actions` per ADR-0035.
- [ ] No write endpoint is used for connection check.
- [ ] Status mapping is covered: HTTP 200 with valid JSON containing `result` -> `active`; 401/403 -> `check_failed/auth_failed`; 429 -> `check_failed/rate_limited`; 5xx/timeout/network -> `check_failed/temporary`; invalid JSON/schema -> `check_failed/invalid_response`.
- [ ] Auth/rate/timeout errors produce safe status/techlog.
- [ ] Ozon API client defaults from ADR-0034 are covered: read page size `100`, write batch size `100`, minimum interval `500 ms`, read-only transient retry with bounded backoff, no automatic retry for sent/uncertain writes.

## Actions

- [ ] `Скачать доступные акции` creates `ozon_api_actions_download` operation.
- [ ] Actions snapshot contains no secrets/raw sensitive response.
- [ ] User can select only Elastic Boosting candidates with `action_type = MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT` and title marker `Эластичный бустинг`.
- [ ] Selected `action_id` is saved per selected Ozon store/account and becomes the workflow basis.
- [ ] No global hard-coded Elastic Boosting `action_id` constant is used.
- [ ] Non-Elastic action or missing explicit selection is blocked.

## Active/candidates/data

- [ ] Participating products download is separate from candidates download.
- [ ] Both downloads paginate and store safe snapshots.
- [ ] Read operations use page/request chunk default `100`, minimum request interval `500 ms`, and retry only transient read failures (`429`, `5xx`, timeout/network) with bounded backoff.
- [ ] `/v1/actions/products` and `/v1/actions/candidates` field mappings use observed/approved fields and match the current official Ozon schema used by implementation.
- [ ] No write endpoint is called by read-only steps.
- [ ] Product info and stocks are downloaded only for union product ids.
- [ ] J/O/P/R source fields are visible in result preview.
- [ ] R uses summed `present` across all `/v4/product/info/stocks` rows, including FBO + FBS, without subtracting `reserved`; missing stock info or summed `present <= 0` produces existing reason `no_stock`.
- [ ] Product in both active and candidate sources is merged as `candidate_and_active`, collision is visible in details/report basis, and no duplicate row is created.

## Calculation/review/files

- [ ] Calculation reuses Ozon Excel 7-rule engine.
- [ ] Equivalent API and Excel fixtures produce same row decisions.
- [ ] Result groups add/update/deactivate/skip/blocked are correct.
- [ ] Active + not_upload_ready rows are marked for deactivate and have mandatory reason.
- [ ] `candidate_and_active` rows are treated as active for write planning: upload_ready -> update, not_upload_ready -> deactivate.
- [ ] `Принять результат` is required before upload.
- [ ] `Не принять результат` blocks upload.
- [ ] Result report Excel is downloadable after calculation.
- [ ] Manual upload Excel is generated only after result acceptance from accepted snapshot using Stage 1-compatible template decision ADR-0032.
- [ ] Manual upload Excel add/update rows have K=`Да` and L=`calculated_action_price`.
- [ ] Manual upload Excel/report includes `Снять с акции` sheet/section with row-level reasons when deactivate rows cannot be directly represented by the template.

## Upload/deactivate

- [ ] Upload requires `ozon.api.elastic.upload` and `ozon.api.elastic.upload.confirm`.
- [ ] Add/update confirmation is required.
- [ ] Pre-upload drift-check runs and blocks changed action/membership/J/O/P/R.
- [ ] Pre-upload drift-check verifies saved `action_id` still exists with expected action type and title marker.
- [ ] Confirmed add/update rows use only approved activate endpoint/payload after `GAP-0018` resolution.
- [ ] Add/update payload contains `action_id`, Ozon-required product identifiers and `action_price`, with exact field names covered by tests against the official schema used by implementation.
- [ ] Deactivate requires `ozon.api.elastic.deactivate.confirm`.
- [ ] UI shows the full `deactivate_from_action` group and row-level reasons before confirmation.
- [ ] Deactivate rows are sent only after one group confirmation for all deactivate rows.
- [ ] Deactivate payload contains `action_id` and Ozon-required product identifiers, with exact field names covered by tests against the official schema used by implementation.
- [ ] Activate/deactivate writes are split into batches <= `100` and observe the `500 ms` minimum request interval.
- [ ] Sent or response-uncertain activate/deactivate is not automatically retried; retry is only an explicit new operation after drift-check.
- [ ] If deactivate group confirmation is absent, upload is not started and result remains `review_pending_deactivate_confirmation`.
- [ ] Add/update does not silently proceed while mandatory deactivate rows are unconfirmed.
- [ ] Partial success/rejection preserves row-level details.
- [ ] Repeated upload is protected from accidental duplicate.
- [ ] Release evidence confirms live activate/deactivate implementation exists and is not mock/stub-only.
- [ ] `/v1/product/import/prices` is never called.

## Release readiness

- [ ] TASK-019..TASK-026 reports are complete.
- [ ] Traceability matrix rows are covered.
- [ ] Stage 2.2 documentation audit has no blocking findings.
- [ ] No open Stage 2.2 GAP blocks the implemented release slice.
- [ ] Backup/retention policy remains valid for new DB/file entities.
