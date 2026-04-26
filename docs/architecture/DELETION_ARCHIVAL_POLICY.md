# DELETION_ARCHIVAL_POLICY.md

Трассировка: ТЗ §11.5, §13.4, §20.2-§20.3, §21, §27.1-§27.2.

## Назначение

Документ фиксирует смешанную модель удаления, блокировки, деактивации и архивирования этапа 1. Правило применяется ко всем продуктовым задачам реализации и миграциям.

## Базовое правило

- Если сущность уже участвовала в работе системы, физическое удаление запрещено. Используется блокировка, деактивация или архивирование.
- Если сущность создана ошибочно и нигде не использовалась, физическое удаление допустимо только при отсутствии связей с operation, audit, techlog, file versions, permissions, store access и history records.
- Завершённые operations, audit records и techlog records не удаляются обычными пользовательскими или административными интерфейсами.
- Удаление физических файлов по сроку хранения не удаляет metadata, operation и связи с file entity.

## Правила по сущностям

| Сущность | Если не использовалась | Если участвовала в работе | Обязательная история/связи |
| --- | --- | --- | --- |
| User | можно физически удалить до первого входа, назначения, audit или operation | блокировать, деактивировать или архивировать; владельца нельзя удалить/заблокировать администратором | `UserChangeHistory`, `UserBlockHistory`, audit |
| Role | можно удалить, если не назначалась пользователям и не попадала в audit/history | деактивировать/архивировать; system role не удаляется | audit, user history |
| Permission / SectionAccess | пользовательское удаление системных codes запрещено | immutable system dictionary; изменение состава только через миграцию/ADR | audit/ADR |
| UserPermissionOverride | можно удалить до применения | после применения закрывается новой записью/деактивацией, история сохраняется | audit, user history |
| StoreAccess | можно удалить до применения | после применения закрывается новой записью/деактивацией, история сохраняется | audit, store/user history |
| BusinessGroup | можно удалить без stores и history | архивировать/деактивировать | store history |
| StoreAccount | можно удалить, если нет operations, files, params, access, products, history | архивировать/деактивировать; операции и история сохраняются | `StoreAccountChangeHistory`, audit |
| ConnectionBlock | можно удалить до сохранения secret/history и без операций | деактивировать/архивировать; protected secrets очищаются только по утверждённому security/retention регламенту | audit, store history |
| MarketplaceProduct | можно удалить, если создан ошибочно и нет operation/file/history links | деактивировать/архивировать; история появления/обновления сохраняется | `MarketplaceProductHistory` |
| Run | можно удалить только черновой контекст без operations/files | после запуска operation не удаляется обычным способом | operation/file links |
| Operation | не применяется | физическое удаление и редактирование запрещены; повторная попытка только новой operation | audit/techlog/file links |
| OperationDetailRow | не применяется | хранится вместе с operation, не редактируется | operation |
| FileObject / FileVersion metadata | можно удалить ошибочную загрузку до operation | metadata и versions сохраняются; физический файл удаляется только по retention | operation links, checksum |
| Физический файл | можно удалить ошибочную загрузку до operation | удаляется по сроку хранения 3 дня; UI показывает истечение срока | file metadata |
| ParameterDefinition | пользовательское удаление запрещено | immutable system dictionary | ADR/migration |
| SystemParameterValue | можно удалить ошибочное значение до применения | закрывается новым effective value; snapshots старых operations сохраняются | parameter history, operation snapshots |
| StoreParameterValue | можно удалить до применения | закрывается новым effective value; snapshots старых operations сохраняются | `ParameterChangeHistory` |
| WarningConfirmation | не применяется | не редактируется и не удаляется обычным способом | audit, operations |
| AuditRecord | не применяется | хранится 90 дней; не редактируется и не удаляется обычным способом; очистка только регламентной процедурой | retention procedure |
| TechLogRecord | не применяется | хранится 90 дней; не редактируется; очистка только регламентной процедурой | retention procedure |
| SystemNotification | можно удалить черновую/ошибочную до публикации | закрывается статусом/архивируется, если была показана пользователям или связана с событием | techlog/operation links |

## UI-ограничения

Интерфейс реализации не должен показывать обычное действие "Удалить" для сущности, если по ней есть признаки использования. Вместо этого показываются действия:

- "Заблокировать" для пользователей;
- "Деактивировать" или "Архивировать" для магазинов/кабинетов, ролей, товаров, подключений и уведомлений;
- "Истёк срок хранения" для физических файлов после retention;
- "Создать новую операцию" для повторной попытки вместо изменения завершённой operation.

## Retention audit/techlog

Audit records и techlog records хранятся 90 дней. Очистка после срока хранения выполняется только регламентной процедурой и не доступна как обычное UI-действие.

Очистка audit/techlog не удаляет operations, metadata, file version links, parameter snapshots, detail rows и business history, которые сохраняются по профильным правилам документации.
