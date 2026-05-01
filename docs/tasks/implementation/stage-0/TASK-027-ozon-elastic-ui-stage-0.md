# TASK-027: Ozon Elastic UI Stage 0 implementation

Статус: ready for implementation  
Этап: Stage 0 UI  
Область: `Маркетплейсы / Ozon / Акции / API / Эластичный бустинг`

## Назначение

Реализовать утверждённую Stage 0 UI-модель для Ozon Elastic: вкладки, 7 операторских шагов, человеко-читаемый результат, диагностику, упорядоченную карточку операции и иерархию `Маркетплейсы`.

Проектная документация Stage 0 прошла аудит с `pass`. Кодирование разрешено только в рамках этой задачи.

## Обязательный пакет чтения

Исполнитель читает:

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/tasks/implementation/stage-0/OZON_ELASTIC_UI_READING_PACKAGE.md`
- `docs/tasks/implementation/stage-0/TASK-027-ozon-elastic-ui-stage-0.md`
- `docs/product/OZON_API_ELASTIC_UI_SPEC.md`
- `docs/testing/STAGE_0_OZON_ELASTIC_UI_ACCEPTANCE_CHECKLIST.md`
- связанные ADR/GAP из reading package.

Итоговое ТЗ целиком не читать. Если в документах нет ответа по функциональности или удобству веб-панели, исполнитель не домысливает поведение и возвращает вопрос оркестратору для заказчика.

## Разрешённые изменения

Разрешено менять только файлы, необходимые для UI-реализации:

- Django templates for web panel;
- `apps/web/views.py` только для подготовки контекста отображения, человеко-читаемых labels, групп результата и безопасной диагностики;
- `apps/web/tests.py` или новые focused UI/view tests;
- docs/test report по результату реализации.

Запрещено без отдельной задачи:

- менять бизнес-логику расчёта Ozon Elastic;
- менять Ozon API client/write behavior;
- менять `Operation.step_code`;
- добавлять/переименовывать reason/result codes;
- менять permission codes, роли и seed permissions;
- менять file scenarios, retention или version links;
- менять audit action codes или techlog event types;
- менять Stage 1 Ozon Excel logic.

## Требования к реализации

### 1. Ozon Elastic page

На странице `marketplaces/ozon/actions/api/elastic-boosting/` реализовать вкладки:

- `Рабочий процесс` по умолчанию;
- `Результат`;
- `Диагностика`.

Пользователь остаётся на странице сценария после действий.

### 2. Рабочий процесс

Показать 7 операторских шагов:

1. `Скачать доступные акции`
2. `Выбрать акцию`
3. `Скачать товары и данные по ним`
4. `Обработать`
5. `Принять / не принять результат`
6. `Скачать Excel для ручной загрузки`
7. `Загрузить в Ozon`

Старые шаги скачивания active/candidate/product-data объединить только в UI. Underlying operations, `step_code`, snapshots, source operation links, audit/techlog, files/checksums must remain unchanged.

В workflow показывать только компактные статусы, время и основные числа. Не показывать raw `basis`, `checksum`, `source_operations`, large JSON-like summaries.

После расчёта в workflow показывать только:

- `Будет обновлено в акции`
- `Будет добавлено в акцию`
- `Будет снято с акции`

### 3. Результат

Показать группы результата:

- `Будет обновлено в акции`
- `Будет добавлено в акцию`
- `Не проходит расчёт сейчас`
- `Будет снято с акции`
- `Ошибки`
- `Отклонено Ozon`, если есть upload rejections.

Пустые группы компактные со счётчиком `0`. Таблицы/списки по 10 строк. Фильтры и обозначения человеко-читаемые. Короткая причина видна в строке, полная причина раскрывается по строке.

Кандидаты, прошедшие расчёт, отображаются как `Будет добавлено в акцию`. Кандидаты без действия не показываются в workflow.

### 4. Файлы

`Excel для ручной загрузки` показать:

- в workflow step 6;
- в `Результат` files block.

`Excel результата` не показывать как основной workflow step, но оставить доступным в `Результат`, `Диагностика` и карточке операции.

Manual upload Excel label must state `Stage 1-compatible template`.

### 5. Диагностика

В `Диагностика` перенести технические данные:

- operation evidence;
- calculation basis;
- snapshots/checksums/source operations;
- API metadata;
- audit/techlog links;
- technical codes.

Большие значения свернуты по умолчанию, в scrollable/preformatted blocks.

Не показывать secrets, Client-Id, Api-Key, authorization headers, bearer/API key values, raw sensitive API responses.

Доступ к диагностике только по существующим permissions, без добавления новых permission codes.

### 6. Review/upload safety

`Принять результат` и `Не принять результат` остаются state actions, not separate operations.

Upload requires accepted non-stale result.

If deactivate rows exist, upload requires one group-level deactivate confirmation. Without it:

- upload blocked;
- no `ozon_api_elastic_upload` operation created;
- add/update does not silently proceed as final upload scenario.

### 7. Operation card

Упорядочить отображение operation card:

- краткий человеко-читаемый блок сверху;
- raw summary/basis/source/API details in collapsed technical blocks;
- long JSON-like values do not stretch page;
- audit/debug visually separate.

Не менять operation data model and step codes.

### 8. Marketplace navigation

Страница `Маркетплейсы` должна использовать иерархию:

`marketplace -> section -> mode -> scenario`.

Текущий активный путь:

`Ozon -> Акции -> API -> Эластичный бустинг`.

Будущие разделы показывать как inactive `Планируется`, без рабочих форм/кнопок/маршрутов.

Глобальную верхнюю навигацию не менять.

## Проверки

Обязательно выполнить:

- focused Django tests for changed views/templates;
- acceptance checklist manual/automated smoke по `docs/testing/STAGE_0_OZON_ELASTIC_UI_ACCEPTANCE_CHECKLIST.md`;
- Playwright screenshots desktop and mobile for Ozon Elastic;
- mobile check: no page-level horizontal overflow around `390x844`;
- regression smoke for Ozon Elastic page and operation card.

Если часть проверок невозможно выполнить, зафиксировать причину в отчёте.

## Выходные артефакты

Исполнитель должен подготовить:

- изменения кода/templates/tests;
- test/implementation report в `docs/testing/` или `docs/reports/`;
- список изменённых файлов;
- выполненные проверки;
- найденные gaps или вопросы оркестратору.

## Acceptance

Задача считается готовой к тестировщику и аудитору, если:

- UI соответствует `docs/product/OZON_API_ELASTIC_UI_SPEC.md`;
- checklist Stage 0 пройден или зафиксированы blockers;
- бизнес-логика, operation contour, rights, file contour, audit/techlog не изменены;
- все UX/functionality gaps либо отсутствуют, либо переданы оркестратору для заказчика.
