# MODULE_SPECIFICATIONS

Трассировка: ТЗ §3, §5-§17, §20-§23, §26.5.

## Назначение

Каталог содержит модульную карту этапа 1 для будущей нарезки задач Codex CLI. Подробные правила находятся в профильных документах `docs/architecture/` и `docs/product/`.

## Модули этапа 1

### 1. Identity & Access

- Вход: `docs/product/PERMISSIONS_MATRIX.md`, `docs/architecture/DATA_MODEL.md`.
- Выход: пользователи, роли, права, section access, individual grants/denies, store access.
- Обязательные свойства: владелец не ограничивается; запреты приоритетнее разрешений; права действий отделены от доступов к разделам и объектных доступов.
- Не делает: расчёт скидок, хранение Excel-файлов.

### 2. Stores & Connections

- Вход: ТЗ §8, `docs/architecture/DATA_MODEL.md`, `docs/product/UI_SPEC.md`.
- Выход: группы/бренды, магазины/кабинеты, карточки, история изменений, API-блок.
- Обязательное UI-сообщение для API-блока: "подготовлено для этапа 2, в этапе 1 не используется".
- Не делает: API-расчёт скидок этапа 2.

### 3. Marketplace Products

- Вход: ТЗ §9, `docs/architecture/DATA_MODEL.md`.
- Выход: карточки маркетплейс-товаров, создаваемые/обновляемые из валидных строк Excel.
- Обязательное: товар привязан к marketplace и store/account; отсутствие товара до загрузки не ошибка.
- Не делает: полноценный производственный справочник.

### 4. Operations & Execution

- Вход: `docs/product/OPERATIONS_SPEC.md`.
- Выход: operation, run, statuses, check/process orchestration, interrupted_failed.
- Обязательное: завершённая operation неизменяема; process связан с check basis; no auto-resume этапа 1.
- Не делает: audit или tech log вместо своих records.

### 5. Files

- Вход: `docs/architecture/FILE_CONTOUR.md`.
- Выход: file objects, versions, storage metadata, retention, download checks.
- Обязательное: физические файлы 3 дня; metadata/history 90 дней; operation links сохраняются.
- Не делает: самостоятельный главный пользовательский файловый реестр.

### 6. Settings

- Вход: `docs/architecture/DATA_MODEL.md`, `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`.
- Выход: system defaults, store values, change history, parameter snapshots.
- Обязательное: WB has exactly three user-managed parameters at этап 1; Ozon has no analogous user params.
- Не делает: скрытые дополнительные WB/Ozon параметры.

### 7. Discounts / WB / Excel

- Вход: `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`, `docs/product/OPERATIONS_SPEC.md`, `docs/architecture/FILE_CONTOUR.md`.
- Выход: WB check, WB process, output workbook, summary/detail audit.
- Обязательное: 1 price file, 1-20 promo files, decimal arithmetic, ceil, only `Новая скидка` changes.
- Не делает: API upload, price editing, extra parameters.

### 8. Discounts / Ozon / Excel

- Вход: `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md`, `docs/product/OPERATIONS_SPEC.md`, `docs/architecture/FILE_CONTOUR.md`.
- Выход: Ozon check, Ozon process, output workbook, summary/detail audit.
- Обязательное: one `.xlsx`, sheet `Товары и цены`, rows from 4, only K/L changes, 7 rules in order; process only по допустимой и актуальной check-основе с сохранением operation/file version links.
- Не делает: процентную скидку как отдельный результат; WB-style parameters.

### 9. Audit

- Вход: ТЗ §20, `docs/audit/AUDIT_PROTOCOL.md`, `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`.
- Выход: immutable audit records, list/card/filtering, links to entities.
- Обязательное: фиксирует значимые действия пользователей и администраторов.
- Не делает: системный stack trace как основной контур.

### 10. Tech Log & Notifications

- Вход: ТЗ §20, §22.6, `docs/product/OPERATIONS_SPEC.md`, `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`.
- Выход: system events, errors, failures, critical notifications.
- Обязательное: чувствительные детали видны только с отдельным правом.
- Не делает: бизнес-историю операций.

### 11. Exports

- Вход: ТЗ §18.6, `docs/product/UI_SPEC.md`, `docs/stages/stage-1/ACCEPTANCE_TESTS.md`.
- Выход: exports for operations, products, stores, operation error/warning details, row result details.
- Обязательное: exports use same system codes as UI/storage/tests.
- Не делает: административные экспорты audit/techlog/users/roles как обязательный этап 1.

## Будущие модули

Будущие API, цены, остатки, продажи, производство, поставки, закупки проектируются только как архитектурная совместимость, если это влияет на базовые сущности этапа 1. Детальная прикладная реализация не входит в этап 1.
