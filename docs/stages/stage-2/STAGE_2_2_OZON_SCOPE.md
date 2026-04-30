# STAGE_2_2_OZON_SCOPE.md

Трассировка: `docs/tasks/implementation/stage-2/TASK-018-DESIGN-STAGE-2-2-OZON-API.md`; `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md`; ADR-0016, ADR-0022..ADR-0035.

## Назначение

Stage 2.2 добавляет Ozon API-контур только для акции `Эластичный бустинг`. Контур не является новой бизнес-логикой расчёта: API-данные приводятся к канонической строке Ozon `J/O/P/R`, затем применяется тот же порядок 7 правил, что в Ozon Excel Stage 1.

```text
Ozon API sources -> canonical Ozon J/O/P/R row -> existing Ozon decision rules -> review -> confirmed API write / Excel output
```

Stage 1 Ozon Excel остаётся штатным режимом и не заменяется API.

## Реализуемый scope

Stage 2.2 реализует только ветку:

```text
Маркетплейсы -> Ozon -> Акции -> API -> Эластичный бустинг
```

В scope:

- Ozon API connection для Ozon store/cabinet с `Client-Id` и `Api-Key` только через `protected_secret_ref`.
- Production connection check через read-only `GET /v1/actions` по ADR-0035; no write endpoint may be used for connection check.
- Скачивание доступных Ozon actions.
- Выбор одной акции, распознанной as Elastic Boosting by `action_type = MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT` and title contains `Эластичный бустинг`; saved `action_id` is the workflow basis for the selected store/account.
- Скачивание participating/active products выбранной акции.
- Скачивание candidates выбранной акции.
- Скачивание product info и stocks по объединённому набору `product_id`.
- Построение canonical rows с полями `J/O/P/R`; J берётся из `/v3/product/info/list` `min_price` по ADR-0030; R берётся как сумма `present` по всем stock rows из `/v4/product/info/stocks`, включая FBO + FBS, без вычитания `reserved`, по ADR-0031.
- Расчёт по существующим 7 правилам Ozon Excel без изменения порядка.
- Review результата: принять или не принять результат.
- Excel report результата расчёта after `Обработать`.
- Отдельный Excel для ручной загрузки в Ozon after accepted result по customer-approved Stage 1-compatible template decision ADR-0032.
- API upload add/update только после accepted result, explicit confirmation and drift-check.
- Customer decision 2026-04-30: active/candidate_and_active + not_upload_ready rows are removed from action as `deactivate_from_action`.
- Deactivate требует one group confirmation for all `deactivate_from_action` rows; перед подтверждением UI показывает весь список товаров на снятие and row-level reasons.
- If deactivate group confirmation is not given, upload is blocked/pending and add/update does not silently proceed.
- Customer decision 2026-04-30 / ADR-0033: write-side `activate/deactivate` is a live Ozon actions API flow using the current official schema, not a mock/stub-only implementation.
- Audit, techlog, operations, files, snapshots без secrets/raw sensitive responses.

## Не входит в scope

- Изменение Stage 1 Ozon Excel logic, workbook template или 7 правил.
- Изменение Stage 2.1 WB API release-ready scope.
- Обычные Ozon акции вне `Эластичного бустинга`.
- Ozon seller-actions, если они не являются подтверждённым контуром Elastic Boosting.
- Изменение базовых цен через `/v1/product/import/prices`.
- Управление Elastic Boosting через `prices.manage_elastic_boosting_through_price`.
- Автоматическая загрузка без review/confirmation.
- Скрытый deactivate внутри общего upload без отдельного group confirmation.
- Штатный сценарий `deactivate declined -> add/update proceeds`.
- Пользовательские параметры скидки для Ozon.
- Реализация будущих разделов `Цены`, `Остатки`, `Продажи`, `В производство`, `Поставки`.

## Навигационная иерархия

Stage 2.2 обязан заложить навигационную структуру без смешивания marketplace/domain/source/workflow:

```text
Маркетплейсы
  -> Ozon
     -> Цены -> Excel / API
     -> Акции -> Excel / API -> Эластичный бустинг
     -> Остатки -> Excel / API
     -> Продажи -> Excel / API
     -> В производство -> Excel / API
     -> Поставки -> Excel / API
  -> WB
     -> Цены -> Excel / API
     -> Акции -> Excel / API
     -> Остатки -> Excel / API
     -> Продажи -> Excel / API
     -> В производство -> Excel / API
     -> Поставки -> Excel / API
```

Только `Ozon -> Акции -> API -> Эластичный бустинг` является рабочим Stage 2.2 flow. Остальные entry points могут отображаться как будущие недоступные разделы только если UI явно не показывает их как реализованную бизнес-функцию.

## Workflow кнопок

Порядок кнопок в master page фиксирован:

1. `Скачать доступные акции`
2. `Выбрать акцию`
3. `Скачать товары участвующие в акции`
4. `Скачать товары кандидаты в акцию`
5. `Скачать данные по полученным товарам`
6. `Обработать`
7. `Принять результат` / `Не принять результат`
8. `Скачать Excel результата`
9. `Скачать Excel для ручной загрузки`
10. `Загрузить в Ozon`

Кнопки 1, 3, 4, 5 являются read-only. Кнопка 10 является write operation. Deactivate внутри upload требует one group confirmation for all `deactivate_from_action` rows и не считается подтверждённым нажатием `Загрузить в Ozon`. Если group confirmation не дано, состояние остаётся `review_pending_deactivate_confirmation` and upload operation is not created.

## Phase gates

До реализации Stage 2.2 требуется audit pass этого комплекта документации.

На 2026-04-30 открытых spec-blocking GAP для Stage 2.2 affected slices в этом документе нет. Implementation agent still checks current `docs/gaps/GAP_REGISTER.md` before coding.

`GAP-0019` is resolved by technical/orchestrator decision 2026-04-30 and ADR-0034: conservative configurable API defaults are read page size `100`, write batch size `100`, minimum interval `500 ms`, read-only transient retry with bounded backoff, no automatic retry for sent/uncertain write activate/deactivate, explicit new write operation only after drift-check, and row-level partial failure persistence/reporting.
`GAP-0022` is resolved by technical decision 2026-04-30 and ADR-0035: production Ozon connection check uses read-only `GET /v1/actions`; HTTP 200 with valid JSON containing `result` maps to `active`; 401/403 -> `check_failed/auth_failed`; 429 -> `check_failed/rate_limited`; 5xx/timeout/network -> `check_failed/temporary`; invalid JSON/schema -> `check_failed/invalid_response`; no write endpoint may be used for connection check.
`GAP-0018` is resolved by customer decision 2026-04-30 and ADR-0033: read-side active/candidate downloads use observed/approved fields from `/v1/actions/products` and `/v1/actions/candidates`; add/update uses Ozon actions activate endpoint with `action_id`, product identifiers and `action_price`; deactivate uses Ozon actions deactivate endpoint with `action_id` and product identifiers; implementation follows official current field names and never uses `/v1/product/import/prices`.
`GAP-0020` is resolved by customer decision 2026-04-30: review UX/state model is calculation result state, not a separate operation.
`GAP-0021` is resolved by customer decision 2026-04-30 and ADR-0028: candidate/active collisions merge as `candidate_and_active`, are treated as active for write planning, and remain visible in details/reports.
`GAP-0014` is resolved by customer decision 2026-04-30 and ADR-0029: action discovery filters candidates by approved action type/title marker, user selection saves `action_id`, and upload drift-check verifies the saved action still matches.
`GAP-0015` is resolved by customer decision 2026-04-30 and ADR-0030: canonical Excel J (`минимально допустимая цена`) uses `/v3/product/info/list` `min_price`; absent/non-numeric `min_price` maps to existing reason `missing_min_price`.
`GAP-0016` is resolved by customer decision 2026-04-30 and ADR-0031: canonical Excel R (`остаток`) uses summed `present` across all `/v4/product/info/stocks` rows, including FBO + FBS; `reserved` is not subtracted; absent stock info or summed `present <= 0` maps to existing reason `no_stock`.
`GAP-0017` is resolved by customer decision 2026-04-30 and ADR-0032: manual upload Excel uses the current Stage 1 Ozon Excel template/format as Stage 1-compatible secondary artifact; add/update rows write K=`Да` and L=`calculated_action_price`; deactivate rows remain visible via `Снять с акции` sheet/section if the template cannot directly encode deactivate.

Connection, UI skeleton and read-only operation scaffolding могут проектироваться как задачи; implementation agent обязан проверить текущий GAP status перед началом кода.

## Документы Stage 2.2

- `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`
- `docs/product/OZON_API_ELASTIC_UI_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/testing/STAGE_2_2_OZON_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_2_OZON_ACCEPTANCE_CHECKLISTS.md`
- `docs/traceability/STAGE_2_2_OZON_TRACEABILITY_MATRIX.md`
- `docs/tasks/implementation/stage-2/IMPLEMENTATION_TASKS.md`
