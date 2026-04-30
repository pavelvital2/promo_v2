# AUDIT_AND_TECHLOG_SPEC.md

Трассировка: ТЗ §12.3, §17.3-§17.5, §18.5, §20, §21, §23.1, §27.1-§27.2.

## Назначение

Документ формализует контуры audit и technical log для реализации этапа 1. Operations, audit и techlog являются разными сущностями и не заменяют друг друга:

- operation фиксирует business operation и результат;
- audit фиксирует значимые действия пользователей и администраторов;
- techlog фиксирует системные события, ошибки и сбои.

## AuditRecord

Обязательные поля:

- `occurred_at`;
- `user_id`, если действие связано с пользователем;
- `action_code`;
- `entity_type`;
- `entity_id`;
- `store_id`, если действие относится к магазину/кабинету;
- `operation_id`, если действие относится к operation;
- `safe_message`;
- `before_snapshot` / `after_snapshot`, если нужно объяснить изменение без раскрытия secret values;
- `source_context`: UI/API/service/future automatic context;
- `visible_scope`: limited/full.
- `retention_until`: дата, после которой запись может быть удалена только регламентной non-UI процедурой.

Audit records формируются автоматически, не редактируются и не удаляются обычным UI/admin action.

## Audit action catalog этапа 1

Коды являются фиксированным системным словарём этапа 1. Добавление action codes выполняется через проектное решение/миграцию и не должно менять бизнес-логику WB/Ozon.

| Action code | Когда создаётся | Entity | Связи |
| --- | --- | --- | --- |
| `operation.check_started` | пользователь/сервис запустил проверку | Operation | operation, store, user |
| `operation.process_started` | пользователь/сервис запустил обработку | Operation | operation, check basis, store, user |
| `operation.warning_confirmed` | пользователь подтвердил confirmable warnings | WarningConfirmation | check operation, process operation, user |
| `file.input_uploaded` | загружена входная версия файла | FileVersion | file, run, store, user |
| `file.input_replaced` | загружена новая версия вместо предыдущей в run context | FileVersion | old/new file versions, run, user |
| `file.output_downloaded` | скачан output file, если контроль скачивания включён | FileVersion | operation, file, user |
| `settings.wb_parameter_changed` | изменён WB system/store parameter | ParameterValue | parameter, store nullable, user |
| `store.created` | создан магазин/кабинет | StoreAccount | store, user |
| `store.changed` | изменена карточка магазина/кабинета | StoreAccount | store, user |
| `store.archived_or_deactivated` | магазин/кабинет архивирован или деактивирован | StoreAccount | store, user |
| `store.connection_changed` | изменён API/connection block без раскрытия secret | ConnectionBlock | store, user |
| `store.connection_secret_changed` | добавлен/изменён protected secret reference | ConnectionBlock | store, user |
| `store.access_changed` | изменён object access к store/account | StoreAccess | store, affected user/role, actor |
| `user.created` | создан пользователь | User | affected user, actor |
| `user.changed` | изменены значимые поля пользователя | User | affected user, actor |
| `user.blocked_or_unblocked` | пользователь заблокирован/разблокирован | User | affected user, actor |
| `user.archived` | пользователь архивирован по policy | User | affected user, actor |
| `role.created` | создана роль | Role | role, actor |
| `role.changed` | изменены role permissions/sections/status | Role | role, actor |
| `role.archived_or_deactivated` | роль архивирована/деактивирована | Role | role, actor |
| `permission.override_changed` | изменён индивидуальный grant/deny | UserPermissionOverride | affected user, store nullable, actor |
| `system.dictionary_changed_by_migration` | fixed dictionary changed by approved migration/ADR | System dictionary | ADR/migration reference |

Минимальный перечень основан на ТЗ §20.2. Если реализации требуется зафиксировать "иное критичное действие", агент обязан добавить action code в этот каталог через документационную задачу и при необходимости GAP/ADR.

## TechLogRecord

Обязательные поля:

- `occurred_at`;
- `severity`;
- `event_type`;
- `operation_id`, если событие связано с operation;
- `store_id`, если событие связано с магазином/кабинетом;
- `user_id`, если безопасно и применимо;
- `safe_message`;
- `sensitive_details_ref`, если есть подробная диагностика;
- `source_component`;
- `handled_status`: recorded/notification_created/resolved_by_operator/future values.
- `retention_until`: дата, после которой запись может быть удалена только регламентной non-UI процедурой.

Techlog records не редактируются и не удаляются обычными UI/admin actions.

## Retention audit/techlog

- Audit records хранятся 90 дней.
- Techlog records хранятся 90 дней.
- Очистка выполняется только регламентной процедурой, не через обычный UI.
- Реализация этапа 1 предоставляет management command `cleanup_audit_techlog` и сервисы cleanup; команда удаляет только записи с истёкшим `retention_until`.
- Операции и метаданные сохраняются по существующим правилам документации; очистка audit/techlog не удаляет operation, file metadata, parameter snapshots, detail rows или historical links.
- Процедура очистки оставляет технический след выполнения в command output / server logger и не раскрывает sensitive details пользователям без `techlog.sensitive.view`.

## Techlog event catalog этапа 1

| Event type | Severity baseline | Когда создаётся | Связи |
| --- | --- | --- | --- |
| `excel.read_error` | error | ошибка чтения Excel/workbook повреждён | operation/run/file |
| `excel.template_missing_sheet` | error | отсутствует обязательный лист, например Ozon `Товары и цены` | operation/run/file |
| `excel.template_missing_columns` | error | отсутствуют обязательные колонки | operation/run/file |
| `excel.safe_write_error` | error | невозможность безопасной записи output workbook | operation/file |
| `file.storage_save_error` | critical | ошибка сохранения файла в storage | operation/run/file |
| `file.storage_read_error` | error | ошибка чтения физического файла из storage | operation/file |
| `operation.execution_failed` | critical | сбой выполнения operation | operation/store |
| `operation.interrupted_marked` | warning | operation переведена в interrupted_failed после сбоя | operation/store |
| `database.error` | critical | ошибка БД, влияющая на сценарий или сохранение данных | operation nullable |
| `application.exception` | error | системное исключение приложения | operation nullable |
| `connection.future_api_error` | error | ошибка будущего API-подключения в protected connection block | store/connection |
| `notification.critical_created` | warning | создано системное уведомление о критичной проблеме | notification/operation nullable |
| `backup.restore_check_failed` | critical | проверка восстановления/целостности неуспешна | deployment/runbook context |

Severity может уточняться реализацией только в пределах технической классификации, без изменения business outcome и без сокрытия critical failures.

## Видимость и чувствительные детали

- `safe_message` должен быть пригоден для UI без раскрытия паролей, API-ключей, protected secret values, bearer values, authorization headers, stack traces с секретами и внутренних путей, если они чувствительны.
- `sensitive_details_ref` виден только при `techlog.sensitive.view`; наличие `logs.scope.full` или object access не заменяет это право. Даже при наличии права `sensitive_details_ref` не содержит token, authorization header, API key, bearer value or secret-like value; такие значения хранятся только через `protected_secret_ref`.
- Пользователь с limited scope видит store-linked и operation-linked audit/techlog records только в пределах доступных stores/accounts и доступных operations. Собственное авторство записи не даёт обход object access для записей, связанных с недоступным store/account или operation.
- Пользователь с limited scope может видеть собственные global/non-store/non-operation audit/techlog records, если запись не раскрывает данные чужих stores/accounts или operations и не содержит sensitive details.
- Full scope даёт видимость records в полном контуре при наличии соответствующего list/card права, но не отменяет запрет на sensitive details без `techlog.sensitive.view` и не разрешает редактирование или обычное удаление audit/techlog.

## UI и фильтры

Списки audit и techlog обязаны поддерживать:

- period;
- user, если применимо;
- action/event type;
- related store;
- related operation;
- severity для techlog и если применимо для audit;
- search by visible_id/entity.

Карточки audit/techlog показывают read-only record, links to related entities and access-aware details.

## Связь с operations

- Operation card показывает links to audit/techlog при наличии связанных записей.
- Audit/techlog card показывает link back to operation, если связь есть.
- Detail row reason/result codes WB/Ozon не являются audit action codes. Они относятся к operation detail/report и системным словарям бизнес-результатов.
- Закрытый перечень WB reason/result codes описан в `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md` и `docs/architecture/DATA_MODEL.md`.
- Закрытый перечень WB API Stage 2.1 reason/result codes описан в `docs/product/WB_DISCOUNTS_API_SPEC.md` и `docs/architecture/DATA_MODEL.md`.

## Stage 2.1 WB API audit actions

Трассировка: `tz_stage_2.1.txt` §10-§11; ADR-0019, ADR-0020.

| Action code | Когда создаётся | Entity | Связи |
| --- | --- | --- | --- |
| `wb_api_connection_created` | создано WB API подключение или secret ref | ConnectionBlock | store, user |
| `wb_api_connection_updated` | изменены metadata/status/secret ref подключения | ConnectionBlock | store, user |
| `wb_api_connection_checked` | выполнена проверка подключения | ConnectionBlock | store, user |
| `wb_api_prices_download_started` | запущено скачивание цен | Operation | operation, store, user |
| `wb_api_prices_download_completed` | скачивание цен завершено | Operation | operation, store, files |
| `wb_api_prices_file_downloaded` | пользователь скачал Excel цен | FileVersion | operation, file, user |
| `wb_api_promotions_download_started` | запущено скачивание текущих акций | Operation | operation, store, user |
| `wb_api_promotions_download_completed` | скачивание текущих акций завершено | Operation | operation, store, files |
| `wb_api_promotions_file_downloaded` | пользователь скачал promo Excel | FileVersion | operation, file, promotion, user |
| `wb_api_discount_calculation_started` | запущен расчёт по API источникам | Operation | operation, store, input files |
| `wb_api_discount_calculation_completed` | расчёт завершён | Operation | operation, output file |
| `wb_api_discount_result_downloaded` | пользователь скачал итоговый Excel/detail | FileVersion | operation, file, user |
| `wb_api_discount_upload_confirmed` | пользователь явно подтвердил API upload | Operation | calculation operation, upload operation, user |
| `wb_api_discount_upload_started` | upload отправлен или начал batch processing | Operation | operation, store, batches |
| `wb_api_discount_upload_completed` | upload завершён без критического сбоя | Operation | operation, batches |
| `wb_api_discount_upload_failed` | upload завершён ошибкой или прерван | Operation | operation, batches |

Audit safe snapshots не содержат token, authorization headers, raw secret values.

## Stage 2.1 WB API techlog event types

| Event type | Severity baseline | Когда создаётся | Связи |
| --- | --- | --- | --- |
| `wb_api_auth_failed` | error | WB API вернул auth/access failure | operation/store/connection |
| `wb_api_rate_limited` | warning | WB API вернул 429 или rate limiter exhausted | operation/store |
| `wb_api_timeout` | warning | timeout внешнего WB API | operation/store |
| `wb_api_response_invalid` | error | ответ WB API не соответствует ожидаемой schema | operation/store |
| `wb_api_prices_download_failed` | error | 2.1.1 завершён ошибкой | operation/store |
| `wb_api_promotions_download_failed` | error | 2.1.2 завершён ошибкой | operation/store |
| `wb_api_upload_failed` | error | 2.1.4 upload failed | operation/store |
| `wb_api_upload_status_poll_failed` | error | не удалось получить итоговый статус upload | operation/store/uploadID |
| `wb_api_upload_partial_errors` | warning | WB status 5 или товарные partial errors | operation/store/uploadID |
| `wb_api_quarantine_detected` | warning | обнаружен quarantine-related upload result | operation/store/product |
| `wb_api_secret_redaction_violation` | critical | защита обнаружила secret в safe контуре | operation nullable |

Sensitive diagnostics доступны только через `sensitive_details_ref` и право `techlog.sensitive.view`, но сами secrets не сохраняются даже туда.

## Stage 2.2 Ozon API audit actions

Трассировка: `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`; ADR-0024, ADR-0027.

`ozon_api_elastic_result_reviewed` is an audit action for calculation result state changes, not an `Operation.step_code`.

| Action code | Когда создаётся | Entity | Связи |
| --- | --- | --- | --- |
| `ozon_api_connection_created` | создано Ozon API подключение или secret ref | ConnectionBlock | store, user |
| `ozon_api_connection_updated` | изменены metadata/status/secret ref подключения | ConnectionBlock | store, user |
| `ozon_api_connection_checked` | выполнена проверка подключения | ConnectionBlock | store, user |
| `ozon_api_actions_download_started` | запущено скачивание actions | Operation | operation, store, user |
| `ozon_api_actions_download_completed` | actions download завершён | Operation | operation, store |
| `ozon_api_elastic_active_download_completed` | participating products download завершён | Operation | operation, store, action |
| `ozon_api_elastic_candidates_download_completed` | candidates download завершён | Operation | operation, store, action |
| `ozon_api_elastic_product_data_download_completed` | product info/stocks join завершён | Operation | operation, store, action |
| `ozon_api_elastic_calculation_completed` | calculation завершён | Operation | operation, output file |
| `ozon_api_elastic_result_reviewed` | пользователь принял или не принял результат | CalculationResult | operation, store, user |
| `ozon_api_elastic_result_file_downloaded` | пользователь скачал result/manual/upload report | FileVersion | operation, file, user |
| `ozon_api_elastic_upload_confirmed` | пользователь подтвердил add/update upload | Operation | calculation operation, upload operation, user |
| `ozon_api_elastic_deactivate_group_confirmed` | пользователь одним действием подтвердил всю группу `deactivate_from_action` | CalculationResult | calculation operation, user, deactivate row count |
| `ozon_api_elastic_upload_blocked_deactivate_unconfirmed` | upload не создан, потому что группа `deactivate_from_action` не подтверждена | CalculationResult | calculation operation, user, deactivate row count |
| `ozon_api_elastic_upload_started` | upload отправлен или начал batch processing | Operation | operation, store, batches |
| `ozon_api_elastic_upload_completed` | upload завершён без критического сбоя | Operation | operation, batches |
| `ozon_api_elastic_upload_failed` | upload завершён ошибкой или прерван | Operation | operation, batches |

Audit safe snapshots never contain Client-Id, Api-Key, authorization headers, raw secret values or raw sensitive API responses.

## Stage 2.2 Ozon API techlog event types

| Event type | Severity baseline | Когда создаётся | Связи |
| --- | --- | --- | --- |
| `ozon_api_auth_failed` | error | Ozon API returned auth/access failure | operation/store/connection |
| `ozon_api_rate_limited` | warning | Ozon API returned 429 or rate limiter exhausted | operation/store |
| `ozon_api_timeout` | warning | timeout external Ozon API | operation/store |
| `ozon_api_response_invalid` | error | response schema invalid for expected endpoint | operation/store |
| `ozon_api_actions_download_failed` | error | actions download failed | operation/store |
| `ozon_api_elastic_product_data_download_failed` | error | product info/stocks join failed | operation/store/action |
| `ozon_api_elastic_calculation_failed` | error | calculation failed | operation/store/action |
| `ozon_api_elastic_upload_failed` | error | upload failed | operation/store/action |
| `ozon_api_elastic_upload_partial_errors` | warning | partial row-level upload errors | operation/store/action |
| `ozon_api_secret_redaction_violation` | critical | secret-like value detected in safe contour | operation nullable |

Sensitive diagnostics follow common rules and never store Client-Id, Api-Key, authorization header, bearer/API key or secret-like values.
