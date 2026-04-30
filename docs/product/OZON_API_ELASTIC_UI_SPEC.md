# OZON_API_ELASTIC_UI_SPEC.md

Трассировка: `docs/tasks/implementation/stage-2/TASK-018-DESIGN-STAGE-2-2-OZON-API.md`; `docs/product/UI_SPEC.md`; `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`; ADR-0026, ADR-0027, ADR-0028, ADR-0029, ADR-0032, ADR-0033.

## Назначение

Экранная спецификация Stage 2.2 для ветки:

```text
Маркетплейсы / Ozon / Акции / API / Эластичный бустинг
```

UI не смешивает:

- marketplace: Ozon/WB;
- domain: цены/акции/остатки/продажи/производство/поставки;
- source/mode: Excel/API;
- workflow: Elastic Boosting.

## Master page

| Поле | Спецификация |
| --- | --- |
| Назначение | Провести пользователя через Ozon Elastic Boosting API flow: download actions, select action, download products/data, calculate, review, export, upload. |
| Раздел | Маркетплейсы -> Ozon -> Акции -> API -> Эластичный бустинг. |
| Роли/права | View: `ozon.api.operation.view`; действия по отдельным `ozon.api.*` rights; object access к Ozon store/account. |
| Входные точки | Навигация marketplace, карточка магазина, карточка operation, Главная. |
| Данные | Store selector, Ozon API connection status, selected action, step status, latest operations, counters, files, warnings/errors, review state. |
| Действия | Выполнить 10 кнопок workflow, скачать файлы, открыть operation/audit/techlog links. |
| Контролы | Store selector, connection status block, breadcrumb, stepper, action buttons, result summary, review table, confirmation panels, file links. |
| Фильтры/поиск/сортировка/пагинация | Store selector search; actions selector search/filter; result table filters by planned action/reason/source_group/upload status; pagination. |
| Сообщения/статусы | Нет active connection, нет прав, action не Elastic Boosting, missing source group, missing J/O/P/R, unresolved GAP blocks implementation, drift detected, `review_pending_deactivate_confirmation`, upload partial rejected. |
| Переходы | Store card, API connection screen, operation card, audit/techlog, file downloads. |
| Критерии готовности | Пользователь остаётся на master page после каждого шага; следующие кнопки disabled до выполнения prerequisite; write действия визуально отделены от read-only; deactivate требует one group confirmation for all `deactivate_from_action` rows. |

## Button order and gating

| # | Button | Enabled when | Result on page |
| --- | --- | --- | --- |
| 1 | `Скачать доступные акции` | store selected, connection active, right `ozon.api.actions.download` | actions count, elastic actions count, operation link |
| 2 | `Выбрать акцию` | actions snapshot has candidate with `action_type = MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT` and title marker `Эластичный бустинг` | selected/saved action block |
| 3 | `Скачать товары участвующие в акции` | action selected, right `ozon.api.elastic.active_products.download` | active count, operation link |
| 4 | `Скачать товары кандидаты в акцию` | action selected, right `ozon.api.elastic.candidates.download` | candidate count, operation link |
| 5 | `Скачать данные по полученным товарам` | active/candidate snapshots exist or missing state explicitly accepted by approved rule | product info count, stock count, missing fields |
| 6 | `Обработать` | canonical rows ready, mapping gaps closed, right `ozon.api.elastic.calculate` | result groups, report link |
| 7 | `Принять результат` / `Не принять результат` | calculation completed, right `ozon.api.elastic.review` | `accepted`, `declined`, `stale` or `review_pending_deactivate_confirmation` review state |
| 8 | `Скачать Excel результата` | calculation completed, right `ozon.api.elastic.files.download` | file download |
| 9 | `Скачать Excel для ручной загрузки` | accepted calculation result and generated Stage 1-compatible manual upload file exists from TASK-024 post-acceptance generation | file download |
| 10 | `Загрузить в Ozon` | result accepted, connection active, upload rights, add/update confirmation, deactivate group confirmation if needed, drift-check pass | upload summary |

Every action button has disabled, processing, completed and failed states. During processing the button is disabled until the operation finishes or fails safely.

Button 10 is a live Ozon actions activate/deactivate write path per ADR-0033, not a mock/stub-only action. UI must still present the same confirmation and drift gates before any write request can be sent.

## Required counters

The result area must show:

- actions downloaded;
- elastic actions found;
- selected action_id;
- selected action_type and title marker status;
- active products count;
- candidate products count;
- product info rows count;
- stock rows count;
- add count;
- update count;
- deactivate count;
- skip candidate count;
- blocked/error count;
- upload success count;
- upload rejected count.

## Review table

The review table must support filters by:

- planned action: add/update/deactivate/skip/blocked;
- reason_code;
- source_group;
- upload_ready;
- deactivate_required;
- row status/error.

Minimum displayed row fields:

- product_id;
- offer_id;
- name;
- source_group;
- source collision/details indicator when `source_group=candidate_and_active`;
- J/O/P/R;
- current action_price;
- calculated action_price;
- reason_code;
- planned action;
- upload_ready;
- deactivate reason, if applicable.

## Confirmation UX

Before upload the user confirms write intent by groups:

1. Add/update action prices.
2. Deactivate active products, only if deactivate count > 0.

Deactivate confirmation is one confirmation for the entire `deactivate_from_action` group, not one confirmation per row. Before that confirmation, UI must show the full group list with:

- product_id;
- offer_id;
- name;
- current action_price;
- source reason_code;
- human-readable reason;
- deactivate_reason_code;
- deactivate_reason.

If the user does not confirm the deactivate group, upload remains blocked as `review_pending_deactivate_confirmation` / `ozon_api_upload_blocked_deactivate_unconfirmed`. Add/update does not proceed as the normal final scenario while mandatory deactivate rows are unconfirmed, no `ozon_api_elastic_upload` operation is created, and no destructive Ozon API call is sent.

## Files

File links appear near the step that created them:

- result report after `Обработать`;
- manual upload Excel after accepted result and TASK-024 post-acceptance generation by ADR-0032;
- upload report after `Загрузить в Ozon`.

Expired files show metadata and unavailable download state according to `docs/architecture/FILE_CONTOUR.md`.

Manual upload Excel link/metadata must state that the file is `manual upload Excel по Stage 1-compatible template`. UI must not present it as the primary write path: API upload remains primary. If deactivate rows exist and are represented through a separate sheet/section `Снять с акции`, the files area must keep that fact visible so the user understands those products need removal from the action.

## Navigation placeholders

The marketplace navigation may show future Ozon/WB domain/source entries, but only `Ozon -> Акции -> API -> Эластичный бустинг` is enabled as Stage 2.2 workflow. Future entries must not expose action buttons or partial business screens.

## Operation card

Operation card must display `mode=api`, `marketplace=ozon`, `module=actions`, and `step_code`. It must not force Stage 2.2 operations into Stage 1 `check/process` type.

For upload operations the card shows:

- accepted calculation basis;
- confirmation facts;
- drift-check result;
- add/update/deactivate batch summaries;
- per-row success/rejection;
- activate/deactivate endpoint family and safe request mapping summary without secrets/raw sensitive payload;
- safe audit/techlog links.
