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
| Operation | проверка/обработка | visible_id, marketplace, module, mode, type, status, run_id, store_id, initiator_user_id, execution_context, launch_method, started_at, finished_at, logic_version, check_basis_operation_id nullable, summary, error_count, warning_count | files, params snapshot, detail rows, warning confirmations, audit, techlog |
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
- type: `check` или `process`;
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

- operation_type: `check`, `process`;
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
