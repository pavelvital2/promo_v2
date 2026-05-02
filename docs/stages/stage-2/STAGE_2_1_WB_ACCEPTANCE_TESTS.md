# STAGE_2_1_WB_ACCEPTANCE_TESTS.md

Трассировка: `docs/source/stage-inputs/tz_stage_2.1.txt` §15; `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`.

## Назначение

Документ задаёт приёмочные сценарии Stage 2.1 WB API до начала разработки. Детальные test classes и mocks описаны в `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`, чек-листы - в `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`.

## Общие acceptance gates

- Реализация стартовала только после audit pass исполнительной документации.
- Stage 1 WB Excel сценарий продолжает проходить существующие тесты без изменения бизнес-логики.
- API tokens не попадают в UI, metadata, audit, techlog, snapshots, файлы и test reports.
- Пользователь без object access к WB store не видит операции, файлы, товары, акции и подключение этого store.
- 2.1.1/2.1.2/2.1.3 не вызывают write endpoints WB.

## 2.1.1 accepted

- Пользователь с правами скачивает цены через `GET /api/v2/list/goods/filter`.
- Пагинация идёт `limit=1000`, `offset` до пустого `listGoods`.
- Rate limit policy соблюдает 10 requests / 6 seconds, interval 600 ms, burst 5.
- Excel цен содержит `Артикул WB`, `Текущая цена`, `Новая скидка`.
- Справочник товаров выбранного магазина создан/обновлён, history создана.
- Size conflict case не обрабатывается молча и получает `wb_api_price_row_size_conflict`.
- Operation, file version, audit и techlog при ошибках созданы.

## 2.1.2 accepted

- Система выбирает именно текущие акции по `startDateTime <= now_utc < endDateTime`.
- `now_utc`, API window и `allPromo=true` сохранены в snapshot.
- Details запрошены батчами до 100 IDs.
- Regular promotions получают nomenclatures с `inAction=true` и `inAction=false`.
- Auto promotions сохранены без выдуманных товарных строк.
- По каждой regular current promotion создан Excel с обязательными promo columns.
- Ошибки API не раскрывают секреты.

## 2.1.3 accepted

- Расчёт использует общее WB calculation core и Stage 1 правила.
- Decimal + ceil подтверждены тестом; float запрещён.
- Итоговый Excel основан на price export 2.1.1 и меняет только `Новая скидка`.
- Ошибки расчёта блокируют upload.
- Snapshot параметров, selected price export, selected promotion exports и logic version сохранены.
- Повторный расчёт создаёт новую operation и новую file version.

## 2.1.4 accepted

- Upload невозможен без successful 2.1.3, explicit confirmation и прав upload/confirm.
- Pre-upload drift check выполняет read перед upload.
- Price drift блокирует upload и требует повторить 2.1.1-2.1.3.
- Payload разбит на batches <= 1000 товаров.
- `uploadID` сохранён по каждому batch.
- Итог определяется status polling, не первым HTTP 200.
- WB statuses 3/4/5/6 корректно маппятся в operation statuses.
- Partial errors видны как `completed_with_warnings`.
- Quarantine errors видны отдельно.
- 208 already exists, 429, auth failure, timeout и invalid response имеют безопасное поведение.

## Acceptance artifacts

Минимальный набор:

- API mock сценарий цен: несколько страниц, пустая последняя страница, один size conflict.
- API mock сценарий акций: current/future/past, regular/auto, missing plan fields.
- Golden comparison: API-generated Excel inputs дают тот же результат WB calculation core, что Stage 1 Excel на эквивалентных данных.
- Upload mock: statuses 3, 4, 5, 6, quarantine, 208, 429.
- Secret redaction check: отсутствуют tokens/authorization headers во всех safe snapshots и UI outputs.

Реальные WB API acceptance checks допускаются только с test/sandbox или явно разрешённым заказчиком store/account. Реальные `test_files/secrets` не трогать.
