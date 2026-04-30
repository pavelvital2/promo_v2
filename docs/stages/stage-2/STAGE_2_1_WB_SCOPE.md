# STAGE_2_1_WB_SCOPE.md

Трассировка: `tz_stage_2.1.txt` §2-§17; ADR-0016, ADR-0017, ADR-0018, ADR-0019, ADR-0020, ADR-0021.

## Назначение

Документ задаёт исполнимую границу Stage 2.1 WB API для проектирования, реализации, тестирования и аудита. Подробные правила вынесены в профильные спецификации:

- 2.1.1: `docs/product/WB_API_PRICE_EXPORT_SPEC.md`
- 2.1.2: `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`
- 2.1.3-2.1.4: `docs/product/WB_DISCOUNTS_API_SPEC.md`
- подключения: `docs/architecture/API_CONNECTIONS_SPEC.md`

## Пользовательская модель

Stage 2.1 сохраняет понятную ручную модель WB:

```text
2.1.1 API скачал цены -> Excel цен
2.1.2 API скачал текущие акции -> Excel акций
2.1.3 расчёт скидок -> итоговый Excel для ручной загрузки в ЛК WB
2.1.4 явная API-загрузка рассчитанных скидок
```

2.1.1, 2.1.2 и 2.1.3 являются read-only относительно WB. Они создают операции, snapshots, файлы и внутренние справочники, но не отправляют изменения в WB.

## 2.1.1 Цены WB

Обязательный flow:

1. Проверить право `wb.api.prices.download`.
2. Проверить object access к WB store/account.
3. Проверить активное WB API-подключение.
4. Получить товары с ценами через WB Prices and Discounts API.
5. Сохранить safe snapshot ответа без секретов.
6. Сформировать Excel цен с обязательными колонками `Артикул WB`, `Текущая цена`, `Новая скидка`.
7. Обновить `MarketplaceProduct` конкретного магазина.
8. Создать operation/run/file/audit/techlog records.

Size-based price conflict не решается молча. Если у одного `nmID` разные `price` по `sizes[]`, строка получает `wb_api_price_row_size_conflict`, исключается из upload-ready набора и блокирует API upload по этому товару до утверждённого правила.

## 2.1.2 Текущие акции WB

Текущая акция WB:

```text
startDateTime <= now_utc < endDateTime
```

`now_utc` фиксируется на момент запуска operation и сохраняется в snapshot.

Обязательный flow:

1. Проверить право `wb.api.promotions.download`.
2. Проверить object access и активное WB API-подключение.
3. Запросить promotions list с окном, покрывающим `now_utc`, и `allPromo=true`.
4. Применить локальный строгий фильтр current promotions.
5. Запросить details батчами до 100 promotion IDs.
6. Для regular promotions запросить nomenclatures с `inAction=true` и `inAction=false`, пагинация до пустого массива.
7. Для auto promotions сохранить акцию и ограничение WB API, не выдумывать строки товаров.
8. Сформировать отдельный Excel promo file на каждую regular current promotion.

Zip/package всех promo файлов не входит в обязательный Stage 2.1 scope и может быть добавлен отдельным enhancement после acceptance базового flow.

### WB auto promotions product-source decision

По ADR-0021 WB API не является источником состава товаров auto promotions. `calendar/promotions` и `calendar/promotions/details` могут подтвердить саму auto promotion, её dates/counts/details, но не дают расчётный список `nmID`.

Для будущего расчёта WB auto promotions требуется отдельный внешний product-source artifact: Excel/export из личного кабинета WB или другой утверждённый заказчиком источник. После загрузки такого artifact WB API можно использовать для обогащения строк карточками, ценами, остатками, заказами/продажами и проверками актуальности, но не для восстановления отсутствующего состава auto-акции.

Запрещено использовать как замену состава auto promotion:

- все карточки магазина;
- товары regular promotions;
- пустые promo files;
- синтетические строки, собранные из summary/count fields.

## 2.1.3 Расчёт скидок

Расчёт использует ту же WB-логику, что Stage 1:

- decimal arithmetic, без float;
- `ceil` для `calculated_discount`;
- тот же порядок fallback/threshold правил;
- тот же запрет частичной обработки при `wb_discount_out_of_range`.

Реализация должна использовать общее расчётное ядро WB. Дублировать формулу отдельно для Excel и API modes запрещено.

Итоговый Excel формируется на основе price Excel из 2.1.1, записывает только колонку `Новая скидка`, хранится как output file version и пригоден для ручной загрузки в личном кабинете WB в рамках формальной схемы Stage 2.1: основной лист с обязательными колонками Stage 1 price workbook.

## 2.1.4 API upload

API upload разрешён только после успешного 2.1.3 и требует:

- право `wb.api.discounts.upload`;
- право `wb.api.discounts.upload.confirm`;
- object access к store;
- активное WB API-подключение;
- explicit confirmation screen;
- pre-upload drift check;
- batch size <= 1000 товаров;
- сохранение uploadID по каждому batch;
- status polling до итогового WB статуса.

Price drift является блокером upload. Пользователь должен повторить скачивание цен/акций и расчёт.

Успех upload не определяется первым HTTP 200. Итог определяется только через WB status polling:

| WB status | Operation.status | Правило |
| --- | --- | --- |
| 3 | `completed_success` | все товары применены без ошибок |
| 5 | `completed_with_warnings` | часть товаров применена, часть с ошибками |
| 6 | `completed_with_error` | все товары с ошибками |
| 4 | `completed_with_error` | upload отменён WB |

Quarantine errors отображаются отдельно и не скрываются внутри partial errors.

## Обязательные внешние API

| Назначение | Endpoint |
| --- | --- |
| Получить товары с ценами | `GET /api/v2/list/goods/filter` |
| Drift check по `nmList` | `POST /api/v2/list/goods/filter` |
| API upload скидок | `POST /api/v2/upload/task` |
| Processed upload state | `GET /api/v2/history/tasks` |
| Processed upload details | `GET /api/v2/history/goods/task` |
| Unprocessed upload state | `GET /api/v2/buffer/tasks` |
| Unprocessed upload details | `GET /api/v2/buffer/goods/task` |
| Quarantine goods | `GET /api/v2/quarantine/goods` |
| Promotions list | `GET /api/v1/calendar/promotions` |
| Promotions details | `GET /api/v1/calendar/promotions/details` |
| Promotion nomenclatures | `GET /api/v1/calendar/promotions/nomenclatures` |

## Границы не входит

- Ozon API Stage 2.2.
- Добавление товаров в WB акции через Promotions Calendar upload.
- Size price upload через `/api/v2/upload/task/size`.
- WB Club discounts.
- Остатки, заказы, поставки, производство, закупки.
- Изменение Stage 1 WB Excel parser/формулы/accepted artifacts.

## GAP evaluation

Потенциальные вопросы из ТЗ закрыты как проектные решения:

- size price conflict: строка блокируется для upload до отдельного правила;
- auto promotions without nomenclatures: акция сохраняется без выдуманных строк товаров;
- WB auto promotions calculation source: требуется внешний product-source artifact, WB API не восстанавливает состав auto-акции;
- promo files: отдельный Excel по акции, zip optional enhancement;
- partial errors: `completed_with_warnings`;
- price drift: блокер upload.

Новых открытых GAP для Stage 2.1 этим документом не создаётся.
