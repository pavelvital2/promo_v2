# OZON_API_ELASTIC_UI_SPEC.md

Трассировка: `docs/tasks/design/stage-0/STAGE_0_OZON_ELASTIC_UI_TZ.md`; `docs/reports/WEB_PANEL_UX_AUDIT_2026-04-30.md`; `docs/product/UI_SPEC.md`; `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`; ADR-0023, ADR-0026..ADR-0035.

Статус: Stage 0 target UI spec, готово к аудиту проектной документации.

## Назначение

Экранная спецификация Stage 0 для приведения страницы:

```text
Маркетплейсы / Ozon / Акции / API / Эластичный бустинг
```

в операторский интерфейс без изменения Stage 2.2 бизнес-логики, прав, operation contour, audit/techlog, file contour, reason/result codes и Excel/API calculation rules.

UI не смешивает:

- marketplace: Ozon/WB;
- domain: цены/акции/остатки/продажи/производство/поставки;
- source/mode: Excel/API;
- operator workflow;
- diagnostics/audit/techlog;
- result review.

## Инварианты Stage 0

- Stage 0 не меняет расчёт Ozon Elastic: API sources -> canonical Ozon `J/O/P/R` -> existing 7-rule Ozon decision engine -> review -> output/upload.
- Stage 0 меняет только целевую UI-документацию; продуктовый код реализуется отдельной задачей после аудита.
- 7 операторских шагов не удаляют и не объединяют underlying operations. Сохраняются `Operation.step_code`, immutable snapshots, source operation links, audit records, techlog records, output links, file versions and checksums.
- Review remains calculation result state, not a separate operation.
- `Excel результата` remains file scenario `ozon_api_elastic_result_report`, but is not a main workflow step.
- `Excel для ручной загрузки` remains file scenario `ozon_api_elastic_manual_upload_excel`, generated after accepted result from immutable accepted calculation snapshot and labelled as `manual upload Excel по Stage 1-compatible template`.
- Diagnostics never exposes Client-Id, Api-Key, authorization headers, bearer/API key values, raw secret-like values or raw sensitive API responses.

## Page Structure

The page has three tabs:

1. `Рабочий процесс`
2. `Результат`
3. `Диагностика`

Default tab: `Рабочий процесс`.

### Common Header

Common header is visible on all tabs:

- breadcrumb: `Маркетплейсы / Ozon / Акции / API / Эластичный бустинг`;
- selected Ozon store/account;
- Ozon API connection status;
- selected action summary, if selected;
- latest relevant status: not started / in progress / completed / needs review / ready to upload / upload completed / error;
- links to related operation cards only when available and permitted.

Header must use human-readable labels. Technical labels such as `mode=api`, `module=actions`, `step_code`, raw `result_code`, `basis`, `checksum` and `source_operations` are not displayed in the header; they belong to `Диагностика` and operation card.

## Permissions

All permissions require object access to the selected Ozon store/account. Absence of object access hides the page data, operations, files, action rows and diagnostics for that store.

| Area/action | Required existing permissions |
| --- | --- |
| Open page / view workflow | `ozon.api.actions.view` |
| View Ozon API connection status | `ozon.api.connection.view` |
| Run `Скачать доступные акции` | `ozon.api.actions.download` |
| Select action | `ozon.api.actions.view` and saved action context access for the store |
| Run combined product/data download step | required sub-step permissions for each operation being started: `ozon.api.elastic.active_products.download`, `ozon.api.elastic.candidates.download`, `ozon.api.elastic.product_data.download` |
| Run `Обработать` | `ozon.api.elastic.calculate` |
| Accept/decline result | `ozon.api.elastic.review` |
| Download Stage 2.2 files | `ozon.api.elastic.files.download` |
| Confirm add/update upload | `ozon.api.elastic.upload.confirm` |
| Confirm deactivate group | `ozon.api.elastic.deactivate.confirm` |
| Run `Загрузить в Ozon` | `ozon.api.elastic.upload` plus confirmations above |
| View related Ozon API operations | `ozon.api.operation.view` |
| Open `Диагностика` tab | owner/global admin/local admin persona with object access and `ozon.api.operation.view` plus existing audit/techlog visibility rights for the records shown: `audit.list.view`/`audit.card.view` and/or `techlog.list.view`/`techlog.card.view`, with `logs.scope.limited` or `logs.scope.full` according to object access |
| View sensitive technical details refs | `techlog.sensitive.view`; secrets still must not be shown |

Stage 0 creates no new permission codes. Seed role effects remain governed by `docs/product/PERMISSIONS_MATRIX.md`: owner and administrators can receive diagnostics through existing audit/techlog permissions; managers work in the workflow/result areas by scenario permissions; observers see only explicitly granted view/download areas. `ozon.api.operation.view` alone is not enough to expose the `Диагностика` tab.

## Tab `Рабочий процесс`

Purpose: guide the operator through the approved Ozon Elastic flow with minimal technical noise.

Visible:

- common header;
- 7-step stepper;
- current/next required action;
- short status lines for completed steps;
- business counters after calculation;
- upload confirmation controls on the final step;
- final upload completion block.

Hidden from this tab:

- raw summaries;
- checksums;
- basis payloads;
- source operation arrays;
- API metadata;
- raw `step_code`, `reason_code`, `result_code`, `source_group`, `planned_action` codes;
- row-level error tables;
- full candidate/skip lists;
- diagnostics counts;
- raw JSON-like values.

### Step States

Each operator step supports:

- `Недоступен` - prerequisites or permissions are missing;
- `Готов к запуску` - user can start the action;
- `Выполняется` - submitted operation is running; current-step buttons are disabled;
- `Выполнено` - step completed without warnings;
- `Выполнено с предупреждениями` - step completed and workflow may continue if enough data exists for calculation;
- `Ошибка` - step failed or data is insufficient for the next required action;
- `Требует решения` - review/confirmation is required.

Completed steps show only a compact line:

- status;
- completion time;
- primary counts;
- human-readable warning/error summary, if any;
- link `Детали` to `Диагностика` or operation card when user has permission.

### Seven Operator Steps

| # | Operator step | UI action | Underlying Stage 2.2 contour |
| --- | --- | --- | --- |
| 1 | `Скачать доступные акции` | Button starts actions download. | Creates `ozon_api_actions_download`; audit `ozon_api_actions_download_started/completed`; safe snapshots/files according to existing specs. |
| 2 | `Выбрать акцию` | Select one Elastic Boosting action from downloaded candidates. | Saves selected `action_id` as workflow basis; no Operation; action identity follows ADR-0029. |
| 3 | `Скачать товары и данные по ним` | One operator step controls three existing read-only operations. | Preserves separate operations `ozon_api_elastic_active_products_download`, `ozon_api_elastic_candidate_products_download`, `ozon_api_elastic_product_data_download`, their snapshots, source links, audit/techlog, file/version links and checksums. |
| 4 | `Обработать` | Runs calculation. | Creates `ozon_api_elastic_calculation`; creates immutable calculation snapshot and `ozon_api_elastic_result_report`. |
| 5 | `Принять / не принять результат` | Review action on the calculation result. | No Operation; state changes on calculation result: `accepted`, `declined`, `stale`, `review_pending_deactivate_confirmation`; audit `ozon_api_elastic_result_reviewed`. |
| 6 | `Скачать Excel для ручной загрузки` | Downloads manual upload Excel after acceptance. | Uses `ozon_api_elastic_manual_upload_excel`, generated from accepted snapshot, Stage 1-compatible template per ADR-0032. |
| 7 | `Загрузить в Ozon` | Confirms and starts live upload. | Creates `ozon_api_elastic_upload` only after accepted result, drift-check and required confirmations; writes via approved Ozon actions activate/deactivate contour. |

Old UI steps 3, 4 and 5 are merged only at operator UI level into step 3. The implementation must still create/read the three existing operations separately and keep their immutable evidence.

Old step `Скачать Excel результата` is removed from the main workflow. The result report file is available in `Результат`, `Диагностика` and operation card.

### Combined Step Warning Rule

If `Скачать товары и данные по ним` completes with warnings but has enough active/candidate/product info/stock data for calculation, the step state is `Выполнено с предупреждениями` and the operator may continue.

Continuation is blocked only by errors that make calculation impossible, including missing required source group without an approved exception, missing selected action basis, unsafe/invalid snapshots, or missing canonical rows.

### Result Summary In Workflow

After calculation, `Рабочий процесс` shows only:

- `Будет обновлено в акции`;
- `Будет добавлено в акцию`;
- `Будет снято с акции`.

The workflow summary must also state that calculation considered:

- participating products;
- candidate products.

Do not show candidate skip rows, non-applicable products, full reasons, row errors or technical fields in `Рабочий процесс`.

### Upload Step

No separate final confirmation screen is created.

The final step contains:

- human-readable totals by write group;
- checkbox/confirmation for add/update if add/update rows exist;
- separate group-level checkbox/confirmation for `Будет снято с акции` if deactivate rows exist;
- active `Загрузить в Ozon` button only after all required confirmations and preconditions pass.

If deactivate rows exist and group confirmation is not given:

- upload remains blocked as `review_pending_deactivate_confirmation` / `ozon_api_upload_blocked_deactivate_unconfirmed`;
- no `ozon_api_elastic_upload` operation is created;
- add/update does not silently proceed as a final upload scenario;
- no destructive Ozon API call is sent.

After successful upload, the user remains on the scenario page and sees `Загрузка завершена`:

- upload status;
- sent rows count;
- accepted by Ozon count;
- rejected by Ozon count;
- link to upload operation card;
- link to `Excel для ручной загрузки`;
- if Ozon row errors exist, link to group `Отклонено Ozon` in `Результат`.

## Tab `Результат`

Purpose: let the user inspect the calculation result and files using human-readable groups.

Availability:

- visible after calculation exists;
- if no calculation exists, show empty state with instruction to complete `Обработать`;
- download actions require `ozon.api.elastic.files.download`.

### Result Groups

All groups are always shown. Empty groups are compact and show counter `0`.

| Group | Rows |
| --- | --- |
| `Будет обновлено в акции` | active or `candidate_and_active` rows with `upload_ready`, planned update. |
| `Будет добавлено в акцию` | candidate rows with `upload_ready`, planned add. |
| `Не проходит расчёт сейчас` | candidate rows with `not_upload_ready` / `skip_candidate`; no action in workflow summary. |
| `Будет снято с акции` | active or `candidate_and_active` rows with `not_upload_ready`, planned `deactivate_from_action`. |
| `Ошибки` | blocked rows, technical invalid rows, row-level calculation/upload errors. |
| `Отклонено Ozon` | shown after upload only when Ozon returns row-level rejections. |

Candidates that pass business logic appear in `Будет добавлено в акцию`. Candidates that do not pass business logic do not appear in `Рабочий процесс`; they appear in `Не проходит расчёт сейчас` with reason.

Products already participating in the action but no longer matching business logic appear in `Будет снято с акции`.

### Tables and Filters

Each non-empty group uses a table with up to 10 rows per page. On mobile, implementation must avoid page-level horizontal overflow by using row cards or local table scroll.

Human-readable filters:

- source: `Участвует в акции`, `Кандидат`, `Кандидат и уже участвует`;
- action: `Обновить`, `Добавить`, `Не добавлять сейчас`, `Снять с акции`, `Ошибка`;
- reason category;
- upload status, after upload;
- search by product id, offer id or product name.

Minimum displayed row fields:

- product id;
- offer id;
- product name;
- source as human-readable text;
- current action price, if available;
- calculated action price, if applicable;
- stock/minimum price/elastic price summary in business labels;
- short human-readable reason;
- status/action group.

Row expansion shows full human-readable reason and safe details required to understand the row. Technical codes (`source_group`, `planned_action`, `reason_code`, `deactivate_reason_code`) may appear only in the expanded technical subsection if the user also has diagnostics permission; otherwise use human-readable labels.

### Files Result Block

`Результат` contains the scenario files block:

- `Excel результата` / `ozon_api_elastic_result_report` after calculation;
- `Excel для ручной загрузки` / `ozon_api_elastic_manual_upload_excel` after accepted result;
- upload report / `ozon_api_elastic_upload_report` after upload, if created.

File metadata follows `docs/architecture/FILE_CONTOUR.md`: file version, checksum availability in diagnostics/card, retention expiry, unavailable download after physical file expiry while metadata remains.

Manual upload Excel must be labelled:

```text
Excel для ручной загрузки - Stage 1-compatible template
```

If deactivate rows exist and the Stage 1-compatible template cannot directly represent deactivate action, the file block must state that the workbook/report includes sheet/section `Снять с акции`.

## Tab `Диагностика`

Purpose: expose operation and technical evidence without overloading the workflow.

Access: existing permissions only, see `Permissions`. No new diagnostics right is introduced.

### Diagnostics Groups

`Диагностика` groups technical data by evidence type:

1. `Операции`
   - operation visible id;
   - `marketplace=ozon`, `mode=api`, `module=actions`;
   - `step_code`;
   - status;
   - start/end;
   - initiator;
   - operation card link;
   - source operation links.
2. `Основание расчёта`
   - selected `action_id`;
   - action type/title marker status;
   - accepted calculation basis;
   - review state;
   - stale/drift-check status.
3. `Снимки и контроль целостности`
   - snapshot ids;
   - safe snapshot summaries;
   - checksums;
   - file version links;
   - source operation ids.
4. `API metadata`
   - endpoint family/method code;
   - response status classes;
   - pagination summary;
   - rate/batch summary;
   - no raw sensitive API responses.
5. `Audit / Techlog`
   - links to related audit records;
   - links to related techlog records;
   - safe messages;
   - sensitive details refs only with `techlog.sensitive.view`.
6. `Технические коды`
   - `source_group`;
   - `planned_action`;
   - review state;
   - API-level reason/result codes;
   - operation status.

Raw JSON-like values are collapsed by default. Large values are rendered in scrollable/preformatted blocks with height limits and line wrapping. Secrets and raw sensitive responses remain prohibited even inside collapsed blocks.

### Fields Moved Out of Workflow

The following fields must not appear in `Рабочий процесс` and belong here or in the operation card:

- `basis`;
- `downstream_basis_source`;
- `selection_basis`;
- `source_operations`;
- `diagnostics_counts`;
- `checksum`;
- raw `summary`;
- raw `result_code`;
- raw `step_code`;
- raw API request/response summaries;
- row-level technical dictionaries.

## Operation Card Amendment

Operation card remains a technical/audit screen at `/operations/OP-.../`.

Short block:

- visible id;
- human-readable operation name;
- marketplace/module/mode;
- store/account;
- classifier/status: `step_code` for Ozon API operations, not forced check/process type;
- initiator;
- start/end;
- primary counts;
- warning/error totals;
- output files and retention state;
- links back to scenario page, audit and techlog.

Technical expandable blocks:

- raw summary;
- basis / accepted basis;
- source operations;
- safe API metadata;
- drift-check details;
- batch summaries;
- row-level success/rejection;
- checksums and file versions;
- audit/techlog links.

Display rules:

- long raw values are collapsed by default;
- large values use scrollable/preformatted blocks;
- detail rows are paginated/filterable;
- user summary and audit/debug data are visually separated;
- Stage 2.2 upload cards show confirmation facts, deactivate group confirmation, activate/deactivate endpoint family and safe mapping summary without secrets.

## Marketplace Navigation Amendment

The `Маркетплейсы` page uses this hierarchy:

```text
Маркетплейсы
  -> WB
     -> Цены
        -> Excel
        -> API
     -> Акции
        -> Excel
        -> API
     -> Остатки
        -> Excel
        -> API
     -> Продажи
        -> Excel
        -> API
     -> В производство
        -> Excel
        -> API
     -> Поставки
        -> Excel
        -> API
  -> Ozon
     -> Цены
        -> Excel
        -> API
     -> Акции
        -> Excel
        -> API
           -> Эластичный бустинг
     -> Остатки
        -> Excel
        -> API
     -> Продажи
        -> Excel
        -> API
     -> В производство
        -> Excel
        -> API
     -> Поставки
        -> Excel
        -> API
```

Current active scenarios:

- `WB -> Скидки/Акции -> Excel`;
- `WB -> Скидки/Акции -> API`, if Stage 2.1 is enabled for the deployment;
- `Ozon -> Скидки/Акции -> Excel`;
- `Ozon -> Акции -> API -> Эластичный бустинг`.

Future sections not implemented in the current release are visible only as inactive items with label `Планируется`. They must not expose action buttons, forms, partial business screens or routes that look implemented.

Global top navigation remains unchanged:

- `Главная`
- `Маркетплейсы`
- `Операции`
- `Справочники`
- `Настройки`
- `Администрирование`
- `Аудит и журналы`

## Human-Readable Labels

Operator-facing labels must use Russian business wording:

| Technical value | Operator label |
| --- | --- |
| `completed_success` | `Выполнено` |
| `completed_with_warnings` | `Выполнено с предупреждениями` |
| `interrupted_failed` | `Ошибка выполнения` |
| `upload_ready` | `Готово к загрузке` |
| `update_action_price` | `Обновить в акции` |
| `add_to_action` | `Добавить в акцию` |
| `skip_candidate` | `Не добавлять сейчас` |
| `deactivate_from_action` | `Снять с акции` |
| `candidate` | `Кандидат` |
| `active` | `Участвует в акции` |
| `candidate_and_active` | `Кандидат и уже участвует` |

Adding/renaming technical codes is forbidden without documentation update and ADR.

## Implementation Acceptance Pointer

Future UI implementation must execute the Stage 0 UI checklist:

- `docs/testing/STAGE_0_OZON_ELASTIC_UI_ACCEPTANCE_CHECKLIST.md`

Future implementers must use the task-scoped reading package:

- `docs/tasks/implementation/stage-0/OZON_ELASTIC_UI_READING_PACKAGE.md`
