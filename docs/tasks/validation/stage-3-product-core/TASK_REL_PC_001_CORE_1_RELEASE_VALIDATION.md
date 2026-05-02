# TASK-REL-PC-001 — Stage 3 CORE-1 Release Validation

Статус: задача на release validation / acceptance gate
Этап: Stage 3.0 / CORE-1 Product Core Foundation
Тип документа: входная задача для оркестратора Codex CLI
Новая функциональность: запрещена
Реализация: запрещена, кроме отдельных bugfix-задач при найденных дефектах
Рекомендуемый путь в проекте: `docs/tasks/validation/stage-3-product-core/TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md`

---

## 1. Назначение

Документ задаёт обязательную проверку уже реализованного CORE-1 на staging или production-like базе перед переходом к CORE-2.

Цель проверки — подтвердить, что CORE-1:

1. корректно применяет миграции;
2. безопасно выполняет backfill `MarketplaceProduct -> MarketplaceListing`;
3. не ломает Stage 1 Excel-сценарии;
4. не ломает Stage 2.1 WB API-сценарии;
5. не ломает Stage 2.2 Ozon Elastic API-сценарии;
6. соблюдает object access по магазинам;
7. не раскрывает секреты в UI, logs, audit, techlog, exports и reports;
8. может быть принят как стабильная база для следующего этапа.

Результат задачи:

```text
CORE-1 RELEASE VALIDATION: PASS / PASS WITH NOTES / FAIL
```

---

## 2. Размещение в проекте

### 2.1. Сам task-документ

```text
docs/tasks/validation/stage-3-product-core/
  TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md
```

Если `docs/tasks/validation/` ещё нет, её нужно создать. Это отдельный тип задач: не `design`, не `implementation`, а `validation/release`.

### 2.2. Документы, которые должны появиться после выполнения

```text
docs/testing/
  TEST_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md

docs/audit/
  AUDIT_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md

docs/reports/
  CORE_1_RELEASE_VALIDATION_REPORT.md
```

### 2.3. Документы, которые может потребоваться обновить после PASS

```text
README.md
docs/DOCUMENTATION_MAP.md
docs/project/CURRENT_STATUS.md
docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md
docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_DESIGN_PLAN.md
```

Обновлять их должен техрайтер после validation/audit результата.

---

## 3. Контекст CORE-1

CORE-1 добавил фундамент Product Core:

- `InternalProduct`;
- `ProductVariant`;
- `ProductCategory`;
- `ProductIdentifier`;
- `MarketplaceListing`;
- `MarketplaceSyncRun`;
- snapshot foundation для prices/stocks/sales/promotions;
- ручное сопоставление listing -> variant;
- non-authoritative candidate suggestions;
- Product Core UI routes;
- CSV exports;
- Product Core permissions;
- audit/history/techlog events;
- legacy compatibility с `MarketplaceProduct`;
- backfill `MarketplaceProduct -> MarketplaceListing`.

CORE-1 не заменяет Stage 1/2 и не является полной ERP-системой.

---

## 4. Protected invariants

Эти правила не должны быть нарушены в ходе validation:

1. `MarketplaceProduct` нельзя удалять, чистить, переименовывать или заменять без отдельного audited migration/removal plan.
2. `OperationDetailRow.product_ref` остаётся историческим raw reference и не переписывается.
3. Stage 1 Excel workflows остаются штатным режимом.
4. Stage 2.1 WB API flow не меняет бизнес-логику.
5. Stage 2.2 Ozon Elastic API flow не меняет бизнес-логику.
6. Excel не создаёт `InternalProduct` / `ProductVariant` и не создаёт confirmed mappings.
7. Candidate suggestions не создают confirmed mapping автоматически.
8. Confirmed mapping создаётся только явным действием пользователя с правом mapping.
9. API secrets/tokens/protected secret refs не попадают в UI/logs/audit/techlog/reports/exports.
10. Client-Id не считается API key, но не должен выводиться без необходимости в пользовательские отчёты и публичные логи.
11. Будущие блоки склада, производства, поставщиков, BOM, упаковки и этикеток не должны выглядеть в UI как реализованные рабочие функции.

---

## 5. Роли агентов

### 5.1. Orchestrator Codex CLI

Отвечает за:

- выдачу задачи тестировщику;
- запрет начала CORE-2 до validation result;
- контроль task-scoped reading packages;
- сбор отчётов тестировщика, аудитора и техрайтера;
- создание bugfix-задач разработчику только при найденных дефектах;
- финальное решение, можно ли переходить к CORE-2 design.

Оркестратор не должен давать разработчику задачу на новую функциональность в рамках TASK-REL-PC-001.

### 5.2. Tester Codex CLI

Отвечает за:

- подготовку staging/production-like проверки;
- запуск команд;
- ручную UI-проверку;
- regression Stage 1/2;
- проверку прав доступа;
- проверку exports;
- первичный secrets check;
- оформление `docs/testing/TEST_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md`.

Тестировщик не меняет production code.

### 5.3. Auditor Codex CLI

Отвечает за:

- проверку полноты validation report;
- сверку с protected invariants;
- проверку, что нет blocking defects;
- проверку классификации замечаний;
- оформление `docs/audit/AUDIT_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md`;
- выдачу `AUDIT PASS` / `AUDIT FAIL`.

Аудитор не исправляет код.

### 5.4. Tech Writer Codex CLI

Отвечает за:

- финализацию `docs/reports/CORE_1_RELEASE_VALIDATION_REPORT.md`;
- обновление документационной карты/статуса после PASS;
- фиксацию следующего разрешённого шага.

### 5.5. Developer Codex CLI

Подключается только если:

- тестировщик или аудитор нашли дефект;
- оркестратор создал отдельную bugfix-задачу;
- bugfix имеет конкретный scope, tests и audit criteria.

---

## 6. Task-scoped reading packages

Каждый агент читает только свой пакет. Полное ТЗ проекта не перечитывается без прямого указания оркестратора.

### 6.1. Orchestrator

```text
README.md
AGENTS.md
docs/DOCUMENTATION_MAP.md
docs/orchestration/ORCHESTRATION.md
docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md
docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_SCOPE.md
docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md
docs/testing/TEST_REPORT_TASK_PC_009_STAGE_3_ACCEPTANCE.md
docs/reports/STAGE_3_PRODUCT_CORE_IMPLEMENTATION_REPORT.md
docs/tasks/validation/stage-3-product-core/TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md
```

При наличии также читать:

```text
docs/PROJECT_NAVIGATOR.md
docs/project/CURRENT_STATUS.md
docs/project/PROJECT_GLOSSARY.md
```

### 6.2. Tester

```text
AGENTS.md
docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_SCOPE.md
docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_ACCEPTANCE_TESTS.md
docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md
docs/testing/TEST_REPORT_TASK_PC_009_STAGE_3_ACCEPTANCE.md
docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md
apps/product_core/
apps/marketplace_products/
apps/operations/
apps/discounts/wb_excel/
apps/discounts/ozon_excel/
apps/discounts/wb_api/
apps/discounts/ozon_api/
apps/web/
```

### 6.3. Auditor

```text
AGENTS.md
docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_SCOPE.md
docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md
docs/testing/TEST_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md
docs/testing/TEST_REPORT_TASK_PC_009_STAGE_3_ACCEPTANCE.md
docs/audit/AUDIT_REPORT_STAGE_3_PRODUCT_CORE_DOCUMENTATION.md
docs/audit/AUDIT_REPORT_TASK_PC_009_TESTS_ACCEPTANCE.md
docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md
```

### 6.4. Tech Writer

```text
README.md
docs/DOCUMENTATION_MAP.md
docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md
docs/testing/TEST_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md
docs/audit/AUDIT_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md
docs/reports/STAGE_3_PRODUCT_CORE_IMPLEMENTATION_REPORT.md
```

### 6.5. Developer при bugfix

Определяется оркестратором отдельно по дефекту:

```text
AGENTS.md
конкретный defect report
конкретные изменяемые файлы
релевантные tests
релевантный stage/spec
```

---

## 7. Предварительные условия

Перед началом validation должны быть доступны:

1. актуальная ветка проекта;
2. staging или production-like база;
3. PostgreSQL backup procedure;
4. media/file backup procedure, если окружение использует media/files;
5. доступ к Django management commands;
6. доступ к UI;
7. тестовые пользователи с разными ролями;
8. магазины WB/Ozon с тестовыми или production-like данными;
9. возможность запустить regression tests;
10. список API-подключений, пригодных для безопасной проверки;
11. запрет на destructive operations без approval.

Если production-like окружения нет, тестировщик обязан явно указать это в отчёте как ограничение проверки.

---

## 8. План validation

### 8.1. Зафиксировать окружение

В отчёте указать:

```text
branch:
commit:
server:
database:
django settings module:
python version:
postgres version:
test command:
validation started at:
validation finished at:
```

### 8.2. Backup gate

До миграций и runtime-проверок:

1. создать PostgreSQL backup;
2. создать media/files backup, если применимо;
3. зафиксировать путь/имя backup;
4. проверить, что backup не пустой;
5. если возможно — выполнить restore check в non-production DB;
6. если restore check не выполнялся — указать это как limitation.

Если в проекте есть `scripts/pre_update_backup.sh` и `scripts/restore_check.sh`, использовать их согласно runbook.

Критерий PASS:

```text
Backup создан, доступен, имеет понятный путь/имя, restore check выполнен или limitation явно зафиксирован.
```

Критерий FAIL:

```text
Миграции/проверки начаты без backup или backup невалиден.
```

### 8.3. Django/system checks

Минимальные команды:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
```

Ожидаемый результат:

- `check` без ошибок;
- `makemigrations --check --dry-run` без незакоммиченных миграций;
- список миграций показывает ожидаемое состояние.

### 8.4. Миграции

Выполнить:

```bash
python manage.py migrate
```

После миграции повторить:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
```

Критерий PASS:

- миграции применились без ошибок;
- новых миграций не требуется;
- приложение проходит `manage.py check`.

### 8.5. Backfill validation

Проверить legacy backfill:

```bash
python manage.py shell -c "from apps.marketplace_products.services import validate_legacy_product_listing_backfill; print(validate_legacy_product_listing_backfill())"
```

В отчёте зафиксировать:

```text
legacy_products:
missing_listing_product_ids:
mismatched_mapping_product_ids:
duplicate/conflict notes:
```

Критерии PASS:

1. legacy `MarketplaceProduct` сохранён;
2. все допустимые legacy rows имеют соответствующий `MarketplaceListing`;
3. backfilled listings не имеют `internal_variant_id`;
4. backfilled listings имеют ожидаемый `mapping_status`, обычно `unmatched`;
5. нет неописанных missing/mismatched rows.

Если есть missing/mismatched rows, они должны быть классифицированы как:

```text
blocking defect / known expected duplicate / data quality issue / requires designer decision
```

### 8.6. Regression Stage 1 Excel

Проверить WB и Ozon Excel flows:

1. upload source Excel;
2. check-only mode;
3. process mode;
4. повторный process после check, если это предусмотрено текущей логикой;
5. output file/link;
6. operation card;
7. detail rows;
8. historical `product_ref`;
9. audit/techlog.

Критерий PASS:

```text
Stage 1 Excel работает не хуже, чем до CORE-1; Excel не создаёт InternalProduct/ProductVariant и confirmed mappings.
```

### 8.7. Regression Stage 2.1 WB API

Проверить минимум:

1. WB API connection/secret reference handling;
2. prices download;
3. price Excel export;
4. current promotions download/export where applicable;
5. discount calculation from approved WB logic;
6. discount upload flow, если безопасно и разрешено для окружения;
7. drift check/status polling, если применимо;
8. отсутствие утечки WB token/API secret.

### 8.8. Regression Stage 2.2 Ozon Elastic API

Проверить минимум:

1. Ozon API connection/secret reference handling;
2. Elastic Boosting actions/product data flow;
3. review/calculation/upload flow, если безопасно и разрешено;
4. summary/snapshot behavior по текущей реализации;
5. отсутствие утечки Ozon API-Key/Client-Id без необходимости.

### 8.9. Product Core UI

Проверить:

1. список внутренних товаров;
2. карточку внутреннего товара;
3. варианты товара;
4. фильтры и поиск;
5. actions только при наличии прав;
6. отсутствие пустых рабочих ERP-блоков, если склад/производство/поставщики не реализованы.

### 8.10. MarketplaceListing UI

Проверить:

1. список листингов;
2. карточку листинга;
3. фильтры по marketplace/store/status/mapping status;
4. поиск по external id, seller article, barcode, title;
5. отображение latest values;
6. отображение source/time/run;
7. отсутствие секретов;
8. object-scoped access.

### 8.11. Mapping statuses

Проверить UI и бизнес-правила для:

```text
unmatched
needs_review
conflict
matched
archived
```

Критерии:

- статусы человекочитаемы;
- конфликт не превращается в confirmed mapping автоматически;
- candidate suggestions остаются non-authoritative;
- ручное подтверждение требует права.

### 8.12. Manual mapping listing -> variant

Проверить:

1. пользователь с правом mapping может связать listing и variant;
2. пользователь без права mapping не может связать;
3. пользователь без доступа к магазину не видит listing и не может связать;
4. создаётся mapping history;
5. создаётся audit entry;
6. unmap сохраняет историю;
7. conflict/needs_review сценарии не обходят approval.

### 8.13. Permissions / object access

Проверить роли:

```text
owner
admin
manager
viewer/observer
user without store access
```

Критерии:

1. пользователь видит только доступные stores/listings;
2. export respects object access;
3. internal product UI не раскрывает hidden listing details;
4. snapshot/latest values не раскрывают данные чужого store;
5. mapping action требует отдельного права.

### 8.14. Exports

Проверить:

1. internal products export;
2. marketplace listings export;
3. latest values export;
4. mapping report export;
5. unmatched listings export;
6. фильтры и права;
7. отсутствие secrets/protected values;
8. корректность CSV/XLSX формата по текущей реализации.

### 8.15. Audit / techlog

Проверить фиксацию:

1. manual map/unmap;
2. export;
3. sync failure, если можно безопасно имитировать;
4. access denied/security-relevant event, если предусмотрено;
5. API errors;
6. отсутствие secrets в details/summary/payload.

### 8.16. Secrets and sensitive data check

Проверить:

```text
UI pages
logs
audit records
techlog records
operation details
export files
reports
```

Запрещённые значения:

```text
WB token
Ozon API-Key
raw protected_secret_ref value
Authorization header
Bearer token
secret
password
private key
```

Ограниченное отображение:

```text
Client-Id
connection id
technical external ids
```

---

## 9. Минимальный набор команд

Актуальные команды проекта могут отличаться. Если есть утверждённый runbook, использовать его. Минимальный набор:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python manage.py migrate
python manage.py shell -c "from apps.marketplace_products.services import validate_legacy_product_listing_backfill; print(validate_legacy_product_listing_backfill())"
python manage.py test
```

Если test suite слишком большой, оркестратор может разрешить targeted suite, но в отчёте нужно явно указать, что именно запускалось и почему этого достаточно.

---

## 10. Формат TEST REPORT

Файл:

```text
docs/testing/TEST_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md
```

Структура:

```md
# TEST_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION

Date:
Role: tester
Environment:
Branch:
Commit:
Database:
Status: PASS / PASS WITH NOTES / FAIL

## 1. Commands

| Command | Result | Notes |
| --- | --- | --- |

## 2. Backup

| Check | Result | Evidence |
| --- | --- | --- |

## 3. Migration And Backfill

| Check | Result | Evidence |
| --- | --- | --- |

## 4. Regression

| Area | Result | Evidence |
| --- | --- | --- |
| Stage 1 WB Excel | | |
| Stage 1 Ozon Excel | | |
| Stage 2.1 WB API | | |
| Stage 2.2 Ozon Elastic | | |

## 5. UI / Permissions / Exports

| Area | Result | Evidence |
| --- | --- | --- |

## 6. Audit / Techlog / Secrets

| Area | Result | Evidence |
| --- | --- | --- |

## 7. Defects

| ID | Severity | Description | Blocking | Owner |
| --- | --- | --- | --- | --- |

## 8. Limitations

## 9. Tester Verdict
```

---

## 11. Формат AUDIT REPORT

Файл:

```text
docs/audit/AUDIT_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md
```

Структура:

```md
# AUDIT_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION

Date:
Role: auditor
Input test report:
Status: AUDIT PASS / AUDIT PASS WITH NOTES / AUDIT FAIL

## 1. Scope Reviewed

## 2. Evidence Reviewed

## 3. Protected Invariants Check

| Invariant | Status | Evidence |
| --- | --- | --- |

## 4. Blocking Defects

## 5. Non-blocking Notes

## 6. Required Follow-ups

## 7. Auditor Decision

CORE-1 release validation is accepted: yes/no
CORE-2 design may start: yes/no
```

---

## 12. Формат финального отчёта

Файл:

```text
docs/reports/CORE_1_RELEASE_VALIDATION_REPORT.md
```

Структура:

```md
# CORE_1_RELEASE_VALIDATION_REPORT

Date:
Environment:
Branch:
Commit:
Tester report:
Audit report:

## Final Status

PASS / PASS WITH NOTES / FAIL

## Summary

## Validation Matrix

| Area | Status | Evidence |
| --- | --- | --- |
| Backup | | |
| Migrations | | |
| Backfill | | |
| Stage 1 Regression | | |
| Stage 2.1 Regression | | |
| Stage 2.2 Regression | | |
| Product Core UI | | |
| Listing UI | | |
| Mapping | | |
| Permissions | | |
| Exports | | |
| Audit/Techlog | | |
| Secrets | | |

## Open Defects

## Non-blocking Notes

## Decision

CORE-1 accepted as stable foundation: yes/no
CORE-2 design allowed: yes/no

## Next Authorized Step

If PASS:
`docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md`
```

---

## 13. PASS / PASS WITH NOTES / FAIL

### PASS

Можно выдать только если:

1. backup создан;
2. migrations прошли;
3. backfill validation прошла;
4. legacy `MarketplaceProduct` не удалён;
5. Stage 1 regression passed;
6. Stage 2.1 regression passed;
7. Stage 2.2 regression passed;
8. Product Core UI работает;
9. MarketplaceListing UI работает;
10. manual mapping работает;
11. permissions/object access работают;
12. exports работают;
13. audit/techlog работают;
14. no secrets leak;
15. no blocking defects.

### PASS WITH NOTES

Допускается, если есть только non-blocking замечания:

- documentation note;
- UI copy issue;
- minor usability issue;
- limitation of staging data;
- known future improvement.

Не допускается при security/access/data-loss/regression issue.

### FAIL

Обязателен, если:

- нет backup;
- migrations fail;
- backfill теряет или портит legacy data;
- Stage 1/2 regression fails;
- user sees data of inaccessible store;
- export leaks inaccessible data;
- secrets leak;
- manual mapping creates wrong state;
- candidate suggestions auto-confirm mapping;
- legacy `MarketplaceProduct` удалён/очищен/переписан;
- blocking defect unresolved.

---

## 14. Defect workflow

Если найден дефект:

1. tester фиксирует дефект в test report;
2. auditor классифицирует blocking/non-blocking;
3. orchestrator создаёт отдельную bugfix-задачу;
4. developer исправляет только defect scope;
5. tester выполняет targeted retest + affected regression;
6. auditor re-audit;
7. только после закрытия blocking defects можно выдать PASS.

Bugfix не должен превращаться в разработку CORE-2.

---

## 15. Запреты в рамках TASK-REL-PC-001

Запрещено:

- начинать CORE-2;
- добавлять новые API flows;
- менять бизнес-логику скидок;
- менять Excel flow;
- автоматически создавать `InternalProduct` / `ProductVariant` из Excel/API;
- автоматически объединять WB/Ozon listings;
- менять vendorCode/offer_id в маркетплейсах;
- удалять legacy `MarketplaceProduct`;
- выполнять destructive migration без отдельного approved plan;
- менять permissions matrix без отдельного design/audit.

---

## 16. Orchestrator opening prompt

```text
Ты — оркестратор Codex CLI проекта promo_v2.

Текущая задача: TASK-REL-PC-001 — Stage 3 CORE-1 Release Validation.

Цель: проверить на staging/production-like базе, что CORE-1 Product Core Foundation корректно работает, не ломает Stage 1/2, сохраняет legacy MarketplaceProduct compatibility, соблюдает object access, audit/techlog и secret safety.

Запрещено начинать CORE-2 или новую функциональность. Разработчик подключается только по отдельной bugfix-задаче, если тестировщик/аудитор найдут blocking defect.

Назначь тестировщику task-scoped reading package из документа, затем получи TEST REPORT. После этого назначь аудитора для проверки TEST REPORT и protected invariants. После AUDIT PASS назначь техрайтера для финального CORE_1_RELEASE_VALIDATION_REPORT и обновления документационной карты/статуса.

Реализация CORE-2 разрешена только после финального PASS.
```

---

## 17. Следующий шаг после PASS

После `CORE-1 RELEASE VALIDATION: PASS` разрешается открыть следующий входной документ:

```text
docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md
```

CORE-2 design также обязан пройти документационный audit-gate до реализации.
