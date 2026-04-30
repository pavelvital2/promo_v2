# TASK-018: Design Stage 2.2 Ozon API executable documentation

ID: TASK-018-DESIGN-STAGE-2-2-OZON-API  
Тип задачи: проектирование исполнительной документации  
Агент: проектировщик Stage 2.2 Ozon API  
Статус: draft for designer  
Дата постановки: 2026-04-29

## Цель

Подготовить полный комплект исполнительной документации для реализации Stage 2.2: Ozon API-контур акции `Эластичный бустинг`.

Stage 2.2 должен проектироваться не как новая бизнес-логика расчёта, а как API-адаптер к уже принятой Ozon Excel-логике Stage 1:

```text
Ozon API sources -> canonical Ozon J/O/P/R row -> existing Ozon decision rules -> result review -> accepted-result manual Excel output / confirmed API write
```

Особое внимание уделить веб-панели: пользовательский сценарий должен быть понятным, пошаговым, с явной иерархией marketplace/domain/source и с раздельным подтверждением действий, которые меняют Ozon.

## Реализация через Codex CLI orchestration

Stage 2.2 должен проектироваться и реализовываться оркестратором Codex CLI через управление task-scoped агентами Codex CLI.

Обязательный процесс:

1. Оркестратор выдаёт проектировщику задачу на исполнительную документацию.
2. Проектировщик читает только task-scoped пакет документов и готовит Stage 2.2 specs, tasks, acceptance и traceability.
3. Аудитор проверяет исполнительную документацию до разработки.
4. Разработка начинается только после audit pass или после закрытия blocking gaps.
5. На каждую implementation task оркестратор создаёт отдельного агента Codex CLI с ролью, задачей, границами изменения и ограниченным пакетом документов.
6. Агент не перечитывает всё ТЗ, а читает только документы, необходимые для выполнения своей задачи.
7. Разработчик реализует только утверждённый task scope.
8. Тестировщик проверяет реализованное поведение по acceptance/test docs и не подменяет аудитора.
9. Аудитор проверяет соответствие реализации утверждённой документации, ТЗ, GAP/ADR и не подменяет тестировщика.
10. Если проектировщик, тестировщик или аудитор обнаруживает пробел по функционалу комплекса или UX веб-панели, вопрос адресуется заказчику через оркестратора.
11. После завершения конкретной задачи агент закрывается/удаляется; следующий task получает нового агента и свой пакет чтения.

Проектировщик должен учесть этот процесс в Stage 2.2 documentation package: reading packages, task split, audit gates, testing gates and handoff format должны быть пригодны для такого оркестраторского режима.

## Источник истины и входные документы

Источник истины:

- `itogovoe_tz_platforma_marketplace_codex.txt`, читать только task-scoped разделы, нужные для Stage 2.2 и UI gaps.

Обязательные входные документы:

- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/orchestration/ORCHESTRATION.md`
- `docs/orchestration/TASK_TEMPLATES.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md`
- `docs/product/UI_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`
- `docs/testing/CONTROL_FILE_REGISTRY.md`
- `docs/reports/STAGE_2_1_WB_RELEASE_READINESS.md`
- `предварительно_2.2.txt`

Существующий код для ориентира:

- `apps/discounts/ozon_excel/services.py`
- `apps/discounts/ozon_excel/tests.py`
- `apps/web/views.py`
- `templates/web/`
- `apps/stores/`
- `apps/operations/`
- `apps/files/`
- `apps/identity_access/seeds.py`

## Контекст discovery по Ozon API

В тестовом read-only контуре Ozon API уже проверено:

- `GET /v1/actions` возвращает доступные акции.
- Найдена акция `Эластичный бустинг. Без ограничения срока действия`.
- Для этой акции есть две группы товаров:
  - participating products: товары уже участвуют в акции;
  - candidates: товары доступны для добавления в акцию.
- `POST /v1/actions/products` и `POST /v1/actions/candidates` возвращают elastic-поля:
  - `price_min_elastic`
  - `price_max_elastic`
  - `current_boost`
  - `min_boost`
  - `max_boost`
  - `action_price`
  - `max_action_price`
  - `add_mode`
- Action-row `stock` не должен автоматически считаться Excel-остатком `R`: в проверке он был `0`, хотя `/v4/product/info/stocks` показывал фактический остаток.
- Для получения canonical input нужны минимум три источника:
  - `/v1/actions/products` + `/v1/actions/candidates` для состава акции и elastic-полей;
  - `/v3/product/info/list` для `offer_id`, name, `min_price`;
  - `/v4/product/info/stocks` для фактических остатков.

Предварительная карта Excel -> API:

| Excel | Смысл | API-источник для проектирования |
| --- | --- | --- |
| `J` | минимально допустимая цена | `min_price` из `/v3/product/info/list` по customer decision 2026-04-30 / ADR-0030; отсутствующее/нечисловое значение даёт existing reason `missing_min_price` |
| `O` | минимальная буст-цена | observed/approved elastic minimum price field from `/v1/actions/products` and `/v1/actions/candidates` per customer decision 2026-04-30 / ADR-0033; exact field name follows current official Ozon schema |
| `P` | максимальная буст-цена | observed/approved elastic maximum price field from `/v1/actions/products` and `/v1/actions/candidates` per customer decision 2026-04-30 / ADR-0033; exact field name follows current official Ozon schema |
| `R` | остаток | сумма `present` по всем stock rows из `/v4/product/info/stocks`, включая FBO + FBS; `reserved` не вычитать; отсутствующий stock info или сумма `present <= 0` даёт existing reason `no_stock` по customer decision 2026-04-30 / ADR-0031 |
| `K` | участие | результат расчёта |
| `L` | итоговая цена акции | результат расчёта, затем `action_price` для upload |

Проектировщик обязан проверить и зафиксировать эту карту в исполнимой документации. `GAP-0015` по J закрыт customer decision 2026-04-30 / ADR-0030. `GAP-0016` по R закрыт customer decision 2026-04-30 / ADR-0031. `GAP-0018` по read-side fields and activate/deactivate payload policy закрыт customer decision 2026-04-30 / ADR-0033. `GAP-0019` по batch/rate/retry/idempotency policy закрыт technical/orchestrator decision 2026-04-30 / ADR-0034. Если по другому endpoint contract остаётся пробел, оформить GAP и вопрос заказчику через оркестратора.

## Граница Stage 2.2

В scope:

- Ozon API connection для Ozon store/cabinet.
- Получение доступных Ozon actions.
- Работа только с акцией `Эластичный бустинг`.
- Получение participating products.
- Получение candidates.
- Получение product info и stocks по объединённому списку товаров.
- Расчёт по существующим 7 правилам Ozon Excel.
- Review результата пользователем.
- Возможность принять или не принять результат.
- Excel-отчёт результата расчёта.
- Excel-файл для ручной загрузки в личный кабинет Ozon после принятия результата по customer-approved Stage 1-compatible template decision ADR-0032.
- API upload после явного подтверждения.
- Deactivate для active + not upload_ready товаров только после отдельного подтверждения и с обязательной причиной по каждой строке.
- Audit, techlog, operations, files, safe snapshots без секретов.

Не в scope:

- изменение Stage 1 Ozon Excel логики;
- изменение WB Stage 2.1;
- Ozon seller-actions, если они не являются нужным контуром Elastic Boosting;
- обычные Ozon акции вне `Эластичного бустинга`;
- изменение базовых цен товара через `/v1/product/import/prices`;
- управление elastic boosting через `prices.manage_elastic_boosting_through_price`;
- автоматическая загрузка без review/confirmation;
- скрытое удаление товаров из акции без отдельного подтверждения;
- пользовательские параметры скидки для Ozon, потому что в Excel-логике их нет.

## Обязательная бизнес-логика расчёта

Использовать существующие Ozon Excel rules без изменения порядка:

| # | Reason | Условие | Результат |
| --- | --- | --- | --- |
| 1 | `missing_min_price` | J отсутствует | не участвует |
| 2 | `no_stock` | R отсутствует или `R <= 0` | не участвует |
| 3 | `no_boost_prices` | O и P одновременно отсутствуют | не участвует |
| 4 | `use_max_boost_price` | P присутствует и `P >= J` | участвует, L = P |
| 5 | `use_min_price` | P присутствует, O присутствует, `P < J`, `O >= J` | участвует, L = J |
| 6 | `below_min_price_threshold` | O присутствует и `O < J` | не участвует |
| 7 | `insufficient_ozon_input_data` | остальные случаи | не участвует |

Требование к архитектуре: расчёт должен быть общим для Excel и API. Проектировщик должен заложить выделение shared decision engine или иное безопасное переиспользование существующей функции, чтобы API-модуль не дублировал формулы.

## Обязательная веб-иерархия

Проектировщик должен спроектировать новую навигационную модель веб-панели с запасом под будущие модули.

Иерархия:

```text
Маркетплейсы
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
```

Stage 2.2 реализует только:

```text
Маркетплейсы -> Ozon -> Акции -> API -> Эластичный бустинг
```

Остальные разделы должны быть заложены как навигационная структура/будущие entry points без реализации бизнес-логики, если проектировщик не оформит отдельный approved scope.

В UI нельзя смешивать:

- marketplace: Ozon/WB;
- domain: цены/акции/остатки/продажи/производство/поставки;
- source/mode: Excel/API;
- concrete workflow: Elastic Boosting.

## Рекомендуемый порядок кнопок Stage 2.2

Порядок пользователя должен быть таким:

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

Пояснение к правке порядка:

- `Выбрать акцию` нужен после скачивания доступных акций, потому что все следующие действия зависят от конкретного `action_id`.
- Participating и candidates можно скачивать отдельными кнопками, как хочет заказчик, но расчёт разрешён только когда обе группы обработаны или когда пользователь явно подтвердил допустимость отсутствующей группы.
- `Скачать данные по полученным товарам` должен идти после получения participating/candidates, потому что product info/stocks запрашиваются по объединённому набору `product_id`.
- `Принять результат` должен идти до API upload. Непринятый результат нельзя загрузить.
- Excel результата должен быть доступен после расчёта. Excel для ручной загрузки доступен только после принятия результата. Manual upload Excel is a separate file scenario and secondary artifact; API upload remains the primary write path.

## Workflow details

### Step 1: Скачать доступные акции

Operation step_code:

```text
ozon_api_actions_download
```

Требования:

- read-only;
- получить `/v1/actions`;
- сохранить safe snapshot без секретов;
- показать только Ozon actions;
- отдельно выделить `Эластичный бустинг` по customer-approved rule: `action_type = MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT` and title contains `Эластичный бустинг`;
- не использовать hard-coded global `action_id`; пользовательский выбор сохраняет `action_id` as workflow basis for selected store/account.

### Step 2: Выбрать акцию

Требования:

- пользователь выбирает конкретный `action_id`;
- UI показывает name, dates, participating count, candidate count, action type/status;
- выбранный/saved `action_id` становится basis для следующих операций;
- нельзя продолжать, если акция не распознана как Elastic Boosting.

### Step 3: Скачать товары участвующие в акции

Operation step_code:

```text
ozon_api_elastic_active_products_download
```

Требования:

- read-only;
- вызвать `/v1/actions/products`;
- пройти пагинацию;
- сохранить source_group=`active`;
- сохранить action row elastic fields;
- не выполнять deactivate/update.

### Step 4: Скачать товары кандидаты в акцию

Operation step_code:

```text
ozon_api_elastic_candidate_products_download
```

Требования:

- read-only;
- вызвать `/v1/actions/candidates`;
- пройти пагинацию;
- сохранить source_group=`candidate`;
- сохранить action row elastic fields;
- не выполнять activate.

### Step 5: Скачать данные по полученным товарам

Operation step_code:

```text
ozon_api_elastic_product_data_download
```

Требования:

- read-only;
- объединить `product_id` из active + candidate;
- получить product info через `/v3/product/info/list`;
- J брать из `min_price`; отсутствующее/нечисловое `min_price` означает отсутствующий J and existing reason `missing_min_price`;
- получить stocks через `/v4/product/info/stocks`;
- R считать как сумму `present` по всем stock rows, включая FBO + FBS; `reserved` не вычитать; отсутствующий stock info или сумма `present <= 0` даёт existing reason `no_stock`;
- построить canonical rows J/O/P/R;
- сохранить immutable source snapshot;
- показать missing fields по каждой строке;
- не использовать action-row `stock` как источник R.

### Step 6: Обработать

Operation step_code:

```text
ozon_api_elastic_calculation
```

Требования:

- использовать существующие Ozon 7 rules;
- рассчитать active и candidate строки;
- сформировать группы результата:
  - `add_to_action`: candidate + upload_ready;
  - `update_action_price`: active + upload_ready;
  - `deactivate_from_action`: active + not_upload_ready;
  - `skip_candidate`: candidate + not_upload_ready;
  - `blocked`: строки с технически неполными/некорректными данными, если они не покрыты business reason;
- для каждой строки сохранить reason_code;
- для `deactivate_from_action` причина обязательна;
- сформировать result Excel/report.

### Step 7: Принять или не принять результат

Review/approval фиксируется как состояние результата расчёта, а не как отдельный `Operation step_code`.

```text
not_reviewed
accepted
declined
stale
review_pending_deactivate_confirmation
```

Customer decision 2026-04-30 resolved `GAP-0020`: TASK-024 uses calculation result review state and audit, not a separate Operation.

Требования:

- пользователь видит summary:
  - добавить в акцию;
  - обновить цену;
  - снять с акции;
  - пропустить кандидатов;
  - blocked/errors;
- пользователь видит строки `Снять с акции` с обязательной причиной;
- `Не принять результат` запрещает upload и фиксирует audit;
- `Принять результат` фиксирует immutable accepted basis для upload;
- after acceptance, generate `ozon_api_elastic_manual_upload_excel` from the immutable accepted calculation snapshot;
- если после принятия пользователь перескачал данные, старый result становится stale для upload или требует drift-check.

### Step 8: Скачать Excel результата

File scenario proposal:

```text
ozon_api_elastic_result_report
```

Файл должен содержать минимум:

- marketplace;
- store/cabinet;
- action_id;
- action name;
- source_group;
- product_id;
- offer_id;
- name;
- current action_price;
- J/min_price;
- O/price_min_elastic;
- P/price_max_elastic;
- R/stock_present;
- current_boost;
- min_boost;
- max_boost;
- reason_code;
- human-readable reason;
- planned action: add/update/deactivate/skip/blocked;
- calculated action_price;
- upload_ready;
- deactivate_required;
- deactivate_reason.

### Step 9: Скачать Excel для ручной загрузки

Customer decision 2026-04-30 / ADR-0032: для Stage 2.2 v1 файл ручной загрузки Ozon Elastic Boosting формируется по текущему Stage 1 Ozon Excel-шаблону/формату as Stage 1-compatible manual upload Excel. Это accepted compatibility risk: если Ozon ЛК не примет файл, это future compatibility issue, но v1 реализует этот формат.

- файл формируется only after `Принять результат` from immutable accepted calculation snapshot;
- файл явно отмечен как manual upload Excel по Stage 1-compatible template;
- Stage 1 Ozon Excel business rules не меняются;
- K = `Да` для add/update rows;
- L = calculated action price;
- deactivate rows не удаляются молча;
- если Stage 1-compatible template не поддерживает deactivate action directly, workbook/report includes separate sheet/section `Снять с акции` with row-level reasons.

File scenario proposal:

```text
ozon_api_elastic_manual_upload_excel
```

`GAP-0017` закрыт этим решением; downstream block for `ozon_api_elastic_manual_upload_excel` removed.

### Step 10: Загрузить в Ozon

Operation step_code:

```text
ozon_api_elastic_upload
```

Требования:

- write operation, требует отдельного подтверждения;
- upload возможен только по accepted result;
- перед upload выполнить drift-check:
  - action still exists;
  - saved `action_id` still has `action_type = MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT`;
  - saved `action_id` title still contains `Эластичный бустинг`;
  - active/candidate membership still relevant;
  - J/O/P/R critical fields не изменились сверх утверждённого правила; для J сравнение идёт по `/v3/product/info/list` `min_price` per ADR-0030;
  - product eligibility не изменилась;
- upload add/update rows через current official Ozon actions activate endpoint, expected as `/v1/actions/products/activate`, with `action_id`, Ozon-required product identifiers and `action_price`;
- deactivate rows через current official Ozon actions deactivate endpoint, expected as `/v1/actions/products/deactivate`, with `action_id` and Ozon-required product identifiers, only if пользователь отдельно подтвердил группу `Снять с акции`;
- exact field names follow the official current Ozon schema and must be covered by request/response mapping tests;
- для каждой deactivate row сохранить reason_code и human-readable reason;
- partial success/rejection не теряет row-level details;
- повторная отправка защищена от случайного дубля;
- не вызывать `/v1/product/import/prices`.

## UI requirements

### General

- Все кнопки должны иметь активное/неактивное состояние.
- При нажатии action button кнопка должна визуально переходить в processing state и блокироваться до завершения запроса.
- После выполнения пользователь остаётся на той же master page; результат и download links появляются на этой же странице.
- Не должно быть перехода на страницу без кнопок продолжения сценария.
- Все file links должны быть рядом с соответствующим шагом.
- Operation card остаётся доступна как детальная страница, но основной workflow ведётся на master page.
- Ошибки API показывать безопасно, без Client-Id, Api-Key, headers, raw secret refs.

### Master page layout

Master page:

```text
Маркетплейсы / Ozon / Акции / API / Эластичный бустинг
```

Основные блоки:

- store selector;
- Ozon API connection status;
- выбранная акция;
- stepper/buttons;
- latest operations per step;
- summary counters;
- result review table;
- files;
- warnings/errors;
- audit/operation links.

### Required counters

На экране результата показать:

- actions downloaded;
- elastic actions found;
- selected action_id;
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

### Confirmation UX

Перед upload пользователь должен подтвердить write intent by groups:

1. add/update action prices;
2. deactivate active products, если таких строк больше 0.

Customer decision 2026-04-30: active/candidate_and_active + not_upload_ready rows are mandatory `deactivate_from_action`. Для deactivate требуется one group confirmation for all `deactivate_from_action` rows, not per-row confirmation. Before the group confirmation UI must show the full deactivate list:

- product_id;
- offer_id;
- name;
- текущая action_price;
- причина снятия;
- source reason_code;
- human-readable reason.

Если пользователь не подтверждает deactivate group, upload target result remains pending as `review_pending_deactivate_confirmation` / `ozon_api_upload_blocked_deactivate_unconfirmed`; upload operation is not created and add/update must not proceed silently. The deprecated scenario `deactivate declined -> add/update proceeds` is not a normal final scenario.

## Permissions

Проектировщик должен добавить отдельные права Ozon API, не смешивая их с Ozon Excel и WB API. Предварительный набор:

```text
ozon.api.connection.view
ozon.api.connection.manage
ozon.api.actions.view
ozon.api.actions.download
ozon.api.elastic.active_products.download
ozon.api.elastic.candidates.download
ozon.api.elastic.product_data.download
ozon.api.elastic.calculate
ozon.api.elastic.review
ozon.api.elastic.upload
ozon.api.elastic.upload.confirm
ozon.api.elastic.deactivate.confirm
ozon.api.elastic.files.download
ozon.api.operation.view
```

Проектировщик должен уточнить scope rights, seed roles and owner/admin/manager/observer behavior in `PERMISSIONS_MATRIX`.

## Data model and files

Проектировщик должен описать:

- Ozon action snapshot;
- Ozon elastic action row snapshot;
- joined product data snapshot;
- calculation result rows;
- accepted result state;
- upload batch/detail rows;
- file scenarios;
- retention and immutable basis rules.

Проектировщик должен решить, нужны ли физические модели или допустимо хранение через existing Operation/detail rows + snapshots. Решение должно быть явно принято и проверяемо аудитором.

## Reason/result codes

Расчётные коды должны совпадать с Ozon Excel:

```text
missing_min_price
no_stock
no_boost_prices
use_max_boost_price
use_min_price
below_min_price_threshold
insufficient_ozon_input_data
```

API-level коды оформить отдельно, например:

```text
ozon_api_action_not_elastic
ozon_api_action_not_found
ozon_api_missing_elastic_fields
ozon_api_missing_product_info
ozon_api_missing_stock_info
ozon_api_upload_blocked_by_drift
ozon_api_upload_rejected
ozon_api_upload_partial_rejected
ozon_api_upload_success
ozon_api_deactivate_required
ozon_api_deactivate_group_confirmed
ozon_api_upload_blocked_deactivate_unconfirmed
ozon_api_auth_failed
ozon_api_rate_limited
ozon_api_timeout
ozon_api_response_invalid
```

`ozon_api_missing_stock_info` is an API-level diagnostic code only. It must not replace the calculation reason: absent stock info maps to existing Ozon reason `no_stock` per ADR-0031.

Добавление/переименование codes требует документации и ADR.

## GAPs/questions designer must close or escalate

Проектировщик обязан закрыть документацией или вынести заказчику:

- стабильное определение Elastic Boosting: `action_type`, title, another API marker;
- J=`min_price` закрыт customer decision 2026-04-30 / ADR-0030; отсутствующее/нечисловое `min_price` маппится в existing reason `missing_min_price`;
- R закрыт customer decision 2026-04-30 / ADR-0031: суммировать `present` по всем stock rows из `/v4/product/info/stocks`, включая FBO + FBS; `reserved` не вычитать; отсутствующий stock info или сумма `present <= 0` маппится в existing reason `no_stock`;
- `GAP-0017` manual upload Excel template закрыт customer decision 2026-04-30 / ADR-0032: use Stage 1-compatible Ozon Excel template/format as accepted v1 artifact;
- `GAP-0022` connection check endpoint/semantics closed by technical decision 2026-04-30 / ADR-0035: use read-only `GET /v1/actions`, map 200+valid `result` to `active`, map auth/rate/temporary/invalid response failures to documented `check_failed/*` results, and never use a write endpoint for connection check;
- `GAP-0018` read-side schemas and activate/deactivate payload policy closed by customer decision 2026-04-30 / ADR-0033: use observed/approved `/v1/actions/products` and `/v1/actions/candidates` fields, verify exact official field names during implementation, implement live activate/deactivate and do not substitute mock/stub-only writes;
- `GAP-0019` batch/rate/retry/idempotency закрыт technical/orchestrator decision 2026-04-30 / ADR-0034: read page size `100`, write batch size `100`, minimum interval `500 ms`, read-only transient retry with bounded backoff, no automatic retry for sent/uncertain writes, explicit new operation after drift-check for write retry.

Customer decision 2026-04-30 closes the behavior if user accepts add/update but does not confirm deactivate: upload is blocked/pending and no Ozon write operation starts.
Customer decision 2026-04-30 also closes `GAP-0020`: review is a calculation result state, not a separate operation.
Customer decision 2026-04-30 also closes `GAP-0021`: if a product exists in both active and candidate sources, merge as `candidate_and_active`, treat as active for write planning, and keep collision visible in details/reports.
Customer decision 2026-04-30 also closes `GAP-0015`: canonical J uses `/v3/product/info/list` `min_price`; absent/non-numeric `min_price` uses existing reason `missing_min_price`.
Customer decision 2026-04-30 also closes `GAP-0018`: Stage 2.2 uses live Ozon actions activate/deactivate with accepted safeguards; `/v1/product/import/prices` remains prohibited.
Technical/orchestrator decision 2026-04-30 closes `GAP-0019`: conservative configurable API policy is documented in ADR-0034 and does not require customer UX/business approval.
Technical decision 2026-04-30 closes `GAP-0022`: production Ozon connection check uses read-only `GET /v1/actions` with status mapping from ADR-0035; no write endpoint may be used for connection check.

Если вопрос связан с функционалом комплекса или удобством веб-панели, проектировщик должен адресовать его заказчику через оркестратора, а не закрывать предположением.

## Required output documents

Проектировщик должен создать/обновить:

- `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`
- `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`
- `docs/product/OZON_API_ELASTIC_UI_SPEC.md` или обновить `docs/product/UI_SPEC.md` с отдельным Stage 2.2 разделом
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/tasks/implementation/stage-2/IMPLEMENTATION_TASKS.md`
- task files for implementation, proposed TASK-019..TASK-026
- `docs/testing/STAGE_2_2_OZON_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_2_OZON_ACCEPTANCE_CHECKLISTS.md`
- `docs/traceability/STAGE_2_2_OZON_TRACEABILITY_MATRIX.md`
- `docs/adr/ADR_LOG.md`
- `docs/gaps/GAP_REGISTER.md`

## Proposed implementation task split

Проектировщик может изменить нумерацию, но должен сохранить разделение ответственности:

- TASK-019: Ozon API connection and secret safety
- TASK-020: Ozon Elastic actions download and action selection
- TASK-021: Active/candidate products download
- TASK-022: Product info/stocks join and canonical input rows
- TASK-023: Shared Ozon calculation engine and result reports
- TASK-024: Result review/acceptance workflow
- TASK-025: Ozon upload add/update/deactivate with confirmations
- TASK-026: Stage 2.2 UI, acceptance, audit and release readiness

Не смешивать реализацию connection, download, calculation, review, upload and UI acceptance в одну большую задачу без reasoned orchestration decision.

## Acceptance requirements for designer output

Документация считается готовой к аудиту, если:

- Stage 2.2 scope самодостаточен;
- Ozon Excel rules не изменены;
- API mapping J/O/P/R явно описан;
- gaps вынесены в `GAP_REGISTER`;
- ADR фиксируют ключевые решения;
- UI hierarchy and step buttons documented;
- deactivate behavior documented with mandatory reasons;
- no API write operation exists without confirmation and drift-check;
- file scenarios and manual Excel output decision documented;
- permissions documented;
- operation step_codes documented;
- tests and acceptance checklist are actionable;
- implementation tasks are small enough for разработчик/тестировщик/аудитор.

## Запреты для проектировщика

- Не читать весь ТЗ вместо task-scoped sections без необходимости.
- Не менять Stage 1 Ozon Excel rules.
- Не менять Stage 2.1 WB release scope.
- Не проектировать upload через `/v1/product/import/prices`.
- Не скрывать destructive deactivate inside generic upload.
- Не оставлять UI/functionality gaps на разработчика.
- Не использовать Telegram/Postman/PyPI как единственный источник истины; они допустимы только как подсказки до проверки по official docs / real sanitized fixtures.
- Не включать реальные secrets или raw API responses with sensitive data in documentation.
