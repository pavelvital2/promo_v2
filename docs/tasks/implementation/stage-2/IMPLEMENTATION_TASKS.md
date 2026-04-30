# IMPLEMENTATION_TASKS.md

Трассировка: `tz_stage_2.1.txt` §5, §16-§18; `docs/orchestration/TASK_TEMPLATES.md`.

## Назначение

Индекс Stage 2 implementation tasks. Stage 2.1 WB API release-ready. Stage 2.2 Ozon API is documented by TASK-018 and may start implementation only after documentation audit pass and affected GAP resolution.

## Preconditions

- Audit pass комплекта соответствующего stage docs.
- No open blocking GAP for affected implementation slice.
- Stage 1 WB Excel tests remain passable.
- Stage 1 Ozon Excel tests remain passable for Stage 2.2 tasks.
- Real `test_files/secrets` не трогать.

## Порядок задач

| Порядок | Task | Подэтап | Назначение | Зависимости |
| --- | --- | --- | --- | --- |
| 11 | `TASK-011-wb-api-connections.md` | prerequisite | WB API connection, secrets, safe API client baseline | audit pass |
| 12 | `TASK-012-wb-api-prices-download.md` | 2.1.1 | Prices download, Excel price export, product update | TASK-011 |
| 13 | `TASK-013-wb-api-current-promotions-download.md` | 2.1.2 | Current promotions download, promo DB/files | TASK-011 |
| 14 | `TASK-014-wb-api-discount-calculation-excel-output.md` | 2.1.3 | Calculation by API sources and result Excel | TASK-012, TASK-013 |
| 15 | `TASK-015-wb-api-discount-upload.md` | 2.1.4 | Confirmation, drift check, upload, polling | TASK-014 |
| 16 | `TASK-016-wb-api-ui-stage-2-1.md` | UI | WB API master and screens | TASK-011..TASK-015 as available |
| 17 | `TASK-017-wb-api-acceptance-and-release.md` | acceptance | test execution, audit handoff, release readiness | TASK-011..TASK-016 |
| 18 | `TASK-018-DESIGN-STAGE-2-2-OZON-API.md` | design | Stage 2.2 executable documentation | orchestrator task |
| 19 | `TASK-019-ozon-api-connection.md` | 2.2 prerequisite | Ozon API connection and production read-only `GET /v1/actions` check | Stage 2.2 audit pass; ADR-0035 |
| 20 | `TASK-020-ozon-elastic-actions-download.md` | 2.2 actions | Actions download and Elastic action selection | TASK-019, ADR-0029 |
| 21 | `TASK-021-ozon-elastic-products-download.md` | 2.2 products | Active/candidate products download | TASK-020, ADR-0033 |
| 22 | `TASK-022-ozon-elastic-product-data-join.md` | 2.2 data | Product info/stocks join and canonical rows | TASK-021, ADR-0030, ADR-0031 |
| 23 | `TASK-023-ozon-elastic-calculation-reports.md` | 2.2 calculation | Shared Ozon calculation engine, calculation artifacts and result reports | TASK-022 |
| 24 | `TASK-024-ozon-elastic-result-review.md` | 2.2 review | Accept/decline workflow, immutable accepted basis and post-acceptance manual upload Excel | TASK-023 |
| 25 | `TASK-025-ozon-elastic-upload-deactivate.md` | 2.2 upload | Add/update/deactivate upload with confirmations | TASK-024, ADR-0033, ADR-0034 |
| 26 | `TASK-026-ozon-elastic-ui-acceptance-release.md` | UI/acceptance | Stage 2.2 UI implementation gate -> acceptance/testing gate -> audit/release handoff gate | TASK-019..TASK-025, no blocking GAP for release slice |

## Общие запреты

- Не писать код до audit pass документации.
- Не менять Stage 1 WB Excel бизнес-логику.
- Не удалять и не заменять Excel mode.
- Не смешивать WB Stage 2.1 и Ozon Stage 2.2.
- Не выполнять WB API write в TASK-012, TASK-013, TASK-014.
- Не выполнять Ozon API write в TASK-019..TASK-024.
- Не реализовывать affected Stage 2.2 slices while a blocking GAP remains open for that slice. `GAP-0014` закрыт решением заказчика 2026-04-30 and ADR-0029. `GAP-0015` закрыт решением заказчика 2026-04-30 and ADR-0030. `GAP-0016` закрыт решением заказчика 2026-04-30 and ADR-0031. `GAP-0017` закрыт решением заказчика 2026-04-30 and ADR-0032. `GAP-0018` закрыт решением заказчика 2026-04-30 and ADR-0033. `GAP-0019` закрыт technical/orchestrator decision 2026-04-30 and ADR-0034. `GAP-0020` закрыт решением заказчика 2026-04-30 and ADR-0027. `GAP-0021` закрыт решением заказчика 2026-04-30 and ADR-0028. `GAP-0022` закрыт technical decision 2026-04-30 and ADR-0035.
- Не хранить token, authorization header, API key, bearer value or secret-like value нигде, кроме `protected_secret_ref`: не в metadata, audit, techlog `safe_message`, techlog `sensitive_details_ref`, snapshots, UI, files, reports or test output.
- Не добавлять reason/result codes без документации и ADR.
- Не оставлять UX/functionality gaps на разработчика.

## Общий data contract Stage 2.1

- Stage 1 `Operation.type=check/process` сохраняется без изменения.
- Stage 2.1 WB API operations use `Operation.step_code` as mandatory primary classifier.
- `Operation.type` for `wb_api_prices_download`, `wb_api_promotions_download`, `wb_api_discount_calculation`, `wb_api_discount_upload` is `NULL` / blank / `not_applicable` by migration decision, never `check/process`.
- Lists, cards, audit links and tests classify Stage 2.1 operations by `step_code`.

## Общий data contract Stage 2.2

- Stage 2.2 Ozon API operations use `Operation.step_code` as mandatory primary classifier.
- `Operation.type` for `ozon_api_connection_check`, `ozon_api_actions_download`, `ozon_api_elastic_active_products_download`, `ozon_api_elastic_candidate_products_download`, `ozon_api_elastic_product_data_download`, `ozon_api_elastic_calculation`, `ozon_api_elastic_upload` is `NULL` / blank / `not_applicable`, never `check/process`.
- Result review is immutable calculation result state, not a separate operation and not an `Operation.step_code`.
- Upload requires accepted result, explicit add/update confirmation, drift-check and one group deactivate confirmation for all `deactivate_from_action` rows if such rows exist.
- If deactivate group confirmation is absent, upload is blocked/pending and add/update does not silently proceed.
- Candidate/active source collisions use `source_group=candidate_and_active`, are treated as active for write planning, and must remain visible in details/reports.
- Ozon Elastic action identity uses saved user-selected `action_id` per store/account after candidates are filtered by `action_type = MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT` and title marker `Эластичный бустинг`; upload drift-check revalidates the saved action.
- Manual upload Excel `ozon_api_elastic_manual_upload_excel` is generated after TASK-024 result acceptance from the immutable accepted calculation snapshot, uses the Stage 1-compatible Ozon Excel template decision from ADR-0032, is secondary to API upload, writes add/update rows with K=`Да` and L=`calculated_action_price`, and keeps deactivate rows visible via `Снять с акции` sheet/section if not directly supported by the template.
- Live upload contract follows ADR-0033: add/update uses Ozon actions activate with `action_id`, product identifiers and `action_price`; deactivate uses Ozon actions deactivate with `action_id` and product identifiers; exact field names follow current official Ozon docs; `/v1/product/import/prices` is prohibited.
- Ozon API rate/batch/retry policy follows ADR-0034: read page size `100`, write batch size `100`, minimum interval `500 ms`, read-only transient retry with bounded backoff, no automatic retry for sent/uncertain writes, explicit new operation after drift-check for write retry, and row-level partial failure persistence/reporting.
- Ozon API connection check follows ADR-0035: read-only `GET /v1/actions`, HTTP 200 with valid JSON containing `result` -> `active`, 401/403 -> `check_failed/auth_failed`, 429 -> `check_failed/rate_limited`, 5xx/timeout/network -> `check_failed/temporary`, invalid JSON/schema -> `check_failed/invalid_response`; no write endpoint may be used for connection check.
