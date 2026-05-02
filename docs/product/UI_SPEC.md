# UI_SPEC.md

Трассировка: ТЗ §5-§6, §11, §17-§20.

## Общая UX-модель

Этап 1 проектируется desktop-first. Интерфейс должен быть читаемым на планшете и телефоне для просмотра статусов, операций, ошибок и кратких результатов. Полная mobile-first работа с файлами, администрированием и настройкой прав не входит в этап 1.

Верхняя навигация:

- Главная;
- Маркетплейсы;
- Операции;
- Справочники;
- Настройки;
- Администрирование;
- Аудит и журналы.

## Формат экранной спецификации

Каждый экран/состояние реализации должен иметь:

- назначение;
- раздел интерфейса;
- роли/права доступа;
- входные точки;
- отображаемые данные;
- действия;
- обязательные элементы управления;
- фильтры, поиск, сортировку, пагинацию, если применимо;
- сообщения, ошибки, предупреждения и статусы;
- переходы;
- связь со сценариями;
- критерии готовности.

## Общие правила списков и карточек

- Все списки этапа 1 должны поддерживать рабочую пагинацию, сортировку по основным колонкам и поиск/фильтры, указанные в соответствующем экране.
- Все карточки должны показывать `visible_id`, статус, связанные сущности в пределах прав пользователя и историю, если она обязательна по ТЗ.
- Пользователь не должен видеть магазины, операции, файлы, товары, параметры и аудит магазинов/кабинетов, к которым у него нет объектного доступа, кроме случаев глобальных административных прав.
- Чувствительные технические детали показываются только при праве `techlog.sensitive.view`.
- Завершённые operations, audit records и techlog records не редактируются через UI.
- Действия удаления/блокировки/деактивации/архивирования должны соответствовать `docs/architecture/DELETION_ARCHIVAL_POLICY.md`.

## Customer decisions для исправления TASK-009

На 2026-04-25 заказчик закрыл `GAP-0010`, `GAP-0011`, `GAP-0012` и `GAP-0013` как `resolved/customer_decision`; проектное решение зафиксировано в ADR-0015. Эти решения являются обязательным scope текущего исправления TASK-009 и не переносятся в TASK-010:

- `GAP-0010`: backend product model/list/card реализуются сейчас; status screen вместо списка/карточки товара не принимается.
- `GAP-0011`: write-flow WB store parameters реализуется сейчас с history/audit; read-only parameters screen не принимается.
- `GAP-0012`: draft run context реализуется сейчас: upload/replace/delete files, version list, затем "Проверить" / "Обработать"; single-submit upload без draft context не принимается.
- `GAP-0013`: admin write-flow реализуется сейчас: users create/edit/block/archive, role edit where allowed, permission assignment, store access assignment; read-only administration не принимается.

## Главная

| Поле | Спецификация |
| --- | --- |
| Назначение | Стартовая рабочая страница после входа. |
| Раздел | Главная. |
| Роли/права | Любой аутентифицированный пользователь; состав блоков зависит от section access и object access. |
| Входные точки | После успешного входа; верхняя навигация "Главная". |
| Данные | Доступные разделы, быстрые действия, последние operations, проблемные/требующие внимания operations, уведомления о сроках хранения файлов, краткие системные уведомления. |
| Действия | Перейти к WB/Ozon Excel, открыть список operations, открыть operation card, перейти к журналам/настройкам при наличии прав. |
| Контролы | Навигационные ссылки/кнопки, компактные списки последних и проблемных operations, индикаторы уведомлений. |
| Фильтры/поиск/сортировка/пагинация | Не обязательны; блоки показывают ограниченный список в пределах прав пользователя. |
| Сообщения/статусы | Нет доступных разделов, нет операций, есть critical notifications, истекает/истёк срок хранения файла. |
| Переходы | Маркетплейсы, Операции, карточка operation, Аудит и журналы, Настройки. |
| Сценарии | Быстрый вход в рабочие сценарии и контроль проблем. |
| Критерии готовности | Пользователь видит только разрешённые данные; проблемные operations и critical notifications доступны для перехода; недоступные разделы не показываются как рабочие. |

## Маркетплейсы -> WB -> Скидки -> Excel

### Экран запуска / загрузки файлов

| Поле | Спецификация |
| --- | --- |
| Назначение | Собрать run-контекст WB и запустить check или process. |
| Раздел | Маркетплейсы -> WB -> Скидки -> Excel. |
| Роли/права | `wb_discounts_excel.view`, `wb_discounts_excel.upload_input`, `wb_discounts_excel.run_check` и/или `wb_discounts_excel.run_process`, object access к WB store/account. |
| Входные точки | Навигация marketplace, Главная, повторная операция из operation card/list. |
| Данные | Выбранный WB store/account, 1 файл цен, 1-20 promo files, file versions, лимиты `.xlsx`, 25 МБ на файл, 100 МБ на run, WB parameters for selected store. |
| Действия | Выбрать магазин, загрузить/заменить/удалить файлы до запуска, открыть параметры WB, запустить "Проверить", запустить "Обработать". |
| Контролы | Store selector, file upload controls, file version list, кнопки "Проверить" и "Обработать", блок параметров WB, индикатор лимитов. |
| Фильтры/поиск/сортировка/пагинация | Поиск/фильтр магазина в selector; пагинация не требуется. |
| Сообщения/статусы | Не выбран магазин, нет price file, нет promo files, больше 20 promo files, неподдерживаемый формат, превышен лимит размера, нет права действия, нет object access. |
| Переходы | Результат проверки, экран подтверждения warnings, результат обработки, карточка operation. |
| Сценарии | WB check/process по Excel. |
| Критерии готовности | Невозможно запустить operation с нарушенным составом файлов; draft run context поддерживает upload/replace/delete files и version list до запуска; замена файла создаёт новую version; UI не предлагает API-режим как замену Excel. |

### Блок параметров расчёта WB

| Поле | Спецификация |
| --- | --- |
| Назначение | Показать и при наличии прав изменить три WB-параметра выбранного магазина/кабинета. |
| Раздел | Встроенное состояние WB Excel и маршруты Настройки. |
| Роли/права | Просмотр: `settings.store_params.view` или `settings.param_source.view`; изменение: `settings.store_params.edit` или `stores.params.edit`; object access к store. |
| Входные точки | WB запуск, карточка магазина, параметры магазина. |
| Данные | `wb_threshold_percent`, `wb_fallback_no_promo_percent`, `wb_fallback_over_threshold_percent`, источник `system`/`store`, effective timestamp/version. |
| Действия | Просмотреть источник, изменить store value, сохранить, отменить. |
| Контролы | Numeric inputs, source badges, save/cancel, link to history. |
| Фильтры/поиск/сортировка/пагинация | Не применимо. |
| Сообщения/статусы | Нет права изменения, значение магазина не задано и используется system default, изменение применится только к новым operations. |
| Переходы | История параметров, карточка магазина. |
| Сценарии | WB parameter cascade and snapshot. |
| Критерии готовности | Изменение фиксируется в истории и audit; уже завершённые operations не меняются; Ozon параметры здесь не появляются; read-only substitute для TASK-009 не допускается. |

### Экран результата проверки

| Поле | Спецификация |
| --- | --- |
| Назначение | Показать итог WB check без создания output workbook. |
| Раздел | Маркетплейсы -> WB -> Скидки -> Excel. |
| Роли/права | `wb_discounts_excel.view_check_result`, `wb_discounts_excel.view_details` для детализации, object access. |
| Входные точки | Завершение check; operation card/list. |
| Данные | Operation visible_id/status, error_count, warning_count, основные проблемы, detail rows, file versions, applied parameter snapshot. |
| Действия | Открыть детализацию, открыть operation card, запустить process при допустимой check-основе, повторить check новой operation. |
| Контролы | Summary panel, tabs/table for detail rows, buttons/process/rerun/card, download detail report при праве. |
| Фильтры/поиск/сортировка/пагинация | Поиск и фильтр detail rows по row status, reason/result code, error/warning, problem field; пагинация detail rows. |
| Сообщения/статусы | Check completed no errors/warnings/errors; process blocked by errors; confirmation required for confirmable warnings. |
| Переходы | Confirmation warnings, result process, operation card. |
| Сценарии | Check-only and process basis selection. |
| Критерии готовности | Output file не создан; process доступен только по правилам актуальности и допустимой основы; detail codes используются единообразно. |

### Экран подтверждения предупреждений

| Поле | Спецификация |
| --- | --- |
| Назначение | Получить явное подтверждение confirmable warnings перед process. |
| Раздел | Маркетплейсы -> WB -> Скидки -> Excel. |
| Роли/права | `wb_discounts_excel.confirm_warnings`, `wb_discounts_excel.run_process`, object access. |
| Входные точки | Нажатие "Обработать" при check без errors и с confirmable warnings. |
| Данные | Check operation, список warning codes/messages, affected rows summary, выбранная check basis. |
| Действия | Отменить, подтвердить и обработать. |
| Контролы | Warning summary, confirmation checkbox/explicit button, cancel. |
| Фильтры/поиск/сортировка/пагинация | Для длинного списка warnings применяется пагинация/поиск по строкам. |
| Сообщения/статусы | Нельзя обработать без подтверждения, check basis потеряла актуальность, нет права подтверждения. |
| Переходы | Результат обработки, результат проверки. |
| Сценарии | Confirmable warnings gate. |
| Критерии готовности | Фиксируются user, time, check_operation_id, process_operation_id, warning_codes; process не стартует до явного действия. |

### Экран результата обработки

| Поле | Спецификация |
| --- | --- |
| Назначение | Показать итог WB process и доступ к output workbook. |
| Раздел | Маркетплейсы -> WB -> Скидки -> Excel. |
| Роли/права | `wb_discounts_excel.view_process_result`, download rights для output/detail, object access. |
| Входные точки | Завершение process; operation card/list. |
| Данные | Operation status, processed rows, warnings/errors, output file/version, detail report, check basis, applied parameter snapshot. |
| Действия | Скачать output, скачать detail report, открыть operation card, повторить process новой operation при допустимой основе. |
| Контролы | Summary, download buttons, detail table, links. |
| Фильтры/поиск/сортировка/пагинация | Detail rows: фильтр по status/reason/error/warning; поиск по артикулу/строке; пагинация. |
| Сообщения/статусы | Output unavailable after retention, download denied, process failed/interrupted. |
| Переходы | Operation card, file unavailable state. |
| Сценарии | WB process completion. |
| Критерии готовности | Изменена только колонка `Новая скидка`; output связан с конкретной file version; скачивание проверяет права и retention. |

## Маркетплейсы -> Ozon -> Скидки -> Excel

### Экран запуска / загрузки файла

| Поле | Спецификация |
| --- | --- |
| Назначение | Собрать run-контекст Ozon и запустить check или process. |
| Раздел | Маркетплейсы -> Ozon -> Скидки -> Excel. |
| Роли/права | `ozon_discounts_excel.view`, `ozon_discounts_excel.upload_input`, `ozon_discounts_excel.run_check` и/или `ozon_discounts_excel.run_process`, object access к Ozon store/account. |
| Входные точки | Навигация marketplace, Главная, повторная operation. |
| Данные | Выбранный Ozon store/account, ровно 1 `.xlsx`, file version, лист `Товары и цены`, строки с 4-й, колонки J/K/L/O/P/R. |
| Действия | Выбрать магазин, загрузить/заменить/удалить файл до запуска, запустить "Проверить", запустить "Обработать". |
| Контролы | Store selector, single file upload, file version list, buttons check/process. |
| Фильтры/поиск/сортировка/пагинация | Поиск/фильтр магазина в selector. |
| Сообщения/статусы | Нет файла, больше одного файла, неверный формат, нет листа/колонок, нет права, нет object access. |
| Переходы | Результат проверки, подтверждение warnings, результат обработки, operation card. |
| Сценарии | Ozon check/process по Excel. |
| Критерии готовности | Draft run context поддерживает upload/replace/delete file и version list до запуска; Ozon не показывает WB-параметры; process использует только допустимую и актуальную check-основу; Excel не заменён API. |

### Экран результата проверки

| Поле | Спецификация |
| --- | --- |
| Назначение | Показать итог Ozon check без создания output workbook. |
| Раздел | Маркетплейсы -> Ozon -> Скидки -> Excel. |
| Роли/права | `ozon_discounts_excel.view_check_result`, `ozon_discounts_excel.view_details`, object access. |
| Входные точки | Завершение check; operation card/list. |
| Данные | Status, errors/warnings, row decisions by 7 Ozon rules, file version, sheet/column checks. |
| Действия | Открыть детализацию, открыть operation card, запустить process, повторить check. |
| Контролы | Summary, detail table, buttons process/rerun/card, detail report download при праве. |
| Фильтры/поиск/сортировка/пагинация | Фильтр по reason code/status/error/warning; поиск по row/product identifiers; пагинация. |
| Сообщения/статусы | Process blocked by errors, confirmation required for confirmable warnings, check basis inactive/outdated. |
| Переходы | Confirmation warnings, result process, operation card. |
| Сценарии | Ozon check-only and process basis. |
| Критерии готовности | Check ничего не пишет в workbook; reason codes соответствуют Ozon spec; process gate соблюдён. |

### Экран подтверждения предупреждений

| Поле | Спецификация |
| --- | --- |
| Назначение | Получить явное подтверждение confirmable warnings перед Ozon process. |
| Раздел | Маркетплейсы -> Ozon -> Скидки -> Excel. |
| Роли/права | `ozon_discounts_excel.confirm_warnings`, `ozon_discounts_excel.run_process`, object access. |
| Входные точки | Нажатие "Обработать" при допустимом check с confirmable warnings. |
| Данные | Check operation, warning codes/messages, affected rows summary, selected check basis. |
| Действия | Отменить, подтвердить и обработать. |
| Контролы | Warning summary, explicit confirmation, cancel. |
| Фильтры/поиск/сортировка/пагинация | Для длинной детализации warnings применяется пагинация. |
| Сообщения/статусы | Нет права подтверждения, check basis неактуальна, processing blocked. |
| Переходы | Result process, result check. |
| Сценарии | Confirmable warnings gate. |
| Критерии готовности | Подтверждение сохраняет user/time/check/process/warning codes и фиксируется в audit. |

### Экран результата обработки

| Поле | Спецификация |
| --- | --- |
| Назначение | Показать итог Ozon process и доступ к output workbook. |
| Раздел | Маркетплейсы -> Ozon -> Скидки -> Excel. |
| Роли/права | `ozon_discounts_excel.view_process_result`, download rights, object access. |
| Входные точки | Завершение process; operation card/list. |
| Данные | Status, processed rows, warnings/errors, output file/version, detail report, check basis, row decisions. |
| Действия | Скачать output, скачать detail report, открыть operation card, повторить process новой operation. |
| Контролы | Summary, download buttons, detail table. |
| Фильтры/поиск/сортировка/пагинация | Detail rows: reason/status/error/warning filters, row/product search, pagination. |
| Сообщения/статусы | Output unavailable after retention, download denied, process failed/interrupted. |
| Переходы | Operation card. |
| Сценарии | Ozon process completion. |
| Критерии готовности | Изменены только K и L; K содержит только `Да` или пусто; L содержит число или пусто; output связан с file version. |

## Маркетплейсы -> WB -> Скидки -> API

Трассировка: `docs/source/stage-inputs/tz_stage_2.1.txt` §13; ADR-0017, ADR-0018, ADR-0019.

Stage 2.1 UI выбирает единый мастер вместо четырёх независимых вкладок:

```text
WB -> Скидки -> API
  Шаг 1: Скачать цены
  Шаг 2: Скачать текущие акции
  Шаг 3: Рассчитать итоговый Excel
  Шаг 4: Загрузить по API
```

Excel route `WB -> Скидки -> Excel` остаётся доступным штатным/резервным режимом.

### Экран мастера WB API

| Поле | Спецификация |
| --- | --- |
| Назначение | Провести пользователя через Stage 2.1 WB API flow без смешивания read-only шагов и API upload. |
| Раздел | Маркетплейсы -> WB -> Скидки -> API. |
| Роли/права | View: `wb.api.operation.view`; действия по отдельным rights; object access к WB store/account. |
| Входные точки | Навигация marketplace, карточка магазина, карточка operation, result screens. |
| Данные | Store selector, состояние API-подключения, последние операции 2.1.1-2.1.4, выбранные price/promo/result basis, ссылки на файлы, warnings/errors. |
| Действия | Скачать цены, скачать текущие акции, рассчитать, подтвердить и загрузить по API, скачать файлы, открыть operation/product/promotion details. |
| Контролы | Store selector, connection status block, step cards, action buttons, file links, operation links, warning/error panels. |
| Фильтры/поиск/сортировка/пагинация | Store selector search; latest operations list filters by step/status/date; detail rows paginate. |
| Сообщения/статусы | Нет подключения, подключение не active, нет прав, нет object access, устаревшая basis, size conflicts, price drift, partial errors, quarantine. |
| Переходы | Store card, API connection screen, operation card, product list/card, audit/techlog. |
| Сценарии | 2.1.1-2.1.4. |
| Критерии готовности | 2.1.1/2.1.2/2.1.3 визуально обозначены как не меняющие WB; upload отделён confirmation screen; пользователь видит выбранную basis и результаты каждого шага. |

### Шаг 1: Цены

| Поле | Спецификация |
| --- | --- |
| Назначение | Скачать цены WB по API и сформировать Excel цен. |
| Роли/права | `wb.api.prices.download`, `wb.api.prices.file.download`, object access. |
| Данные | Operation status, fetched_at, goods count, Excel rows count, size-conflict count, checksum, initiator, file retention state. |
| Действия | Скачать цены по API, скачать Excel цен, открыть operation, открыть справочник товаров. |
| Сообщения/статусы | Нет active connection, API auth/rate/timeout error, size conflicts found, file expired. |
| Критерии готовности | Size conflicts видны; Excel download проверяет право; справочник товаров доступен только в object scope. |

### Шаг 2: Текущие акции

| Поле | Спецификация |
| --- | --- |
| Назначение | Скачать именно текущие акции WB и сформировать promo Excel files. |
| Роли/права | `wb.api.promotions.download`, `wb.api.promotions.file.download`, object access. |
| Данные | `current_filter_timestamp`, current/regular/auto counts, products count, actions without nomenclatures, file links. |
| Действия | Скачать текущие акции, скачать Excel по акции, открыть operation. |
| Сообщения/статусы | Нет current promotions, auto promotion without nomenclatures, invalid promo rows, API failures. |
| Критерии готовности | UI показывает правило current через timestamp/result, не предлагает "все/будущие" как замену; auto promotions не имеют выдуманных строк. |

### Шаг 3: Расчёт

| Поле | Спецификация |
| --- | --- |
| Назначение | Рассчитать скидки по API-источникам через WB logic Stage 1 и сформировать итоговый Excel. |
| Роли/права | `wb.api.discounts.calculate`, `wb.api.discounts.result.download`, object access. |
| Данные | Selected price export, selected promo exports, applied WB params, calculation logic version, rows/errors/warnings, result Excel, detail report. |
| Действия | Выбрать basis, рассчитать, скачать итоговый Excel, открыть operation. |
| Сообщения/статусы | Нет price export, нет promo export, source mismatch, outdated basis, errors block upload. |
| Критерии готовности | Выбранная basis видна явно; расчёт не меняет WB; результат можно скачать для ручной загрузки в ЛК WB. |

### Шаг 4: API-загрузка

| Поле | Спецификация |
| --- | --- |
| Назначение | Отправить рассчитанные скидки в WB по API только после confirmation и drift check. |
| Роли/права | `wb.api.discounts.upload`, `wb.api.discounts.upload.confirm`, object access. |
| Данные | Calculation operation, result file, товар count, excluded rows, drift check status, batch uploadIDs, success/error counts, partial/quarantine errors. |
| Действия | Открыть confirmation, подтвердить, выполнить upload, открыть upload report. |
| Контролы | Confirmation checkbox/button with exact phrase, cancel, upload action disabled until preconditions pass, batch/detail tables. |
| Сообщения/статусы | Upload blocked by drift, size conflict, invalid rows, status polling pending/failed, partial errors, quarantine errors, WB canceled upload. |
| Критерии готовности | Upload невозможен без explicit confirmation; успех не показывается до WB status polling; partial errors отображаются как `completed_with_warnings`; quarantine выделен отдельно. |

## Маркетплейсы -> Ozon -> Акции -> API -> Эластичный бустинг

Трассировка: `docs/tasks/design/stage-0/STAGE_0_OZON_ELASTIC_UI_TZ.md`; `docs/product/OZON_API_ELASTIC_UI_SPEC.md`.

Stage 2.2 использует отдельный master page. Stage 0 target UI specification находится в `docs/product/OZON_API_ELASTIC_UI_SPEC.md` и является обязательной для будущей реализации приведения Ozon Elastic UI в порядок.

Action selection follows ADR-0029: actions download marks Elastic Boosting candidates by `action_type = MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT` and title marker `Эластичный бустинг`; user-selected/saved `action_id` is the basis for downstream steps in the selected Ozon store/account.

Иерархия навигации закладывается с запасом:

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

Только `Ozon -> Акции -> API -> Эластичный бустинг` является рабочим Stage 2.2 flow. Future entry points не показываются как реализованные сценарии.

Целевая Stage 0 страница имеет вкладки:

1. `Рабочий процесс`
2. `Результат`
3. `Диагностика`

По умолчанию открывается `Рабочий процесс`. Диагностика доступна только через существующие права `ozon.api.operation.view`, audit/techlog permissions and object access; новые permission codes не создаются.

Целевой Stage 0 порядок operator workflow:

1. `Скачать доступные акции`
2. `Выбрать акцию`
3. `Скачать товары и данные по ним`
4. `Обработать`
5. `Принять / не принять результат`
6. `Скачать Excel для ручной загрузки`
7. `Загрузить в Ozon`

Объединение шага 3 является только операторским UI-объединением. Underlying operations, `Operation.step_code`, snapshots, audit/techlog, file versions, source links and checksums сохраняются: `ozon_api_elastic_active_products_download`, `ozon_api_elastic_candidate_products_download`, `ozon_api_elastic_product_data_download`.

`Скачать Excel результата` не является шагом основного рабочего процесса Stage 0. Файл `ozon_api_elastic_result_report` показывается в `Результат`, `Диагностика` и карточке операции.

`Загрузить в Ozon` is the live Ozon actions activate/deactivate write path per ADR-0033 and requires accepted result, drift-check and confirmation for each non-empty write group. Active/candidate_and_active + not_upload_ready rows are mandatory `deactivate_from_action`: UI shows the full deactivate group with row-level reasons and requests one group confirmation for all deactivate rows. Without this group confirmation upload is blocked as `review_pending_deactivate_confirmation` / `ozon_api_upload_blocked_deactivate_unconfirmed`; add/update does not silently proceed.

`Скачать Excel для ручной загрузки` downloads the ADR-0032 Stage 1-compatible manual upload artifact after accepted Stage 2.2 calculation result; the file is secondary to API upload and must keep `Снять с акции` rows visible when deactivate rows exist.

Future implementation acceptance uses `docs/testing/STAGE_0_OZON_ELASTIC_UI_ACCEPTANCE_CHECKLIST.md`; reading package is `docs/tasks/implementation/stage-0/OZON_ELASTIC_UI_READING_PACKAGE.md`.

## Операции

### Списки операций

| Поле | Спецификация |
| --- | --- |
| Назначение | Реестр пользовательских, автоматических и сервисных business operations. |
| Раздел | Операции: все операции, мои операции, проверки, обработки, проблемные/требующие внимания, архив/история. |
| Роли/права | Section access к Операциям; scenario-specific view rights; object access к stores/accounts. |
| Входные точки | Верхняя навигация, Главная, карточки магазина/товара, result screens. |
| Данные | visible_id, marketplace, module, mode, store/account, classifier (`type` для check/process, `step_code` для Stage 2.1 WB API and Stage 2.2 Ozon API), status, initiator, start/end, errors/warnings, file/output availability. |
| Действия | Открыть карточку, скачать output/detail при праве, перейти к повторной проверке/обработке, открыть связанные store/files. |
| Контролы | Tabs/views, table, filters, search, sort, pagination, export list. |
| Фильтры/поиск/сортировка/пагинация | Marketplace, store/account, module, mode, type for check/process, API step_code for Stage 2.1 and Stage 2.2, status, user, period, errors/warnings; search by visible_id; сортировка по времени/status; пагинация. |
| Сообщения/статусы | Нет операций, скрыто по object access, output expired, interrupted_failed, process requires attention. |
| Переходы | Operation card, WB/Ozon scenario, store card. |
| Сценарии | Контроль, поиск, история и разбор проблем. |
| Критерии готовности | Списки не показывают недоступные stores; check/process разделены по `type`; Stage 2.1 WB API and Stage 2.2 Ozon API steps разделены по `step_code` and not shown as check/process; Stage 2.2 filters/cards show `marketplace=ozon`, `mode=api`, `module=actions`; archive/history не удаляет metadata. |

### Карточка операции

| Поле | Спецификация |
| --- | --- |
| Назначение | Главный экран разбора результата operation без перегруза внутренними technical details. |
| Раздел | Операции и переходы из WB/Ozon results. |
| Роли/права | Operation view прав соответствующего сценария; detail/download rights по действиям; object access. |
| Входные точки | Список operations, result screens, карточки store/product, audit/techlog links. |
| Данные | visible_id, marketplace/module/mode, store, classifier/status (`type` for check/process or `step_code` for Stage 2.1 WB API and Stage 2.2 Ozon API), initiator, start/end, input file versions, output file, check basis if applicable, applied parameters, logic version, summary, errors/warnings, detail rows, warning confirmations if applicable, audit/techlog links. |
| Действия | Скачать output/detail, открыть file/store/product/audit/techlog, повторить check/process новой operation. |
| Контролы | Summary blocks, file/version links, parameter snapshot, detail table, links, download buttons, collapsed technical blocks for long raw values. |
| Фильтры/поиск/сортировка/пагинация | Detail rows: row number/product/reason/status/problem field; sort by row/status/reason; pagination. |
| Сообщения/статусы | Operation immutable, file expired, technical details hidden, process blocked/failed/interrupted. |
| Переходы | Related check/process, store card, product card, audit record, techlog record. |
| Сценарии | Explainability, support, repeat operations. |
| Критерии готовности | Все обязательные поля ТЗ §17.3 отображены; Stage 2.1 WB API and Stage 2.2 Ozon API operation cards show `step_code` instead of forcing check/process type; Stage 2.2 card shows `marketplace=ozon`, `mode=api`, `module=actions`; длинные raw JSON-like значения collapsed by default and rendered in scrollable/preformatted blocks; user summary separated from audit/debug data; завершённая operation не редактируется; links сохраняют конкретные versions. |

## Справочники

### Список магазинов / кабинетов / подключений

| Поле | Спецификация |
| --- | --- |
| Назначение | Найти и открыть рабочие store/account entities и connection blocks. |
| Раздел | Справочники; административный маршрут в Администрировании. |
| Роли/права | `stores.list.view`; object access или global admin rights. |
| Входные точки | Навигация Справочники, Администрирование, operation card. |
| Данные | visible_id, name, group/brand, marketplace, cabinet_type, status, API-block indicator, доступность пользователю. |
| Действия | Открыть карточку, создать store при `stores.create`, перейти к operations/products/settings. |
| Контролы | Table, create button, filters, search, sort, pagination, export. |
| Фильтры/поиск/сортировка/пагинация | Group/brand, marketplace, status, API-block presence, responsible/available user if applicable; search by name/visible_id; pagination. |
| Сообщения/статусы | Нет object access, archived/deactivated store, API block prepared for stage 2. |
| Переходы | Store card, store parameters, store operations, access assignments. |
| Сценарии | Stores, settings, access, operations context. |
| Критерии готовности | Фильтры из ТЗ §18.4 реализуемы; пользователь видит только разрешённые stores; административный маршрут не нарушает owner/object constraints. |

### Карточка магазина / кабинета / подключения

| Поле | Спецификация |
| --- | --- |
| Назначение | Основная карточка store/account для параметров, доступов, подключений, истории и связанных operations/products. |
| Раздел | Справочники; Администрирование. |
| Роли/права | `stores.card.view`; edit/actions by `stores.edit`, `stores.params.edit`, `stores.connection.*`, `stores.access.assign`, object access. |
| Входные точки | Store list, operation card, product card, settings, access assignments. |
| Данные | visible_id, name, group/brand/business direction, marketplace, cabinet_type, status, WB params if applicable, API block, user access, change history, related operations/products, service comments. |
| Действия | Edit store, deactivate/archive per policy, edit params, edit connection, assign access, open related operations/products/history. |
| Контролы | Tabs/sections for details, params, connection, access, history, operations, products; edit/save/cancel controls. |
| Фильтры/поиск/сортировка/пагинация | Related operations/products/history use their list filters and pagination. |
| Сообщения/статусы | API block: "подготовлено для этапа 2, в этапе 1 не используется"; archived/deactivated; no right to secrets; changes affect future operations only. |
| Переходы | Settings, access assignment, operation/product cards, audit records. |
| Сценарии | Store administration and operation context. |
| Критерии готовности | Все поля ТЗ §8.3 отображены; история §8.4 ведётся; API secrets hidden without right; deletion policy enforced. |

### Список товаров

| Поле | Спецификация |
| --- | --- |
| Назначение | Рабочий список marketplace products этапа 1. |
| Раздел | Справочники -> Товары. |
| Роли/права | Section access to products; object access to store/account. |
| Входные точки | Navigation, store card, operation detail row. |
| Данные | marketplace, store/account, external identifiers, title, SKU/barcode, status, last update. |
| Действия | Open product card, export list. |
| Контролы | Table, filters, search, sort, pagination, export. |
| Фильтры/поиск/сортировка/пагинация | Marketplace, store/account, article/SKU/identifier, status, last update date; pagination. |
| Сообщения/статусы | Нет товаров, товар archived/deactivated, hidden by object access. |
| Переходы | Product card, store card, related operations. |
| Сценарии | Product lookup and explainability. |
| Критерии готовности | Товары создаются/обновляются из valid Excel rows; отсутствие товара до загрузки не считается ошибкой; backend list реализован сейчас и status screen не считается покрытием TASK-009. |

### Карточка товара

| Поле | Спецификация |
| --- | --- |
| Назначение | Показать marketplace product, связанные operations/files и историю появления/обновления. |
| Раздел | Справочники -> Товары. |
| Роли/права | Product view within object access. |
| Входные точки | Product list, operation details, store card. |
| Данные | Marketplace, store, external ids, title, SKU/barcode, last_values, status, appearance/update history, related checks/processes, input/output files, future internal nomenclature block. |
| Действия | Open related operation/file/store; archive/deactivate if policy allows. |
| Контролы | Detail sections, history table, related operations/files tables. |
| Фильтры/поиск/сортировка/пагинация | Related lists filter/sort/paginate by date/status/type. |
| Сообщения/статусы | Future internal nomenclature is architectural placeholder, not production directory in stage 1. |
| Переходы | Operation card, store card. |
| Сценарии | Explainability and product history. |
| Критерии готовности | Backend card реализована сейчас; история появления/обновления сохранена; links to operations/files are immutable. |

## Настройки

### Системные параметры по умолчанию

| Поле | Спецификация |
| --- | --- |
| Назначение | Управлять системными default values для параметров этапа 1. |
| Раздел | Настройки. |
| Роли/права | View: `settings.system_params.view`; edit: `settings.system_params.edit`. |
| Входные точки | Navigation Настройки, WB params source link. |
| Данные | Parameter code, module, value, value type, active_from, history; WB system defaults: `wb_threshold_percent = 70`, `wb_fallback_over_threshold_percent = 55`, `wb_fallback_no_promo_percent = 55`. |
| Действия | View, edit future effective value, open history. |
| Контролы | Parameter table/form, save/cancel, history link. |
| Фильтры/поиск/сортировка/пагинация | Filter by module/code/status; search by code; pagination if list grows. |
| Сообщения/статусы | Changes affect only new operations; past operation snapshots unchanged. |
| Переходы | Parameter history, WB scenario. |
| Сценарии | Parameter cascade and snapshots. |
| Критерии готовности | No hidden Ozon discount parameters; changes audited and historized; past operation snapshots unchanged. |

### Параметры магазина / кабинета

| Поле | Спецификация |
| --- | --- |
| Назначение | Управлять store-level WB parameter values. |
| Раздел | Настройки; store card; WB scenario block. |
| Роли/права | `settings.store_params.view`, `settings.store_params.edit`, object access. |
| Входные точки | Settings, store card, WB scenario. |
| Данные | Store selector, WB parameters, effective value/source, history. |
| Действия | Set/clear store value, save, cancel, open history. |
| Контролы | Store selector, numeric inputs, source indicators. |
| Фильтры/поиск/сортировка/пагинация | Store selector search/filter; history paginates. |
| Сообщения/статусы | Store has no local value; using system default; changes affect new operations only. |
| Переходы | Store card, history. |
| Сценарии | WB store settings. |
| Критерии готовности | Ozon params absent; all changes generate history and audit; read-only substitute для TASK-009 не допускается. |

### История изменений параметров и настроек

| Поле | Спецификация |
| --- | --- |
| Назначение | Просмотреть изменения параметров и настроек. |
| Раздел | Настройки. |
| Роли/права | `settings.param_history.view` plus object/global scope. |
| Входные точки | Settings, WB params block, store card. |
| Данные | Date/time, user, field/parameter, old/new value, source, store/global scope, linked audit record. |
| Действия | Filter, search, open related store/audit. |
| Контролы | Table, filters, search, sort, pagination. |
| Фильтры/поиск/сортировка/пагинация | Period, user, store, parameter/field, source; pagination. |
| Сообщения/статусы | No history, hidden by access. |
| Переходы | Store card, audit record. |
| Сценарии | Explainability of settings and parameters. |
| Критерии готовности | История неизменяема через UI; old/new values shown without exposing protected secrets. |

## Администрирование

### Список пользователей

| Поле | Спецификация |
| --- | --- |
| Назначение | Управлять пользователями stage 1. |
| Раздел | Администрирование. |
| Роли/права | Global/local admin rights according to `docs/product/PERMISSIONS_MATRIX.md`; owner unrestricted. |
| Входные точки | Navigation Администрирование. |
| Данные | visible_id, login, display_name, status, primary_role, store access summary, block/archive state. |
| Действия | Create user, open card, block/unblock/archive according to policy, assign role/access. |
| Контролы | Table, create button, filters/search/sort/pagination. |
| Фильтры/поиск/сортировка/пагинация | Status, role, store access, login/name; pagination. |
| Сообщения/статусы | Owner cannot be limited/deleted/blocked by admin; user archived/blocked. |
| Переходы | User card, role card, access assignments, audit records. |
| Сценарии | Identity & Access administration. |
| Критерии готовности | UI не даёт ограничить владельца; direct denies priority is visible where relevant; create/block/unblock/archive actions реализованы сейчас в пределах прав. |

### Карточка пользователя

| Поле | Спецификация |
| --- | --- |
| Назначение | Просмотреть и изменить пользователя, роль, индивидуальные grants/denies и store access. |
| Раздел | Администрирование. |
| Роли/права | Admin rights scoped by global/local limitations; owner protected. |
| Входные точки | User list, audit record. |
| Данные | Login, display name, status, primary role, individual permissions, individual denies, store access, change/block history. |
| Действия | Edit allowed fields, change role, add/remove grants/denies, block/unblock/archive, open history/audit. |
| Контролы | Forms, permission selectors, store access selectors, save/cancel, history tabs. |
| Фильтры/поиск/сортировка/пагинация | Permission/store selectors support search/filter; histories paginate. |
| Сообщения/статусы | Owner action blocked, direct deny overrides allow, blocked user cannot sign in. |
| Переходы | Role card, access assignment, audit. |
| Сценарии | User access management. |
| Критерии готовности | Edit allowed fields, role changes, grants/denies, store access changes and block/archive actions реализованы сейчас; история значимых изменений и блокировок ведётся; protected owner controls disabled/absent. |

### Список ролей

| Поле | Спецификация |
| --- | --- |
| Назначение | Просмотр и управление role templates. |
| Раздел | Администрирование. |
| Роли/права | Admin rights; seed matrix approved by ADR-0007 and detailed in `docs/product/PERMISSIONS_MATRIX.md`. |
| Входные точки | Navigation Администрирование, user card. |
| Данные | Code/name/status/is_system, assigned users count, permissions summary. |
| Действия | Create role, open card, deactivate/archive according to policy. |
| Контролы | Table, create button, filters/search/sort/pagination. |
| Фильтры/поиск/сортировка/пагинация | Status, system/custom, search by code/name; pagination. |
| Сообщения/статусы | Role used in history cannot be physically deleted; owner/system roles protected. |
| Переходы | Role card, users. |
| Сценарии | Access template management. |
| Критерии готовности | Role management реализует create/open/deactivate/archive where allowed; roles are templates, not sole access mechanism; delete/archive policy enforced. |

### Карточка роли

| Поле | Спецификация |
| --- | --- |
| Назначение | Настроить role permissions and section access template. |
| Раздел | Администрирование. |
| Роли/права | Admin rights; owner/system protections. |
| Входные точки | Role list, user card. |
| Данные | Code, name, status, is_system, action rights, section access, permissible scopes, assigned users, change history. |
| Действия | Edit role, assign permissions/sections, deactivate/archive. |
| Контролы | Permission matrix, section toggles, save/cancel, history. |
| Фильтры/поиск/сортировка/пагинация | Permission search/filter by module/scope; assigned users paginate. |
| Сообщения/статусы | Cannot remove critical owner rights by admin; direct user deny may override role allow. |
| Переходы | Permission list, user list, audit. |
| Сценарии | Role template management. |
| Критерии готовности | Role edit and permission/section assignment реализованы сейчас where allowed; action rights, section access and object access remain separated. |

### Список прав доступа

| Поле | Спецификация |
| --- | --- |
| Назначение | Просмотр fixed permission and section access codes. |
| Раздел | Администрирование. |
| Роли/права | Admin/view access. |
| Входные точки | Navigation Администрирование, role card. |
| Данные | Permission code, name, scope_type, module/section, system dictionary status. |
| Действия | Search/filter; no user editing of system codes. |
| Контролы | Table, filters, search, sort, pagination. |
| Фильтры/поиск/сортировка/пагинация | Module, scope_type, section, search by code/name; pagination. |
| Сообщения/статусы | System codes are immutable through UI. |
| Переходы | Role card, user card. |
| Сценарии | Access review. |
| Критерии готовности | Permissions are visible for administration but not user-editable as dictionaries. |

### Экран назначений доступа к магазинам / кабинетам

| Поле | Спецификация |
| --- | --- |
| Назначение | Назначить object access к stores/accounts пользователям или ролям where applicable. |
| Раздел | Администрирование. |
| Роли/права | `stores.access.assign`; global/local admin scope; owner protected. |
| Входные точки | User card, store card, admin navigation. |
| Данные | Users, stores/accounts, access_level/effect, individual allow/deny, current grants, history. |
| Действия | Add/change/deactivate access, set direct deny, save, cancel. |
| Контролы | User selector, store selector, access matrix/table, effect controls. |
| Фильтры/поиск/сортировка/пагинация | Search users/stores; filter by marketplace/status/group; pagination for assignments. |
| Сообщения/статусы | Direct deny priority, no access means hidden store data, cannot limit owner. |
| Переходы | User card, store card, audit. |
| Сценарии | Object access administration. |
| Критерии готовности | Store access assignment write-flow реализован сейчас; object access is separate from roles/sections; changes historized and audited. |

## Аудит и журналы

### Аудит действий

| Поле | Спецификация |
| --- | --- |
| Назначение | Список immutable audit records of significant user/admin actions. |
| Раздел | Аудит и журналы. |
| Роли/права | `audit.list.view`, scope rights `logs.scope.limited`/`logs.scope.full`, object access. |
| Входные точки | Navigation, links from operations/settings/users/stores. |
| Данные | Occurred_at, user, action_code, entity_type/entity_id, store, operation, safe message/context. |
| Действия | Filter/search/sort, open audit card, open related entity. |
| Контролы | Table, filters, search, sort, pagination. |
| Фильтры/поиск/сортировка/пагинация | Period, user, action type, related store, related operation, severity if applicable; search by visible_id/entity. |
| Сообщения/статусы | No records, records hidden by scope/object access, immutable record, retention 90 days, cleanup only by regulated procedure outside ordinary UI. |
| Переходы | Audit card, related operation/store/user/role/parameter. |
| Сценарии | User/admin action traceability. |
| Критерии готовности | Action codes follow `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`; records cannot be edited/deleted through UI. |

### Карточка записи аудита

| Поле | Спецификация |
| --- | --- |
| Назначение | Просмотреть одну audit record и связанные сущности. |
| Раздел | Аудит и журналы. |
| Роли/права | `audit.card.view` plus scope/object access. |
| Входные точки | Audit list, related entity links. |
| Данные | Record id, occurred_at, user, action_code, entity, store, operation, safe before/after/context if stored, related links. |
| Действия | Open related entity, return to list. |
| Контролы | Read-only fields, related links. |
| Фильтры/поиск/сортировка/пагинация | Not applicable inside card. |
| Сообщения/статусы | Record immutable; details hidden by scope if applicable; ordinary UI deletion unavailable. |
| Переходы | Related operation/store/user/role/file. |
| Сценарии | Audit investigation. |
| Критерии готовности | Token, authorization header, API key, bearer value and secret-like values are not exposed; object access restrictions applied. |

### Технический журнал / системные ошибки

| Поле | Спецификация |
| --- | --- |
| Назначение | Список system events, errors and failures separate from operations and audit. |
| Раздел | Аудит и журналы. |
| Роли/права | `techlog.list.view`, scope rights, `techlog.sensitive.view` only for sensitive details. |
| Входные точки | Navigation, operation card, system notifications. |
| Данные | Occurred_at, severity, event_type, operation, store, safe_message, notification link if any. |
| Действия | Filter/search/sort, open techlog card, open related operation/store. |
| Контролы | Table, filters, search, sort, pagination. |
| Фильтры/поиск/сортировка/пагинация | Period, user if applicable, event type, related store, related operation, severity; pagination. |
| Сообщения/статусы | Sensitive details hidden, no records, records immutable, retention 90 days, cleanup only by regulated procedure outside ordinary UI. |
| Переходы | Techlog card, operation card, store card. |
| Сценарии | Support, failure investigation, system health. |
| Критерии готовности | Event types follow `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`; techlog does not replace business operations. |

### Карточка записи технического журнала

| Поле | Спецификация |
| --- | --- |
| Назначение | Просмотреть one technical log record with safe details and protected diagnostic link/details by right. |
| Раздел | Аудит и журналы. |
| Роли/права | `techlog.card.view`; `techlog.sensitive.view` for sensitive details. |
| Входные точки | Techlog list, operation card, notification. |
| Данные | Record id, occurred_at, severity, event_type, safe_message, operation/store links, sensitive_details_ref availability. |
| Действия | Open related operation/store, view sensitive details only with right, return to list. |
| Контролы | Read-only fields, related links, protected sensitive details area. |
| Фильтры/поиск/сортировка/пагинация | Not applicable inside card. |
| Сообщения/статусы | Sensitive details hidden, record immutable, no related operation. |
| Переходы | Operation card, store card, notification. |
| Сценарии | Technical diagnostics. |
| Критерии готовности | Safe message and sensitive area never expose token, authorization header, API key, bearer value or secret-like values; sensitive area respects rights. |

## Базовые экспорты

Обязательные экспорты этапа 1:

- список операций;
- список товаров;
- список магазинов/кабинетов;
- детализация ошибок и warnings по operation;
- детализация результата обработки по строкам.

Экспорты используют те же system codes, object access restrictions and visible identifiers, что UI/storage/tests.
