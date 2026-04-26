# IMPLEMENTATION_TASKS.md

Трассировка: `tz_stage_2.1.txt` §5, §16-§18; `docs/orchestration/TASK_TEMPLATES.md`.

## Назначение

Индекс Stage 2 implementation tasks. На 2026-04-26 разрешён только Stage 2.1 WB API после audit pass исполнительной документации. Ozon API Stage 2.2 не входит.

## Preconditions

- Audit pass комплекта Stage 2.1 docs.
- No open Stage 2.1 blocking GAP.
- Stage 1 WB Excel tests remain passable.
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

## Общие запреты

- Не писать код до audit pass документации.
- Не менять Stage 1 WB Excel бизнес-логику.
- Не удалять и не заменять Excel mode.
- Не смешивать WB Stage 2.1 и Ozon Stage 2.2.
- Не выполнять WB API write в TASK-012, TASK-013, TASK-014.
- Не хранить token, authorization header, API key, bearer value or secret-like value нигде, кроме `protected_secret_ref`: не в metadata, audit, techlog `safe_message`, techlog `sensitive_details_ref`, snapshots, UI, files, reports or test output.
- Не добавлять reason/result codes без документации и ADR.
- Не оставлять UX/functionality gaps на разработчика.

## Общий data contract Stage 2.1

- Stage 1 `Operation.type=check/process` сохраняется без изменения.
- Stage 2.1 WB API operations use `Operation.step_code` as mandatory primary classifier.
- `Operation.type` for `wb_api_prices_download`, `wb_api_promotions_download`, `wb_api_discount_calculation`, `wb_api_discount_upload` is `NULL` / blank / `not_applicable` by migration decision, never `check/process`.
- Lists, cards, audit links and tests classify Stage 2.1 operations by `step_code`.
