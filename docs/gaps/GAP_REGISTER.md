# GAP_REGISTER.md

Трассировка: ТЗ §1.4, §24-§26.

## Правила ведения

GAP - это пробел, противоречие или неоднозначность, которую нельзя закрыть предположением агента. Спорный участок не реализуется до решения. Решение фиксируется здесь и при необходимости в `docs/adr/ADR_LOG.md`.

Если gap блокирует исправление аудиторского замечания или проектировщик не может устранить проблему без пробела в ТЗ / нового утверждённого решения, запись получает маршрут эскалации `проектировщик -> оркестратор -> заказчик`. Такой gap не закрывается молча, не маскируется в тексте документации и не переводится в resolved без зафиксированного решения.

## Открытые gaps по phase gates

Phase gate определяет, какая фаза заблокирована пробелом. Открытый gap не закрывается предположением агента. Если gap является blocking gate, задачи в указанной фазе не стартуют до фиксации решения в этом реестре и, если требуется, в `docs/adr/ADR_LOG.md`.

### blocks_before_any_development

На 2026-04-25 открытых gaps в этом phase gate нет. `GAP-0001`, `GAP-0005` и `GAP-0006` закрыты решениями заказчика и перенесены в раздел "Закрытые gaps".

### blocks_before_module_implementation

Эти gaps не блокируют документационное проектирование и общий платформенный каркас после закрытия предыдущего gate, но блокируют реализацию соответствующих WB/Ozon module slices, seed-словарей и приёмочных проверок по затронутой логике.

На 2026-04-25 открытых gaps в этом phase gate нет. `GAP-0002`, `GAP-0003` и `GAP-0004` закрыты решениями заказчика и перенесены в раздел "Закрытые gaps".

### blocks_before_acceptance/production

Эти gaps не блокируют внутреннюю разработку после закрытия предыдущих gates, но блокируют формальную приёмку, production readiness или эксплуатационный запуск.

На 2026-04-25 ранее открытые gaps в этом phase gate были закрыты: `GAP-0007`, `GAP-0008`, `GAP-0009`, `GAP-0010`, `GAP-0011`, `GAP-0012` и `GAP-0013` закрыты решениями заказчика и перенесены в раздел "Закрытые gaps".

Важно: для `GAP-0008` проектное решение закрыто, но фактические контрольные файлы WB/Ozon, checksums, результаты старой программы и expected results остаются обязательным acceptance artifact gate. Формальная приёмка не может быть завершена до получения и фиксации этих артефактов.

TASK-009 после аудита остаётся blocked не из-за открытого gap, а до реализации customer decisions по `GAP-0010`..`GAP-0013` в текущем исправлении TASK-009. Перенос этих решений в TASK-010 запрещён.

## Закрытые gaps

### GAP-0001: Технологический стек этапа 1

- Статус: resolved
- Phase gate: blocks_before_any_development
- Blocking gate: снят
- Где обнаружен: `docs/architecture/ARCHITECTURE.md`, `docs/architecture/PROJECT_STRUCTURE.md`
- Требование ТЗ: §4, §22
- Затронутая область: backend, frontend, ORM, deployment commands
- Решение: технологический стек этапа 1 = Django + PostgreSQL + server-rendered UI / Django templates.
- ADR: ADR-0006
- Кто принял решение: заказчик
- Дата решения: 2026-04-25

### GAP-0005: Seed-набор прав для типовых ролей

- Статус: resolved
- Phase gate: blocks_before_any_development
- Blocking gate: снят
- Где обнаружен: `docs/product/PERMISSIONS_MATRIX.md`
- Требование ТЗ: §11.9-§11.13
- Затронутая область: начальная настройка ролей
- Решение: утверждён консервативный seed-набор:
  - Владелец: полный доступ ко всему, без ограничений.
  - Глобальный администратор: всё администрирование, кроме ограничения/блокировки/удаления владельца.
  - Локальный администратор: управление пользователями, магазинами, параметрами и доступами только в назначенных магазинах/кабинетах.
  - Менеджер маркетплейсов: работа с WB/Ozon Excel-сценариями, операциями, файлами, товарами и параметрами доступных магазинов, без управления ролями и системными правами.
  - Наблюдатель: только просмотр доступных магазинов, операций, результатов, товаров и ограниченных журналов, без изменений и скачивания итоговых файлов, если отдельно не разрешено.
- ADR: ADR-0007
- Кто принял решение: заказчик
- Дата решения: 2026-04-25

### GAP-0006: Формат видимых идентификаторов

- Статус: resolved
- Phase gate: blocks_before_any_development
- Blocking gate: снят
- Где обнаружен: `docs/architecture/DATA_MODEL.md`
- Требование ТЗ: §23.2
- Затронутая область: operations, stores, users, files, run
- Решение: формат visible identifiers:
  - operation: `OP-YYYY-NNNNNN`
  - run: `RUN-YYYY-NNNNNN`
  - file: `FILE-YYYY-NNNNNN`
  - store/cabinet: `STORE-NNNNNN`
  - user: `USR-NNNNNN`
- ADR: ADR-0008
- Кто принял решение: заказчик
- Дата решения: 2026-04-25

### GAP-0002: Конкретные значения системных WB-параметров по умолчанию

- Статус: resolved
- Phase gate: blocks_before_module_implementation
- Blocking gate: снят
- Где обнаружен: `docs/architecture/DATA_MODEL.md`, `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`
- Требование ТЗ: §14, §15.9-§15.10
- Затронутая область: параметры расчёта WB
- Решение: утверждены системные WB defaults:
  - `wb_threshold_percent = 70`
  - `wb_fallback_over_threshold_percent = 55`
  - `wb_fallback_no_promo_percent = 55`
- ADR: ADR-0009
- Кто принял решение: заказчик
- Дата решения: 2026-04-25

### GAP-0003: Полный закрытый перечень reason/result codes WB

- Статус: resolved
- Phase gate: blocks_before_module_implementation
- Blocking gate: снят
- Где обнаружен: `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`, `docs/architecture/DATA_MODEL.md`
- Требование ТЗ: §12.12, §17.5, §23.1
- Затронутая область: detail audit, UI, exports, tests
- Решение: утверждён минимальный закрытый перечень WB reason/result codes:
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
- ADR: ADR-0010
- Кто принял решение: заказчик
- Дата решения: 2026-04-25

### GAP-0004: Warning/error semantics для WB результата вне диапазона 0-100

- Статус: resolved
- Phase gate: blocks_before_module_implementation
- Blocking gate: снят
- Где обнаружен: `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`
- Требование ТЗ: §15.8
- Затронутая область: WB row validation, блокировка process, detail audit
- Решение: WB итоговая скидка вне диапазона 0..100 является error строки с кодом `wb_discount_out_of_range`; check завершается с ошибками; process запрещён; обрезка значения и частичная обработка запрещены.
- ADR: ADR-0011
- Кто принял решение: заказчик
- Дата решения: 2026-04-25

### GAP-0007: Частота и глубина хранения backup

- Статус: resolved
- Phase gate: blocks_before_acceptance/production
- Blocking gate: снят
- Где обнаружен: `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md`
- Требование ТЗ: §22.5
- Затронутая область: эксплуатация
- Решение: backup policy этапа 1 = daily PostgreSQL backup + daily server file storage backup, retention 14 days, mandatory backup before production update, restore check by documented manual procedure after setup and before important releases.
- ADR: ADR-0012
- Кто принял решение: заказчик
- Дата решения: 2026-04-25

### GAP-0008: Контрольные файлы WB/Ozon и ожидаемые результаты

- Статус: resolved
- Phase gate: blocks_before_acceptance/production
- Blocking gate: проектное решение снято; acceptance artifact gate остаётся
- Где обнаружен: `docs/stages/stage-1/ACCEPTANCE_TESTS.md`, `docs/testing/TEST_PROTOCOL.md`
- Требование ТЗ: §24
- Затронутая область: приёмка
- Решение: заказчик передаёт реальные контрольные WB/Ozon файлы и результаты старой программы; дополнительно должны быть edge-case наборы. До получения фактических файлов, checksums и expected results формальная приёмка остаётся заблокирована как acceptance artifact gate. Агенты не выдумывают файлы, checksums или expected results.
- ADR: ADR-0013
- Кто принял решение: заказчик
- Дата решения: 2026-04-25

### GAP-0009: Правило очистки audit/techlog после сроков хранения

- Статус: resolved
- Phase gate: blocks_before_acceptance/production
- Blocking gate: снят
- Где обнаружен: `docs/architecture/DATA_MODEL.md`, `docs/audit/AUDIT_PROTOCOL.md`
- Требование ТЗ: §20, §21
- Затронутая область: хранение audit/techlog
- Решение: audit records и techlog records хранятся 90 дней; очистка выполняется только регламентной процедурой, не через обычный UI; операции и метаданные сохраняются по существующим правилам документации.
- ADR: ADR-0014
- Кто принял решение: заказчик
- Дата решения: 2026-04-25

### GAP-0010: Товарный справочник в UI при отсутствии backend-модели товаров

- Статус: resolved/customer_decision
- Phase gate: blocks_before_acceptance/production
- Blocking gate: снят как gap; реализация решения обязательна в текущем исправлении TASK-009
- Где обнаружен: TASK-009 UI audit; `apps/marketplace_products/models.py`
- Требование ТЗ: §18, `docs/product/UI_SPEC.md` "Список товаров" / "Карточка товара"
- Затронутая область: UI справочников, карточка товара, связи product -> operations/files
- Проблема: UI_SPEC требует список и карточку товаров, но текущий backend-модуль `marketplace_products` не содержит модели товара, сервисов выборки, истории появления/обновления и связей с operations/files. Реализация полноценного экрана потребовала бы backend model/list/card вместо status screen.
- Решение: сделать backend product model/list/card сейчас в рамках исправления TASK-009. Status screen или deferral не считаются покрытием UI_SPEC для TASK-009.
- ADR: ADR-0015
- Кто принял решение: заказчик
- Дата решения: 2026-04-25
- Связанные документы: `docs/product/UI_SPEC.md`, `docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md`, `docs/architecture/DATA_MODEL.md`

### GAP-0011: Write-flow параметров магазина через UI без утверждённого audit/history сервиса

- Статус: resolved/customer_decision
- Phase gate: blocks_before_acceptance/production
- Blocking gate: снят как gap; реализация решения обязательна в текущем исправлении TASK-009
- Где обнаружен: TASK-009 UI audit; `apps/platform_settings/models.py`
- Требование ТЗ: §11, §17, `docs/product/UI_SPEC.md` "Параметры магазина / кабинета"
- Затронутая область: UI настроек WB-параметров, audit/history параметров
- Проблема: UI_SPEC требует изменение store-level WB-параметров с историей и audit. В текущем backend есть модели `SystemParameterValue`/`StoreParameterValue`, но нет утверждённого service-layer write-flow, который одновременно валидирует права, создаёт новую effective value, ведёт историю параметров и создаёт audit record `settings.wb_parameter_changed`.
- Решение: реализовать write-flow WB store parameters сейчас в рамках исправления TASK-009, включая history/audit. Read-only параметры не считаются покрытием UI_SPEC для TASK-009.
- ADR: ADR-0015
- Кто принял решение: заказчик
- Дата решения: 2026-04-25
- Связанные документы: `docs/product/UI_SPEC.md`, `docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md`, `docs/architecture/DATA_MODEL.md`

### GAP-0012: Черновой pre-run контекст загрузки/замены/удаления файлов в UI

- Статус: resolved/customer_decision
- Phase gate: blocks_before_acceptance/production
- Blocking gate: снят как gap; реализация решения обязательна в текущем исправлении TASK-009
- Где обнаружен: TASK-009 UI audit; `docs/product/OPERATIONS_SPEC.md` "Run"
- Требование ТЗ: §13, §17, `docs/product/UI_SPEC.md` WB/Ozon upload screens
- Затронутая область: WB/Ozon Excel upload UX, file version list before operation start
- Проблема: UI_SPEC требует загрузить/заменить/удалить файлы до запуска и показать file versions в активном сценарном контексте. Текущий backend имеет file version metadata и pre-operation delete helpers, но нет утверждённой draft/run-context сущности или session contract для многошагового pre-run UI с replace/delete до запуска operation.
- Решение: реализовать draft run context сейчас в рамках исправления TASK-009: upload/replace/delete files, version list, затем "Проверить" / "Обработать". Single-submit upload без draft replace/delete не считается покрытием UI_SPEC для TASK-009.
- ADR: ADR-0015
- Кто принял решение: заказчик
- Дата решения: 2026-04-25
- Связанные документы: `docs/product/UI_SPEC.md`, `docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md`, `docs/product/OPERATIONS_SPEC.md`, `docs/architecture/FILE_CONTOUR.md`

### GAP-0013: Admin write-flow TASK-009 не был зарегистрирован как gap

- Статус: resolved/customer_decision
- Phase gate: blocks_before_acceptance/production
- Blocking gate: снят как gap; реализация решения обязательна в текущем исправлении TASK-009
- Где обнаружен: `docs/audit/AUDIT_REPORT_TASK_009.md`
- Требование ТЗ: §11, `docs/product/UI_SPEC.md` "Администрирование"
- Затронутая область: users, roles, permissions, store access administration
- Проблема: аудит TASK-009 зафиксировал, что UI_SPEC требует create/edit/assign flows and controls для пользователей, ролей и store access, но текущая реализация silently downgraded administration to read-only и отдельный gap не был зарегистрирован.
- Решение: реализовать admin write-flow сейчас в рамках исправления TASK-009: users create/edit/block/archive, role edit where allowed, permission assignment, store access assignment. Read-only administration не считается покрытием UI_SPEC для TASK-009.
- ADR: ADR-0015
- Кто принял решение: заказчик
- Дата решения: 2026-04-25
- Связанные документы: `docs/product/UI_SPEC.md`, `docs/tasks/implementation/stage-1/TASK-009-ui-stage-1-screens.md`, `docs/product/PERMISSIONS_MATRIX.md`, `docs/architecture/DELETION_ARCHIVAL_POLICY.md`
