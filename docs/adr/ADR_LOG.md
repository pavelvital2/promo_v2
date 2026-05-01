# ADR_LOG.md

Трассировка: ТЗ §25-§26.

## Правила ADR

ADR фиксирует архитектурное или проектное решение, принятое на основании ТЗ или утверждённого GAP. ADR не может изменять бизнес-логику WB/Ozon, модель прав, операции или файловый контур без явного утверждения заказчика.

## ADR-0001: Итоговое ТЗ является источником истины

- Статус: accepted
- Дата: 2026-04-25
- Контекст: в репозитории есть итоговое ТЗ и стартовый оркестраторский документ
- Решение: все документы и будущая реализация обязаны опираться на `itogovoe_tz_platforma_marketplace_codex.txt`; прежние материалы, старая программа и скрытый контекст не являются источником правил
- Последствия: пробелы фиксируются в `docs/gaps/GAP_REGISTER.md`; старая программа используется только как источник контрольных результатов
- Трассировка: ТЗ §1, §24

## ADR-0002: Этап 1 проектируется как модульный монолит

- Статус: accepted
- Дата: 2026-04-25
- Контекст: ТЗ требует единое приложение, единую БД, единый UI/API и жёсткие границы модулей
- Решение: исполнительная документация фиксирует модульный монолит с отдельными доменными модулями identity, stores, operations, files, discounts, settings, audit, tech log
- Последствия: будущие сервисы возможны без переписывания доменного ядра; на этапе 1 не вводятся отдельные базы или инсталляции

- Трассировка: ТЗ §4

## ADR-0003: Excel является штатным режимом этапа 1 и не удаляется будущим API

- Статус: accepted
- Дата: 2026-04-25
- Контекст: ТЗ запрещает подменять Excel API-режимом и требует сохранить Excel как штатный/резервный режим
- Решение: WB/Ozon Excel спецификации являются обязательными для этапа 1; API-блоки в магазинах помечаются как подготовка этапа 2 и не используются для расчёта скидок этапа 1
- Последствия: API-задачи будущих этапов не должны ломать Excel-сценарии
- Трассировка: ТЗ §2.4-§2.5, §3.1-§3.3, §8.5

## ADR-0004: Check и process являются разными operations

- Статус: accepted
- Дата: 2026-04-25
- Контекст: ТЗ требует разделить проверку и обработку, но допускает кнопку "Обработать" с автоматической проверкой при отсутствии актуальной
- Решение: check и process всегда создают отдельные operation records; process хранит ссылку на check basis
- Последствия: UI может вести пользователя как единый сценарий, но данные и аудит должны сохранять раздельность
- Трассировка: ТЗ §12

## ADR-0005: Открытые проектные параметры не заполняются предположениями

- Статус: accepted
- Дата: 2026-04-25
- Контекст: ТЗ не задаёт часть проектных и эксплуатационных параметров, включая default values WB, полный перечень некоторых codes, backup schedule и retention cleanup audit/techlog
- Решение: такие вопросы вносятся в `docs/gaps/GAP_REGISTER.md`; реализация соответствующих участков блокируется до решения; после решения заказчика gap закрывается отдельной записью/ADR и профильные документы синхронизируются
- Последствия: документация остаётся самодостаточной по утверждённым правилам и явно показывает незакрытые решения или remaining artifact gates
- Трассировка: ТЗ §1.4, §26.8

## ADR-0006: Технологический стек этапа 1

- Статус: accepted
- Дата: 2026-04-25
- Контекст: `GAP-0001` блокировал старт реализации, потому что ТЗ не задавало backend/frontend stack и способ server-side UI.
- Решение: этап 1 реализуется на Django + PostgreSQL + server-rendered UI / Django templates. Django ORM используется как штатный слой доступа к PostgreSQL. UI этапа 1 строится как серверно-рендеримые страницы и формы Django templates; отдельный SPA-фреймворк не вводится как baseline этапа 1.
- Последствия: будущие задачи реализации могут создавать Django-проект, Django apps по модульным границам, миграции Django и deployment через nginx/systemd. Решение не меняет бизнес-логику WB/Ozon и не отменяет Excel как штатный режим этапа 1.
- Закрывает: `GAP-0001`
- Трассировка: ТЗ §4, §22, §27

## ADR-0007: Консервативный seed-набор прав типовых ролей

- Статус: accepted
- Дата: 2026-04-25
- Контекст: `GAP-0005` блокировал seed ролей, потому что ТЗ задавало модель ролей и прав, но не утверждало начальный набор прав для типовых ролей.
- Решение: seed-набор этапа 1:
  - Владелец: полный доступ ко всему, без ограничений.
  - Глобальный администратор: всё администрирование, кроме ограничения/блокировки/удаления владельца.
  - Локальный администратор: управление пользователями, магазинами, параметрами и доступами только в назначенных магазинах/кабинетах.
  - Менеджер маркетплейсов: работа с WB/Ozon Excel-сценариями, операциями, файлами, товарами и параметрами доступных магазинов, без управления ролями и системными правами.
  - Наблюдатель: только просмотр доступных магазинов, операций, результатов, товаров и ограниченных журналов, без изменений и скачивания итоговых файлов, если отдельно не разрешено.
- Последствия: `docs/product/PERMISSIONS_MATRIX.md` является источником детализации seed для миграций/seed-команд. Индивидуальные разрешения и запреты продолжают действовать поверх роли; прямой запрет приоритетнее разрешения. Владелец не может быть ограничен администратором.
- Закрывает: `GAP-0005`
- Трассировка: ТЗ §8, §11, §20, §27

## ADR-0008: Формат видимых идентификаторов

- Статус: accepted
- Дата: 2026-04-25
- Контекст: `GAP-0006` блокировал реализацию ключевых сущностей, потому что ТЗ требовало единые visible identifiers, но не задавало маски.
- Решение: утвердить формат:
  - operation: `OP-YYYY-NNNNNN`
  - run: `RUN-YYYY-NNNNNN`
  - file: `FILE-YYYY-NNNNNN`
  - store/cabinet: `STORE-NNNNNN`
  - user: `USR-NNNNNN`
- Последствия: идентификаторы стабильны после создания, уникальны в рамках типа сущности, пригодны для поиска и не раскрывают чувствительные данные. Для operation/run/file номер сквозной внутри года и типа сущности; для store/cabinet и user номер сквозной внутри типа сущности.
- Закрывает: `GAP-0006`
- Трассировка: ТЗ §23.2

## ADR-0009: Системные WB defaults этапа 1

- Статус: accepted
- Дата: 2026-04-25
- Контекст: `GAP-0002` блокировал seed/system defaults для WB-параметров, потому что ТЗ задавало перечень и каскад параметров, но не числовые значения по умолчанию.
- Решение: системные значения по умолчанию:
  - `wb_threshold_percent = 70`
  - `wb_fallback_over_threshold_percent = 55`
  - `wb_fallback_no_promo_percent = 55`
- Последствия: WB settings/default seed и WB calculation snapshots могут быть реализованы по утверждённому каскаду store value -> system default. Изменение store-level параметров продолжает влиять только на новые операции.
- Закрывает: `GAP-0002`
- Трассировка: ТЗ §14, §15.9-§15.10

## ADR-0010: Минимальный закрытый каталог WB reason/result codes

- Статус: accepted
- Дата: 2026-04-25
- Контекст: `GAP-0003` блокировал WB detail audit, exports и tests, потому что ТЗ требовало fixed codes, но не содержало закрытого row-level перечня.
- Решение: для WB Discounts Excel этапа 1 утверждён минимальный закрытый перечень codes:
  - `wb_valid_calculated`
  - `wb_no_promo_item`
  - `wb_over_threshold`
  - `wb_missing_article`
  - `wb_invalid_current_price`
  - `wb_duplicate_price_article`
  - `wb_missing_required_column`
  - `wb_invalid_promo_row`
  - `wb_invalid_workbook`
  - `wb_output_write_error`
  - `wb_discount_out_of_range`
- Последствия: WB implementation, detail rows, exports, UI filters and tests use only this catalog unless a future approved documentation change extends it.
- Закрывает: `GAP-0003`
- Трассировка: ТЗ §12.12, §17.5, §23.1

## ADR-0011: WB out-of-range скидка является row error

- Статус: accepted
- Дата: 2026-04-25
- Контекст: `GAP-0004` блокировал WB check/process для случая итоговой скидки вне диапазона 0..100, потому что ТЗ требовало warning/error semantics, но не задавало уровень блокировки.
- Решение: WB итоговая скидка вне диапазона 0..100 является ошибкой строки с code `wb_discount_out_of_range`; check завершается с ошибками; process запрещён; обрезка значения и частичная обработка запрещены.
- Последствия: WB check обязан показать row-level error и summary errors; WB process недоступен до исправления входных данных/параметров и успешной проверки.
- Закрывает: `GAP-0004`
- Трассировка: ТЗ §15.8

## ADR-0012: Backup policy этапа 1

- Статус: accepted
- Дата: 2026-04-25
- Контекст: `GAP-0007` блокировал production readiness, потому что ТЗ требовало backup/restore, но не задавало расписание и срок хранения backup.
- Решение: выполнять daily PostgreSQL backup и daily server file storage backup; хранить backup 14 дней; перед production update backup обязателен; restore check выполняется по документированной manual procedure после setup и перед важными релизами.
- Последствия: release/update runbook и production readiness checks получают утверждённую backup policy. Конкретные команды зависят от Django deployment task, но не могут ослаблять частоту, retention или обязательный pre-update backup.
- Закрывает: `GAP-0007`
- Трассировка: ТЗ §22.5, §27

## ADR-0013: Контрольные файлы как acceptance artifact gate

- Статус: accepted
- Дата: 2026-04-25
- Контекст: `GAP-0008` блокировал формальную приёмку из-за отсутствия реальных WB/Ozon файлов, checksums, результатов старой программы и expected results.
- Решение: заказчик передаёт реальные контрольные WB/Ozon файлы и результаты старой программы; дополнительно могут готовиться edge-case наборы. Проектное решение закрыто; фактические файлы, checksums и expected results являются обязательными для formal comparison соответствующего набора.
- Последствия: агенты не создают фиктивные customer files/checksums/expected results. До получения артефактов можно выполнять разработческие и synthetic edge-case tests, но formal comparison соответствующего customer artifact set не завершается.
- Обновление 2026-04-26: real WB/Ozon output comparison artifact gate закрыт для `WB-REAL-001` и `OZ-REAL-001`; checksums, результаты старой программы и expected results зафиксированы в `docs/testing/CONTROL_FILE_REGISTRY.md`, сравнение принято в `docs/testing/TEST_REPORT_STAGE_1_FORMAL_ACCEPTANCE.md`.
- Закрывает: `GAP-0008`
- Трассировка: ТЗ §24

## ADR-0014: Retention audit/techlog records

- Статус: accepted
- Дата: 2026-04-25
- Контекст: `GAP-0009` блокировал production retention policy для audit/techlog, потому что ТЗ запрещало обычное удаление, но не задавало срок и процедуру регламентной очистки.
- Решение: audit records и techlog records хранятся 90 дней. Очистка выполняется только регламентной процедурой, не через обычный UI. Operations and metadata сохраняются по существующим правилам документации.
- Последствия: implementation может добавить non-UI cleanup procedure для записей старше 90 дней с operational safeguards. UI deletion audit/techlog остаётся запрещённым.
- Закрывает: `GAP-0009`
- Трассировка: ТЗ §20, §21, §27

## ADR-0015: TASK-009 UI gaps реализуются сейчас

- Статус: accepted
- Дата: 2026-04-25
- Контекст: аудит TASK-009 подтвердил, что product list/card, WB store parameter write-flow, draft pre-run file context and admin write-flow являются обязательными для покрытия `docs/product/UI_SPEC.md`; customer decisions по `GAP-0010`, `GAP-0011`, `GAP-0012` и `GAP-0013` запрещают status/read-only substitutes и перенос в TASK-010.
- Решение: реализовать в текущем исправлении TASK-009:
  - backend product model/list/card для `MarketplaceProduct` по уже описанной модели данных;
  - WB store parameter write-flow с history/audit;
  - draft run context: upload/replace/delete files, version list, затем "Проверить" / "Обработать";
  - admin write-flow: users create/edit/block/archive, role edit where allowed, permission assignment, store access assignment.
- Последствия: TASK-009 остаётся blocked до реализации этих решений. TASK-010 не принимает перенос этих экранов/workflows. Решение не расширяет WB/Ozon business logic, reason/result codes, approved WB defaults или поля `MarketplaceProduct` сверх профильной документации.
- Закрывает: `GAP-0010`, `GAP-0011`, `GAP-0012`, `GAP-0013`
- Трассировка: ТЗ §5, §6, §11, §17-§20, §27

## ADR-0016: Stage 2 split - 2.1 WB API, 2.2 Ozon API

- Статус: accepted
- Дата: 2026-04-26
- Контекст: `tz_stage_2.1.txt` требует подготовить Stage 2.1 только для WB API и не смешивать его с будущим Ozon API.
- Решение: Stage 2 разделён на 2.1 WB API и 2.2 Ozon API. Документы и implementation tasks Stage 2.1 покрывают только WB.
- Последствия: Ozon API не реализуется в TASK-011..TASK-017; Excel Stage 1 остаётся штатным/резервным режимом.
- Трассировка: `docs/stages/stage-2/STAGE_2_SCOPE.md`

## ADR-0017: WB API source-to-Excel flow before API upload

- Статус: accepted
- Дата: 2026-04-26
- Контекст: ТЗ требует сохранить понятную модель ручной работы WB, заменить источники на API и добавить опциональную API-загрузку.
- Решение: Stage 2.1 строится как 2.1.1 price export -> 2.1.2 current promotion exports -> 2.1.3 result Excel -> 2.1.4 upload. 2.1.1-2.1.3 не меняют WB.
- Последствия: API-generated Excel files являются формальной basis; API upload не может обходить расчётный Excel/result operation.
- Трассировка: `docs/product/WB_DISCOUNTS_API_SPEC.md`

## ADR-0018: WB current promotions definition

- Статус: accepted
- Дата: 2026-04-26
- Контекст: пользователь явно требует текущие акции, не ближайшие/будущие/все.
- Решение: current promotion = `startDateTime <= now_utc < endDateTime`; API window покрывает `now_utc`, `allPromo=true`, затем применяется локальный строгий фильтр.
- Последствия: auto promotions сохраняются без выдуманных nomenclature rows; current filter timestamp сохраняется в snapshot.
- Трассировка: `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`

## ADR-0019: WB API upload safety - confirmation + drift check

- Статус: accepted
- Дата: 2026-04-26
- Контекст: 2.1.4 является единственным шагом, меняющим WB по API.
- Решение: upload требует explicit confirmation, pre-upload drift check, batch size <= 1000, uploadID per batch, WB status polling. Price drift блокирует upload.
- Последствия: HTTP 200 не считается успехом; partial errors маппятся в `completed_with_warnings`; quarantine errors показываются отдельно.
- Трассировка: `docs/product/WB_DISCOUNTS_API_SPEC.md`

## ADR-0020: WB API reason/result codes

- Статус: accepted
- Дата: 2026-04-26
- Контекст: Stage 1 WB reason/result codes закрыты; Stage 2.1 требует API-specific detail rows.
- Решение: Stage 2.1 получает отдельный закрытый каталог WB API codes в `docs/product/WB_DISCOUNTS_API_SPEC.md` и `docs/architecture/DATA_MODEL.md`.
- Последствия: разработчики не добавляют/переименовывают codes без документации и ADR; Stage 1 Excel codes не смешиваются с API codes без явного правила.
- Трассировка: `docs/product/WB_DISCOUNTS_API_SPEC.md`

## ADR-0021: WB auto promotions require an external product-source artifact

- Статус: accepted
- Дата: 2026-04-29
- Контекст: live read-only проверка WB Promotions Calendar показала, что API возвращает auto promotions в списке и details, но `GET /api/v1/calendar/promotions/nomenclatures` не отдаёт товарные строки для auto promotions. Заказчик подтвердил, что для бизнес-сценария нужны именно auto promotions.
- Решение: WB API не считается источником состава товаров auto promotions. Для расчёта скидок по WB auto promotions обязателен внешний подтверждённый source artifact со списком товаров auto-акции, например Excel/export из личного кабинета WB или другой утверждённый источник. WB API может использоваться вокруг этого artifact для получения карточек, цен, остатков, заказов/продаж и другой справочной/аналитической информации, но не для восстановления состава auto-акции.
- Последствия: проектировщик не должен ставить задачи, которые требуют получить `nmID` auto promotion только из WB Promotions Calendar API. Реализация не должна создавать пустые или синтетические promo files для auto promotions, подставлять все карточки магазина как состав auto-акции или использовать regular-promotion nomenclatures как замену. Будущий контур WB auto promotions начинается с проектирования внешнего product-source artifact и его приёмки.
- Трассировка: `docs/product/WB_API_PROMOTIONS_EXPORT_SPEC.md`, `docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md`, `docs/gaps/GAP_REGISTER.md`

## ADR-0022: Ozon API Elastic Boosting reuses Ozon Excel decision engine

- Статус: accepted
- Дата: 2026-04-29
- Контекст: Stage 2.2 должен добавить Ozon API-контур акции `Эластичный бустинг` без изменения Stage 1 Ozon Excel rules.
- Решение: Stage 2.2 строится как adapter: Ozon API sources -> canonical `J/O/P/R` row -> existing 7-rule Ozon decision engine -> review -> output/upload. API-модуль не дублирует формулы и не добавляет пользовательские параметры скидки.
- Последствия: implementation must extract/reuse shared Ozon calculation core. Stage 1 Ozon Excel remains штатный режим.
- Трассировка: `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`

## ADR-0023: Ozon Elastic Boosting UI workflow and deactivate safety

- Статус: accepted, amended by ADR-0026 for deactivate behavior and ADR-0027 for review state
- Дата: 2026-04-29
- Контекст: заказчик требует явную веб-иерархию marketplace/domain/source/workflow and fixed button workflow for Ozon Elastic Boosting.
- Решение: Stage 2.2 master page path is `Маркетплейсы -> Ozon -> Акции -> API -> Эластичный бустинг`; button order is fixed from actions download to upload. Review is an immutable calculation result state, not a separate Operation. Deactivate rows require separate confirmation and mandatory row-level reason.
- Последствия: no API write without accepted result, explicit confirmation and drift-check. Deactivate cannot be hidden inside generic upload. The older option "deactivate declined -> add/update proceeds" is superseded by ADR-0026.
- Трассировка: `docs/product/OZON_API_ELASTIC_UI_SPEC.md`, `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`

## ADR-0024: Ozon API connection and secret safety

- Статус: accepted
- Дата: 2026-04-29
- Контекст: Ozon API uses separate Client-Id/Api-Key credentials and must not share WB token handling.
- Решение: Ozon API has separate `ConnectionBlock` module/connection type. Client-Id and Api-Key are stored only via `protected_secret_ref`. Metadata, snapshots, audit, techlog, UI, files, reports and test output must not contain secret-like values or raw sensitive API responses.
- Последствия: `ozon.api.connection.*` rights are separate from WB and Ozon Excel rights. Connection manage never grants secret readback.
- Трассировка: `docs/architecture/API_CONNECTIONS_SPEC.md`, `docs/product/PERMISSIONS_MATRIX.md`

## ADR-0025: Ozon API operation/data/file contracts

- Статус: accepted, amended by ADR-0032 for manual upload Excel
- Дата: 2026-04-29
- Контекст: Stage 2.2 needs operation classification, snapshots, file scenarios and reason/result codes that do not collide with Stage 1 Excel or Stage 2.1 WB.
- Решение: Ozon API operations use `Operation.step_code`, not `Operation.type=check/process`. Required snapshots/results may be dedicated models or equivalent immutable operation/detail/snapshot storage. Result report is always available after calculation; manual upload Excel format is defined by ADR-0032.
- Последствия: implementation tasks must preserve row-level traceability for actions, active/candidates, joined product data, calculation, review and upload details. Adding/renaming codes requires documentation update and ADR.
- Трассировка: `docs/product/OPERATIONS_SPEC.md`, `docs/architecture/DATA_MODEL.md`, `docs/architecture/FILE_CONTOUR.md`

## ADR-0026: Ozon Elastic active not-upload-ready rows are removed from action

- Статус: accepted
- Дата: 2026-04-30
- Контекст: аудит Stage 2.2 выявил противоречие в destructive deactivate flow: часть документов разрешала upload add/update даже если пользователь отказался от снятия active + not_upload_ready строк. Заказчик уточнил целевую модель.
- Решение: если товар уже участвует в Ozon Elastic Boosting (`active` или `candidate_and_active`), но по каноническому расчёту получает `not_upload_ready`, целевое действие равно `deactivate_from_action`. UI обязан до подтверждения показать весь список строк группы `deactivate_from_action` и причину по каждой строке. Подтверждение запрашивается один раз на всю группу `deactivate_from_action`, а не отдельно по строкам. Без этого группового подтверждения destructive deactivate API call невозможен, and the target upload does not start; add/update must not silently proceed while mandatory deactivate rows remain unconfirmed.
- Последствия: `not_uploaded_user_declined` не является штатным result code Stage 2.2. Upload preconditions include confirmation for each non-empty write group: add/update group if add/update rows exist, and deactivate group if deactivate rows exist. If the user does not confirm deactivate, the accepted/reviewed result stays pending with `review_pending_deactivate_confirmation` / `ozon_api_upload_blocked_deactivate_unconfirmed`; no Ozon write operation is created.
- Трассировка: `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`, `docs/product/OZON_API_ELASTIC_UI_SPEC.md`, `docs/gaps/GAP_REGISTER.md`

## ADR-0027: Ozon Elastic result review is calculation result state

- Статус: accepted
- Дата: 2026-04-30
- Контекст: `GAP-0020` blocked TASK-024 because Stage 2.2 needed customer approval for whether result review is a separate operation or a state of the calculation result.
- Решение: approved option A. Stage 2.2 Ozon Elastic Boosting review is stored as immutable calculation result state, not as a separate `Operation` and not as a separate `Operation.step_code`. Approved review states are `not_reviewed`, `accepted`, `declined`, `stale`, `review_pending_deactivate_confirmation`. Upload is allowed only from an accepted result. If an accepted result has `deactivate_from_action` rows, it may stay in `review_pending_deactivate_confirmation` until one confirmation for the whole deactivate group is provided. `Не принять результат` fixes `declined` state and audit.
- Последствия: TASK-024 is no longer blocked by `GAP-0020`; implementation must not create `ozon_api_elastic_result_review` or another review operation step code. Upload and UI gating use calculation result review state plus audit records.
- Закрывает: `GAP-0020`
- Трассировка: `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`, `docs/product/OZON_API_ELASTIC_UI_SPEC.md`, `docs/product/OPERATIONS_SPEC.md`, `docs/tasks/implementation/stage-2/TASK-024-ozon-elastic-result-review.md`

## ADR-0028: Ozon Elastic candidate/active collision handling

- Статус: accepted
- Дата: 2026-04-30
- Контекст: `GAP-0021` blocked Stage 2.2 active/candidate merge behavior because the same `product_id` may be returned by both active products and candidate products for the selected Ozon Elastic Boosting action.
- Решение: if one `product_id` is present in both active and candidates for the selected action, the two source rows are merged into one canonical row with `source_group=candidate_and_active`. For write planning this row is treated as already participating in the action (`active`): do not create a duplicate add row; if calculation result is `upload_ready`, planned action is `update_action_price`; if calculation result is `not_upload_ready`, planned action is `deactivate_from_action`.
- Последствия: implementation must preserve the collision fact in source snapshots/details and result reports. Duplicate source rows must not produce duplicate add/update/deactivate writes. `candidate_and_active` rows follow the same deactivate confirmation and row-level reason requirements as active rows.
- Закрывает: `GAP-0021`
- Трассировка: `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`, `docs/product/OZON_API_ELASTIC_UI_SPEC.md`, `docs/architecture/DATA_MODEL.md`, `docs/tasks/implementation/stage-2/TASK-021-ozon-elastic-products-download.md`, `docs/tasks/implementation/stage-2/TASK-023-ozon-elastic-calculation-reports.md`, `docs/tasks/implementation/stage-2/TASK-025-ozon-elastic-upload-deactivate.md`

## ADR-0029: Ozon Elastic Boosting action identification

- Статус: accepted
- Дата: 2026-04-30
- Контекст: `GAP-0014` blocked Stage 2.2 actions selection and downstream upload drift-check because the system needed a customer-approved way to identify the Ozon Elastic Boosting action without mixing seller actions or unrelated Ozon actions.
- Решение: during actions discovery/download, Elastic Boosting candidates are actions for the selected Ozon store/account where `action_type = MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT` and title contains `Эластичный бустинг`. The user selects the concrete action. The selected/saved `action_id` is the primary identifier for all following workflow steps in that store context. The system must not hard-code a global Elastic Boosting `action_id` constant, even if the customer observes that the current Elastic Boosting `action_id` has remained stable for a long time. Before upload, drift-check re-reads actions and verifies that the saved `action_id` still exists and still has the expected `action_type` and title marker.
- Последствия: TASK-020 is no longer blocked by `GAP-0014`. Product downloads, calculation, review, reports and upload use the saved `action_id` from the selected action context. If the saved action disappears or no longer matches the expected action type/title marker, downstream steps are blocked with drift/action-not-elastic status and require a fresh actions download/selection.
- Закрывает: `GAP-0014`
- Трассировка: `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`, `docs/product/OZON_API_ELASTIC_UI_SPEC.md`, `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`, `docs/tasks/implementation/stage-2/TASK-020-ozon-elastic-actions-download.md`, `docs/tasks/implementation/stage-2/TASK-025-ozon-elastic-upload-deactivate.md`

## ADR-0030: Ozon Elastic canonical J source from product min_price

- Статус: accepted
- Дата: 2026-04-30
- Контекст: `GAP-0015` blocked Stage 2.2 product data join, calculation and drift-check because canonical Excel column J (`минимально допустимая цена`) needed a customer-approved API source.
- Решение: for Stage 2.2 Ozon Elastic Boosting canonical row, Excel J (`минимально допустимая цена`) is sourced from `/v3/product/info/list` field `min_price`. If `min_price` is absent or non-numeric, J is treated as absent and the existing Ozon business reason `missing_min_price` applies.
- Последствия: TASK-022 is no longer blocked by `GAP-0015`. Calculation/report and upload drift-check compare J against the accepted `min_price` basis and do not introduce a new reason code for invalid `min_price`.
- Закрывает: `GAP-0015`
- Трассировка: `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`, `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`, `docs/tasks/implementation/stage-2/TASK-022-ozon-elastic-product-data-join.md`, `docs/tasks/implementation/stage-2/TASK-023-ozon-elastic-calculation-reports.md`, `docs/tasks/implementation/stage-2/TASK-025-ozon-elastic-upload-deactivate.md`

## ADR-0031: Ozon Elastic canonical R stock aggregation from present

- Статус: accepted
- Дата: 2026-04-30
- Контекст: `GAP-0016` blocked Stage 2.2 product data join, calculation and drift-check because canonical Excel column R (`остаток`) needed a customer-approved aggregation rule for `/v4/product/info/stocks`, including FBO/FBS and `reserved` handling.
- Решение: for Stage 2.2 Ozon Elastic Boosting canonical row, Excel R (`остаток`) is the sum of `present` across all stock rows returned by `/v4/product/info/stocks`, including FBO + FBS. `reserved` is not subtracted. If stock info is absent or the summed `present <= 0`, the existing Ozon business reason `no_stock` applies.
- Последствия: TASK-022 is no longer blocked by `GAP-0016`. Calculation/report and upload drift-check compare R against the accepted summed-`present` basis and do not introduce a new reason code for absent stock info or non-positive stock.
- Закрывает: `GAP-0016`
- Трассировка: `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`, `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`, `docs/tasks/implementation/stage-2/TASK-022-ozon-elastic-product-data-join.md`, `docs/tasks/implementation/stage-2/TASK-023-ozon-elastic-calculation-reports.md`, `docs/tasks/implementation/stage-2/TASK-025-ozon-elastic-upload-deactivate.md`

## ADR-0032: Ozon Elastic manual upload Excel uses Stage 1-compatible template

- Статус: accepted
- Дата: 2026-04-30
- Контекст: `GAP-0017` blocked `ozon_api_elastic_manual_upload_excel` because no official Ozon Elastic Boosting manual cabinet upload template was confirmed for Stage 2.2 v1.
- Решение: for Stage 2.2 v1, the manual upload Excel for Ozon Elastic Boosting uses the current Stage 1 Ozon Excel template/format as a Stage 1-compatible manual upload file. This is a customer-approved risk acceptance: if Ozon ЛК does not accept the file, that is a future compatibility issue, while v1 implements this approved format. The workbook must be explicitly marked as manual upload Excel по Stage 1-compatible template. Stage 1 Ozon Excel business rules, workbook behavior and 7-rule calculation order are not changed. For add/update rows the manual file reflects the accepted Stage 2.2 calculation result with K=`Да` and L=`calculated_action_price`. Deactivate rows must remain visible: if the Stage 1-compatible template cannot directly represent deactivate action, the workbook/report includes a separate sheet/section `Снять с акции` with row-level reasons.
- Последствия: `GAP-0017` no longer blocks `ozon_api_elastic_manual_upload_excel`. API upload remains the primary write path; manual Excel is a secondary artifact for ручная загрузка/контроль. Deactivate rows must not be silently omitted from manual artifacts. Stage 1 Ozon Excel regression remains mandatory.
- Закрывает: `GAP-0017`
- Трассировка: `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`, `docs/product/OZON_API_ELASTIC_UI_SPEC.md`, `docs/architecture/FILE_CONTOUR.md`, `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`, `docs/tasks/implementation/stage-2/TASK-023-ozon-elastic-calculation-reports.md`, `docs/tasks/implementation/stage-2/TASK-026-ozon-elastic-ui-acceptance-release.md`, `docs/testing/STAGE_2_2_OZON_TEST_PROTOCOL.md`, `docs/testing/STAGE_2_2_OZON_ACCEPTANCE_CHECKLISTS.md`, `docs/traceability/STAGE_2_2_OZON_TRACEABILITY_MATRIX.md`

## ADR-0033: Ozon Elastic live activate/deactivate payload policy

- Статус: accepted
- Дата: 2026-04-30
- Контекст: `GAP-0018` blocked Stage 2.2 active/candidate product downloads and upload because the read-side actions product schemas and write-side activate/deactivate payload policy had to be customer-approved before implementation. Customer decision 2026-04-30 requires live write-side `activate/deactivate` by current Ozon documentation, not mock/stub-only, while preserving safety gates.
- Решение: Stage 2.2 read-side uses observed/approved fields from `/v1/actions/products` and `/v1/actions/candidates`; implementation must verify exact field names against the official current Ozon schema and cover them with contract tests/sanitized fixtures. Add/update writes use the Ozon actions activate endpoint with `action_id` and product rows containing Ozon-required identifiers and `action_price`. Deactivate writes use the Ozon actions deactivate endpoint with `action_id` and product identifiers. If exact field names in official Ozon docs differ from examples in project documentation, implementation follows the official schema and updates tests/fixtures accordingly. The flow must never use `/v1/product/import/prices`.
- Последствия: TASK-021 is no longer blocked by `GAP-0018` for read-side product schemas. TASK-025 is no longer blocked by `GAP-0018` for activate/deactivate payload policy. Batch size, rate limits and retry/idempotency policy are governed by ADR-0034. Live writes remain gated by accepted result, explicit upload confirmation, one group deactivate confirmation when deactivate rows exist, drift-check, duplicate protection, row-level reporting and safe error handling.
- Закрывает: `GAP-0018`
- Трассировка: `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`, `docs/product/OZON_API_ELASTIC_UI_SPEC.md`, `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`, `docs/tasks/implementation/stage-2/TASK-021-ozon-elastic-products-download.md`, `docs/tasks/implementation/stage-2/TASK-025-ozon-elastic-upload-deactivate.md`, `docs/testing/STAGE_2_2_OZON_TEST_PROTOCOL.md`, `docs/testing/STAGE_2_2_OZON_ACCEPTANCE_CHECKLISTS.md`, `docs/traceability/STAGE_2_2_OZON_TRACEABILITY_MATRIX.md`

## ADR-0034: Ozon API conservative configurable rate/batch/retry policy

- Статус: accepted
- Дата: 2026-04-30
- Контекст: `GAP-0019` blocked Stage 2.2 Ozon API client implementation because page sizes, write batches, rate limiting and retry/idempotency policy had to be explicit before implementation. The issue is technical/orchestrator scope, not customer business logic or web-panel UX.
- Решение: use conservative configurable API defaults for implementation and tests: read page size `100`; write batch size `100`; minimum interval between Ozon API requests `500 ms`; retry only read operations for transient failures (`429`, `5xx`, timeout/network) with bounded backoff. Write `activate/deactivate` requests are not automatically retried after the request was sent or the response is uncertain. A write retry is allowed only as an explicit new operation after drift-check. Defaults must be configurable via settings/env later, while these documented values remain the baseline unless changed by a future ADR. Row-level partial failures must still be persisted and reported.
- Последствия: `GAP-0019` no longer blocks TASK-020..TASK-025 implementation. Read clients must expose page size/rate/backoff behavior in tests with safe snapshots. Upload must split activate/deactivate writes into batches of at most `100`, persist per-batch and per-row results, and classify uncertain sent writes as safe failure requiring explicit new operation rather than automatic replay.
- Закрывает: `GAP-0019`
- Трассировка: `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`, `docs/architecture/API_CONNECTIONS_SPEC.md`, `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`, `docs/tasks/implementation/stage-2/TASK-020-ozon-elastic-actions-download.md`, `docs/tasks/implementation/stage-2/TASK-021-ozon-elastic-products-download.md`, `docs/tasks/implementation/stage-2/TASK-022-ozon-elastic-product-data-join.md`, `docs/tasks/implementation/stage-2/TASK-025-ozon-elastic-upload-deactivate.md`, `docs/testing/STAGE_2_2_OZON_TEST_PROTOCOL.md`, `docs/testing/STAGE_2_2_OZON_ACCEPTANCE_CHECKLISTS.md`, `docs/traceability/STAGE_2_2_OZON_TRACEABILITY_MATRIX.md`

## ADR-0035: Ozon API connection check uses read-only actions endpoint

- Статус: accepted
- Дата: 2026-04-30
- Контекст: `GAP-0022` blocked TASK-019 production live connection check because the endpoint had to be read-only, relevant to the Stage 2.2 actions API and safe for Client-Id/Api-Key verification. A write-like endpoint or ambiguous health check could either mutate Ozon data or mark a connection active without proving access to the actions API.
- Решение: Stage 2.2 Ozon API connection check uses read-only `GET /v1/actions`. The endpoint was verified against test credentials as read-only and relevant for actions API. Status mapping: HTTP 200 with valid JSON containing `result` -> connection `active`; 401/403 -> `check_failed/auth_failed`; 429 -> `check_failed/rate_limited`; 5xx/timeout/network -> `check_failed/temporary`; invalid JSON/schema -> `check_failed/invalid_response`. No write endpoint may be used for connection check.
- Последствия: TASK-019 can implement the production connection check via `GET /v1/actions` and is no longer limited to scaffolding-only check behavior. The check must still preserve secret safety: no Client-Id, Api-Key, headers or raw sensitive response data in metadata, snapshots, audit, techlog, UI, files, reports or test output. Tests must cover the status mapping with mocks/sanitized fixtures.
- Закрывает: `GAP-0022`
- Трассировка: `docs/architecture/API_CONNECTIONS_SPEC.md`, `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`, `docs/tasks/implementation/stage-2/TASK-019-ozon-api-connection.md`, `docs/tasks/implementation/stage-2/IMPLEMENTATION_TASKS.md`, `docs/testing/STAGE_2_2_OZON_TEST_PROTOCOL.md`, `docs/testing/STAGE_2_2_OZON_ACCEPTANCE_CHECKLISTS.md`, `docs/traceability/STAGE_2_2_OZON_TRACEABILITY_MATRIX.md`

## ADR-0036: InternalProduct/ProductVariant is the Product Core

- Статус: accepted
- Дата: 2026-05-01
- Контекст: Stage 3.0 / CORE-1 must stop treating WB/Ozon marketplace rows as the company product identity and prepare future warehouse, production, suppliers, packaging and labels.
- Решение: `InternalProduct` and `ProductVariant` are the company product core. Future stock, production, supplier, BOM, packaging and label modules must reference the internal product/variant layer, not marketplace ids.
- Последствия: marketplace data can enrich or link to the internal core but cannot overwrite internal identity. Excel/API rows do not automatically create internal products.
- Трассировка: `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md`, `docs/product/PRODUCT_CORE_SPEC.md`, `docs/architecture/DATA_MODEL.md`

## ADR-0037: MarketplaceListing is external layer and MarketplaceProduct migrates by compatibility backfill

- Статус: accepted
- Дата: 2026-05-01
- Контекст: current `MarketplaceProduct` is used by Stage 1/2 flows and UI but represents marketplace products/listings, not internal company products.
- Решение: CORE-1 introduces `MarketplaceListing` as external WB/Ozon listing layer. Migration uses option B: create new `MarketplaceListing`, backfill from existing `MarketplaceProduct`, keep `MarketplaceProduct` as deprecated compatibility data until a later audited removal/rename task.
- Последствия: direct model/table rename is avoided in CORE-1 v1. Existing operations and product refs remain compatible. Deleting/truncating legacy product data is prohibited without separate migration/backup/rollback/regression plan.
- Трассировка: `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md`, `docs/product/MARKETPLACE_LISTINGS_SPEC.md`

## ADR-0038: Marketplace listing mapping requires explicit human confirmation

- Статус: accepted
- Дата: 2026-05-01
- Контекст: WB and Ozon can contain the same physical item with different identifiers and also erroneous duplicate data. Auto-merge would create business risk.
- Решение: persisted `MarketplaceListing -> ProductVariant` mapping is created only by explicit manual user confirmation by a user with mapping permission, with audit and `ProductMappingHistory`. Customer decision 2026-05-01 closes `GAP-0023` with Option B: CORE-1 may show semi-automatic non-authoritative candidates only by exact `seller_article`, `barcode` or external identifier matches. CORE-1 must not auto-confirm or auto-merge by title, barcode, fuzzy/partial seller article or any automatic confirmed rule.
- Последствия: candidate suggestions are non-authoritative UI/workflow aids. Selecting a suggestion still requires manual confirmation before `matched`. Multiple candidates or conflicting exact matches must remain `needs_review` or `conflict` until a permitted user resolves them. Automatic confirmed mapping is prohibited.
- Трассировка: `docs/product/MARKETPLACE_LISTINGS_SPEC.md`, `docs/product/PRODUCT_CORE_UI_SPEC.md`, `docs/gaps/GAP_REGISTER.md`

## ADR-0039: Product Core sync snapshots are separated from listing current cache

- Статус: accepted
- Дата: 2026-05-01
- Контекст: CORE-1 needs current listing values for UI and immutable source records for audit, regression and future analytics.
- Решение: `MarketplaceListing.last_values` is only latest-state cache. Historical/source truth is stored in `MarketplaceSyncRun` and snapshot tables/contracts: price, stock, sales period and promotion snapshots.
- Последствия: failed sync does not erase last successful values. Any future analytical use of sales/buyout metrics requires separate source/formula specification.
- Трассировка: `docs/product/MARKETPLACE_LISTINGS_SPEC.md`, `docs/architecture/DATA_MODEL.md`

## ADR-0040: Product Core preserves immutable operations and raw product references

- Статус: accepted
- Дата: 2026-05-01
- Контекст: Stage 1/2 operations and detail rows are already immutable and use `OperationDetailRow.product_ref` as raw product identifier.
- Решение: CORE-1 does not rewrite completed operation summaries, files or row outcomes. `product_ref` remains raw. Nullable FK enrichment to `MarketplaceListing` is allowed only by deterministic audited migration rules that do not alter historical outcomes.
- Последствия: Stage 1/2 regression is mandatory after migration. Product Core can improve navigation and linking without changing old operation truth.
- Трассировка: `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md`, `docs/product/OPERATIONS_SPEC.md`

## ADR-0041: Excel is not automatic source of Product Core

- Статус: accepted
- Дата: 2026-05-01
- Контекст: Excel remains a normal operational mode, but product core must not be inflated automatically from every workbook row.
- Решение: existing Excel operations remain unchanged and do not automatically create internal products, variants or confirmed mappings. Any Excel import into Product Core/listings must be a separate explicit workflow with validation, diff, impact warning, confirmation, operation/audit/history and rollback notes.
- Последствия: Stage 1 Excel remains штатный/резервный mode. Product Core imports are gated and cannot be hidden inside discounts check/process flows.
- Трассировка: `docs/product/PRODUCT_CORE_UI_SPEC.md`, `docs/product/OPERATIONS_SPEC.md`, `docs/product/PRODUCT_CORE_SPEC.md`
