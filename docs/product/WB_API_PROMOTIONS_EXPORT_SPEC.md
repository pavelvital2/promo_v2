# WB_API_PROMOTIONS_EXPORT_SPEC.md

Трассировка: `docs/source/stage-inputs/tz_stage_2.1.txt` §7; ADR-0018, ADR-0020, ADR-0021.

## Назначение

2.1.2 скачивает именно текущие WB акции из Promotions Calendar API, сохраняет акции и товарные строки, формирует Excel promo files. Подэтап не меняет данные в WB и не добавляет товары в акции.

## Определение текущей акции

```text
current promotion = startDateTime <= now_utc < endDateTime
```

`now_utc` фиксируется на момент запуска operation и сохраняется в `WBPromotionSnapshot.current_filter_timestamp`.

## Внешние API

Base URL Promotions Calendar: `https://dp-calendar-api.wildberries.ru`.

| Назначение | Endpoint | Правила |
| --- | --- | --- |
| Список акций | `GET /api/v1/calendar/promotions` | `allPromo=true`, window покрывает `now_utc`, пагинация |
| Детали акций | `GET /api/v1/calendar/promotions/details` | до 100 unique promotion IDs за запрос |
| Товары акции | `GET /api/v1/calendar/promotions/nomenclatures` | `promotionID`, `inAction`, `limit<=1000`, `offset`; не применимо к auto promotions |

Rate limit Promotions Calendar: 10 requests / 6 seconds, interval 600 ms, burst 5.

## Flow

1. Проверить право `wb.api.promotions.download`.
2. Проверить object access и active WB API connection.
3. Создать `Operation` с `mode=api`, `step_code=wb_api_promotions_download`.
4. Сформировать API window:
   - `startDateTime = now_utc - 24h`;
   - `endDateTime = now_utc + 24h`;
   - `allPromo=true`.
5. Получить promotions list с пагинацией.
6. Применить локальный current filter.
7. Получить details для current promotion IDs батчами до 100.
8. Для regular promotions получить nomenclatures:
   - `inAction=true`;
   - `inAction=false`;
   - `limit=1000`, `offset` до пустого массива.
9. Для auto promotions сохранить акцию и reason `wb_api_promotion_auto_no_nomenclatures`.
10. Сформировать отдельный Excel promo file по каждой regular current promotion.

Если API window по факту не покрывает `now_utc` из-за clock/timezone error, operation завершается `completed_with_error`.

## Data mapping

### WBPromotion

| Поле | Значение |
| --- | --- |
| `store_id` | выбранный WB store |
| `wb_promotion_id` | `id` из API |
| `name` | API name |
| `type` | API type |
| `start_datetime` | `startDateTime` |
| `end_datetime` | `endDateTime` |
| `is_current_at_fetch` | результат current filter |
| `last_seen_at` | operation timestamp |
| `snapshot_ref` | safe snapshot |

### WBPromotionSnapshot

Хранит `operation_id`, `store_id`, `fetched_at`, `api_window_start`, `api_window_end`, `current_filter_timestamp`, counts и safe raw response references без secrets.

### WBPromotionProduct

| Поле | Источник |
| --- | --- |
| `promotion_id` | current regular promotion |
| `nmID` | `nomenclatures[].id` |
| `inAction` | API field |
| `price` | API field |
| `currencyCode` | API field |
| `planPrice` | API field |
| `discount` | API field |
| `planDiscount` | API field |
| `row_status` | valid/invalid/blocked |

Если `planPrice` или `planDiscount` отсутствует, строка невалидна для расчёта и получает `wb_api_promotion_product_invalid`.

## Excel promo files

По каждой current regular promotion формируется отдельный `.xlsx`.

Filename pattern:

```text
wb_promo_<promotionID>_<YYYYMMDD_HHMMSS_UTC>.xlsx
```

Обязательные колонки:

| Колонка | Источник |
| --- | --- |
| `Артикул WB` | `nomenclatures[].id` |
| `Плановая цена для акции` | `nomenclatures[].planPrice` |
| `Загружаемая скидка для участия в акции` | `nomenclatures[].planDiscount` |

Zip/package всех promo files не является обязательным scope Stage 2.1. Если будет добавлен позднее, он должен получить отдельный file scenario и UI/download правила.

## Auto promotions

Для auto promotions:

- сохранять `WBPromotion` и details;
- фиксировать, что nomenclatures не применимы по WB API;
- не создавать `WBPromotionProduct` с выдуманными nmID;
- не создавать promo Excel с пустыми фиктивными строками;
- показывать ограничение в UI и detail report.

WB API не является источником состава товаров auto promotions. Если будущая задача требует расчёт именно по WB auto promotion, входным prerequisite является внешний product-source artifact со списком товаров auto-акции: Excel/export из личного кабинета WB или другой утверждённый источник. Такой artifact должен пройти отдельные правила загрузки, проверки, traceability и acceptance до использования в расчёте.

После получения внешнего списка товаров WB API может использоваться для обогащения и проверки строк:

- карточки и идентификаторы товара;
- текущие цены/скидки;
- остатки;
- заказы/продажи за период, если это требуется для отдельного supply-planning или аналитического сценария.

Нельзя подменять внешний список товаров auto promotion всеми карточками магазина, товарами regular promotions или summary/count fields из details.

## Reason/result codes

| Code | Когда применяется |
| --- | --- |
| `wb_api_promotion_current` | акция прошла current filter |
| `wb_api_promotion_not_current_filtered` | акция получена API, но отфильтрована локальным current filter |
| `wb_api_promotion_regular` | regular promotion обработана с nomenclatures |
| `wb_api_promotion_auto_no_nomenclatures` | auto promotion сохранена без товарных строк |
| `wb_api_promotion_product_valid` | товарная строка акции валидна для расчёта |
| `wb_api_promotion_product_invalid` | товарная строка акции невалидна для расчёта |

## Запреты

- Нельзя использовать будущие, ближайшие, все или последние акции вместо current filter.
- Нельзя вызывать `POST /api/v1/calendar/promotions/upload` в Stage 2.1.
- Нельзя выдумывать товарные строки для auto promotions.
- Нельзя считать все карточки магазина составом auto promotion без внешнего product-source artifact.
- Нельзя сохранять authorization headers или tokens в snapshots.
