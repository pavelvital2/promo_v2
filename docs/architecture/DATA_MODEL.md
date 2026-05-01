# DATA_MODEL.md

Трассировка: ТЗ §7-§14, §17, §20-§23.

## Общие правила модели данных

- Одна PostgreSQL БД для всех прикладных и системных сущностей этапа 1.
- Завершённые операции, audit records и tech log records не редактируются через пользовательский или административный интерфейс.
- Изменение параметров влияет только на новые операции.
- Физические файлы хранятся в серверном файловом хранилище, в БД хранятся метаданные.
- Системные словари фиксированы и не редактируются пользователем.
- Удаление, блокировка, деактивация и архивирование выполняются по `docs/architecture/DELETION_ARCHIVAL_POLICY.md`.

## Обязательные сущности этапа 1

| Сущность | Назначение | Ключевые поля | Связи |
| --- | --- | --- | --- |
| User | учётная запись | visible_id, login, password_secret, display_name, status, primary_role_id | roles, grants/denies, store_access, audit |
| UserChangeHistory | история значимых изменений пользователя | user_id, changed_at, changed_by, field_code, old_value, new_value, source | user, audit |
| UserBlockHistory | история блокировок пользователя | user_id, changed_at, changed_by, old_status, new_status, reason, source | user, audit |
| Role | шаблон доступа | code, name, status, is_system | role_permissions, role_section_access |
| Permission | право действия | code, name, scope_type | role/user grants |
| SectionAccess | доступ к разделу/вкладке | code, section, mode | role/user grants |
| UserPermissionOverride | индивидуальное разрешение/запрет | user_id, permission_code, effect, store_id nullable | user, store |
| StoreAccess | объектный доступ | user_id, store_id, access_level, effect | user, store |
| BusinessGroup | группа/бренд/направление | visible_id, name, status, comments, created_at, updated_at | stores |
| StoreAccount | магазин/кабинет | visible_id, name, group_id, marketplace, cabinet_type, status, comments, created_at, updated_at | operations, files, params, access, products |
| StoreAccountChangeHistory | история изменений магазина/кабинета | store_id, changed_at, changed_by, field_code, old_value, new_value, source | store, audit |
| ConnectionBlock | блок подключения/API | store_id, module, connection_type, status, protected_secret_ref, metadata, is_stage1_used=false | store |
| MarketplaceProduct | товар этапа 1 | marketplace, store_id, external_ids, title, sku/barcode, status, last_values | store, operations, files |
| MarketplaceProductHistory | история появления/обновления товара | product_id, detected_at, operation_id, file_version_id, change_type, changed_fields, previous_values, new_values | product, operation, files |
| Run | контейнер запуска | visible_id, marketplace, module, mode, store_id, initiated_by, status, created_at | files, checks, processes |
| Operation | исполнимая бизнес-операция | visible_id, marketplace, module, mode, type, step_code, status, run_id, store_id, initiator_user_id, execution_context, launch_method, started_at, finished_at, logic_version, check_basis_operation_id nullable, summary, error_count, warning_count | files, params snapshot, detail rows, warning confirmations, audit, techlog |
| FileObject | файл | visible_id, store_id, kind, scenario, marketplace, module, logical_name, original_name, status, created_by, created_at, updated_at | file_versions |
| FileVersion | версия файла | file_id, version_no, original_name, content_type, storage_backend, storage_path, size, checksum_sha256, uploaded_by, created_at, retention_until, physical_status, physical_deleted_at, operation_ref, run_ref | operations, run |
| OperationInputFile | связь operation с входными версиями файлов | operation_id, file_version_id, role_in_operation, ordinal_no | operation, file_version |
| OperationOutputFile | связь operation с выходной версией файла | operation_id, file_version_id, output_kind | operation, file_version |
| AppliedParameterSnapshot | снимок параметра операции | operation_id, parameter_code, applied_value, source, parameter_version, effective_at | operation, parameter |
| CheckResult | результат проверки | operation_id, summary, error_count, warning_count | detail rows |
| ProcessResult | результат обработки | operation_id, output_file_version_id, summary | detail rows |
| OperationDetailRow | детализация строки | operation_id, row_no, product_ref, row_status, reason_code, message, final_value | operation |
| ParameterDefinition | параметр | code, module, value_type, is_user_managed | values |
| SystemParameterValue | системное значение | parameter_code, value, active_from | operations snapshot |
| StoreParameterValue | значение магазина | store_id, parameter_code, value, active_from | store |
| ParameterChangeHistory | история параметров | changed_by, store_id nullable, old_value, new_value, source | audit |
| WarningConfirmation | подтверждение предупреждений | check_operation_id, process_operation_id, user_id, confirmed_at, warning_codes | operations |
| AuditRecord | аудит действий | occurred_at, retention_until, user_id, action_code, entity_type, entity_id, store_id, operation_id | related entities |
| TechLogRecord | технический журнал | occurred_at, retention_until, severity, event_type, operation_id, store_id, safe_message, sensitive_details_ref | operation |
| SystemNotification | системное уведомление | severity, topic, message, status, related_operation_id | home page |

## Будущие сущности, заложенные архитектурно

Не являются рабочими производственными справочниками этапа 1, но модель не должна блокировать их добавление:

- InternalProductModel;
- InternalProductVariation;
- MarketplaceOffer;
- Stock;
- Sale;
- AverageDailySale;
- Demand;
- WorkOrder;
- ProductionOrder;
- ProductionRoute;
- Operator;
- ProductionOperation;
- ProductionFact;
- Batch;
- Supply;
- Shipment;
- Warehouse;
- InventoryMovementState;
- Purchase.

## Связи магазинов / кабинетов

`StoreAccount` является основной рабочей сущностью этапа 1. К нему привязываются:

- операции и run;
- файлы и версии через операции/run;
- параметры;
- права пользователей;
- история изменений;
- API-блоки будущих подключений;
- маркетплейс-товары;
- будущие цены, остатки, продажи и поставки.

История магазина/кабинета ведётся через `StoreAccountChangeHistory` и покрывает все поля карточки из ТЗ §8.3-§8.4:

- `visible_id`, если формат допускает отображение исторического значения;
- `name`;
- `group_id`;
- `marketplace`;
- `cabinet_type`;
- `status`;
- параметры этапа 1;
- API-блок/connection metadata без раскрытия protected secret;
- доступы пользователей;
- служебные комментарии.

Изменение параметров магазина дополнительно фиксируется в `ParameterChangeHistory`, чтобы сохранить специализированную историю параметров и единый пользовательский экран истории настроек.

## Пользователь и история доступа

`User` хранит минимальный обязательный состав ТЗ §11.7: login, password secret, display name, status, primary role, объектные доступы, индивидуальные разрешения и запреты. Значимые изменения пользователя фиксируются в `UserChangeHistory`, включая:

- изменение отображаемого имени;
- изменение статуса активности;
- назначение или смену основной роли;
- изменение индивидуальных разрешений/запретов;
- изменение объектных доступов.

Блокировки, разблокировки и архивирование пользователя фиксируются в `UserBlockHistory`. Для владельца действует отдельное ограничение из `docs/product/PERMISSIONS_MATRIX.md`: администратор не может удалить, заблокировать или лишить владельца критичных прав.

## MarketplaceProduct и история появления/обновления

`MarketplaceProduct` создаётся и обновляется только из валидных строк Excel WB/Ozon. Отсутствие товара до загрузки файла не является ошибкой.

`MarketplaceProductHistory` хранит историю появления/обновления из ТЗ §9.3:

- когда товар впервые обнаружен или обновлён;
- в какой operation и file version это произошло;
- какие external identifiers, title, sku/barcode или last_values были добавлены/изменены;
- предыдущее и новое значение для изменённых полей, если это применимо;
- статус товара после изменения.

## Operation как исполнимая запись

`Operation` обязана покрывать поля ТЗ §12.3 и `docs/product/OPERATIONS_SPEC.md`:

- visible_id;
- marketplace;
- module;
- mode: `excel`, future `api`;
- store/account;
- type: `check` или `process` только для check/process-сценариев; для Stage 2.1 WB API and Stage 2.2 Ozon API steps без модели check/process поле nullable/blank/not_applicable по миграционному решению;
- step_code: обязательный primary classifier для Stage 2.1 WB API, Stage 2.2 Ozon API and future non-check/process steps;
- status;
- initiator_user_id;
- execution_context: от чьего имени и в каком контуре выполнялась operation;
- launch_method: `manual`, future `automatic`, `service`, `api`;
- started_at и finished_at;
- input file versions через `OperationInputFile`;
- output file version через `OperationOutputFile`, если output существует;
- check_basis_operation_id для process;
- applied parameters snapshot через `AppliedParameterSnapshot`;
- logic_version;
- summary;
- error_count и warning_count;
- row details через `OperationDetailRow`;
- warning confirmations через `WarningConfirmation`;
- links to audit/techlog через `AuditRecord.operation_id` и `TechLogRecord.operation_id`.

Завершённая operation, её file version links, applied parameter snapshot, results и detail rows не редактируются через пользовательский или административный интерфейс. Повторное действие создаёт новую operation.

## Связи audit/techlog

Audit и techlog являются отдельными контурами и не заменяют operation:

- `AuditRecord.operation_id` используется для значимых пользовательских действий, связанных с operation: запуск check/process, подтверждение warnings, скачивание output при включённом контроле доступа.
- `AuditRecord.entity_type/entity_id` связывает записи с пользователями, ролями, магазинами, параметрами, файлами и подключениями.
- `TechLogRecord.operation_id` используется для системных ошибок/сбоев в контексте operation.
- `TechLogRecord.sensitive_details_ref` не выводится пользователю без отдельного права `techlog.sensitive.view`.

Каталог action/event codes и правила видимости описаны в `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`.

Audit records и techlog records хранятся 90 дней. Очистка выполняется только регламентной процедурой вне обычного UI и не удаляет operations, metadata, file links, parameter snapshots или detail rows.

## Параметры WB

На этапе 1 управляемы только:

- `wb_threshold_percent`;
- `wb_fallback_no_promo_percent`;
- `wb_fallback_over_threshold_percent`.

Системные defaults:

| Parameter code | System default |
| --- | --- |
| `wb_threshold_percent` | `70` |
| `wb_fallback_over_threshold_percent` | `55` |
| `wb_fallback_no_promo_percent` | `55` |

Каскад: значение магазина/кабинета -> системное значение. Каждая операция хранит snapshot:

- code;
- applied_value;
- source: `store` или `system`;
- parameter_version/effective timestamp.

Ozon на этапе 1 не имеет пользовательских параметров расчёта скидок.

## Системные словари

Фиксируются как immutable codes:

- operation_type: `check`, `process` только для check/process-сценариев;
- operation_step_code Stage 2.1: `wb_api_prices_download`, `wb_api_promotions_download`, `wb_api_discount_calculation`, `wb_api_discount_upload`;
- mode: `excel`, future `api`;
- launch_method: `manual`, future `automatic`, `service`, `api`;
- check statuses: `created`, `running`, `completed_no_errors`, `completed_with_warnings`, `completed_with_errors`, `interrupted_failed`;
- process statuses: `created`, `running`, `completed_success`, `completed_with_warnings`, `completed_with_error`, `interrupted_failed`;
- message level: `info`, `warning_confirmable`, `warning_info`, `error`, `critical`;
- marketplace: `wb`, `ozon`.

WB reason/result codes этапа 1:

- `wb_valid_calculated`;
- `wb_no_promo_item`;
- `wb_over_threshold`;
- `wb_missing_article`;
- `wb_invalid_current_price`;
- `wb_duplicate_price_article`;
- `wb_missing_required_column`;
- `wb_invalid_promo_row`;
- `wb_invalid_workbook`;
- `wb_output_write_error`;
- `wb_discount_out_of_range`.

Расширение системных словарей выполняется только через утверждённое изменение документации/ADR и миграцию.

## Stage 2.1 WB API additions

Трассировка: `tz_stage_2.1.txt` §6-§14; ADR-0016..ADR-0020.

Stage 2.1 использует ту же PostgreSQL БД и существующие инварианты immutable operations/files/audit. Excel mode Stage 1 не заменяется.

### Operation classification

Для Stage 2.1 выбран явный контракт: `Operation.step_code` является обязательным primary classifier для всех API steps 2.1.1-2.1.4. Поле должно быть отдельным DB-полем или immutable indexed/generated field из `execution_context`, но реализация обязана предоставить его как явное значение для фильтров UI, audit, tests and traceability.

`Operation.type` не расширяется Stage 2.1 значениями и не используется для API download/upload/calculation steps. Для операций с `mode=api`, `marketplace=wb` и одним из Stage 2.1 `step_code` поле `type` должно быть `NULL` / blank / `not_applicable` согласно выбранной миграции, но не `check` и не `process`. `check/process` сохраняются без изменений для Stage 1 Excel и будущих сценариев, где это реально check/process.

Migration guidance:

- не менять семантику Stage 1 `Operation.type=check/process`;
- добавить `Operation.step_code` или эквивалентный immutable indexed contract до реализации TASK-012..TASK-015;
- добавить constraint/validation: Stage 2.1 WB API operation требует один из закрытых `step_code`;
- добавить constraint/validation: Stage 2.1 WB API operation не должна иметь `type=check/process`;
- списки, карточки, audit links, tests and traceability используют `step_code` как классификатор API steps.

Закрытый перечень Stage 2.1 step codes:

- `wb_api_prices_download`;
- `wb_api_promotions_download`;
- `wb_api_discount_calculation`;
- `wb_api_discount_upload`.

`Operation.mode=api`, `marketplace=wb`. `Operation.type=check/process` остаётся только для check/process-сценариев; все Stage 2.1 API steps, включая 2.1.3 calculation, классифицируются через `step_code` и не маскируются под Stage 1 Excel check/process.

### New entities

| Сущность | Назначение | Ключевые поля | Связи |
| --- | --- | --- | --- |
| WBApiRequestSnapshot | safe snapshot API запроса/ответа | operation_id, store_id, api_category, endpoint_code, method, request_safe, response_safe, status_code, checksum, created_at | operation, store |
| WBPriceSnapshot | snapshot 2.1.1 | operation_id, store_id, fetched_at, page_count, goods_count, size_conflict_count, safe_snapshot_ref, source_checksum | operation, store |
| WBPriceSnapshotRow | строка цены API | snapshot_id, nmID, vendorCode, derived_price, currency, discount, sizes_safe, editableSizePrice, isBadTurnover, row_status, reason_code | price snapshot, product |
| WBPromotion | акция WB | store_id, wb_promotion_id, name, type, start_datetime, end_datetime, is_current_at_fetch, last_seen_at, snapshot_ref | store, products, export files |
| WBPromotionSnapshot | snapshot 2.1.2 | operation_id, store_id, fetched_at, api_window_start, api_window_end, current_filter_timestamp, raw_response_safe_snapshot, promotions_count, current_promotions_count | operation, store |
| WBPromotionProduct | товар акции | promotion_id, nmID, inAction, price, currencyCode, planPrice, discount, planDiscount, source_snapshot_id, row_status, reason_code | promotion, snapshot |
| WBPromotionExportFile | связь акции и Excel export | promotion_id, operation_id, file_version_id | promotion, operation, file |
| WBApiUploadBatch | batch 2.1.4 | operation_id, batch_no, payload_checksum, goods_count, uploadID, wb_status, status_checked_at, summary, safe_snapshot_ref | upload operation |
| WBApiUploadDetail | строка результата upload | batch_id, nmID, requested_discount, result_status, reason_code, errorText_safe, quarantine_flag | batch, product |

### MarketplaceProduct Stage 2.1 mapping

2.1.1 обновляет `MarketplaceProduct` выбранного WB store:

- `marketplace=wb`;
- `sku=str(nmID)`;
- `external_ids` включает `nmID`, `vendorCode`, `sizeIDs`, `techSizeNames`, `source=wb_prices_api`;
- `last_values` включает price/discount/discountedPrice/clubDiscount/clubDiscountedPrice/currency/editableSizePrice/isBadTurnover;
- `title` не выдумывается, если не приходит из официального источника;
- `MarketplaceProductHistory` фиксирует create/update from `wb_api_prices_download`.

### ConnectionBlock Stage 2.1

`ConnectionBlock` становится рабочим для WB API по `docs/architecture/API_CONNECTIONS_SPEC.md`. `protected_secret_ref` остаётся единственным местом хранения token, authorization header, API key, bearer value and secret-like value. `metadata`, audit, techlog `safe_message`, techlog `sensitive_details_ref`, snapshots, UI, files and reports не содержат такие значения.

### Stage 2.1 system dictionaries

Operation step codes:

- `wb_api_prices_download`;
- `wb_api_promotions_download`;
- `wb_api_discount_calculation`;
- `wb_api_discount_upload`.

WB API reason/result codes:

- `wb_api_price_download_success`;
- `wb_api_price_download_failed`;
- `wb_api_price_row_valid`;
- `wb_api_price_row_size_conflict`;
- `wb_api_price_row_invalid`;
- `wb_api_promotion_current`;
- `wb_api_promotion_not_current_filtered`;
- `wb_api_promotion_regular`;
- `wb_api_promotion_auto_no_nomenclatures`;
- `wb_api_promotion_product_valid`;
- `wb_api_promotion_product_invalid`;
- `wb_api_calculated_from_api_sources`;
- `wb_api_upload_ready`;
- `wb_api_upload_blocked_by_drift`;
- `wb_api_upload_sent`;
- `wb_api_upload_success`;
- `wb_api_upload_partial_error`;
- `wb_api_upload_all_error`;
- `wb_api_upload_canceled`;
- `wb_api_upload_quarantine`;
- `wb_api_upload_status_unknown`.

Connection statuses:

- `not_configured`;
- `configured`;
- `active`;
- `check_failed`;
- `disabled`;
- `archived`.

## Stage 2.2 Ozon API additions

Трассировка: `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`; `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`; ADR-0022..ADR-0028.

Stage 2.2 uses the same PostgreSQL DB and immutable operations/files/audit invariants. Physical model choice is conservative: implementation may use dedicated tables below or equivalent existing `Operation`/detail/snapshot storage only if it preserves the same queryable contract, immutable basis and row-level traceability.

### Operation classification

For `mode=api`, `marketplace=ozon`, `module=actions`, `Operation.step_code` is mandatory and must be one of:

- `ozon_api_connection_check`;
- `ozon_api_actions_download`;
- `ozon_api_elastic_active_products_download`;
- `ozon_api_elastic_candidate_products_download`;
- `ozon_api_elastic_product_data_download`;
- `ozon_api_elastic_calculation`;
- `ozon_api_elastic_upload`.

`Operation.type` must not be `check` or `process` for these API steps.

### Snapshot/result entities

| Сущность | Назначение | Ключевые поля | Связи |
| --- | --- | --- | --- |
| OzonApiRequestSnapshot | safe snapshot API request/response | operation_id, store_id, endpoint_code, method, request_safe, response_safe, status_code, checksum, created_at | operation, store |
| OzonActionSnapshot | actions list snapshot | operation_id, store_id, fetched_at, actions_count, elastic_actions_count, safe_snapshot_ref | operation, store |
| OzonElasticActionRowSnapshot | active/candidate action row | operation_id, action_id, source_group, product_id, offer_id nullable, action_price, price_min_elastic, price_max_elastic, boost fields, row_status, reason_code, source_details/collision_details, safe_snapshot_ref | operation, store |
| OzonElasticProductDataSnapshot | joined product info/stocks basis | operation_id, action_id, product_count, stock_rows_count, source_checksum, safe_snapshot_ref | operation, store |
| OzonElasticProductDataRow | canonical input row | snapshot_id, product_id, offer_id, name, source_group, source_details/collision_details, J_min_price, O_price_min_elastic, P_price_max_elastic, R_stock_present, row_status, reason_code | product data snapshot |
| OzonElasticCalculationResult | calculation summary and review | operation_id, action_id, basis_snapshot_ids, review_state, deactivate_confirmation_status, reviewed_by, reviewed_at, accepted_basis_checksum, summary | calculation operation |
| OzonElasticCalculationRow | row result | result_id, product_id, offer_id, source_group, source_details/collision_details, reason_code, planned_action, calculated_action_price, upload_ready, deactivate_required, deactivate_reason_code, deactivate_reason | calculation result |
| OzonElasticUploadBatch | upload batch | operation_id, batch_no, operation_kind, payload_checksum, rows_count, ozon_request_id_safe nullable, result_status, safe_snapshot_ref | upload operation |
| OzonElasticUploadDetail | row-level upload result | batch_id, product_id, offer_id, requested_action_price, result_status, reason_code, error_safe | upload batch |

If dedicated physical models are deferred, `Operation.summary`, `OperationDetailRow`, safe snapshots and file metadata must still expose every field required by `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`.

### Ozon API reason/result codes

Ozon Excel business reason codes remain:

- `missing_min_price`;
- `no_stock`;
- `no_boost_prices`;
- `use_max_boost_price`;
- `use_min_price`;
- `below_min_price_threshold`;
- `insufficient_ozon_input_data`.

Ozon API-specific codes:

- `ozon_api_action_not_elastic`;
- `ozon_api_action_not_found`;
- `ozon_api_missing_elastic_fields`;
- `ozon_api_missing_product_info`;
- `ozon_api_missing_stock_info`;
- `ozon_api_product_not_eligible`;
- `ozon_api_upload_blocked_by_drift`;
- `ozon_api_upload_blocked_deactivate_unconfirmed`;
- `ozon_api_upload_ready`;
- `ozon_api_upload_rejected`;
- `ozon_api_upload_partial_rejected`;
- `ozon_api_upload_success`;
- `ozon_api_deactivate_required`;
- `ozon_api_deactivate_group_confirmed`;
- `ozon_api_auth_failed`;
- `ozon_api_rate_limited`;
- `ozon_api_timeout`;
- `ozon_api_response_invalid`;
- `ozon_api_secret_redaction_violation`.

Adding or renaming codes requires documentation update and ADR.

Deactivate-related closed catalogs:

- `deactivate_confirmation_status`: `not_required`, `pending`, `confirmed`;
- `review_state`: `not_reviewed`, `accepted`, `declined`, `stale`, `review_pending_deactivate_confirmation`;
- allowed `deactivate_reason_code`: `missing_min_price`, `no_stock`, `no_boost_prices`, `below_min_price_threshold`, `insufficient_ozon_input_data`.

The previous `not_uploaded_user_declined`/`ozon_api_deactivate_declined` model is not part of the accepted Stage 2.2 target model after ADR-0026. Review is calculation result state, not a separate Operation, after ADR-0027.

## Stage 3.0 Product Core additions

Трассировка: `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_SCOPE.md`; `docs/architecture/PRODUCT_CORE_ARCHITECTURE.md`; `docs/product/PRODUCT_CORE_SPEC.md`; `docs/product/MARKETPLACE_LISTINGS_SPEC.md`; ADR-0036..ADR-0041.

Stage 3.0 / CORE-1 adds the internal product core and external marketplace listing layer. It does not remove or truncate current `MarketplaceProduct`; migration follows `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_MIGRATION_PLAN.md`.

### Product core entities

| Сущность | Назначение | Ключевые поля | Связи |
| --- | --- | --- | --- |
| InternalProduct | внутренний товар/материал/набор/артефакт компании | visible_id/internal_code, name, product_type, category_id nullable, status, attributes, comments, created_by, updated_by, timestamps | variants, category, audit/history |
| ProductVariant | конкретный внутренний вариант | product_id, internal_sku, name, barcode_internal nullable, variant_attributes, status, timestamps | product, identifiers, marketplace listings |
| ProductCategory | внутренняя категория | parent_id nullable, name, status, sort_order, timestamps | products |
| ProductIdentifier | alternate identifiers for variant | variant_id, identifier_type, value, source, is_primary, created_at | variant |

`InternalProduct` and `ProductVariant` are the identity core for future stock, production, suppliers, BOM, packaging and labels. Marketplace ids do not become internal identity.

### Marketplace listing entities

| Сущность | Назначение | Ключевые поля | Связи |
| --- | --- | --- | --- |
| MarketplaceListing | внешний листинг WB/Ozon in one store/account | marketplace, store_id, internal_variant_id nullable, external_primary_id, external_ids, seller_article, barcode, title, brand, category_name, category_external_id, listing_status, mapping_status, last_values, first_seen_at, last_seen_at, last_successful_sync_at, last_sync_run_id, last_source, timestamps | store, variant, sync runs, snapshots, histories, operations via nullable enrichment |
| ListingHistory | append-only listing history | listing_id, changed_at, changed_by nullable, operation_id nullable, sync_run_id nullable, change_type, changed_fields, previous_values, new_values, source | listing, operation, sync run, user |
| ProductMappingHistory | append-only mapping history | listing_id, old_variant_id nullable, new_variant_id nullable, changed_at, changed_by, action, mapping_status_after, source_context, reason/comment; for confirmed candidate mapping `source_context` records exact match basis without making it authoritative | listing, variants, user, audit |

Recommended unique constraints:

- `MarketplaceListing(marketplace, store_id, external_primary_id)` unique for non-blank primary ids;
- additional partial/functional indexes for `seller_article`, `barcode`, `mapping_status`, `listing_status`, `last_successful_sync_at`;
- `ProductIdentifier(variant_id, identifier_type, value, source)` unique unless a future import workflow documents duplicates.

### Sync/snapshot entities

| Сущность | Назначение | Ключевые поля | Связи |
| --- | --- | --- | --- |
| MarketplaceSyncRun | sync attempt | operation_id nullable, marketplace, store_id, sync_type, source, launch_method, status, started_at, finished_at, requested_by nullable, summary, error_summary, created_at | operation, store, snapshots |
| PriceSnapshot | immutable price source record | listing_id, sync_run_id, operation_id nullable, snapshot_at, price, price_with_discount nullable, discount_percent nullable, currency, raw_safe, source_endpoint, created_at | listing, sync run, operation |
| StockSnapshot | immutable stock source record | listing_id, sync_run_id, operation_id nullable, snapshot_at, total_stock nullable, stock_by_warehouse, in_way_to_client nullable, in_way_from_client nullable, raw_safe, source_endpoint, created_at | listing, sync run, operation |
| SalesPeriodSnapshot | immutable sales/orders period source record | listing_id, sync_run_id, operation_id nullable, period_start, period_end, orders_qty nullable, sales_qty nullable, buyout_qty nullable, returns_qty nullable, sales_amount nullable, currency nullable, raw_safe, source_endpoint, created_at | listing, sync run, operation |
| PromotionSnapshot | foundation for promotion/action participation | listing_id, sync_run_id, operation_id nullable, marketplace_promotion_id, action_name, participation_status, action_price nullable, constraints, reason_code nullable, raw_safe, source_endpoint, created_at | listing, sync run, operation |

`MarketplaceListing.last_values` is a latest-state cache. History, source, period and raw-safe details live in sync runs and snapshot rows.

### Stage 3 system dictionaries

Product type:

- `finished_good`;
- `material`;
- `packaging`;
- `semi_finished`;
- `kit`;
- `service_or_design_artifact`;
- `unknown`.

Product/variant/category status:

- `active`;
- `inactive`;
- `archived`.

Listing status:

- `active`;
- `not_seen_last_sync`;
- `inactive`;
- `archived`;
- `sync_error`.

Mapping status:

- `unmatched`;
- `matched`;
- `needs_review`;
- `conflict`;
- `archived`.

Sync type:

- `listings`;
- `prices`;
- `stocks`;
- `sales`;
- `orders`;
- `promotions`;
- `full_catalog_refresh`;
- `mapping_import`.

### Legacy compatibility

`MarketplaceProduct` is legacy marketplace product data, not the internal company catalog. CORE-1 uses migration option B:

```text
MarketplaceProduct -> MarketplaceListing backfill
MarketplaceProduct remains deprecated/compatibility data
```

`OperationDetailRow.product_ref` remains a raw immutable reference. A nullable FK to `MarketplaceListing` may be added only when deterministic enrichment does not alter historical operation results.

## Видимые идентификаторы

Формат утверждён решением заказчика и зафиксирован в ADR-0008:

| Сущность | Формат | Правило нумерации |
| --- | --- | --- |
| Operation | `OP-YYYY-NNNNNN` | сквозной номер внутри года для operations |
| Run | `RUN-YYYY-NNNNNN` | сквозной номер внутри года для runs |
| FileObject | `FILE-YYYY-NNNNNN` | сквозной номер внутри года для files |
| StoreAccount | `STORE-NNNNNN` | сквозной номер для stores/cabinets |
| User | `USR-NNNNNN` | сквозной номер для users |

Общие требования:

- идентификатор уникален в рамках типа сущности;
- после создания не меняется;
- видим пользователю в списках, карточках, экспортах и поддержке;
- не раскрывает чувствительные данные;
- пригоден для поиска;
- `YYYY` берётся из даты создания сущности в системной timezone.
