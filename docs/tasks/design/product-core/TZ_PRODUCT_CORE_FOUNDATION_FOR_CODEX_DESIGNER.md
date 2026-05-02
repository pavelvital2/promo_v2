# ТЗ для проектировщика Codex CLI
# Этап CORE-1 / Stage 3.0: Product Core Foundation — внутреннее ядро товаров и внешний слой WB/Ozon листингов

Статус: ТЗ для подготовки исполнительной проектной документации.  
Дата: 2026-05-01.  
Проект: `promo_v2`.  
Репозиторий: `https://github.com/pavelvital2/promo_v2`.  
Рабочий корень на VPS: `/home/pavel/projects/promo_v2/`.  
Исполнитель этого ТЗ: проектировщик Codex CLI.  
Реализация по результатам проектирования: только после аудита документации и статуса `AUDIT PASS`.

---

## 0. Назначение документа

Этот документ является входным ТЗ для проектировщика Codex CLI. Проектировщик должен подготовить не код, а комплект исполнительной проектной документации, по которой дальше оркестратор Codex CLI сможет управлять агентами реализации:

- проектировщиком;
- разработчиком;
- аудитором;
- тестировщиком;
- техрайтером.

Документация должна быть самодостаточной, декомпозированной, пригодной для task-scoped работы агентов и органично встроенной в уже существующую структуру документации проекта `promo_v2`.

Ключевое требование: каждый агент на следующих фазах должен получать только минимально достаточный пакет чтения для своей текущей задачи, а не перечитывать всё ТЗ и всю документацию проекта.

---

## 1. Краткий вывод для проектировщика

Нужно спроектировать минимальный фундамент будущей корпоративной системы для работы с WB/Ozon, производством, складом, поставщиками и внутренними товарами.

На этом этапе не нужно строить полную ERP-систему. Нужно заложить правильное ядро:

1. внутренний товар / вариант товара;
2. внешний marketplace-листинг WB/Ozon;
3. связь между внутренним товаром и внешним листингом;
4. API-снимки актуальных данных по листингам;
5. миграция текущего `MarketplaceProduct` в слой внешних листингов.

Главная архитектурная мысль:

```text
Внутренний товар / вариант / материал = ядро компании.
WB/Ozon товар = внешний листинг конкретного магазина на конкретном маркетплейсе.
WB/Ozon магазин = канал продаж.
Склад, производство, поставщики, упаковка, потребность и отгрузки должны строиться вокруг внутреннего товара.
Маркетплейсы должны синхронизировать данные с ядром, но не быть ядром системы.
```

---

## 2. Бизнес-контекст

Компания работает с несколькими магазинами на WB и Ozon. У каждого маркетплейса может быть несколько магазинов/кабинетов. В каждом магазине есть:

- уникальные товары;
- дублирующиеся товары;
- один и тот же физический товар, который может продаваться на разных маркетплейсах и в разных магазинах под разными внешними идентификаторами, артикулами, карточками, ценами, скидками, остатками и статусами.

В компании есть сотрудники и операционные роли:

- менеджеры маркетплейсов;
- операторы вышивальных машин;
- упаковщики;
- кладовщики;
- дизайнеры;
- администраторы;
- владелец.

Есть производственный контур:

- заявки в работу;
- распределение заданий по операторам;
- ежедневный факт выполнения;
- передача на упаковку;
- упаковка;
- готовность к отгрузке;
- отгрузка на маркетплейсы.

Есть складской и закупочный контур:

- поставщики материалов и продукции;
- сведения о том, какой поставщик что поставляет;
- остатки материалов;
- остатки готовой продукции;
- закупки;
- поступления;
- фасовка;
- наклейка штрихкодов;
- отгрузка на WB/Ozon.

Есть отдельное направление магазина швейной фурнитуры:

```text
закупка у разных поставщиков
→ фасовка
→ упаковка
→ наклейка штрихкода
→ отгрузка на маркетплейс
→ продажа
→ повторная закупка у поставщика
```

Проблема: ассортимент большой, есть путаница, у какого поставщика что покупается, какие товары являются одним внутренним товаром, а какие — разными внешними листингами.

Этот этап должен устранить архитектурную причину будущей путаницы: нельзя строить систему вокруг WB/Ozon карточек. Нужно строить её вокруг внутреннего каталога компании.

---

## 3. Текущий контекст проекта

Проект `promo_v2` уже реализован как Django/PostgreSQL modular monolith с server-rendered web UI. В текущей документации и кодовой базе уже есть:

- пользователи, роли, права и object access;
- магазины/кабинеты и API-подключения;
- операции, run, файлы, audit trail, techlog;
- Stage 1 Excel-сценарии WB/Ozon;
- Stage 2.1 WB API-контур;
- Stage 2.2 Ozon Elastic Boosting API-контур;
- текущий модуль `marketplace_products` с моделью `MarketplaceProduct`.

Существующий `MarketplaceProduct` сейчас нельзя считать полноценным внутренним каталогом компании. Он отражает marketplace-товар/карточку/строку, найденную через операции и API, и должен быть переосмыслен как слой внешних листингов.

Проектировщик обязан изучить перед началом работы следующие существующие документы и файлы:

```text
README.md
AGENTS.md
itogovoe_tz_platforma_marketplace_codex.txt
promt_start_project.txt

docs/DOCUMENTATION_MAP.md

docs/orchestration/AGENTS.md
docs/orchestration/ORCHESTRATION.md
docs/orchestration/TASK_TEMPLATES.md
docs/orchestration/HANDOFF_TEMPLATES.md
docs/orchestration/PARALLEL_WORK_RULES.md
docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md

docs/roles/AGENT_ROLES_MATRIX.md
docs/roles/READING_PACKAGES.md

docs/architecture/ARCHITECTURE.md
docs/architecture/DATA_MODEL.md
docs/architecture/API_CONNECTIONS_SPEC.md
docs/architecture/AUDIT_AND_TECHLOG_SPEC.md
docs/architecture/FILE_CONTOUR.md
docs/architecture/DELETION_ARCHIVAL_POLICY.md

docs/product/UI_SPEC.md
docs/product/PERMISSIONS_MATRIX.md
docs/product/OPERATIONS_SPEC.md
docs/product/WB_DISCOUNTS_API_SPEC.md
docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md

docs/stages/stage-2/STAGE_2_SCOPE.md
docs/stages/stage-2/STAGE_2_1_WB_SCOPE.md
docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md

docs/tasks/implementation/stage-2/IMPLEMENTATION_TASKS.md

docs/adr/ADR_LOG.md
docs/gaps/GAP_REGISTER.md

docs/testing/TEST_PROTOCOL.md
docs/testing/ACCEPTANCE_CHECKLISTS.md

docs/traceability/TRACEABILITY_MATRIX.md
```

Если какого-то документа нет в репозитории, проектировщик не должен выдумывать его содержимое. Нужно зафиксировать факт отсутствия и предложить корректное место интеграции.

Уточнение по чтению документов:

- проектировщик читает этот широкий пакет один раз для подготовки исполнительной проектной документации;
- это правило не распространяется на агентов реализации;
- агенты реализации, аудита, тестирования и техрайтинга должны получать только task-scoped reading packages, подготовленные проектировщиком;
- запрещено переносить широкий пакет чтения проектировщика в задачи реализации.

Дополнительный UX-reference:

```text
docs/reports/WBARCODE_CABINET_UX_REFERENCE_2026-05-01.md
```

Этот отчёт можно использовать только как ориентир по удобству веб-панели: навигация, карточки магазинов, счётчики товаров, товарная таблица, быстрые действия, сценарии этикеток и поиска по файлу.

Запрещено использовать wbarcode как источник архитектуры, бизнес-логики, структуры данных, подписочных/платёжных механик, рекламных блоков, текстов или коммерческих сценариев. Проектировщик должен проектировать Promo v2 по этому ТЗ и решениям проекта, а не копировать внешний сервис.

---

## 4. Главная архитектурная цель этапа

Цель этапа CORE-1 / Stage 3.0 — подготовить проектную документацию для перехода от `MarketplaceProduct` как накопительного marketplace-справочника к архитектуре:

```text
InternalProduct
  └── ProductVariant
        └── MarketplaceListing WB / Store A / nmID / vendorCode / barcode
        └── MarketplaceListing WB / Store B / nmID / vendorCode / barcode
        └── MarketplaceListing Ozon / Store C / product_id / offer_id / sku
        └── будущие связи: склад, производство, поставщики, BOM, упаковка, этикетки
```

На этом этапе проектируется только минимальный фундамент. Полный склад, закупки, производство, упаковка и поставщики должны быть учтены архитектурно, но не должны попадать в объём реализации CORE-1, кроме тех полей/связей/расширяемости, без которых ядро потом придётся ломать.

---

## 5. Границы этапа

### 5.1 Входит в этап CORE-1

Проектировщик должен подготовить исполнительную документацию для реализации следующих блоков.

#### 5.1.1 Внутренний товар

Минимальные сущности:

```text
InternalProduct
ProductVariant
ProductCategory
ProductIdentifier
```

Назначение:

- хранить внутреннюю номенклатуру компании;
- отделить физический/внутренний товар от WB/Ozon карточек;
- подготовить основу для будущих склада, производства, поставщиков и упаковки;
- дать компании единый слой управления ассортиментом.

#### 5.1.2 Внешний marketplace-листинг

Минимальная сущность:

```text
MarketplaceListing
```

Назначение:

- хранить конкретный товар/карточку/предложение WB или Ozon в конкретном магазине/кабинете;
- хранить внешние идентификаторы маркетплейса;
- хранить актуальные marketplace-атрибуты;
- связываться с внутренним `ProductVariant`, если соответствие известно.

#### 5.1.3 Связь внутреннего товара и внешнего листинга

Минимально:

```text
MarketplaceListing.internal_variant_id nullable
```

Допускается отдельная модель сопоставления, если проектировщик обоснует её необходимость:

```text
ProductListingMapping
```

Требование: связь должна поддерживать статусы сопоставления и ручную проверку.

#### 5.1.4 API-снимки

Минимальные сущности или эквивалентный queryable immutable contract:

```text
MarketplaceSyncRun
PriceSnapshot
StockSnapshot
SalesSnapshot
PromotionSnapshot
```

Требование: текущие значения могут храниться в кэше листинга, но история и источник данных должны фиксироваться в снимках/операциях.

Уточнение по `PromotionSnapshot`: в CORE-1 проектируется модель и контракт заполнения. Полная реализация всех API акций WB/Ozon не входит в CORE-1. Заполнение `PromotionSnapshot` допускается только:

- из уже реализованных Stage 2.1 / Stage 2.2 контуров;
- или из явно включённых в CORE-1 задач, прошедших проектирование и аудит.

Проектировщик не должен расширять CORE-1 до полной реализации всех акционных API маркетплейсов.

#### 5.1.5 Миграция текущего `MarketplaceProduct`

Нужно спроектировать миграцию:

```text
MarketplaceProduct → MarketplaceListing
```

При миграции:

- каждый текущий marketplace-товар становится внешним листингом;
- связь с внутренним `ProductVariant` по умолчанию пустая;
- исторические данные и связи с операциями сохраняются;
- старые операции и Excel/API-сценарии не ломаются;
- `product_ref` в старых detail rows сохраняется как raw-reference для совместимости;
- если возможно безопасно сопоставить строку операции с листингом, добавляется FK-связь.

Текущий `MarketplaceProduct` запрещено удалять, очищать или заменять без утверждённого migration plan, backup/rollback plan и regression-тестов Stage 1/2.

Допускается только контролируемая миграция:

```text
MarketplaceProduct → MarketplaceListing
```

с сохранением совместимости существующих операций, файлов, audit/techlog и Excel/API-сценариев.

#### 5.1.6 Web UI минимального ядра

Нужно спроектировать экраны:

```text
Товары компании
  Внутренние товары
  Варианты товаров
  Несопоставленные листинги
  Сопоставление WB/Ozon

Маркетплейсы
  WB
    Товары / листинги
  Ozon
    Товары / листинги
```

Минимальный UI должен позволять:

- видеть внутренние товары;
- видеть внешние листинги WB/Ozon;
- фильтровать по маркетплейсу, магазину, статусу, наличию связи;
- открыть карточку внутреннего товара;
- открыть карточку листинга;
- вручную связать листинг с внутренним товаром/вариантом;
- снять ошибочную связь;
- видеть источник последнего обновления;
- видеть дату последнего успешного API-снимка;
- видеть связанные операции и файлы там, где это уже возможно.

#### 5.1.7 Права доступа

Нужно спроектировать права и access control:

- пользователь видит только листинги доступных магазинов;
- внутренние товары компании могут иметь отдельные права просмотра/редактирования;
- связывать листинги с внутренними товарами может только пользователь с отдельным правом;
- экспорт данных проверяет права;
- API-снимки и технические детали доступны только ролям с соответствующими разрешениями;
- owner/admin правила из текущей модели не ломаются.

#### 5.1.8 Audit, techlog, operations

Нужно спроектировать:

- операции синхронизации каталога/цен/остатков/продаж/акций;
- audit actions для ручных изменений и сопоставлений;
- techlog events для API-ошибок и partial sync;
- безопасное хранение snapshot data без API-секретов;
- сохранение неизменяемости завершённых операций.

#### 5.1.9 Excel-роль

Нужно зафиксировать:

- Excel остаётся штатным операционным источником для существующих сценариев;
- Excel не создаёт `InternalProduct`/`ProductVariant`, confirmed mappings или `ProductMappingHistory` автоматически;
- legacy `MarketplaceProduct` compatibility sync may mirror operation `product_ref` into unmatched `MarketplaceListing` compatibility records, and that mirror is not explicit Excel import workflow;
- импорт из Excel в ядро, confirmed mappings или полноценный listing-management contour допускается только как отдельное явное действие с подтверждением и audit;
- старые Excel-сценарии Stage 1 не ломаются;
- API становится основным источником актуальности marketplace-листингов там, где доступен API.

### 5.2 Не входит в этап CORE-1

В реализацию этого этапа не должны попадать:

```text
полный складской ledger;
закупки у поставщиков;
полный справочник Supplier/SupplierItem;
заказы поставщикам;
производственные задания операторам;
ежедневные отчёты операторов;
упаковочные смены;
печать этикеток;
BOM/состав изделия в полном промышленном виде;
автоматический расчёт потребности;
маржинальность;
финансовый учёт;
новые API-загрузки цен/скидок, не входящие в уже утверждённые Stage 2.1/2.2;
замена существующих WB/Ozon Excel-сценариев.
```

Эти контуры должны быть учтены как будущие расширения, но проектировщик не должен размывать этап CORE-1 до полной ERP.

Если future-разделы склада, производства, поставщиков, BOM, упаковки или этикеток упоминаются в UI, они должны быть оформлены как будущие entry points или архитектурные hooks. Нельзя выводить в рабочий интерфейс CORE-1 пустые рабочие блоки, которые выглядят как реализованная функциональность.

---

## 6. Обязательные архитектурные решения, которые проектировщик должен зафиксировать

Проектировщик обязан подготовить ADR или обновление ADR_LOG, где будут зафиксированы следующие решения.

### 6.1 Внутренний товар является ядром

Решение:

```text
InternalProduct/ProductVariant является ядром товарной модели компании.
MarketplaceListing является внешним представлением товара в конкретном магазине WB/Ozon.
```

Последствие:

- WB/Ozon не управляют внутренней идентичностью товара;
- склад, производство, поставщики и упаковка в будущих этапах будут ссылаться на внутренний товар/вариант, а не на marketplace ID.

### 6.2 WB/Ozon листинги не склеиваются автоматически

Решение:

```text
Связь внешнего листинга с внутренним вариантом создаётся только по явному правилу:
ручное сопоставление, подтверждённое полуавтоматическое сопоставление или будущий утверждённый алгоритм.
```

Запрещено:

- автоматически объединять WB и Ozon по похожему названию;
- автоматически объединять по одному barcode без проверки, если в данных возможны ошибки;
- автоматически связывать все листинги с одним внутренним товаром по частичному совпадению артикула.

Рекомендация для CORE-1: разрешить полуавтоматические кандидаты по `seller_article`, `barcode` и внешним идентификаторам, но финальная связь `ProductVariant ↔ MarketplaceListing` создаётся только вручную пользователем с правом сопоставления.

Система может показать подсказку вида "возможный кандидат", но не должна сама создавать подтверждённую связь без действия пользователя.

### 6.3 Текущий `MarketplaceProduct` становится legacy-слоем внешних листингов

Решение:

```text
Текущий MarketplaceProduct не является внутренним товаром компании.
Он мигрируется или переименовывается концептуально в MarketplaceListing.
```

Проектировщик должен предложить один из вариантов:

- A: переименовать модель в `MarketplaceListing` с миграциями;
- B: создать новую модель `MarketplaceListing`, перенести данные, старую оставить как deprecated/compatibility layer;
- C: оставить физическое имя `MarketplaceProduct`, но в документации и сервисном слое трактовать как listing.

Рекомендация для проектировщика: вариант B или A. Вариант C допустим только если переименование создаёт чрезмерный риск для миграции и тестов.

### 6.4 API-снимки отделены от текущих значений

Решение:

```text
Актуальные значения в листинге — это кэш/последнее состояние.
История, источник, период и состав данных фиксируются в sync run и snapshot tables.
```

### 6.5 Операции остаются immutable

Решение:

```text
Завершённые операции, файлы, detail rows, audit и techlog не редактируются через UI.
Исправление или повторная синхронизация создаёт новую operation/sync run.
```

### 6.6 Excel не является автоматическим источником ядра

Решение:

```text
Excel может быть входом операции и источником временных строк.
Excel не создаёт InternalProduct/ProductVariant, confirmed mappings или ProductMappingHistory автоматически.
Legacy MarketplaceProduct compatibility sync may mirror operation product_ref into unmatched MarketplaceListing compatibility records, and that mirror is not explicit Excel import workflow.
Excel-импорт в ядро, confirmed mappings или полноценный listing-management contour допускается только как отдельное явное действие с подтверждением и audit.
```

---

## 7. Требования к целевой модели данных

Проектировщик должен подготовить детальную модель данных и миграционный план. Ниже указана минимальная обязательная структура. Имена полей могут быть уточнены проектировщиком, но смысл и связи должны сохраниться.

### 7.1 InternalProduct

Назначение: внутренняя карточка товара, материала, набора, полуфабриката или готового изделия.

Минимальные поля:

```text
id
visible_id / internal_code
name
product_type
category_id nullable
status
attributes json
comments
created_at
updated_at
created_by
updated_by
```

Предварительные значения `product_type`:

```text
finished_good
material
packaging
semi_finished
kit
service_or_design_artifact
unknown
```

Проектировщик должен определить, какие значения входят в CORE-1 как system dictionary, а какие остаются future.

### 7.2 ProductVariant

Назначение: конкретный вариант внутреннего товара, к которому будут привязываться marketplace-листинги.

Минимальные поля:

```text
id
product_id
internal_sku
name
barcode_internal nullable
variant_attributes json
status
created_at
updated_at
```

Примеры variant attributes:

```text
размер
цвет
модель
тип вышивки
тип упаковки
количество в фасовке
```

### 7.3 ProductIdentifier

Назначение: хранить внутренние и внешние идентификаторы, которые не являются главным ключом.

Минимальные поля:

```text
id
variant_id
identifier_type
value
source
is_primary
created_at
```

Примеры `identifier_type`:

```text
internal_sku
internal_barcode
supplier_sku
wb_vendor_code
ozon_offer_id
legacy_article
```

### 7.4 MarketplaceListing

Назначение: внешний листинг в конкретном магазине WB/Ozon.

Минимальные поля:

```text
id
marketplace
store_id
internal_variant_id nullable
external_primary_id
external_ids json
seller_article
barcode
title
brand
category_name
category_external_id nullable
listing_status
mapping_status
last_values json
first_seen_at
last_seen_at
last_successful_sync_at
last_sync_run_id nullable
last_source
created_at
updated_at
```

Для WB в `external_ids` должны поддерживаться:

```text
nmID
vendorCode
skus
sizeIDs
techSizeNames
```

Для Ozon в `external_ids` должны поддерживаться:

```text
product_id
offer_id
sku
fbo_sku nullable
fbs_sku nullable
```

### 7.5 Mapping status

Минимальные статусы:

```text
unmatched
matched
needs_review
conflict
archived
```

Смысл:

- `unmatched` — листинг ещё не связан с внутренним вариантом;
- `matched` — связь подтверждена;
- `needs_review` — есть кандидат на связь, требуется человек;
- `conflict` — есть противоречивые данные или несколько кандидатов;
- `archived` — связь/листинг не используется в текущей работе.

### 7.6 Listing status

Минимальные статусы:

```text
active
not_seen_last_sync
inactive
archived
sync_error
```

Смысл статусов должен быть человекочитаемо описан в UI_SPEC и DATA_MODEL.

### 7.7 MarketplaceSyncRun

Назначение: фиксировать запуск синхронизации.

Минимальные поля:

```text
id
operation_id nullable
marketplace
store_id
sync_type
source
launch_method
status
started_at
finished_at
requested_by nullable
summary json
error_summary
created_at
```

Минимальные `sync_type`:

```text
listings
prices
stocks
sales
orders
promotions
full_catalog_refresh
mapping_import
```

### 7.8 PriceSnapshot

Минимальные поля:

```text
id
listing_id
sync_run_id
operation_id nullable
snapshot_at
price
price_with_discount nullable
discount_percent nullable
currency
raw_safe json
source_endpoint
created_at
```

### 7.9 StockSnapshot

Минимальные поля:

```text
id
listing_id
sync_run_id
operation_id nullable
snapshot_at
total_stock nullable
stock_by_warehouse json
in_way_to_client nullable
in_way_from_client nullable
raw_safe json
source_endpoint
created_at
```

### 7.10 SalesSnapshot / SalesPeriodSnapshot

Минимальные поля:

```text
id
listing_id
sync_run_id
operation_id nullable
period_start
period_end
orders_qty nullable
sales_qty nullable
buyout_qty nullable
returns_qty nullable
sales_amount nullable
currency nullable
raw_safe json
source_endpoint
created_at
```

Поля `orders_qty`, `sales_qty`, `buyout_qty`, `returns_qty`, `sales_amount` являются nullable. WB и Ozon могут по-разному определять продажи, заказы, выкупы и возвраты, а часть показателей может не отдаваться API напрямую.

Источник данных, формулы и правила трактовки продаж/выкупов должны быть отдельно специфицированы до использования этих полей в расчёте потребности, производства или аналитики.

### 7.11 PromotionSnapshot

Минимальные поля:

```text
id
listing_id
sync_run_id
operation_id nullable
marketplace_promotion_id
action_name
participation_status
action_price nullable
constraints json
reason_code nullable
raw_safe json
source_endpoint
created_at
```

В CORE-1 проектируется contract/foundation `PromotionSnapshot`. Полное покрытие всех WB/Ozon promotion/action API не входит в CORE-1, если это не вынесено в отдельную утверждённую задачу.

### 7.12 ListingHistory / MappingHistory

Нужно спроектировать историю:

```text
ListingHistory
ProductMappingHistory
```

История должна фиксировать:

- появление листинга;
- обновление ключевых полей;
- изменение статуса;
- создание связи с внутренним товаром;
- снятие связи;
- конфликт сопоставления;
- источник изменения;
- пользователя или operation/sync run.

---

## 8. Требования к операциям и execution layer

Проектировщик должен спроектировать, как новый слой будет использовать существующий `Operation`/`Run`/`FileObject`/`Audit`/`TechLog` контур.

### 8.1 Новые operation step codes

Нужно предложить закрытый каталог step codes для CORE-1.

Предварительный минимум:

```text
core_product_create
core_product_update
core_variant_create
core_variant_update
marketplace_listings_sync
marketplace_prices_sync
marketplace_stocks_sync
marketplace_sales_sync
marketplace_promotions_sync
marketplace_full_catalog_refresh
marketplace_listing_mapping_update
marketplace_listing_mapping_import_excel
marketplace_listing_export_excel
```

Проектировщик должен проверить, какие действия являются `Operation`, а какие обычными audit-only действиями. Не нужно искусственно превращать каждое редактирование формы в operation, если текущая архитектура проекта лучше требует audit + history без operation.

### 8.2 Совместимость со Stage 1 и Stage 2

Запрещено:

- ломать Stage 1 Excel check/process;
- менять business decision engine WB/Ozon скидок;
- подменять существующие Stage 2.1/2.2 step codes;
- менять meaning `Operation.type=check/process`;
- удалять или переписывать старые operation records;
- заставлять старые Excel-сценарии обязательно требовать внутренний товар.

Обязательно:

- добавить nullable FK из detail rows/новых rows к `MarketplaceListing`, если это безопасно;
- сохранить `product_ref` как raw reference;
- обеспечить обратную совместимость старых detail rows;
- сделать так, чтобы новые API-снимки могли ссылаться на листинг.

### 8.3 Автообновления

Полное расписание автообновления может быть future, но проектировщик должен заложить контракт:

- ручной запуск sync из UI;
- будущий автоматический запуск по расписанию;
- защита от параллельного запуска одинакового sync по одному магазину/маркетплейсу;
- использование последнего успешного снимка, если новый запуск завершился ошибкой;
- понятный статус в UI.

---

## 9. Требования к UI/UX

Проектировщик должен подготовить изменения к `docs/product/UI_SPEC.md` или отдельную спецификацию `docs/product/PRODUCT_CORE_UI_SPEC.md` с последующим подключением в `DOCUMENTATION_MAP.md`.

### 9.1 Навигация

Рекомендуемая навигация:

```text
Товары компании
  Внутренние товары
  Варианты товаров
  Сопоставление WB/Ozon
  Несопоставленные листинги

Маркетплейсы
  WB
    Товары / листинги
    Цены
    Акции
    Остатки
    Продажи
    В производство — future entry point
    Поставки — future entry point
  Ozon
    Товары / листинги
    Цены
    Акции
    Остатки
    Продажи
    В производство — future entry point
    Поставки — future entry point
```

### 9.2 Список внутренних товаров

Минимальные колонки:

- internal code / visible id;
- название;
- тип товара;
- категория;
- количество вариантов;
- количество связанных WB листингов;
- количество связанных Ozon листингов;
- статус;
- дата обновления.

Фильтры:

- тип товара;
- категория;
- статус;
- наличие связанных листингов;
- поиск по названию, internal SKU, barcode.

### 9.3 Карточка внутреннего товара

Минимальные блоки:

- основные данные;
- варианты;
- идентификаторы;
- связанные WB/Ozon листинги;
- история изменений;
- будущие разделы-заглушки: склад, производство, поставщики, BOM, упаковка.

Future-разделы должны быть явно помечены как не реализованные в CORE-1, если они отображаются в UI.

Рекомендация: не показывать пустые рабочие блоки склада, производства, поставщиков, BOM и упаковки в основном UI CORE-1. Допускаются только аккуратные future entry points или вкладки/ссылки, если они не создают впечатление реализованного функционала.

### 9.4 Список marketplace-листингов

Минимальные колонки:

- marketplace;
- магазин;
- external primary id;
- seller article;
- barcode;
- название marketplace;
- бренд;
- категория;
- listing status;
- mapping status;
- связанный internal variant;
- последняя цена;
- последний остаток;
- дата последнего успешного sync;
- источник.

Фильтры:

- marketplace;
- магазин;
- listing status;
- mapping status;
- категория;
- бренд;
- наличие остатка;
- дата обновления;
- поиск по id, артикулу, названию, barcode.

### 9.5 Карточка marketplace-листинга

Минимальные блоки:

- основные marketplace-данные;
- внешние идентификаторы;
- связанный внутренний вариант;
- последние API-снимки;
- цены;
- остатки;
- продажи/заказы за период;
- акции;
- история листинга;
- связанные операции;
- связанные файлы;
- ошибки последней синхронизации.

### 9.6 Сопоставление листинга с внутренним товаром

Минимальный workflow:

1. Пользователь открывает список несопоставленных листингов.
2. Выбирает листинг.
3. Система показывает кандидатов на внутренний товар/вариант, если они есть.
4. Пользователь может:
   - связать с существующим вариантом;
   - создать новый внутренний товар и вариант;
   - создать новый вариант у существующего товара;
   - пометить как `needs_review`;
   - оставить несопоставленным.
5. Система создаёт audit record и history record.
6. Система не изменяет старые operation rows задним числом, кроме разрешённого nullable FK enrichment, если он безопасен и не нарушает immutable-инвариант.

---

## 10. Требования к правам доступа

Проектировщик должен обновить или дополнить `docs/product/PERMISSIONS_MATRIX.md`.

### 10.1 Предварительные permission codes

```text
product_core.view
product_core.create
product_core.update
product_core.archive
product_core.export

product_variant.view
product_variant.create
product_variant.update
product_variant.archive

marketplace_listing.view
marketplace_listing.sync
marketplace_listing.export
marketplace_listing.map
marketplace_listing.unmap
marketplace_listing.archive

marketplace_snapshot.view
marketplace_snapshot.technical_view
```

Проектировщик должен привести эти к принятому style guide существующей permission matrix.

### 10.2 Object access

Правила:

- `MarketplaceListing` наследует object access от `StoreAccount`;
- пользователь без доступа к магазину не видит его листинги и snapshots;
- внутренние товары могут быть видны шире, но операции связывания с листингами должны проверять доступ к конкретному магазину;
- экспорт листингов ограничивается доступными магазинами;
- экспорт внутренних товаров должен учитывать, раскрывает ли он данные недоступных магазинов через связанные листинги.

### 10.3 Роли

Проектировщик должен предложить seed-права для существующих ролей:

- Владелец;
- Глобальный администратор;
- Локальный администратор;
- Менеджер маркетплейсов;
- Наблюдатель.

Новые производственные роли, такие как оператор вышивальной машины, упаковщик, кладовщик, дизайнер, могут быть описаны как future roles, но не должны требоваться для реализации CORE-1.

---

## 11. Требования к audit и techlog

Проектировщик должен обновить или дополнить `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`.

### 11.1 Audit actions

Минимальные audit actions:

```text
product_core.created
product_core.updated
product_core.archived
product_variant.created
product_variant.updated
product_variant.archived
marketplace_listing.synced
marketplace_listing.status_changed
marketplace_listing.mapped
marketplace_listing.unmapped
marketplace_listing.mapping_conflict_marked
marketplace_listing.exported
marketplace_listing.import_from_excel_confirmed
```

### 11.2 Techlog events

Минимальные techlog events:

```text
marketplace_sync.started
marketplace_sync.completed
marketplace_sync.completed_with_warnings
marketplace_sync.failed
marketplace_sync.partial_response
marketplace_sync.rate_limited
marketplace_sync.timeout
marketplace_sync.response_invalid
marketplace_sync.secret_redaction_violation
product_core.migration.started
product_core.migration.completed
product_core.migration.failed
```

### 11.3 Secret safety

Запрещено сохранять в UI, audit, techlog, snapshots, Excel, summary и reports:

- API tokens;
- Api-Key;
- Client-Id как технический идентификатор ограниченного отображения;
- Authorization headers;
- raw request/response с секретами;
- любые secret-like значения.

Если в snapshots хранится raw-safe payload, проектировщик должен описать redaction policy.

`Client-Id` не равен API key, но не должен выводиться в UI, logs, reports, Excel, audit или techlog без явной необходимости. Если он нужен для диагностики, проектировщик должен описать маскирование или ограничение отображения по правам.

---

## 12. Требования к Excel и экспорту

### 12.1 Excel как вход операции

Excel остаётся входом существующих сценариев и не должен автоматически создавать внутренние товары, варианты, подтверждённые связи или `ProductMappingHistory`. Существующая legacy-совместимость `MarketplaceProduct` может зеркалить product refs операций в unmatched `MarketplaceListing` compatibility records; это не считается явным импортом Excel в Product Core или workflow подтверждения связей.

### 12.2 Явный импорт из Excel

Если нужен импорт из Excel в ядро или листинги, он должен быть отдельным workflow:

```text
загрузить Excel
→ проверить строки
→ показать diff
→ показать предупреждение о влиянии на каталог
→ запросить подтверждение
→ создать operation/import run
→ записать history/audit
```

### 12.3 Экспорт

Нужно спроектировать экспорт:

- внутренних товаров;
- marketplace-листингов;
- несопоставленных листингов;
- листингов с ценами/остатками;
- mapping report.

Сохранённые шаблоны можно описать как future, если CORE-1 ограничивается базовыми выгрузками.

---

## 13. Требования к миграции

Проектировщик должен подготовить отдельный документ миграции.

### 13.1 Инвентаризация текущей модели

Проектировщик должен изучить:

```text
apps/marketplace_products/models.py
apps/marketplace_products/services.py, если есть
apps/marketplace_products/views.py, если есть
apps/operations/models.py
apps/discounts/**
apps/exports/**
apps/files/**
apps/stores/**
```

И определить:

- кто создаёт `MarketplaceProduct`;
- кто читает `MarketplaceProduct`;
- какие constraints существуют;
- какие tests затрагивают `MarketplaceProduct`;
- где `OperationDetailRow.product_ref` используется как единственный идентификатор.

### 13.2 План миграции данных

Обязательные шаги:

1. Создать новые модели или мигрировать старую модель.
2. Сохранить все текущие marketplace/store/sku/external_ids/title/barcode/status/last_values.
3. Создать `MarketplaceListing` для каждой текущей записи.
4. Установить `internal_variant_id = null`.
5. Сохранить историю появления/обновления.
6. Добавить mapping status `unmatched` для записей без внутренней связи.
7. Не удалять старые данные без reversible migration или backup plan.
8. Добавить backfill индексов/constraints.
9. Проверить Stage 1/2 операции после миграции.

Запрещено начинать реализацию миграции без:

- утверждённого migration plan;
- backup/rollback plan;
- data validation queries/checks;
- regression-проверок Stage 1 Excel;
- regression-проверок Stage 2.1 WB API;
- regression-проверок Stage 2.2 Ozon Elastic Boosting.

### 13.3 Совместимость

Если проектировщик выбирает переименование модели, он должен описать:

- migration dependency order;
- изменение imports;
- изменение admin/views/templates;
- изменение tests;
- переходный compatibility alias, если нужен;
- rollback limitations.

### 13.4 Запреты миграции

Запрещено:

- удалять существующие operation records;
- менять historical operation summaries;
- перезаписывать старые output files;
- скрыто объединять WB/Ozon товары;
- создавать внутренние товары автоматически без явного правила;
- менять старую бизнес-логику скидок.

---

## 14. Требования к тестированию и приёмке

Проектировщик должен подготовить:

```text
docs/testing/STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md
docs/testing/STAGE_3_PRODUCT_CORE_ACCEPTANCE_CHECKLISTS.md
docs/traceability/STAGE_3_PRODUCT_CORE_TRACEABILITY_MATRIX.md
```

Или аналогичные документы с именованием, согласованным с существующей структурой.

### 14.1 Минимальные тестовые группы

1. Data model tests.
2. Migration tests.
3. Permission tests.
4. UI list/card tests.
5. Mapping workflow tests.
6. API sync snapshot tests with mocked/safe data.
7. Excel import/export boundary tests.
8. Backward compatibility tests for Stage 1 Excel.
9. Backward compatibility tests for Stage 2.1 WB API.
10. Backward compatibility tests for Stage 2.2 Ozon Elastic Boosting.
11. Audit/techlog tests.
12. Secret redaction tests.

### 14.2 Приёмочные критерии

Минимальные acceptance criteria:

1. Существует внутренний каталог товаров и вариантов.
2. Существуют marketplace-листинги WB/Ozon, привязанные к магазину и маркетплейсу.
3. Один внутренний вариант может иметь несколько marketplace-листингов.
4. Один marketplace-листинг может быть временно несопоставленным.
5. Листинг можно вручную связать с внутренним вариантом.
6. Ошибочную связь можно снять с audit/history.
7. Текущий `MarketplaceProduct` мигрирован или переосмыслен без потери данных.
8. Старые Stage 1 Excel операции продолжают работать.
9. Stage 2.1 WB API не ломается.
10. Stage 2.2 Ozon Elastic Boosting не ломается.
11. API-снимки сохраняют источник, время, sync run и безопасные данные.
12. Пользователь без доступа к магазину не видит листинги этого магазина.
13. Экспорт не раскрывает недоступные магазины.
14. Excel не создаёт товары в ядре автоматически без явного режима импорта.
15. Все ручные изменения сопоставления фиксируются в audit/history.
16. Секреты API не попадают в UI, logs, audit, techlog, snapshots, Excel или reports.
17. Документация прошла аудит до реализации.

---

## 15. Требования к исполнительной проектной документации

Проектировщик должен подготовить комплект документов, который органично впишется в текущую структуру `docs/`.

### 15.1 Рекомендуемая структура новых документов

```text
docs/stages/stage-3-product-core/
  STAGE_3_PRODUCT_CORE_SCOPE.md
  STAGE_3_PRODUCT_CORE_DESIGN_PLAN.md
  STAGE_3_PRODUCT_CORE_ACCEPTANCE_TESTS.md
  STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md
  STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md

# Новые или обновлённые архитектурные документы:
docs/architecture/PRODUCT_CORE_ARCHITECTURE.md
docs/architecture/DATA_MODEL.md
docs/architecture/API_CONNECTIONS_SPEC.md
docs/architecture/AUDIT_AND_TECHLOG_SPEC.md
docs/architecture/DELETION_ARCHIVAL_POLICY.md

# Новые или обновлённые product specs:
docs/product/PRODUCT_CORE_SPEC.md
docs/product/MARKETPLACE_LISTINGS_SPEC.md
docs/product/PRODUCT_CORE_UI_SPEC.md
docs/product/PERMISSIONS_MATRIX.md
docs/product/OPERATIONS_SPEC.md

# Задачи реализации:
docs/tasks/implementation/stage-3-product-core/IMPLEMENTATION_TASKS.md
docs/tasks/implementation/stage-3-product-core/TASK-PC-001-data-model.md
docs/tasks/implementation/stage-3-product-core/TASK-PC-002-migration.md
docs/tasks/implementation/stage-3-product-core/TASK-PC-003-listings-sync-foundation.md
docs/tasks/implementation/stage-3-product-core/TASK-PC-004-ui-internal-products.md
docs/tasks/implementation/stage-3-product-core/TASK-PC-005-ui-marketplace-listings.md
docs/tasks/implementation/stage-3-product-core/TASK-PC-006-mapping-workflow.md
docs/tasks/implementation/stage-3-product-core/TASK-PC-007-permissions-audit-techlog.md
docs/tasks/implementation/stage-3-product-core/TASK-PC-008-excel-export-boundary.md
docs/tasks/implementation/stage-3-product-core/TASK-PC-009-tests-and-acceptance.md
docs/tasks/implementation/stage-3-product-core/TASK-PC-010-docs-and-runbook.md

# Testing / traceability:
docs/testing/STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md
docs/testing/STAGE_3_PRODUCT_CORE_ACCEPTANCE_CHECKLISTS.md
docs/traceability/STAGE_3_PRODUCT_CORE_TRACEABILITY_MATRIX.md

# Control docs:
docs/adr/ADR_LOG.md
docs/gaps/GAP_REGISTER.md
docs/audit/AUDIT_REPORT_STAGE_3_PRODUCT_CORE_DOCUMENTATION.md
```

Если в репозитории уже существует другой Stage 3 с утверждённым scope, проектировщик должен не конфликтовать с ним и предложить альтернативный путь, например:

```text
docs/stages/product-core-foundation/
docs/tasks/implementation/product-core-foundation/
```

Но выбранное именование должно быть единым во всех документах и добавлено в `docs/DOCUMENTATION_MAP.md`.

### 15.2 Обязательные документы результата проектировщика

Проектировщик обязан подготовить минимум:

1. `STAGE_3_PRODUCT_CORE_SCOPE.md` — границы этапа, in/out, бизнес-цели.
2. `PRODUCT_CORE_ARCHITECTURE.md` — архитектура ядра.
3. `PRODUCT_CORE_SPEC.md` — внутренняя товарная модель.
4. `MARKETPLACE_LISTINGS_SPEC.md` — внешний слой WB/Ozon.
5. `STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md` — миграция `MarketplaceProduct`.
6. `PRODUCT_CORE_UI_SPEC.md` — UI списков, карточек, сопоставления.
7. Updates to `DATA_MODEL.md` — модель данных и системные словари.
8. Updates to `PERMISSIONS_MATRIX.md` — права и роли.
9. Updates to `OPERATIONS_SPEC.md` — новые operation/sync contracts.
10. Updates to `AUDIT_AND_TECHLOG_SPEC.md` — audit/techlog events.
11. Updates to `ADR_LOG.md` — архитектурные решения.
12. Updates to `GAP_REGISTER.md` — только если есть реальные blocking gaps.
13. `IMPLEMENTATION_TASKS.md` — индекс задач реализации.
14. Task-scoped файлы задач реализации.
15. `STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md` — пакеты чтения для агентов.
16. Test protocol, acceptance checklists, traceability matrix.
17. Audit handoff package for auditor.

---

## 16. Требования к декомпозиции реализации для будущего оркестратора

Проектировщик должен подготовить такие implementation tasks, чтобы оркестратор мог выдавать их агентам по очереди или частично параллельно.

### 16.1 Общие правила задач

Каждая задача должна содержать:

```text
ID
Тип задачи
Агент
Цель
Границы задачи
Источник истины
Входные документы
Разделы ТЗ для чтения
Связанные ADR/GAP
Разрешённые файлы изменения
Запрещённые файлы изменения
Ожидаемый результат
Критерии завершённости
Обязательные проверки
Формат отчёта
Получатель результата
Нужен ли аудит
Нужны ли тесты
Нужен ли техрайтер
```

### 16.2 Рекомендуемая декомпозиция implementation tasks

#### TASK-PC-001 — Data model foundation

Агент: разработчик.  
Цель: создать модели внутреннего ядра и marketplace-листингов.  
Не должен делать: UI, API-интеграции, склад, производство.

#### TASK-PC-002 — MarketplaceProduct migration

Агент: разработчик.  
Цель: мигрировать/сопоставить текущий `MarketplaceProduct` в новый слой листингов.  
Не должен делать: автоматическое связывание WB/Ozon с внутренними товарами без утверждённого правила.

#### TASK-PC-003 — Sync run and snapshot foundation

Агент: разработчик.  
Цель: создать основу sync runs и snapshot tables/contract.  
Не должен делать: расширять WB/Ozon business API beyond approved scope.

#### TASK-PC-004 — Internal products UI

Агент: разработчик.  
Цель: список и карточка внутренних товаров/вариантов.

#### TASK-PC-005 — Marketplace listings UI

Агент: разработчик.  
Цель: список и карточка WB/Ozon листингов.

#### TASK-PC-006 — Manual mapping workflow

Агент: разработчик.  
Цель: ручная связь/снятие связи между листингом и внутренним вариантом.

#### TASK-PC-007 — Permissions, audit, techlog

Агент: разработчик.  
Цель: права, проверки доступа, audit/history, techlog.

#### TASK-PC-008 — Excel export/import boundary

Агент: разработчик.  
Цель: базовый экспорт и запрет автоматического раздувания ядра из Excel; если импорт включён, только explicit workflow.

#### TASK-PC-009 — Tests and acceptance

Агент: тестировщик.  
Цель: покрыть acceptance criteria и regression по Stage 1/2.

#### TASK-PC-010 — Documentation and runbook update

Агент: техрайтер.  
Цель: синхронизировать пользовательскую/эксплуатационную документацию после реализации.

### 16.3 Аудит задач

Каждая задача, меняющая модель данных, права, операции, audit/techlog, миграции или business logic, должна идти в аудит до merge/принятия.

---

## 17. Task-scoped reading packages

Проектировщик обязан подготовить отдельный документ с пакетами чтения для агентов.

### 17.1 Принцип

Агент читает только документы, необходимые для текущей задачи. Если агенту нужен документ вне пакета, он запрашивает его у оркестратора или фиксирует gap/need-more-context.

Запрещено:

- требовать от каждого агента перечитать всё итоговое ТЗ;
- требовать от каждого агента читать всю документацию проекта;
- давать разработчику документы по будущему складу/производству, если задача только про миграцию листингов;
- смешивать design-task и implementation-task в одном пакете.

### 17.2 Пример пакетов чтения

#### Пакет для TASK-PC-001 Data model foundation

```text
README.md
docs/DOCUMENTATION_MAP.md
docs/architecture/ARCHITECTURE.md
docs/architecture/DATA_MODEL.md
docs/architecture/PRODUCT_CORE_ARCHITECTURE.md
docs/product/PRODUCT_CORE_SPEC.md
docs/product/MARKETPLACE_LISTINGS_SPEC.md
docs/product/PERMISSIONS_MATRIX.md
docs/adr/ADR_LOG.md
docs/gaps/GAP_REGISTER.md
docs/tasks/implementation/stage-3-product-core/TASK-PC-001-data-model.md
apps/marketplace_products/models.py
apps/stores/models.py
apps/operations/models.py
```

#### Пакет для TASK-PC-002 Migration

```text
docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md
docs/architecture/DATA_MODEL.md
docs/product/MARKETPLACE_LISTINGS_SPEC.md
docs/product/OPERATIONS_SPEC.md
docs/adr/ADR_LOG.md
docs/gaps/GAP_REGISTER.md
docs/tasks/implementation/stage-3-product-core/TASK-PC-002-migration.md
apps/marketplace_products/**
apps/operations/**
apps/discounts/** relevant files only
```

#### Пакет для TASK-PC-006 Mapping workflow

```text
docs/product/PRODUCT_CORE_UI_SPEC.md
docs/product/PRODUCT_CORE_SPEC.md
docs/product/MARKETPLACE_LISTINGS_SPEC.md
docs/product/PERMISSIONS_MATRIX.md
docs/architecture/AUDIT_AND_TECHLOG_SPEC.md
docs/tasks/implementation/stage-3-product-core/TASK-PC-006-mapping-workflow.md
relevant views/forms/templates only
```

#### Пакет для аудитора документации

```text
this source TZ
docs/DOCUMENTATION_MAP.md
docs/stages/stage-3-product-core/**
docs/architecture/PRODUCT_CORE_ARCHITECTURE.md
docs/product/PRODUCT_CORE_SPEC.md
docs/product/MARKETPLACE_LISTINGS_SPEC.md
docs/product/PRODUCT_CORE_UI_SPEC.md
docs/architecture/DATA_MODEL.md
docs/product/PERMISSIONS_MATRIX.md
docs/product/OPERATIONS_SPEC.md
docs/architecture/AUDIT_AND_TECHLOG_SPEC.md
docs/adr/ADR_LOG.md
docs/gaps/GAP_REGISTER.md
docs/tasks/implementation/stage-3-product-core/**
docs/testing/STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md
docs/testing/STAGE_3_PRODUCT_CORE_ACCEPTANCE_CHECKLISTS.md
docs/traceability/STAGE_3_PRODUCT_CORE_TRACEABILITY_MATRIX.md
```

Проектировщик должен подготовить полный список пакетов, а не ограничиваться примерами.

---

## 18. Обязательный audit-gate до реализации

Перед началом реализации документацию обязательно проверяет аудитор Codex CLI.

### 18.1 Запрещено начинать реализацию, пока нет `AUDIT PASS`

Оркестратор не имеет права передавать задачи разработчику, тестировщику или техрайтеру на реализацию, пока аудитор не проверил проектную документацию и не выдал итог:

```text
AUDIT PASS
```

Статусы:

```text
AUDIT FAIL — реализация запрещена, проектировщик исправляет документацию.
AUDIT PASS WITH REMARKS — реализация запрещена, если remarks являются spec-blocking; допускается только если аудитор явно указал non-blocking remarks.
AUDIT PASS — реализация разрешена.
```

### 18.2 Что должен проверить аудитор

Аудитор должен проверить:

1. Соответствие этому ТЗ.
2. Соответствие текущей архитектуре проекта.
3. Отсутствие попытки реализовать полную ERP в CORE-1.
4. Наличие внутреннего товара как ядра.
5. Отделение marketplace-листинга от внутреннего товара.
6. Наличие связи internal variant ↔ listing.
7. Наличие плана миграции текущего `MarketplaceProduct`.
8. Наличие API snapshot/sync run contract.
9. Совместимость со Stage 1 Excel.
10. Совместимость со Stage 2.1 WB API.
11. Совместимость со Stage 2.2 Ozon API.
12. Корректность прав доступа.
13. Корректность audit/techlog.
14. Secret safety.
15. Наличие task-scoped reading packages.
16. Наличие implementation tasks.
17. Наличие testing/acceptance/traceability docs.
18. Обновление `DOCUMENTATION_MAP.md`.
19. Отсутствие незафиксированных архитектурных решений.
20. Все blocking gaps зарегистрированы в `GAP_REGISTER.md`.

### 18.3 Формат audit report

Проектировщик должен подготовить handoff-пакет для аудитора, а аудитор должен выпустить отчёт:

```text
docs/audit/AUDIT_REPORT_STAGE_3_PRODUCT_CORE_DOCUMENTATION.md
```

Минимальный формат:

```md
# Audit report: Stage 3 Product Core documentation

Проверенная область:
Проверенные файлы:
Источник требований:
Связанные ADR/GAP:

## Итог
PASS / FAIL / PASS WITH NON-BLOCKING REMARKS

## Проверка по требованиям
| Требование | Документ/раздел | Статус | Замечание |
| --- | --- | --- | --- |

## Нарушения

## Риски

## Spec-blocking вопросы

## Обязательные исправления

## Non-blocking рекомендации

## Решение
Реализация разрешена / запрещена.
```

---

## 19. Правила работы проектировщика с GAP и ADR

### 19.1 ADR

Проектировщик должен добавить ADR для всех архитектурных решений, которые меняют или уточняют текущую архитектуру:

- внутренний товар как ядро;
- marketplace listing как внешний слой;
- правило несопоставления WB/Ozon автоматически;
- миграционный подход к `MarketplaceProduct`;
- snapshot/sync run contract;
- Excel boundary.

### 19.2 GAP

GAP нужен только если проектировщик не может продолжить без решения заказчика.

Не нужно создавать GAP по вопросам, которые уже решены этим ТЗ:

- внутренний товар является ядром;
- WB/Ozon листинги не являются ядром;
- автоматическое склеивание запрещено;
- полный склад/производство/поставщики не входят в CORE-1;
- аудит документации до реализации обязателен.

GAP нужен, например, если:

- обнаружен конфликт с уже утверждённым Stage 3 в репозитории;
- текущая модель прав не позволяет безопасно показать внутренние товары без раскрытия недоступных магазинов;
- migration path технически конфликтует с уже реализованными constraints;
- невозможно сохранить совместимость Stage 1/2 без дополнительного решения.

---

## 19.3 Вопрос заказчику до финализации проектной документации

Проектировщик должен явно зафиксировать и передать оркестратору вопрос:

```text
В CORE-1 сопоставление MarketplaceListing с ProductVariant должно быть только ручным,
или разрешаем полуавтоматические кандидаты по seller_article / barcode / external identifiers
с обязательным ручным подтверждением финальной связи?
```

Рекомендация в этом ТЗ: разрешить полуавтоматические кандидаты, но финальную связь создавать только после ручного подтверждения пользователем.

Если проектировщик обнаружит дополнительные вопросы по бизнес-логике, функциональности или удобству веб-панели, он не должен решать их самостоятельно. Эти вопросы идут по маршруту:

```text
проектировщик → оркестратор → заказчик
```

---

## 20. Ограничения и запреты для проектировщика

Проектировщику запрещено:

1. Проектировать WB/Ozon карточки как ядро компании.
2. Автоматически объединять WB и Ozon товары без утверждённого правила сопоставления.
3. Расширять этап до полной ERP.
4. Убирать или ломать Stage 1 Excel-сценарии.
5. Менять бизнес-логику скидок WB/Ozon.
6. Нарушать immutable-инвариант завершённых операций.
7. Добавлять API-секреты в snapshots/audit/techlog/UI/files.
8. Давать агентам реализации слишком широкие reading packages.
9. Скрывать открытые вопросы внутри текста без GAP.
10. Начинать реализацию или формировать developer tasks как ready-to-run без обязательного audit-gate.
11. Подменять проектирование фразами “как в старой программе”.
12. Считать Excel главным источником внутреннего каталога по умолчанию.
13. Проектировать складские остатки как простое поле товара в рамках CORE-1.
14. Проектировать производственные задания как часть CORE-1, кроме future hooks.

---

## 21. Пошаговый порядок работы проектировщика

### Шаг 1. Изучить входной контекст

Прочитать документы из раздела 3 этого ТЗ. Составить короткое internal design note:

```text
что уже есть;
какие документы нужно обновить;
какие места кода зависят от MarketplaceProduct;
есть ли конфликт с текущей stage-нумерацией;
есть ли blocking gaps.
```

### Шаг 2. Зафиксировать stage naming

Выбрать итоговое именование этапа:

```text
stage-3-product-core
```

или альтернативу, если есть конфликт.

Обновить `DOCUMENTATION_MAP.md`.

### Шаг 3. Подготовить scope-документ этапа

Создать `STAGE_3_PRODUCT_CORE_SCOPE.md`:

- цель;
- in/out;
- бизнес-ограничения;
- архитектурные границы;
- зависимости от Stage 1/2;
- запреты;
- acceptance overview.

### Шаг 4. Подготовить архитектурный документ

Создать `PRODUCT_CORE_ARCHITECTURE.md`:

- доменная модель;
- границы модулей;
- внутреннее ядро;
- внешний listing layer;
- sync/snapshot layer;
- future hooks для склада/производства/поставщиков;
- зависимости между apps;
- migration strategy overview.

### Шаг 5. Подготовить product specs

Создать/обновить:

```text
PRODUCT_CORE_SPEC.md
MARKETPLACE_LISTINGS_SPEC.md
PRODUCT_CORE_UI_SPEC.md
```

### Шаг 6. Обновить data model

Обновить `DATA_MODEL.md`:

- новые сущности;
- связи;
- индексы;
- constraints;
- системные словари;
- snapshot contracts;
- legacy compatibility.

### Шаг 7. Подготовить migration plan

Создать `STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md`:

- инвентаризация текущих зависимостей;
- варианты миграции;
- выбранный вариант;
- последовательность миграций;
- rollback/backup considerations;
- regression impact;
- data validation queries/checks.

### Шаг 8. Обновить операции, права, audit/techlog

Обновить:

```text
docs/product/OPERATIONS_SPEC.md
docs/product/PERMISSIONS_MATRIX.md
docs/architecture/AUDIT_AND_TECHLOG_SPEC.md
```

### Шаг 9. Подготовить ADR/GAP

Добавить ADR. Добавить GAP только при реальной блокировке.

### Шаг 10. Подготовить task-scoped reading packages

Создать `STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`.

### Шаг 11. Подготовить implementation tasks

Создать индекс и task files.

Каждая задача должна быть независимой настолько, насколько возможно, и пригодной для выдачи конкретному агенту.

### Шаг 12. Подготовить testing/acceptance/traceability

Создать:

```text
STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md
STAGE_3_PRODUCT_CORE_ACCEPTANCE_CHECKLISTS.md
STAGE_3_PRODUCT_CORE_TRACEABILITY_MATRIX.md
```

### Шаг 13. Подготовить handoff в аудит

Создать audit handoff:

```text
docs/audit/HANDOFF_STAGE_3_PRODUCT_CORE_DOCUMENTATION_TO_AUDITOR.md
```

В handoff включить:

- список документов;
- что проверять;
- known risks;
- known gaps;
- spec-blocking вопросы;
- требование выдать PASS/FAIL.

### Шаг 14. Передать документацию аудитору

После подготовки проектировщик не должен передавать задачи разработчику. Только аудитору.

### Шаг 15. Исправить замечания аудитора

Если аудитор выдал `FAIL`, проектировщик исправляет документацию и снова передаёт на аудит.

### Шаг 16. Завершить только после `AUDIT PASS`

Результат проектировщика считается завершённым только если:

- все обязательные документы подготовлены;
- audit report существует;
- audit result = `PASS` или `PASS WITH NON-BLOCKING REMARKS`;
- spec-blocking remarks отсутствуют;
- `IMPLEMENTATION_TASKS.md` готов для оркестратора.

---

## 22. Критерии готовности результата проектировщика

Работа проектировщика считается выполненной, если:

1. Подготовлен полный комплект документов из раздела 15.
2. Документация встроена в `DOCUMENTATION_MAP.md`.
3. Архитектура фиксирует внутренний товар как ядро.
4. Marketplace listing отделён от внутреннего товара.
5. Связь internal variant ↔ listing спроектирована.
6. API sync/snapshot layer спроектирован.
7. Миграция текущего `MarketplaceProduct` описана.
8. Старые Stage 1/2 сценарии защищены от поломки.
9. Excel boundary описан.
10. Права доступа описаны.
11. Audit/techlog описаны.
12. Secret safety описана.
13. Реализация декомпозирована на task-scoped задачи.
14. Для каждой задачи указаны reading packages.
15. Аудиторская проверка документации проведена.
16. Получен `AUDIT PASS` до реализации.
17. Все blocking gaps либо отсутствуют, либо явно зарегистрированы и не скрыты.

---

## 23. Итоговая формула этапа

Этот этап должен подготовить проект к дальнейшему росту:

```text
Не ERP целиком.
Не склад целиком.
Не производство целиком.
Не поставщики целиком.

А минимальный правильный фундамент:

InternalProduct / ProductVariant
+ MarketplaceListing WB/Ozon
+ связь между ними
+ API sync/snapshot foundation
+ миграция текущего MarketplaceProduct
+ UI и права для просмотра/сопоставления
+ audit/techlog
+ task-scoped документация для Codex CLI agents
+ обязательный audit-gate перед реализацией.
```

Именно этот фундамент должен стать новым ядром дальнейшего развития `promo_v2`.
