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

Важно: для `GAP-0008` проектное решение закрыто, а фактический acceptance artifact gate для реальных WB/Ozon output comparisons закрыт 2026-04-26. Контрольные наборы `WB-REAL-001` и `OZ-REAL-001`, checksums, результаты старой программы и expected results зарегистрированы в `docs/testing/CONTROL_FILE_REGISTRY.md` со статусом `accepted`. Новые customer edge-case artifacts могут добавляться отдельно, но не блокируют переход к следующему этапу разработки.

TASK-009 после аудита остаётся blocked не из-за открытого gap, а до реализации customer decisions по `GAP-0010`..`GAP-0013` в текущем исправлении TASK-009. Перенос этих решений в TASK-010 запрещён.

## Stage 2.1 WB API GAP evaluation

На 2026-04-26 новых открытых GAP для проектирования Stage 2.1 не создано. Потенциальные кандидаты из `tz_stage_2.1.txt` закрыты самим ТЗ как рекомендуемые проектные решения и зафиксированы в ADR-0017..ADR-0020:

- size price conflict: строка блокируется для upload до отдельного утверждённого правила;
- auto promotions without nomenclatures: акция сохраняется, товарные строки не выдумываются;
- promo Excel files: отдельный файл по акции; zip/package только optional enhancement;
- partial errors: отображаются и маппятся в `completed_with_warnings`;
- price drift: блокер upload, требуется повторить скачивание и расчёт.

Если заказчик позднее изменит одно из этих решений, требуется новая запись GAP/ADR и обновление Stage 2.1 specs до implementation.

Обновление 2026-04-29: по результатам live read-only проверки и решения заказчика оформлен ADR-0021. WB API не является источником состава товаров auto promotions. Это не открывает новый Stage 2.1 GAP, потому что Stage 2.1 release scope уже не выдумывает строки auto promotions. Для будущего расчёта WB auto promotions нужен отдельный внешний product-source artifact со списком товаров auto-акции; его формат, загрузка, проверка и acceptance должны быть спроектированы отдельной задачей до реализации.

## Stage 2.2 Ozon API GAP evaluation

На 2026-04-29 Stage 2.2 documentation package создан с открытыми spec-blocking gaps. Эти gaps не блокируют аудит проектной документации как фиксацию известных пробелов, но блокируют implementation affected slices until resolution is recorded here and, where needed, in `docs/adr/ADR_LOG.md`.

### GAP-0014: Stable Elastic Boosting action identification

- Статус: resolved/customer_decision
- Phase gate: blocks_before_stage_2_2_actions_implementation
- Blocking gate: нет, закрыт решением заказчика 2026-04-30
- Где обнаружен: `docs/tasks/implementation/stage-2/TASK-018-DESIGN-STAGE-2-2-OZON-API.md`
- Требование ТЗ/task: выбрать только акцию `Эластичный бустинг` and not mix seller-actions/other Ozon actions
- Затронутая область: actions download, UI action selector, upload drift-check
- Почему нельзя продолжать без решения: фильтрация по названию может ошибочно выбрать не тот action or break after Ozon naming change
- Варианты решения без изменения бизнес-логики: official stable action type/code; approved title pattern plus real sanitized fixture; customer-approved manual action selection with warning
- Рекомендуемый вариант: official stable action marker or sanitized fixture proving exact marker
- Кто принимает решение: заказчик through orchestrator after official schema/sanitized fixture review
- Требуется эскалация заказчику через оркестратора: закрыта
- Решение: на этапе `ozon_api_actions_download` система ищет candidates only within selected Ozon store/account by `action_type = MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT` and title contains `Эластичный бустинг`. Пользователь выбирает конкретную action. Выбранный/сохранённый `action_id` становится основным идентификатором дальнейшего workflow for that store context. Несмотря на наблюдение заказчика, что `action_id` Elastic Boosting долго остаётся одним и тем же, система не hard-code global constant and does not proceed without selection/saved context. Все следующие steps use saved `action_id`. Before upload drift-check verifies that saved `action_id` still exists and still has expected `action_type` and title marker.
- Дата решения: 2026-04-30
- ADR: ADR-0029

### GAP-0015: Confirm J source as product `min_price`

- Статус: resolved/customer_decision
- Phase gate: blocks_before_stage_2_2_calculation_implementation
- Blocking gate: нет, закрыт решением заказчика 2026-04-30
- Где обнаружен: `предварительно_2.2.txt`, TASK-018 discovery
- Требование ТЗ/task: API mapping J/O/P/R must be explicit and fixture-confirmed
- Затронутая область: product info join, Ozon shared calculation, drift-check
- Почему нельзя продолжать без решения: Excel rule uses J as minimum allowed price; wrong API field changes business outcome
- Варианты решения без изменения бизнес-логики: sanitized Ozon response proving `/v3/product/info/list` `min_price`; official Ozon schema note; customer-provided mapping artifact
- Рекомендуемый вариант: sanitized fixture with several rows where Excel J and API min_price can be compared
- Кто принимает решение: заказчик through orchestrator
- Требуется эскалация заказчику через оркестратора: закрыта
- Решение: для Stage 2.2 Ozon Elastic Boosting canonical row Excel J (`минимально допустимая цена`) использовать `min_price` из `/v3/product/info/list`. Если `min_price` отсутствует/нечисловой, J считается отсутствующим and existing Ozon reason `missing_min_price` applies.
- Дата решения: 2026-04-30
- ADR: ADR-0030

### GAP-0016: Ozon stock R aggregation rule

- Статус: resolved/customer_decision
- Phase gate: blocks_before_stage_2_2_calculation_implementation
- Blocking gate: нет, закрыт решением заказчика 2026-04-30
- Где обнаружен: TASK-018 discovery that action-row `stock=0` differed from `/v4/product/info/stocks`
- Требование ТЗ/task: R source and aggregation must be explicit
- Затронутая область: stocks join, no_stock rule, drift-check
- Почему нельзя продолжать без решения: R drives participation; summing wrong stock fields can add/remove products incorrectly
- Варианты решения без изменения бизнес-логики: sum confirmed `present` across all relevant warehouses; split FBO/FBS by approved rule; exclude reserved by approved rule
- Рекомендуемый вариант: customer/official confirmation to sum available `present` values from `/v4/product/info/stocks`, with explicit FBO/FBS/reserved handling
- Кто принимает решение: заказчик through orchestrator
- Требуется эскалация заказчику через оркестратора: закрыта
- Решение: для Stage 2.2 Ozon Elastic Boosting canonical row Excel R (`остаток`) использовать сумму `present` по всем stock rows из `/v4/product/info/stocks`, включая FBO + FBS. `reserved` не вычитать. Если stock info отсутствует или сумма `present <= 0`, применяется existing Ozon reason `no_stock`.
- Дата решения: 2026-04-30
- ADR: ADR-0031

### GAP-0017: Official manual upload Excel template for Ozon Elastic Boosting

- Статус: resolved/customer_decision
- Phase gate: blocks_before_stage_2_2_manual_excel_implementation
- Blocking gate: нет, закрыт решением заказчика 2026-04-30
- Где обнаружен: TASK-018 required workflow step 9
- Требование ТЗ/task: provide Excel for manual upload if official format is confirmed
- Затронутая область: file contour, UI file link, acceptance tests
- Почему нельзя продолжать без решения: generating an unconfirmed template may mislead user and cannot be accepted as cabinet-compatible
- Варианты решения без изменения бизнес-логики: use official Ozon cabinet template; use Stage 1 Ozon workbook only if confirmed compatible; remove manual upload file from release slice until template is confirmed
- Рекомендуемый вариант: request official template/export from customer and register sanitized artifact
- Кто принимает решение: заказчик through orchestrator
- Требуется эскалация заказчику через оркестратора: закрыта
- Решение: для Stage 2.2 v1 Excel для ручной загрузки результата в Ozon использовать текущий Stage 1 Ozon Excel-шаблон/формат как manual upload file. Это customer-approved risk acceptance: если Ozon ЛК не примет файл, это будущий compatibility issue, но v1 реализует этот формат. Файл должен быть явно отмечен как manual upload Excel по Stage 1-compatible template. Stage 1 Ozon Excel business rules не меняются. Manual upload Excel отражает рассчитанный Stage 2.2 результат: для add/update rows K=`Да`, L=`calculated_action_price`. Для deactivate rows, если Stage 1-compatible template не поддерживает deactivate action directly, workbook/report includes separate sheet/section `Снять с акции` with row-level reasons; deactivate rows must not be silently omitted. API upload remains the primary write path; manual Excel is a secondary artifact for ручная загрузка/контроль.
- Дата решения: 2026-04-30
- ADR: ADR-0032

### GAP-0018: Exact Ozon actions product schemas and activate/deactivate payload for Elastic Boosting

- Статус: resolved/customer_decision
- Phase gate: blocks_before_stage_2_2_products_and_upload_implementation
- Blocking gate: нет, закрыт решением заказчика 2026-04-30 для read-side active/candidate implementation fields and API write upload/deactivate
- Где обнаружен: TASK-018 API discovery and preliminary notes
- Требование ТЗ/task: read-side active/candidate schemas and write upload/deactivate payloads must be exact, row-level errors retained, no `/v1/product/import/prices`
- Затронутая область: `/v1/actions/products`, `/v1/actions/candidates`, `ozon_api_elastic_active_products_download`, `ozon_api_elastic_candidate_products_download`, `ozon_api_elastic_upload`, drift-check, upload report, tests
- Почему нельзя продолжать без решения: wrong read schema can build incorrect source rows; wrong write payload can fail or modify Ozon incorrectly
- Варианты решения без изменения бизнес-логики: official current schemas for `/v1/actions/products`, `/v1/actions/candidates`, `/v1/actions/products/activate` and `/v1/actions/products/deactivate`; sanitized successful/failed fixtures; customer-provided API contract
- Рекомендуемый вариант: official schemas plus sanitized fixtures for active/candidate rows, Elastic Boosting add/update and deactivate
- Кто принимает решение: заказчик through orchestrator after official schema/sanitized fixture review
- Требуется эскалация заказчику через оркестратора: закрыта
- Решение: для Stage 2.2 Ozon Elastic Boosting реализуется live write-side `activate/deactivate` по актуальной официальной документации Ozon, not mock/stub-only. Read-side uses observed/approved fields from `/v1/actions/products` and `/v1/actions/candidates`; exact field names and normalizers must follow the official current schema at implementation time and be covered by contract tests/sanitized fixtures. Add/update uses the Ozon actions activate endpoint with `action_id` and product rows containing Ozon-required identifiers and `action_price`; deactivate uses the Ozon actions deactivate endpoint with `action_id` and product identifiers. If official Ozon field names differ from documentation examples, implementation follows the official schema and tests must cover the actual request/response mapping. `/v1/product/import/prices` is explicitly prohibited for this flow. Write-side remains gated by accepted result, drift-check, explicit upload confirmation, one group deactivate confirmation when deactivate rows exist, row-level reporting, duplicate protection and safe error handling.
- Дата решения: 2026-04-30
- ADR: ADR-0033

### GAP-0019: Ozon batch size, rate limits and retry/idempotency policy

- Статус: resolved/technical_decision
- Phase gate: blocks_before_stage_2_2_api_client_implementation
- Blocking gate: нет, закрыт техническим решением оркестратора/technical design 2026-04-30
- Где обнаружен: TASK-018 required gaps/questions
- Требование ТЗ/task: rate limits and batch size for all used Ozon endpoints must be documented
- Затронутая область: API client, downloader pagination, upload batching, retry policy, acceptance tests
- Почему нельзя продолжать без решения: unsafe retry/batch settings can hit limits or duplicate writes
- Варианты решения без изменения бизнес-логики: official Ozon limits per endpoint/category; customer-approved conservative limits; environment-configured values with documented defaults after official review
- Рекомендуемый вариант: official limits and endpoint batch sizes documented before implementation
- Кто принимает решение: orchestrator/technical design; not customer
- Требуется эскалация заказчику через оркестратора: нет, gap не касается UX веб-панели и бизнес-логики
- Решение: conservative configurable API policy. Defaults for implementation/tests: read page size `100`; write batch size `100`; minimum interval between Ozon API requests `500 ms`; retry allowed only for read operations and transient failures (`429`, `5xx`, timeout/network) with bounded backoff. Write `activate/deactivate` must not be automatically retried after request was sent or response is uncertain; write retry is allowed only as an explicit new operation after drift-check. All defaults must be configurable via settings/env later, but documented defaults are the implementation/test baseline. Row-level partial failures are still persisted and reported.
- Дата решения: 2026-04-30
- ADR: ADR-0034

### GAP-0021: Customer approval for candidate/active collision handling

- Статус: resolved/customer_decision
- Phase gate: blocks_before_stage_2_2_calculation_implementation
- Blocking gate: нет, закрыт решением заказчика 2026-04-30
- Где обнаружен: audit Stage 2.2 documentation FAIL 2026-04-30
- Требование ТЗ/task: behavior for same product in active and candidate sources must be customer-approved or documented as open business/functionality gap
- Затронутая область: active/candidate source merge, `candidate_and_active`, upload planning, duplicate protection
- Почему нельзя продолжать без решения: treating duplicate source rows as active avoids duplicate writes, but it is still business behavior that must not be assumed by implementation
- Вопрос заказчику: подтвердить, что если один `product_id` есть и в active, и в candidates выбранной акции, строка объединяется как `candidate_and_active`, считается уже участвующей в акции for write planning, and cannot create duplicate add/update/deactivate rows.
- Варианты решения без изменения бизнес-логики: approve current merge-as-active model; block such rows for manual review; prefer active row and ignore candidate row; another customer-approved rule
- Рекомендуемый вариант: approve current merge-as-active model because it prevents duplicate Ozon writes
- Кто принимает решение: заказчик through orchestrator
- Требуется эскалация заказчику через оркестратора: нет, решение получено 2026-04-30
- Решение: если один `product_id` есть и в active, и в candidates выбранной Ozon Elastic Boosting action, строки объединяются как `candidate_and_active`. Для write planning такой товар считается уже участвующим в акции (`active`): повторное добавление не создаётся; если расчёт даёт `upload_ready`, планируется `update_action_price`; если `not_upload_ready`, планируется `deactivate_from_action`. Факт collision обязательно сохраняется в `source_group`, detail rows/details и result report.
- Дата решения: 2026-04-30

### GAP-0022: Approved Ozon API connection check endpoint and semantics

- Статус: resolved/technical_decision
- Phase gate: blocks_before_stage_2_2_connection_check_production_endpoint
- Blocking gate: нет, закрыт technical decision 2026-04-30
- Где обнаружен: audit Stage 2.2 documentation FAIL 2026-04-30
- Требование ТЗ/task: connection check endpoint must be approved, read-only and secret-safe before implementation uses it as production check
- Затронутая область: TASK-019 connection check endpoint, status transition to `active`, auth/rate/timeout/schema failure handling
- Почему нельзя продолжать без решения: ambiguous or write-like endpoint could mutate Ozon data or mark connection active based on the wrong capability
- Вопрос, закрытый решением: определить approved read-only endpoint/contract for Ozon Client-Id/Api-Key check.
- Варианты решения без изменения бизнес-логики: official Ozon read-only endpoint; customer-provided sanitized check fixture; keep TASK-019 limited to scaffolding-only check behavior until technical endpoint decision
- Рекомендуемый вариант: official read-only endpoint plus sanitized success/auth failure fixtures
- Кто принимает решение: orchestrator/technical design after read-only verification
- Требуется эскалация заказчику через оркестратора: нет, закрыто техническим решением
- Решение: Ozon API connection check for Stage 2.2 uses read-only `GET /v1/actions`. It was verified against test credentials as read-only and relevant for actions API. Status mapping: HTTP 200 with valid JSON containing `result` -> connection `active`; 401/403 -> `check_failed/auth_failed`; 429 -> `check_failed/rate_limited`; 5xx/timeout/network -> `check_failed/temporary`; invalid JSON/schema -> `check_failed/invalid_response`. No write endpoint may be used for connection check.
- Дата решения: 2026-04-30
- ADR: ADR-0035

## Stage 3.0 Product Core GAP evaluation

На 2026-05-01 `GAP-0023` закрыт решением заказчика по Option B. Stage 3.0 / CORE-1 documentation package has no open spec-blocking GAP for the candidate suggestion slice after this update. Automatic confirmed mapping remains prohibited.

### GAP-0023: CORE-1 semi-automatic mapping candidate scope

- Статус: resolved/customer_decision
- Phase gate: closed_for_stage_3_candidate_suggestion_implementation
- Blocking gate: нет, закрыт решением заказчика 2026-05-01; implementation still requires documentation `AUDIT PASS`
- Где обнаружен: `docs/tasks/design/product-core/TZ_PRODUCT_CORE_FOUNDATION_FOR_CODEX_DESIGNER.md` §19.3
- Требование ТЗ/task: explicitly ask whether CORE-1 mapping is manual-only or may show semi-automatic candidates by seller_article/barcode/external identifiers with mandatory manual confirmation
- Затронутая область: `TASK-PC-006-mapping-workflow.md`, `docs/product/PRODUCT_CORE_UI_SPEC.md`, candidate display/scoring in mapping workflow
- Почему нельзя продолжать без решения: showing candidates is UX/functionality behavior; a wrong candidate model can mislead users even if final mapping requires confirmation
- Варианты решения без изменения бизнес-логики:
  - Option A: CORE-1 v1 is manual search/link only; candidate suggestions are future.
  - Option B: CORE-1 v1 shows non-authoritative candidates by exact seller_article/barcode/external identifier matches, but final mapping always requires user confirmation.
  - Option C: candidate suggestions are allowed only after a later sanitized data review/audit.
- Рекомендуемый/утверждённый вариант: Option B, because it improves workflow while preserving the no-auto-merge rule.
- Кто принимает решение: заказчик через оркестратора
- Требуется эскалация заказчику через оркестратора: нет, решение получено 2026-05-01
- Решение: Option B approved. CORE-1 may show semi-automatic non-authoritative candidates only by exact `seller_article`, `barcode` or external identifier matches. The final `ProductVariant <-> MarketplaceListing` relationship is created only by explicit manual user confirmation by a user with mapping permission, with audit and `ProductMappingHistory`. Automatic confirmed mapping is prohibited. Fuzzy/title/partial-article candidates are out of CORE-1. Multiple candidates or conflicting exact matches must leave the listing in `needs_review` or `conflict` until the user resolves it.
- Дата решения: 2026-05-01
- ADR: ADR-0038

## Закрытые gaps

### GAP-0020: Customer approval for Stage 2.2 result review model

- Статус: resolved/customer_decision
- Phase gate: blocks_before_stage_2_2_review_implementation
- Blocking gate: снят для TASK-024 review UX/state implementation and downstream release acceptance
- Где обнаружен: audit Stage 2.2 documentation FAIL 2026-04-30
- Требование ТЗ/task: review/acceptance model must be customer-approved or documented as open UX/functionality gap
- Затронутая область: `Принять результат` / `Не принять результат`, immutable accepted basis, stale state, upload gating, UI labels
- Решение: customer decision 2026-04-30 approves option A. Stage 2.2 Ozon Elastic Boosting result review is a calculation result state, not a separate `Operation`. Approved review states are `not_reviewed`, `accepted`, `declined`, `stale`, `review_pending_deactivate_confirmation`. `Принять результат` freezes accepted upload basis. Upload is allowed only from an accepted result; if the accepted result contains `deactivate_from_action` rows, it can remain pending until one group deactivate confirmation is provided. `Не принять результат` fixes `declined` state and audit, and blocks upload.
- ADR: ADR-0027
- Кто принял решение: заказчик
- Дата решения: 2026-04-30

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
- Blocking gate: снят; real WB/Ozon output comparison artifact gate закрыт 2026-04-26
- Где обнаружен: `docs/stages/stage-1/ACCEPTANCE_TESTS.md`, `docs/testing/TEST_PROTOCOL.md`
- Требование ТЗ: §24
- Затронутая область: приёмка
- Решение: заказчик передаёт реальные контрольные WB/Ozon файлы и результаты старой программы; дополнительно могут добавляться edge-case наборы. На 2026-04-26 реальные WB/Ozon comparison artifacts получены и зарегистрированы как `WB-REAL-001` / `OZ-REAL-001` со статусом `accepted`. Агенты не выдумывают файлы, checksums или expected results.
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
