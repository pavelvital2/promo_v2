# WB_API_PRICE_EXPORT_SPEC.md

Трассировка: `tz_stage_2.1.txt` §6; ADR-0017, ADR-0020.

## Назначение

2.1.1 скачивает цены WB по API, формирует проверочный Excel цен и обновляет справочник товаров выбранного WB магазина. Подэтап не меняет данные в WB.

## Внешний источник

Официальный WB Prices and Discounts API:

- base URL: `https://discounts-prices-api.wildberries.ru`
- endpoint: `GET /api/v2/list/goods/filter`
- auth: `HeaderApiKey`
- pagination: `limit=1000`, `offset=0,1000,2000...`, stop when `listGoods` is empty
- rate limit: 10 requests / 6 seconds, interval 600 ms, burst 5

Документация WB указывает поля `nmID`, `vendorCode`, `sizes`, `currencyIsoCode4217`, `discount`, `clubDiscount`, `editableSizePrice`, `isBadTurnover`; в `sizes[]` есть `sizeID`, `price`, `discountedPrice`, `clubDiscountedPrice`, `techSizeName`.

## Preconditions

- WB store/account выбран.
- Пользователь имеет `wb.api.prices.download`.
- Пользователь имеет object access к store.
- У store есть active WB API connection по `docs/architecture/API_CONNECTIONS_SPEC.md`.
- Токен доступен только через `protected_secret_ref`.

## Flow

1. Создать `Run` и `Operation` с `mode=api`, `step_code=wb_api_prices_download`.
2. Выполнить read-only API calls с rate limiter и timeout policy.
3. Сохранить safe response snapshot без headers/token.
4. Нормализовать товары и sizes.
5. Сформировать price rows.
6. Обновить `MarketplaceProduct` и `MarketplaceProductHistory` для выбранного store.
7. Создать Excel price export.
8. Сохранить output `FileObject/FileVersion`.
9. Создать audit completed/failed action и techlog при ошибках.

## Excel price export

Основной лист должен быть совместим с Stage 1 WB price parser.

Обязательные колонки:

| Колонка | Источник | Правило |
| --- | --- | --- |
| `Артикул WB` | `nmID` | строковое представление nmID |
| `Текущая цена` | derived price | единая цена по sizes; см. size-based rules |
| `Новая скидка` | пусто | колонка для 2.1.3 |

Дополнительные диагностические поля запрещено добавлять в основной лист, если они могут сломать Stage 1 parser. Диагностика хранится в detail rows, safe snapshot или отдельном листе `_api_raw`, который не используется расчётным ядром.

## Size-based price rules

| Случай | Поведение |
| --- | --- |
| `sizes[]` пустой или price отсутствует | row status error, code `wb_api_price_row_invalid`; строка не upload-ready |
| Все `sizes[].price` одного `nmID` одинаковые | использовать эту price как `Текущая цена` |
| Есть разные `sizes[].price` по одному `nmID` | code `wb_api_price_row_size_conflict`; не выбирать размер молча; строка блокируется для API upload |

`editableSizePrice=true` сохраняется в `last_values` и detail rows, но Stage 2.1 не использует `/api/v2/upload/task/size`.

## Product directory mapping

Для каждого полученного `nmID` создать или обновить товар конкретного магазина:

| Поле | Значение |
| --- | --- |
| `MarketplaceProduct.marketplace` | `wb` |
| `store_id` | выбранный `StoreAccount` |
| `sku` | `str(nmID)` |
| `external_ids` | `nmID`, `vendorCode`, `sizeIDs`, `techSizeNames`, `source=wb_prices_api` |
| `last_values` | price, discount, discountedPrice, clubDiscount, clubDiscountedPrice, currencyIsoCode4217, editableSizePrice, isBadTurnover |
| `status` | `active` |
| `last_seen_at` | operation timestamp |

Если title не приходит из Prices API, название товара не выдумывается. `title` остаётся пустым или заполняется только из отдельного официально подключённого API-источника, которого нет в scope Stage 2.1.

## Operation details

Detail row минимум:

- nmID;
- vendorCode;
- sizes count;
- derived price;
- discount;
- currency;
- size conflict flag;
- row_status;
- reason/result code;
- safe message.

## Reason/result codes

| Code | Когда применяется |
| --- | --- |
| `wb_api_price_download_success` | operation скачивания цен завершена успешно |
| `wb_api_price_download_failed` | operation скачивания цен завершена ошибкой |
| `wb_api_price_row_valid` | строка цены валидна и пригодна для расчёта |
| `wb_api_price_row_size_conflict` | у nmID разные prices по sizes; upload по строке блокируется |
| `wb_api_price_row_invalid` | строка цены невалидна для расчёта |

## Outputs

- `Operation` summary.
- `WBPriceSnapshot` / safe snapshot metadata.
- `MarketplaceProduct` and history changes.
- `FileObject` scenario `wb_discounts_api_price_export`.
- Price Excel file.
- Detail report if requested by implementation task.

## Запреты

- Нельзя вызывать write endpoints WB.
- Нельзя сохранять API token/header в snapshot, metadata, audit, techlog или Excel.
- Нельзя выбирать первый size price при конфликте.
- Нельзя смешивать этот flow с Ozon API.
