# TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md

Статус: ТЗ заказчика для проектировщика Codex CLI
Назначение: подготовка исполнительной проектной документации следующего этапа
Этап: Stage 3 / CORE-2 — Product Core Integration with WB/Ozon Operations
Тип документа: design task / project documentation brief
Реализация по этому документу: запрещена
Реализация допускается только после подготовки проектной документации, аудита документации и `AUDIT PASS`
Рекомендуемый путь в проекте: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md`

---

## 1. Краткий вывод для проектировщика

CORE-1 создал фундамент Product Core:

```text
InternalProduct / ProductVariant
MarketplaceListing
Manual mapping
SyncRun/Snapshot foundation
Legacy MarketplaceProduct compatibility
```

CORE-2 должен сделать следующий безопасный шаг: связать Product Core с реальными рабочими сценариями WB/Ozon и существующими операциями.

Главная цель CORE-2:

```text
WB/Ozon API + Excel/API operations
        ↓
MarketplaceListing
        ↓
ProductVariant / InternalProduct
        ↓
Snapshots / exports / operation links
```

CORE-2 не должен начинать склад, производство, поставщиков, BOM, упаковку, этикетки или машинное зрение. Эти контуры появятся позже и должны опираться на Product Core после его интеграции с marketplace-операциями.

---

## 2. Обязательное предварительное условие

До начала проектирования CORE-2 должен быть выполнен и принят release validation CORE-1:

```text
docs/tasks/validation/stage-3-product-core/TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md
docs/reports/CORE_1_RELEASE_VALIDATION_REPORT.md
docs/audit/AUDIT_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md
```

CORE-2 можно проектировать только если:

```text
CORE-1 RELEASE VALIDATION: PASS
или
CORE-1 RELEASE VALIDATION: PASS WITH NOTES без blocking defects
```

Если CORE-1 validation имеет `FAIL`, проектировщик не должен готовить исполнительную документацию CORE-2. Сначала должны быть закрыты blocking defects.

---

## 3. Размещение в проекте

### 3.1. Входное ТЗ

```text
docs/tasks/design/product-core/
  TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md
```

Этот путь выбран потому, что CORE-1 design TZ уже лежит в `docs/tasks/design/product-core/`.

### 3.2. Исполнительная документация, которую должен подготовить проектировщик

```text
docs/stages/stage-3-product-core/core-2/
  CORE_2_SCOPE.md
  CORE_2_ARCHITECTURE.md
  CORE_2_DATA_FLOW.md
  CORE_2_MODEL_AND_MIGRATION_PLAN.md
  CORE_2_API_SYNC_SPEC.md
  CORE_2_OPERATION_LINKING_SPEC.md
  CORE_2_MAPPING_RULES_SPEC.md
  CORE_2_SNAPSHOT_FILLING_SPEC.md
  CORE_2_EXCEL_EXPORT_SPEC.md
  CORE_2_UI_UX_SPEC.md
  CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md
  CORE_2_TEST_PLAN.md
  CORE_2_ACCEPTANCE_CHECKLIST.md
  CORE_2_AGENT_TASKS.md
  CORE_2_READING_PACKAGES.md
  CORE_2_ROLLOUT_RUNBOOK.md
```

Если проектировщик предложит иной набор файлов, он должен явно показать, как новый набор покрывает все разделы этого ТЗ.

### 3.3. Документы, которые должны быть обновлены после утверждения документации

```text
docs/DOCUMENTATION_MAP.md
docs/roles/READING_PACKAGES.md
docs/adr/ADR_LOG.md
docs/gaps/GAP_REGISTER.md
docs/project/CURRENT_STATUS.md
```

Если какого-то документа нет в репозитории, проектировщик не должен домысливать его содержимое. Нужно открыть documentation GAP и предложить создать/не создавать документ.

---

## 4. Задача проектировщика

Проектировщик Codex CLI должен не писать код, а подготовить исполнительную проектную документацию для оркестратора и агентов Codex CLI.

Документация должна быть:

1. самодостаточной;
2. трассируемой к этому ТЗ;
3. декомпозированной на task-scoped implementation tasks;
4. совместимой с текущей структурой `promo_v2`;
5. понятной разработчику, аудитору, тестировщику и техрайтеру;
6. пригодной для работы оркестратора Codex CLI;
7. безопасной для Stage 1/2 regression;
8. заблокированной для реализации до документационного `AUDIT PASS`.

---

## 5. Контекст проекта

`promo_v2` — корпоративный кабинет для работы с WB/Ozon магазинами, скидками, ценами, товарами, операциями, файлами, audit/techlog и дальнейшим развитием в сторону склада, производства, поставщиков и упаковки.

Реализованные направления:

- Stage 1 WB/Ozon Excel workflows;
- Stage 2.1 WB API flow;
- Stage 2.2 Ozon Elastic API flow;
- Stage 3.0 / CORE-1 Product Core Foundation;
- users/roles/permissions/object access;
- stores/cabinets/API connection records;
- operation lifecycle;
- files;
- audit trail;
- techlog;
- Product Core routes and exports.

Главная архитектурная идея:

```text
InternalProduct / ProductVariant = ядро компании
MarketplaceListing = внешний листинг WB/Ozon в конкретном магазине
WB/Ozon stores = каналы продаж
Excel = операционный формат, не основной источник истины
API WB/Ozon = источник внешних marketplace-данных
```

---

## 6. Цель CORE-2

Цель CORE-2 — перевести существующие и ближайшие marketplace-сценарии на Product Core так, чтобы дальнейшие этапы строились вокруг `InternalProduct` / `ProductVariant`, а не вокруг legacy `MarketplaceProduct` или разовых Excel-строк.

CORE-2 должен обеспечить:

1. синхронизацию WB/Ozon listings в `MarketplaceListing`;
2. связь listings с `ProductVariant` по утверждённым правилам;
3. поддержку унифицированного артикула как business key;
4. конфликтный контур для неоднозначных артикулов/дублей;
5. nullable FK-связь operation rows с `MarketplaceListing`;
6. заполнение snapshot-слоя из уже существующих flows;
7. exports из Product Core как рабочий источник для следующих этапов;
8. сохранение Stage 1/2 backward compatibility.

---

## 7. Что входит в CORE-2

### 7.1. Marketplace listing sync integration

Проектировщик должен описать, как WB/Ozon данные попадают в `MarketplaceListing`.

Минимально:

- source marketplace;
- store/account;
- external primary id;
- seller article;
- barcode;
- title;
- brand/category if available;
- listing status;
- first seen / last seen / last successful sync;
- source sync run;
- safe current cache.

Важно:

```text
CORE-2 может использовать только утверждённые API-источники.
Если нужен новый WB/Ozon API endpoint, проектировщик должен явно описать endpoint, ограничения, права, rate limits, error handling и открыть GAP, если данных недостаточно.
```

### 7.2. ProductVariant linkage by normalized article

Проектировщик должен описать правила связи:

```text
MarketplaceListing.seller_article / vendorCode / offer_id
        ↓
ProductVariant.internal_sku
```

Базовое допущение:

```text
Вне promo_v2 может существовать отдельная программа нормализации артикулов.
Она меняет артикулы в WB/Ozon на единые внутренние артикулы.
promo_v2 не реализует машинное зрение и не меняет vendorCode/offer_id в CORE-2.
promo_v2 получает уже унифицированные seller_article / vendorCode / offer_id через API маркетплейсов.
```

Проектировщик должен предложить точные правила:

- когда listing можно автоматически связать с existing `ProductVariant`;
- когда нужно создать draft/imported `ProductVariant`;
- когда нужно оставить listing `unmatched`;
- когда нужно выставить `needs_review`;
- когда нужно выставить `conflict`;
- когда требуется ручное подтверждение.

Рекомендуемый принцип:

```text
Exact normalized article match can create or suggest deterministic linkage only under approved rules.
Fuzzy/title/image matching is out of scope.
Conflict cases never auto-confirm.
```

### 7.3. ProductVariant auto-create policy

Проектировщик должен вынести на решение заказчика и/или ADR вопрос:

```text
Создавать ли ProductVariant автоматически по новому унифицированному seller_article?
```

Варианты:

- A: Не создавать автоматически. Только unmatched listing + manual create/map.
- B: Создавать `ProductVariant` в статусе `imported/draft` по точному normalized article и связывать listing при отсутствии конфликтов.
- C: Создавать активный `ProductVariant` и confirmed mapping автоматически.

Рекомендация для CORE-2: **B**, но только при строгих условиях:

1. seller article соответствует формату internal_sku;
2. в системе нет другого `ProductVariant` с конфликтующим sku;
3. listing не конфликтует с уже существующим mapping;
4. источник — marketplace API sync, не Excel;
5. действие фиксируется в audit/history;
6. есть отчёт по auto-created draft/imported variants;
7. пользователь может review/confirm/archive.

Вариант C не рекомендуется для CORE-2.

### 7.4. OperationDetailRow -> MarketplaceListing

Проектировщик должен описать nullable enrichment:

```text
OperationDetailRow.marketplace_listing_id nullable
```

Требования:

1. `product_ref` остаётся raw historical reference;
2. FK добавляется только если match deterministic and safe;
3. FK enrichment не меняет старые summaries/results/files/reason codes;
4. FK можно очистить без потери исторического `product_ref`;
5. старые Stage 1/2 операции остаются читаемыми;
6. новые операции по возможности сразу пишут FK.

Проектировщик должен указать:

- какие операции получают FK в CORE-2;
- какие операции остаются только с `product_ref`;
- как выполняется backfill FK для старых rows;
- как логируются конфликты;
- как проверяется regression.

### 7.5. Snapshot filling

CORE-1 создал foundation. CORE-2 должен описать заполнение snapshot-слоя из существующих flows.

Минимально:

- `PriceSnapshot`;
- `StockSnapshot`, если данные доступны;
- `SalesPeriodSnapshot`, если данные доступны;
- `PromotionSnapshot`, если данные уже есть в Stage 2.1/2.2 или явно включены в задачу.

Ограничения:

1. CORE-2 не обязан реализовать все API акций WB/Ozon.
2. `PromotionSnapshot` в CORE-2 — это contract/foundation + заполнение только из уже существующих approved flows или явно включённых endpoints.
3. Sales, buyouts и returns по WB/Ozon могут различаться по смыслу.
4. Поля `sales_qty`, `buyout_qty`, `return_qty` должны быть nullable, если источник не даёт точного показателя.
5. Формулы продаж/выкупов/возвратов для расчёта потребности не входят в CORE-2 без отдельной спецификации.

### 7.6. Excel/export integration

CORE-2 должен сделать Product Core exports практически применимыми для дальнейших этапов, но не менять Excel business logic Stage 1 без отдельного решения.

Проектировщик должен описать:

- какие данные можно выгружать из `ProductVariant`;
- какие данные можно выгружать из `MarketplaceListing`;
- как фильтруются exports по store/marketplace/status;
- как exports уважают object access;
- как в exports не попадают secrets;
- как сохранять compatibility со Stage 1 Excel flows.

Excel boundary:

```text
Excel remains operational input/output.
Excel does not automatically create InternalProduct/ProductVariant or confirmed mappings unless a future explicit audited import mode is approved.
```

### 7.7. UI integration

Проектировщик должен описать UI только для реализуемых CORE-2 функций:

- listing sync status;
- linked/unlinked listings;
- imported/draft variants;
- mapping conflicts;
- operation row link visibility;
- snapshot/latest values;
- exports;
- review pages for unmatched/needs_review/conflict.

Запрещено показывать как рабочие функции:

- склад;
- производство;
- поставщиков;
- BOM;
- упаковку;
- этикетки;
- машинное зрение;
- массовое изменение vendorCode/offer_id.

Можно показать будущие разделы только как disabled/future entry points, если это соответствует UX проекта.

### 7.8. Permissions, audit, techlog

Проектировщик должен описать:

- права на sync;
- права на view listings;
- права на mapping;
- права на auto-created/draft variants review;
- права на exports;
- store-scoped object access;
- audit actions;
- techlog events;
- secret redaction.

Минимальные audit events:

```text
listing synced
variant auto-created as draft/imported
listing linked to variant
listing unlinked from variant
mapping conflict detected
operation row enriched with listing FK
export generated
sync failed
snapshot write failed
```

Минимальные techlog events:

```text
api sync error
snapshot write error
mapping conflict
backfill/enrichment error
secret redaction guard triggered
```

### 7.9. Regression and compatibility

CORE-2 не принимается без regression:

- Stage 1 WB Excel;
- Stage 1 Ozon Excel;
- Stage 2.1 WB API;
- Stage 2.2 Ozon Elastic API;
- Product Core UI;
- Product Core permissions;
- Product Core exports;
- legacy `MarketplaceProduct` compatibility.

---

## 8. Что не входит в CORE-2

Запрещено включать в CORE-2:

1. складской ledger;
2. производство;
3. поставщиков;
4. закупки;
5. BOM в промышленном виде;
6. упаковку;
7. этикетки;
8. расчёт потребности в производство;
9. машинное зрение;
10. внешнюю программу нормализации артикулов;
11. автоматическое изменение vendorCode/offer_id в WB/Ozon;
12. новые скидочные бизнес-формулы;
13. автоматическое объединение товаров по fuzzy/title/image matching;
14. удаление legacy `MarketplaceProduct`;
15. переписывание historical operation results.

Если проектировщик считает, что какой-то пункт нужно включить, он обязан открыть GAP и запросить решение заказчика. Нельзя расширять scope молча.

---

## 9. Архитектурные решения, которые нужно зафиксировать

Проектировщик должен подготовить или обновить ADR по следующим темам.

### 9.1. ADR: CORE-2 Product Core Integration Boundary

Фиксирует:

```text
CORE-2 integrates Product Core with WB/Ozon operations.
CORE-2 does not implement ERP modules.
```

### 9.2. ADR: Normalized Article As Business Key

Фиксирует:

```text
internal_sku = business key company side.
seller_article/vendorCode/offer_id can be normalized to internal_sku.
external marketplace ids remain technical source keys.
```

Нельзя считать один артикул единственным техническим ключом.

### 9.3. ADR: OperationDetailRow FK Enrichment

Фиксирует:

```text
product_ref remains immutable raw historical reference.
marketplace_listing_id is nullable enrichment.
```

### 9.4. ADR: Auto-created ProductVariant Policy

Фиксирует выбранный вариант A/B/C.

### 9.5. ADR: Snapshot Semantics

Фиксирует:

- какие snapshot types заполняются в CORE-2;
- какие остаются foundation-only;
- какие поля nullable;
- где нужны будущие formula specs.

---

## 10. GAP-вопросы, которые проектировщик обязан проверить

Если ответы уже есть в документации, проектировщик должен сослаться на них. Если нет — открыть GAP.

### GAP-CORE2-001: ProductVariant auto-create mode

Нужно ли CORE-2 создавать draft/imported ProductVariant по unified seller_article?

Рекомендация: B — создавать draft/imported при строгих условиях.

### GAP-CORE2-002: Источники WB/Ozon listings

Какие API endpoints утверждены для получения полного каталога/listings в CORE-2?

Проектировщик не должен домысливать endpoint.

### GAP-CORE2-003: OperationDetailRow enrichment scope

Какие operation types/step_codes обогащаются FK в CORE-2?

### GAP-CORE2-004: Snapshot scope

Какие snapshot types реально заполняются в CORE-2, а какие остаются contract/foundation?

### GAP-CORE2-005: External normalization mapping import

Нужен ли импорт mapping-файла из внешней программы нормализации артикулов в CORE-2?

Варианты:

- A: Нет, promo_v2 получает нормализованные артикулы только через WB/Ozon API.
- B: Да, добавить read-only import mapping report.
- C: Да, добавить полноценный mapping import workflow с audit.

Рекомендация для CORE-2: A или B. C лучше вынести отдельно.

---

## 11. Требования к исполнительной документации

Каждый документ должен быть пригоден для работы оркестратора и агентов.

### 11.1. `CORE_2_SCOPE.md`

Должен содержать:

- цель;
- входит;
- не входит;
- protected invariants;
- dependencies;
- acceptance overview;
- links to ADR/GAP.

### 11.2. `CORE_2_ARCHITECTURE.md`

Должен содержать:

- целевую схему;
- связи моделей;
- sequence/data flow;
- source of truth matrix;
- boundaries with Stage 1/2;
- boundaries with future ERP.

### 11.3. `CORE_2_DATA_FLOW.md`

Должен описать:

```text
WB/Ozon API -> sync run -> listing -> variant/mapping -> snapshots -> operation links -> export/UI
```

Для каждого flow:

- input;
- processing;
- output;
- audit;
- error handling;
- retry/partial failure;
- secrets redaction.

### 11.4. `CORE_2_MODEL_AND_MIGRATION_PLAN.md`

Должен описать:

- model changes;
- nullable FK changes;
- data migrations;
- backfill/re-run safety;
- rollback;
- backup;
- validation queries;
- non-destructive constraints.

### 11.5. `CORE_2_API_SYNC_SPEC.md`

Должен описать:

- endpoints;
- request/response fields;
- pagination;
- rate limits if known;
- permissions;
- token handling;
- retry/backoff;
- partial failures;
- sync run statuses;
- mapping to models;
- tests/mocks.

### 11.6. `CORE_2_OPERATION_LINKING_SPEC.md`

Должен описать:

- how operations relate to listings;
- FK enrichment rules;
- operation immutability;
- old rows;
- new rows;
- conflict logging;
- UI/report effect.

### 11.7. `CORE_2_MAPPING_RULES_SPEC.md`

Должен описать:

- exact normalized article matching;
- matching by external ids;
- barcode role;
- conflict rules;
- manual review;
- auto-created draft/imported variant policy;
- prohibited fuzzy/title/image matching.

### 11.8. `CORE_2_SNAPSHOT_FILLING_SPEC.md`

Должен описать:

- snapshot types;
- source operations;
- source sync runs;
- latest cache;
- immutable history;
- nullable fields;
- marketplace-specific semantics.

### 11.9. `CORE_2_EXCEL_EXPORT_SPEC.md`

Должен описать:

- exports;
- columns;
- filters;
- permissions;
- secret redaction;
- compatibility with current Excel flows.

### 11.10. `CORE_2_UI_UX_SPEC.md`

Должен описать:

- routes/pages;
- lists/cards;
- filters;
- statuses;
- mapping review;
- conflict pages;
- future-disabled blocks;
- error messages.

### 11.11. `CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md`

Должен описать:

- permissions;
- object access;
- audit actions;
- techlog events;
- redaction;
- security tests.

### 11.12. `CORE_2_TEST_PLAN.md`

Должен описать:

- unit tests;
- integration tests;
- migration tests;
- permissions tests;
- UI tests;
- export tests;
- API mock tests;
- regression Stage 1/2;
- secrets tests.

### 11.13. `CORE_2_ACCEPTANCE_CHECKLIST.md`

Должен иметь PASS/FAIL критерии по всем блокам.

### 11.14. `CORE_2_AGENT_TASKS.md`

Должен декомпозировать реализацию на task-scoped задачи.

Каждая задача должна иметь:

- ID;
- role;
- goal;
- input docs;
- files allowed/expected;
- prohibited changes;
- implementation steps;
- tests;
- audit criteria;
- handoff.

### 11.15. `CORE_2_READING_PACKAGES.md`

Должен указать, что читает каждый агент по каждой задаче. Нельзя заставлять агента читать весь проект без необходимости.

### 11.16. `CORE_2_ROLLOUT_RUNBOOK.md`

Должен описать:

- backup;
- migration;
- validation commands;
- smoke checks;
- rollback;
- post-deploy checks;
- release report requirements.

---

## 12. Предварительная декомпозиция реализации для проектировщика

Проектировщик может изменить декомпозицию, но должен покрыть эти блоки.

### TASK-PC2-001 — Data model and migration design

Содержит:

- nullable FK `OperationDetailRow.marketplace_listing_id`;
- safe migration;
- validation helpers;
- no legacy deletion.

### TASK-PC2-002 — Marketplace listing sync integration

Содержит:

- WB/Ozon listing sync;
- sync runs;
- current cache;
- API source mapping;
- error handling.

### TASK-PC2-003 — Normalized article linkage

Содержит:

- exact `seller_article -> internal_sku` logic;
- draft/imported ProductVariant policy;
- conflicts;
- audit/history.

### TASK-PC2-004 — Operation row enrichment

Содержит:

- new operation rows write FK where possible;
- backfill old rows if safe;
- preserve `product_ref`;
- tests.

### TASK-PC2-005 — Snapshot filling

Содержит:

- price/stock/sales/promotion snapshot filling from approved flows;
- nullable marketplace-specific fields;
- source run/operation.

### TASK-PC2-006 — Product Core UI integration

Содержит:

- sync status;
- linked/unlinked;
- conflicts;
- operation links;
- snapshots;
- exports entry points.

### TASK-PC2-007 — Permissions, audit, techlog, redaction

Содержит:

- object access;
- export access;
- audit;
- techlog;
- secret redaction tests.

### TASK-PC2-008 — Regression and acceptance tests

Содержит:

- Stage 1/2 regression;
- Product Core tests;
- migration tests;
- security tests.

### TASK-PC2-009 — Documentation and runbook update

Содержит:

- README/map/status updates;
- release runbook;
- final implementation report.

---

## 13. Agent model for future implementation

Проектировщик должен адаптировать документацию под такую цепочку:

```text
Orchestrator Codex CLI
  -> Designer Codex CLI
  -> Auditor Codex CLI
  -> Developer Codex CLI
  -> Tester Codex CLI
  -> Auditor Codex CLI
  -> Tech Writer Codex CLI
```

### 13.1. Design phase

```text
Designer prepares docs.
Auditor checks docs.
Designer fixes docs.
Auditor issues AUDIT PASS.
```

Implementation is forbidden before documentation `AUDIT PASS`.

### 13.2. Implementation phase

```text
Orchestrator assigns task-scoped task.
Developer reads only task package.
Developer implements.
Tester runs task tests.
Auditor verifies implementation.
Tech writer updates docs/report.
```

### 13.3. Agent reading rule

Каждый агент должен читать только:

1. `AGENTS.md`;
2. `PROJECT_NAVIGATOR.md` / `DOCUMENTATION_MAP.md`, если требуется навигация;
3. task file;
4. task-scoped reading package;
5. релевантные specs;
6. релевантные tests;
7. релевантные ADR/GAP.

Полное исходное ТЗ читается только проектировщиком и аудитором документации или по прямому указанию оркестратора.

---

## 14. Documentation audit gate

Проектировщик должен включить в комплект документации явный audit-gate.

До реализации аудитор обязан проверить:

1. scope полно и непротиворечиво описан;
2. non-scope явно защищён;
3. Stage 1/2 regressions защищены;
4. legacy `MarketplaceProduct` защищён;
5. `product_ref` immutability защищена;
6. Product Core source-of-truth описан;
7. API endpoints не домыслены;
8. open questions вынесены в GAP;
9. permissions/audit/techlog описаны;
10. secret redaction описана;
11. task-scoped packages есть;
12. acceptance checklist есть;
13. rollout/backup/rollback есть.

Реализация разрешена только после:

```text
AUDIT PASS
```

Если аудитор выдаёт `AUDIT FAIL`, проектировщик исправляет документацию. Оркестратор не запускает разработчика.

---

## 15. Acceptance criteria для проектной документации

Документация CORE-2 считается готовой только если:

1. есть полный комплект документов из раздела 3.2 или эквивалент с покрытием;
2. каждый документ имеет назначение, scope, non-scope, inputs/outputs;
3. task decomposition пригодна для Codex CLI agents;
4. reading packages ограничивают контекст для каждого агента;
5. есть migration/backup/rollback план;
6. есть regression requirements Stage 1/2;
7. есть rules for `OperationDetailRow.marketplace_listing_id`;
8. есть mapping rules by normalized article;
9. есть conflict rules;
10. есть snapshot semantics;
11. есть UI/permissions/export/audit/techlog specs;
12. secrets handling описан;
13. gaps/ADR обновлены;
14. acceptance checklist есть;
15. auditor issued `AUDIT PASS`.

---

## 16. Что должен вернуть проектировщик

Проектировщик должен вернуть:

1. список созданных/изменённых документов;
2. краткий executive summary;
3. open GAP list;
4. ADR list;
5. task decomposition;
6. reading packages;
7. acceptance checklist;
8. self-check против этого ТЗ.

Формат handoff:

```md
# CORE-2 Design Handoff

## Created / Updated Docs

## Scope Summary

## Non-Scope Protected

## ADR

## GAP

## Implementation Task Index

## Reading Packages

## Acceptance Checklist

## Known Risks

## Ready For Audit

Yes/No
```

---

## 17. Orchestrator opening prompt

```text
Ты — оркестратор Codex CLI проекта promo_v2.

Текущая задача: подготовить исполнительную проектную документацию для Stage 3 / CORE-2 — Product Core Integration with WB/Ozon Operations.

Входное ТЗ:
docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md

Предварительное условие:
CORE-1 Release Validation должен иметь PASS или PASS WITH NOTES без blocking defects.

Назначь проектировщику task-scoped design package. Проектировщик должен подготовить комплект документов в:
docs/stages/stage-3-product-core/core-2/

Проектировщик не пишет production code. После подготовки документации назначь аудитора документации. Если аудит FAIL, верни документацию проектировщику. Реализация CORE-2 запрещена до AUDIT PASS.

Особые ограничения:
- не начинать склад, производство, поставщиков, BOM, упаковку, этикетки;
- не включать машинное зрение;
- не менять vendorCode/offer_id через WB/Ozon API;
- не удалять legacy MarketplaceProduct;
- не ломать Stage 1/2;
- не считать Excel источником истины;
- не создавать confirmed mapping по fuzzy/title/image logic;
- каждый агент реализации позже должен читать только task-scoped package.
```

---

## 18. Краткое резюме для заказчика

Этот документ запускает не разработку, а проектирование CORE-2.

CORE-2 нужен, чтобы:

```text
закрепить Product Core как рабочую основу для WB/Ozon операций,
а не оставить его отдельным справочником рядом со старыми Excel/API процессами.
```

После CORE-2 можно будет безопасно проектировать:

- склад;
- производство;
- поставщиков;
- закупки;
- упаковку;
- этикетки;
- потребность.

Без CORE-2 эти будущие модули рискуют снова начать строиться от marketplace-товаров или Excel-строк, а не от внутреннего товара компании.
