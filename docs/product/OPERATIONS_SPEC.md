# OPERATIONS_SPEC.md

Трассировка: ТЗ §12, §17, §20, §22-§23.

## Раздел "Операции"

Раздел "Операции" - самостоятельный реестр пользовательских, автоматических и сервисных бизнес-операций. Он не заменяет аудит и технический журнал.

Основной пользовательский запуск этапа 1 выполняется через сценарии:

- `Маркетплейсы -> WB -> Скидки -> Excel`;
- `Маркетплейсы -> Ozon -> Скидки -> Excel`.

Раздел операций нужен для журнала, контроля, поиска, истории и разбора проблемных случаев.

## Операция

Операция после завершения неизменяема. Нельзя менять результат, связанные версии файлов, применённые параметры или итоговые данные. Для повторной попытки создаётся новая операция.

Удаление завершённых operations, их detail rows, связей с файлами, snapshots, warning confirmations, audit links и techlog links обычным пользовательским или административным способом запрещено. Общие правила удаления/архивирования см. в `docs/architecture/DELETION_ARCHIVAL_POLICY.md`.

Обязательные поля:

- visible_id;
- marketplace;
- module;
- mode;
- store/account;
- type: `check` или `process` только для check/process-сценариев; для Stage 2.1 WB API and Stage 2.2 Ozon API steps без check/process semantics поле nullable/blank/not_applicable по миграционному решению;
- step_code: обязательный classifier для Stage 2.1 WB API, Stage 2.2 Ozon API and future non-check/process steps;
- status;
- initiator;
- execution context;
- launch method;
- start/end datetime;
- input file versions;
- output file version, если есть;
- check operation basis для process;
- applied parameters snapshot;
- business logic version;
- summary;
- errors/warnings;
- row details;
- warning confirmation facts;
- links to audit/tech log при проблемах.

## Run

Run - внутренняя контейнерная сущность пользовательского запуска. Он объединяет:

- связанные файлы;
- версии файлов;
- проверки;
- обработки;
- результаты.

В UI главным объектом остаётся operation. На этапе 1 обязателен временный черновой контекст активного сценария, позволяющий загрузить, заменить и удалить файлы до запуска операции. Постоянный черновик между отдельными входами пользователя не обязателен.

## Модель "Проверить / Обработать"

Пользователь может нажать "Проверить" или "Обработать".

Если нажато "Проверить":

- создаётся operation типа `check`;
- выполняется только проверка;
- output workbook не создаётся;
- workbook не изменяется;
- результат показывается пользователю.

Если нажато "Обработать":

- обработка выполняется только по допустимой проверке-основанию;
- если есть актуальная успешная проверка, повторная проверка не выполняется;
- если актуальной успешной проверки нет, система автоматически создаёт check и при отсутствии ошибок продолжает process;
- check и process остаются отдельными operations;
- process хранит ссылку на конкретный check.

## Актуальность проверки

Check актуален для process только при совпадении:

- marketplace;
- store/account;
- набора входных файлов;
- конкретных file versions;
- применённых параметров;
- business logic version.

Если изменился любой элемент, при "Обработать" выполняется новая проверка.

## Допустимая основа обработки

- Ошибки есть: process запрещён.
- Ошибок нет, есть подтверждаемые warnings: process разрешён только после явного подтверждения.
- Ошибок нет, подтверждаемых warnings нет: process запускается без дополнительного подтверждения.

Факт подтверждения хранит:

- кто подтвердил;
- когда;
- по какой check operation;
- для какой process operation;
- какие warnings подтверждены.

## Повторные операции

Повторная проверка всегда создаёт новую operation. Повторная обработка всегда создаёт новую operation и новый output file при формировании. Если допустимых проверок несколько, система не выбирает скрыто: пользователь должен видеть основание обработки.

## Статусы

Check:

- `created` - создана / принята;
- `running` - выполняется;
- `completed_no_errors` - завершена без ошибок;
- `completed_with_warnings` - завершена с предупреждениями;
- `completed_with_errors` - завершена с ошибками;
- `interrupted_failed` - прервана / сбойная.

Process:

- `created` - создана / принята;
- `running` - выполняется;
- `completed_success` - завершена успешно;
- `completed_with_warnings` - завершена с предупреждениями;
- `completed_with_error` - завершена с ошибкой;
- `interrupted_failed` - прервана / сбойная.

Ручная отмена операции пользователем на этапе 1 не реализуется.

## Карточка операции

Карточка операции показывает:

- visible_id;
- marketplace/module/mode;
- store/account;
- classifier/status: `type` for check/process operations or `step_code` for Stage 2.1 WB API / Stage 2.2 Ozon API operations;
- initiator;
- start/end time;
- input files and versions;
- output file if any;
- check basis for process, if applicable;
- applied parameters and sources;
- logic version;
- summary;
- errors/warnings;
- row details;
- warning confirmations;
- links to audit/tech log if any.

Детализация по строкам:

- row number;
- product identifier;
- row status;
- reason/result code;
- human-readable explanation;
- error/warning;
- problem field;
- final value if applicable.

Полная техническая трассировка не показывается по умолчанию и относится к техжурналу или расширенной диагностике с отдельным правом.

## Сбои

При сбое приложения, сервера, БД или файлового хранилища operation переводится в `interrupted_failed`. Автоматическое продолжение на этапе 1 запрещено. Новая попытка выполняется новой operation.

## Stage 2.1 WB API operations

Трассировка: `tz_stage_2.1.txt` §6-§11.

Stage 2.1 добавляет `mode=api` для WB. Excel mode Stage 1 не заменяется.

Для классификации API flow используется обязательный `Operation.step_code`. `Operation.type` не расширяется и не заполняется `check/process` для Stage 2.1 API steps; допустимое значение для этих operations - `NULL` / blank / `not_applicable` по выбранной миграции. 2.1.3 calculation не является Stage 1 check/process и также классифицируется через `step_code`.

| Step code | Подэтап | Тип действия | Меняет WB |
| --- | --- | --- | --- |
| `wb_api_prices_download` | 2.1.1 | read/download + internal product update | нет |
| `wb_api_promotions_download` | 2.1.2 | read/download + internal promotions save | нет |
| `wb_api_discount_calculation` | 2.1.3 | internal calculation + Excel output | нет |
| `wb_api_discount_upload` | 2.1.4 | API upload | да |

Migration guidance:

- сохранить Stage 1 `Operation.type=check/process` без изменения;
- добавить `step_code` как явный indexed/immutable classifier для `mode=api`, `marketplace=wb`;
- запретить `type=check/process` для `wb_api_prices_download`, `wb_api_promotions_download`, `wb_api_discount_calculation`, `wb_api_discount_upload`;
- обновить filters/list/card/report serializers so API operations label/filter by `step_code`, while check/process views continue to use `type`.

2.1.4 запрещён без successful 2.1.3, explicit confirmation, pre-upload drift check and active WB API connection.

Status mapping 2.1.4:

- WB status 3 -> `completed_success`;
- WB status 5 -> `completed_with_warnings`;
- WB status 6 -> `completed_with_error`;
- WB status 4 -> `completed_with_error`;
- API failure before uploadID -> `interrupted_failed`;
- API failure after uploadID -> `completed_with_error` until status can be resolved.

Повтор каждого Stage 2.1 step создаёт новую operation. UploadID хранится по каждому batch and operation remains immutable after completion.

## Stage 2.2 Ozon API operations

Трассировка: `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`; `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`; ADR-0023, ADR-0025, ADR-0026, ADR-0027.

Stage 2.2 adds `mode=api` for Ozon actions. Excel mode Stage 1 remains available.

Ozon API operations use `Operation.step_code` as mandatory primary classifier. `Operation.type` is not `check/process` for these API steps and must be `NULL` / blank / `not_applicable` according to the migration decision.

| Step code | Тип действия | Меняет Ozon |
| --- | --- | --- |
| `ozon_api_connection_check` | read-only connection check | нет |
| `ozon_api_actions_download` | read-only actions download | нет |
| `ozon_api_elastic_active_products_download` | read-only participating products download | нет |
| `ozon_api_elastic_candidate_products_download` | read-only candidates download | нет |
| `ozon_api_elastic_product_data_download` | read-only product info/stocks join | нет |
| `ozon_api_elastic_calculation` | internal calculation + result files | нет |
| `ozon_api_elastic_upload` | live Ozon actions activate/update/deactivate after confirmations per ADR-0033 | да |

Result review is not a separate operation and has no `Operation.step_code`. It is an immutable review state on the calculation result with audit actions for `accepted`, `declined`, `stale` and `review_pending_deactivate_confirmation` transitions.

`ozon_api_elastic_upload` is forbidden without:

- successful accepted calculation;
- active Ozon API connection;
- if add/update rows exist, explicit add/update confirmation;
- pre-upload drift-check;
- if deactivate rows exist, one group confirmation for all `deactivate_from_action` rows.

If deactivate group confirmation is absent, upload does not start and add/update must not proceed silently. The accepted result remains pending as `review_pending_deactivate_confirmation` / `ozon_api_upload_blocked_deactivate_unconfirmed`; no `not_uploaded_user_declined` terminal scenario is part of the Stage 2.2 target model.

`ozon_api_elastic_upload` must not call `/v1/product/import/prices`; add/update/deactivate request mapping follows the current official Ozon actions schema and preserves row-level reporting.
