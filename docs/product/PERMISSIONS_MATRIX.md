# PERMISSIONS_MATRIX.md

Трассировка: ТЗ §8, §11, §20, §27.

## Принципы доступа

В системе разделены:

- права на действия;
- доступы к разделам/вкладкам;
- объектные доступы к магазинам/кабинетам.

Роль является шаблоном. Поверх роли пользователь может иметь индивидуальные разрешения и запреты. Прямой запрет имеет приоритет над разрешением, включая запрет на уровне конкретного магазина/кабинета.

Если у пользователя нет доступа к магазину/кабинету, он не видит связанные операции, файлы, товары, параметры и аудит, кроме случаев глобальных административных прав.

Удаление, блокировка, деактивация и архивирование пользователей, ролей и доступов выполняются по `docs/architecture/DELETION_ARCHIVAL_POLICY.md`. Административный UI не должен давать способ удалить, заблокировать или лишить критичных прав владельца.

## Типовые роли этапа 1

| Роль | Назначение | Ограничения |
| --- | --- | --- |
| Владелец | полный аварийно-управленческий доступ | не может быть ограничен, удалён, заблокирован или лишён критичных прав администратором |
| Глобальный администратор | всё администрирование | не может ограничивать, блокировать или удалять владельца |
| Локальный администратор | управление пользователями, магазинами, параметрами и доступами в назначенных магазинах/кабинетах | ограничивается объектными доступами; не управляет владельцем и глобальными системными правами |
| Менеджер маркетплейсов | рабочие сценарии WB/Ozon Excel, операции, файлы, товары и параметры доступных магазинов | не управляет ролями и системными правами |
| Наблюдатель | просмотр доступных магазинов, операций, результатов, товаров и ограниченных журналов | не меняет данные; не скачивает итоговые файлы, если право не выдано отдельно |

## Административные права

| Право | Code | Область |
| --- | --- | --- |
| просмотр пользователей | `users.list.view` | global/store |
| просмотр карточки пользователя | `users.card.view` | global/store |
| создание пользователя | `users.create` | global/store |
| изменение пользователя | `users.edit` | global/store |
| блокировка/разблокировка пользователя | `users.status.change` | global/store |
| архивирование пользователя | `users.archive` | global/store |
| управление владельцем | `users.owner.manage` | owner-only |
| просмотр ролей | `roles.list.view` | global |
| просмотр карточки роли | `roles.card.view` | global |
| изменение ролей и состава прав | `roles.edit` | global |
| назначение ролей и индивидуальных прав | `permissions.assign` | global/store |
| просмотр разделов и доступов | `section_access.view` | global/store |
| изменение разделов и доступов | `section_access.edit` | global/store |

## Права сценариев Excel

Права WB и Ozon должны быть отдельными наборами даже при совпадении действий.

| Право | WB code | Ozon code |
| --- | --- | --- |
| видеть сценарий | `wb_discounts_excel.view` | `ozon_discounts_excel.view` |
| загружать входной файл | `wb_discounts_excel.upload_input` | `ozon_discounts_excel.upload_input` |
| запускать проверку | `wb_discounts_excel.run_check` | `ozon_discounts_excel.run_check` |
| просматривать результат проверки | `wb_discounts_excel.view_check_result` | `ozon_discounts_excel.view_check_result` |
| просматривать ошибки/предупреждения | `wb_discounts_excel.view_details` | `ozon_discounts_excel.view_details` |
| подтверждать предупреждения | `wb_discounts_excel.confirm_warnings` | `ozon_discounts_excel.confirm_warnings` |
| запускать обработку | `wb_discounts_excel.run_process` | `ozon_discounts_excel.run_process` |
| просматривать результат обработки | `wb_discounts_excel.view_process_result` | `ozon_discounts_excel.view_process_result` |
| скачивать выходной файл | `wb_discounts_excel.download_output` | `ozon_discounts_excel.download_output` |
| скачивать отчёт детализации | `wb_discounts_excel.download_detail_report` | `ozon_discounts_excel.download_detail_report` |
| просматривать связанные операции | `wb_discounts_excel.view_related_operations` | `ozon_discounts_excel.view_related_operations` |
| запускать повторную проверку | `wb_discounts_excel.rerun_check` | `ozon_discounts_excel.rerun_check` |
| запускать повторную обработку | `wb_discounts_excel.rerun_process` | `ozon_discounts_excel.rerun_process` |

## Права параметров и настроек

| Право | Code | Область |
| --- | --- | --- |
| просмотр системных параметров | `settings.system_params.view` | global |
| изменение системных параметров | `settings.system_params.edit` | global |
| просмотр параметров магазина | `settings.store_params.view` | store |
| изменение параметров магазина | `settings.store_params.edit` | store |
| просмотр истории параметров | `settings.param_history.view` | store/global |
| просмотр источника значения | `settings.param_source.view` | store/global |
| просмотр служебных настроек | `settings.service.view` | global |
| изменение служебных настроек | `settings.service.edit` | global |

## Права магазинов / кабинетов / подключений

| Право | Code |
| --- | --- |
| просмотр списка магазинов | `stores.list.view` |
| просмотр карточки магазина | `stores.card.view` |
| создание магазина | `stores.create` |
| изменение магазина | `stores.edit` |
| изменение параметров магазина | `stores.params.edit` |
| просмотр блока подключения | `stores.connection.view` |
| изменение блока подключения | `stores.connection.edit` |
| добавление/изменение API-ключей | `stores.connection.secret_edit` |
| назначение доступов к магазину | `stores.access.assign` |
| просмотр операций магазина | `stores.operations.view` |
| просмотр истории изменений магазина | `stores.history.view` |

## Права аудита и техжурнала

| Право | Code |
| --- | --- |
| просмотр списка аудита | `audit.list.view` |
| просмотр карточки аудита | `audit.card.view` |
| просмотр списка техжурнала | `techlog.list.view` |
| просмотр карточки техжурнала | `techlog.card.view` |
| ограниченный контур записей | `logs.scope.limited` |
| полный контур записей | `logs.scope.full` |
| чувствительные технические детали | `techlog.sensitive.view` |

Правила применения scope:

- `logs.scope.limited` не открывает store-linked или operation-linked audit/techlog records без object access к соответствующему store/account или operation; собственное авторство записи не является обходом object access.
- При `logs.scope.limited` пользователь может видеть собственные global/non-store/non-operation records, если они не раскрывают данные чужих stores/accounts или operations и не содержат sensitive details.
- Sensitive details в techlog доступны только при `techlog.sensitive.view`, независимо от limited/full scope и object access.
- `logs.scope.full` даёт полный контур видимости records при наличии соответствующего list/card права, но не разрешает sensitive details без `techlog.sensitive.view` и не даёт права редактировать или удалять audit/techlog обычным UI/admin action.

## Минимальная матрица ролей

Seed-набор утверждён решением заказчика и зафиксирован в ADR-0007. Это начальный conservative template; индивидуальные разрешения и запреты могут уточнять доступ пользователя, но не могут ограничить владельца административным действием.

| Право/область | Владелец | Глоб. админ | Лок. админ | Менеджер | Наблюдатель |
| --- | --- | --- | --- | --- | --- |
| Все разделы | да | да | административные в пределах store scope | рабочие WB/Ozon и справочники доступных магазинов | просмотр доступных |
| Управление владельцем | только сам владелец | нет | нет | нет | нет |
| Пользователи | да | да, кроме владельца | да, только пользователи назначенных магазинов/кабинетов | нет | нет |
| Роли и системные права | да | да, кроме ограничения владельца | нет | нет | нет |
| Object access / store access | да | да | да, только назначенные магазины/кабинеты | нет | нет |
| Магазины/кабинеты | да | да | да, только назначенные | просмотр доступных | просмотр доступных |
| WB/Ozon Excel check/process | да | да | нет по умолчанию, кроме отдельной выдачи | да для доступных магазинов | нет |
| Файлы сценариев | да | да | просмотр/администрирование в назначенных магазинах | upload/download по рабочим правам сценариев | просмотр metadata; download output/detail только отдельным правом |
| Marketplace products | да | да | просмотр/администрирование в назначенных магазинах | просмотр и обновление через Excel-операции доступных магазинов | просмотр доступных |
| WB-параметры магазина | да | да | да, только назначенные магазины/кабинеты | просмотр и изменение доступных магазинов при выданном праве | просмотр при праве |
| Системные параметры | да | да | нет | нет | нет |
| API-блок / подключения | да | да | да, только назначенные магазины/кабинеты | просмотр при праве, без secret edit по умолчанию | нет |
| Аудит/техжурнал | да | да | ограниченно по назначенным магазинам/кабинетам | ограниченно по доступным операциям/магазинам | ограниченно по доступным объектам |

## Seed-набор по правам

| Роль | Seed permissions |
| --- | --- |
| Владелец | все permission codes, все section access, все object access; владелец не ограничивается индивидуальными запретами администратора |
| Глобальный администратор | все административные, store/settings/files/operations/audit/techlog permissions, кроме `users.owner.manage`; полный object scope |
| Локальный администратор | `users.*`, `permissions.assign`, `section_access.view`, `section_access.edit`, `stores.*`, `settings.store_params.*`, `settings.param_history.view`, `settings.param_source.view`, `audit.*`, `techlog.list.view`, `techlog.card.view`, `logs.scope.limited` только в назначенном store scope; без `roles.edit`, `settings.system_params.edit`, `techlog.sensitive.view`, `users.owner.manage` |
| Менеджер маркетплейсов | `wb_discounts_excel.*`, `ozon_discounts_excel.*`, `stores.list.view`, `stores.card.view`, `stores.operations.view`, `settings.store_params.view`, `settings.store_params.edit`, `settings.param_history.view`, `settings.param_source.view`, file upload/download rights через scenario permissions, product view/update через Excel operations только в доступном store scope; без `users.*`, `roles.*`, `permissions.assign`, `settings.system_params.edit` |
| Наблюдатель | view-only permissions для доступных stores, operations, check/process results, products, `settings.store_params.view`, `settings.param_history.view`, `audit.list.view`, `audit.card.view`, `techlog.list.view`, `techlog.card.view`, `logs.scope.limited`; без upload/run/process/edit/delete/download output/detail по умолчанию |
