# STAGE_2_SCOPE.md

Трассировка: `tz_stage_2.1.txt` §2, §16-§18; ADR-0016.

## Назначение

Stage 2 добавляет API-контуры маркетплейсов поверх платформы Stage 1. Stage 2 не заменяет Excel-режимы Stage 1 и не меняет принятую WB/Ozon Excel бизнес-логику.

## Split Stage 2

| Этап | Контур | Статус проектирования | Граница |
| --- | --- | --- | --- |
| 2.1 | WB API | этот комплект документации | API-скачивание цен, текущих акций, расчёт по WB-логике, опциональная API-загрузка скидок |
| 2.2 | Ozon API | будущий этап | не проектируется и не реализуется в задачах Stage 2.1 |

WB 2.1 и Ozon 2.2 запрещено смешивать в одной implementation task, миграции, UI-flow или acceptance checklist без отдельного orchestration decision.

## Инварианты Stage 1

- WB Excel Stage 1 остаётся штатным и резервным режимом.
- Ozon Excel Stage 1 остаётся штатным режимом своего контура.
- Stage 2.1 не меняет формулу, порядок правил, reason/result codes Stage 1 Excel без отдельного ADR.
- Реальные Stage 1 acceptance artifacts и контрольные сравнения не удаляются и не заменяются.
- API-режим добавляется как новый `mode=api`, а не как переименование или скрытая замена `mode=excel`.

## Stage 2.1 WB API

Stage 2.1 состоит из четырёх подэтапов:

| Подэтап | Назначение | Меняет данные в WB |
| --- | --- | --- |
| 2.1.1 | Скачать цены WB по API, сформировать Excel цен, обновить справочник товаров магазина | нет |
| 2.1.2 | Скачать текущие WB акции, сохранить акции/товары, сформировать Excel акций | нет |
| 2.1.3 | Рассчитать скидки по API-источникам через WB-логику Stage 1 и сформировать итоговый Excel | нет |
| 2.1.4 | Загрузить рассчитанные скидки в WB по API | да |

2.1.4 является единственным подэтапом Stage 2.1, который отправляет изменения в WB.

## Внешние источники

- WB Prices and Discounts API: `https://dev.wildberries.ru/docs/openapi/work-with-products#tag/Ceny-i-skidki/paths/~1api~1v2~1list~1goods~1filter/get`
- WB Promotions Calendar API: `https://dev.wildberries.ru/docs/openapi/promotion`

## Документы Stage 2.1

- `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`
- `docs/product/WB_DISCOUNTS_API_SPEC.md`
- `docs/product/WB_API_PRICE_EXPORT_SPEC.md`
- `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md`
- `docs/tasks/implementation/stage-2/IMPLEMENTATION_TASKS.md`
- `docs/traceability/STAGE_2_1_WB_TRACEABILITY_MATRIX.md`

## Запреты для реализации

- Нельзя писать код Stage 2.1 до аудита этого комплекта документации.
- Нельзя менять итоговое ТЗ и Stage 1 Excel бизнес-логику.
- Нельзя удалять или заменять Excel-режимы.
- Нельзя использовать API upload в 2.1.1, 2.1.2 или 2.1.3.
- Нельзя хранить API tokens в metadata, audit, techlog, snapshots или UI.
- Нельзя оставлять UX/functionality gaps на разработчика.
