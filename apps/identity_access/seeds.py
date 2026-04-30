"""Seed data and idempotent helpers for TASK-002 roles and permissions."""

from __future__ import annotations

from django.db import transaction

from .models import (
    OWNER_ROLE_CODE,
    Permission,
    Role,
    RolePermission,
    RoleSectionAccess,
    SectionAccess,
    system_dictionary_mutation,
)


ROLE_OWNER = OWNER_ROLE_CODE
ROLE_GLOBAL_ADMIN = "global_admin"
ROLE_LOCAL_ADMIN = "local_admin"
ROLE_MARKETPLACE_MANAGER = "marketplace_manager"
ROLE_OBSERVER = "observer"

ROLE_DEFINITIONS = {
    ROLE_OWNER: "Владелец",
    ROLE_GLOBAL_ADMIN: "Глобальный администратор",
    ROLE_LOCAL_ADMIN: "Локальный администратор",
    ROLE_MARKETPLACE_MANAGER: "Менеджер маркетплейсов",
    ROLE_OBSERVER: "Наблюдатель",
}

PERMISSION_DEFINITIONS = {
    "users.list.view": ("просмотр пользователей", Permission.ScopeType.GLOBAL_STORE),
    "users.card.view": ("просмотр карточки пользователя", Permission.ScopeType.GLOBAL_STORE),
    "users.create": ("создание пользователя", Permission.ScopeType.GLOBAL_STORE),
    "users.edit": ("изменение пользователя", Permission.ScopeType.GLOBAL_STORE),
    "users.status.change": ("блокировка/разблокировка пользователя", Permission.ScopeType.GLOBAL_STORE),
    "users.archive": ("архивирование пользователя", Permission.ScopeType.GLOBAL_STORE),
    "users.owner.manage": ("управление владельцем", Permission.ScopeType.OWNER_ONLY),
    "roles.list.view": ("просмотр ролей", Permission.ScopeType.GLOBAL),
    "roles.card.view": ("просмотр карточки роли", Permission.ScopeType.GLOBAL),
    "roles.edit": ("изменение ролей и состава прав", Permission.ScopeType.GLOBAL),
    "permissions.assign": ("назначение ролей и индивидуальных прав", Permission.ScopeType.GLOBAL_STORE),
    "section_access.view": ("просмотр разделов и доступов", Permission.ScopeType.GLOBAL_STORE),
    "section_access.edit": ("изменение разделов и доступов", Permission.ScopeType.GLOBAL_STORE),
    "wb_discounts_excel.view": ("WB: видеть сценарий", Permission.ScopeType.STORE),
    "wb_discounts_excel.upload_input": ("WB: загружать входной файл", Permission.ScopeType.STORE),
    "wb_discounts_excel.run_check": ("WB: запускать проверку", Permission.ScopeType.STORE),
    "wb_discounts_excel.view_check_result": ("WB: просматривать результат проверки", Permission.ScopeType.STORE),
    "wb_discounts_excel.view_details": ("WB: просматривать ошибки/предупреждения", Permission.ScopeType.STORE),
    "wb_discounts_excel.confirm_warnings": ("WB: подтверждать предупреждения", Permission.ScopeType.STORE),
    "wb_discounts_excel.run_process": ("WB: запускать обработку", Permission.ScopeType.STORE),
    "wb_discounts_excel.view_process_result": ("WB: просматривать результат обработки", Permission.ScopeType.STORE),
    "wb_discounts_excel.download_output": ("WB: скачивать выходной файл", Permission.ScopeType.STORE),
    "wb_discounts_excel.download_detail_report": ("WB: скачивать отчёт детализации", Permission.ScopeType.STORE),
    "wb_discounts_excel.view_related_operations": ("WB: просматривать связанные операции", Permission.ScopeType.STORE),
    "wb_discounts_excel.rerun_check": ("WB: запускать повторную проверку", Permission.ScopeType.STORE),
    "wb_discounts_excel.rerun_process": ("WB: запускать повторную обработку", Permission.ScopeType.STORE),
    "ozon_discounts_excel.view": ("Ozon: видеть сценарий", Permission.ScopeType.STORE),
    "ozon_discounts_excel.upload_input": ("Ozon: загружать входной файл", Permission.ScopeType.STORE),
    "ozon_discounts_excel.run_check": ("Ozon: запускать проверку", Permission.ScopeType.STORE),
    "ozon_discounts_excel.view_check_result": ("Ozon: просматривать результат проверки", Permission.ScopeType.STORE),
    "ozon_discounts_excel.view_details": ("Ozon: просматривать ошибки/предупреждения", Permission.ScopeType.STORE),
    "ozon_discounts_excel.confirm_warnings": ("Ozon: подтверждать предупреждения", Permission.ScopeType.STORE),
    "ozon_discounts_excel.run_process": ("Ozon: запускать обработку", Permission.ScopeType.STORE),
    "ozon_discounts_excel.view_process_result": ("Ozon: просматривать результат обработки", Permission.ScopeType.STORE),
    "ozon_discounts_excel.download_output": ("Ozon: скачивать выходной файл", Permission.ScopeType.STORE),
    "ozon_discounts_excel.download_detail_report": ("Ozon: скачивать отчёт детализации", Permission.ScopeType.STORE),
    "ozon_discounts_excel.view_related_operations": ("Ozon: просматривать связанные операции", Permission.ScopeType.STORE),
    "ozon_discounts_excel.rerun_check": ("Ozon: запускать повторную проверку", Permission.ScopeType.STORE),
    "ozon_discounts_excel.rerun_process": ("Ozon: запускать повторную обработку", Permission.ScopeType.STORE),
    "settings.system_params.view": ("просмотр системных параметров", Permission.ScopeType.GLOBAL),
    "settings.system_params.edit": ("изменение системных параметров", Permission.ScopeType.GLOBAL),
    "settings.store_params.view": ("просмотр параметров магазина", Permission.ScopeType.STORE),
    "settings.store_params.edit": ("изменение параметров магазина", Permission.ScopeType.STORE),
    "settings.param_history.view": ("просмотр истории параметров", Permission.ScopeType.GLOBAL_STORE),
    "settings.param_source.view": ("просмотр источника значения", Permission.ScopeType.GLOBAL_STORE),
    "settings.service.view": ("просмотр служебных настроек", Permission.ScopeType.GLOBAL),
    "settings.service.edit": ("изменение служебных настроек", Permission.ScopeType.GLOBAL),
    "stores.list.view": ("просмотр списка магазинов", Permission.ScopeType.GLOBAL_STORE),
    "stores.card.view": ("просмотр карточки магазина", Permission.ScopeType.GLOBAL_STORE),
    "stores.create": ("создание магазина", Permission.ScopeType.GLOBAL_STORE),
    "stores.edit": ("изменение магазина", Permission.ScopeType.GLOBAL_STORE),
    "stores.params.edit": ("изменение параметров магазина", Permission.ScopeType.STORE),
    "stores.connection.view": ("просмотр блока подключения", Permission.ScopeType.STORE),
    "stores.connection.edit": ("изменение блока подключения", Permission.ScopeType.STORE),
    "stores.connection.secret_edit": ("добавление/изменение API-ключей", Permission.ScopeType.STORE),
    "stores.access.assign": ("назначение доступов к магазину", Permission.ScopeType.GLOBAL_STORE),
    "stores.operations.view": ("просмотр операций магазина", Permission.ScopeType.STORE),
    "stores.history.view": ("просмотр истории изменений магазина", Permission.ScopeType.STORE),
    "audit.list.view": ("просмотр списка аудита", Permission.ScopeType.GLOBAL_STORE),
    "audit.card.view": ("просмотр карточки аудита", Permission.ScopeType.GLOBAL_STORE),
    "techlog.list.view": ("просмотр списка техжурнала", Permission.ScopeType.GLOBAL_STORE),
    "techlog.card.view": ("просмотр карточки техжурнала", Permission.ScopeType.GLOBAL_STORE),
    "logs.scope.limited": ("ограниченный контур записей", Permission.ScopeType.GLOBAL_STORE),
    "logs.scope.full": ("полный контур записей", Permission.ScopeType.GLOBAL),
    "techlog.sensitive.view": ("чувствительные технические детали", Permission.ScopeType.GLOBAL),
    "wb.api.connection.view": ("WB API: просмотр подключения", Permission.ScopeType.STORE),
    "wb.api.connection.manage": ("WB API: управление подключением", Permission.ScopeType.STORE),
    "wb.api.prices.download": ("WB API: скачать цены", Permission.ScopeType.STORE),
    "wb.api.prices.file.download": ("WB API: скачать Excel цен", Permission.ScopeType.STORE),
    "wb.api.promotions.download": ("WB API: скачать текущие акции", Permission.ScopeType.STORE),
    "wb.api.promotions.file.download": ("WB API: скачать Excel акций", Permission.ScopeType.STORE),
    "wb.api.discounts.calculate": ("WB API: рассчитать скидки", Permission.ScopeType.STORE),
    "wb.api.discounts.result.download": (
        "WB API: скачать итоговый Excel/detail",
        Permission.ScopeType.STORE,
    ),
    "wb.api.discounts.upload": ("WB API: выполнить upload скидок", Permission.ScopeType.STORE),
    "wb.api.discounts.upload.confirm": (
        "WB API: подтвердить upload скидок",
        Permission.ScopeType.STORE,
    ),
    "wb.api.operation.view": ("WB API: просмотр операций", Permission.ScopeType.STORE),
    "ozon.api.connection.view": ("Ozon API: просмотр подключения", Permission.ScopeType.STORE),
    "ozon.api.connection.manage": ("Ozon API: управление подключением", Permission.ScopeType.STORE),
    "ozon.api.actions.view": ("Ozon API: просмотр actions/Elastic workflow", Permission.ScopeType.STORE),
    "ozon.api.actions.download": ("Ozon API: скачать доступные акции", Permission.ScopeType.STORE),
    "ozon.api.elastic.active_products.download": (
        "Ozon API: скачать товары участвующие в акции",
        Permission.ScopeType.STORE,
    ),
    "ozon.api.elastic.candidates.download": (
        "Ozon API: скачать кандидаты в акцию",
        Permission.ScopeType.STORE,
    ),
    "ozon.api.elastic.product_data.download": (
        "Ozon API: скачать product info/stocks",
        Permission.ScopeType.STORE,
    ),
    "ozon.api.elastic.calculate": ("Ozon API: рассчитать Elastic Boosting", Permission.ScopeType.STORE),
    "ozon.api.elastic.review": ("Ozon API: принять/не принять результат", Permission.ScopeType.STORE),
    "ozon.api.elastic.upload": ("Ozon API: выполнить API upload add/update", Permission.ScopeType.STORE),
    "ozon.api.elastic.upload.confirm": (
        "Ozon API: подтвердить API upload add/update",
        Permission.ScopeType.STORE,
    ),
    "ozon.api.elastic.deactivate.confirm": (
        "Ozon API: подтвердить группу deactivate",
        Permission.ScopeType.STORE,
    ),
    "ozon.api.elastic.files.download": ("Ozon API: скачать Stage 2.2 файлы", Permission.ScopeType.STORE),
    "ozon.api.operation.view": ("Ozon API: просмотр операций", Permission.ScopeType.STORE),
}

SECTION_DEFINITIONS = {
    "home.view": ("home", "view", "Главная"),
    "wb_discounts_excel.view": ("wb_discounts_excel", "view", "WB Excel"),
    "ozon_discounts_excel.view": ("ozon_discounts_excel", "view", "Ozon Excel"),
    "operations.view": ("operations", "view", "Операции"),
    "stores.view": ("stores", "view", "Магазины/кабинеты"),
    "products.view": ("products", "view", "Товары"),
    "settings_system.view": ("settings_system", "view", "Системные параметры"),
    "settings_store.view": ("settings_store", "view", "Параметры магазина"),
    "users.view": ("users", "view", "Пользователи"),
    "roles.view": ("roles", "view", "Роли"),
    "permissions.view": ("permissions", "view", "Права доступа"),
    "store_access.view": ("store_access", "view", "Доступы к магазинам"),
    "audit.view": ("audit", "view", "Аудит"),
    "techlog.view": ("techlog", "view", "Техжурнал"),
    "wb_discounts_api.view": ("wb_discounts_api", "view", "WB API"),
    "ozon_discounts_api.view": ("ozon_discounts_api", "view", "Ozon API"),
}


ALL_PERMISSION_CODES = set(PERMISSION_DEFINITIONS)
ADMIN_PERMISSION_CODES = {
    code
    for code in ALL_PERMISSION_CODES
    if code.startswith(("users.", "roles.", "permissions.", "section_access."))
}
STORE_SETTINGS_CODES = {
    "settings.store_params.view",
    "settings.store_params.edit",
    "settings.param_history.view",
    "settings.param_source.view",
}
STORE_CODES = {code for code in ALL_PERMISSION_CODES if code.startswith("stores.")}
AUDIT_TECHLOG_CODES = {
    "audit.list.view",
    "audit.card.view",
    "techlog.list.view",
    "techlog.card.view",
    "logs.scope.limited",
}
SCENARIO_CODES = {
    code
    for code in ALL_PERMISSION_CODES
    if code.startswith(("wb_discounts_excel.", "ozon_discounts_excel."))
}
WB_API_CONNECTION_CODES = {
    "wb.api.connection.view",
    "wb.api.connection.manage",
    "wb.api.operation.view",
}
OZON_API_CONNECTION_CODES = {
    "ozon.api.connection.view",
    "ozon.api.connection.manage",
    "ozon.api.operation.view",
}
WB_API_MANAGER_CODES = {
    "wb.api.prices.download",
    "wb.api.prices.file.download",
    "wb.api.promotions.download",
    "wb.api.promotions.file.download",
    "wb.api.discounts.calculate",
    "wb.api.discounts.result.download",
    "wb.api.operation.view",
}
OZON_API_MANAGER_CODES = {
    "ozon.api.actions.view",
    "ozon.api.actions.download",
    "ozon.api.elastic.active_products.download",
    "ozon.api.elastic.candidates.download",
    "ozon.api.elastic.product_data.download",
    "ozon.api.elastic.calculate",
    "ozon.api.elastic.review",
    "ozon.api.elastic.files.download",
    "ozon.api.operation.view",
}

LOCAL_ADMIN_PERMISSION_CODES = (
    {code for code in ADMIN_PERMISSION_CODES if not code.startswith("roles.")}
    | STORE_CODES
    | STORE_SETTINGS_CODES
    | AUDIT_TECHLOG_CODES
    | WB_API_CONNECTION_CODES
    | OZON_API_CONNECTION_CODES
) - {
    "users.owner.manage",
    "roles.edit",
    "settings.system_params.edit",
    "techlog.sensitive.view",
}

MANAGER_PERMISSION_CODES = (
    SCENARIO_CODES
    | WB_API_MANAGER_CODES
    | OZON_API_MANAGER_CODES
    | {
        "stores.list.view",
        "stores.card.view",
        "stores.operations.view",
        "settings.store_params.view",
        "settings.store_params.edit",
        "settings.param_history.view",
        "settings.param_source.view",
    }
) - {
    "users.owner.manage",
    "settings.system_params.edit",
}

OBSERVER_PERMISSION_CODES = {
    "stores.list.view",
    "stores.card.view",
    "stores.operations.view",
    "wb_discounts_excel.view",
    "wb_discounts_excel.view_check_result",
    "wb_discounts_excel.view_details",
    "wb_discounts_excel.view_process_result",
    "wb_discounts_excel.view_related_operations",
    "ozon_discounts_excel.view",
    "ozon_discounts_excel.view_check_result",
    "ozon_discounts_excel.view_details",
    "ozon_discounts_excel.view_process_result",
    "ozon_discounts_excel.view_related_operations",
    "settings.store_params.view",
    "settings.param_history.view",
    "audit.list.view",
    "audit.card.view",
    "techlog.list.view",
    "techlog.card.view",
    "logs.scope.limited",
}

ROLE_PERMISSION_CODES = {
    ROLE_OWNER: ALL_PERMISSION_CODES,
    ROLE_GLOBAL_ADMIN: ALL_PERMISSION_CODES - {"users.owner.manage"},
    ROLE_LOCAL_ADMIN: LOCAL_ADMIN_PERMISSION_CODES,
    ROLE_MARKETPLACE_MANAGER: MANAGER_PERMISSION_CODES,
    ROLE_OBSERVER: OBSERVER_PERMISSION_CODES,
}

ROLE_SECTION_CODES = {
    ROLE_OWNER: set(SECTION_DEFINITIONS),
    ROLE_GLOBAL_ADMIN: set(SECTION_DEFINITIONS),
    ROLE_LOCAL_ADMIN: {
        "home.view",
        "stores.view",
        "wb_discounts_api.view",
        "ozon_discounts_api.view",
        "settings_store.view",
        "users.view",
        "permissions.view",
        "store_access.view",
        "audit.view",
        "techlog.view",
    },
    ROLE_MARKETPLACE_MANAGER: {
        "home.view",
        "wb_discounts_excel.view",
        "wb_discounts_api.view",
        "ozon_discounts_api.view",
        "ozon_discounts_excel.view",
        "operations.view",
        "stores.view",
        "products.view",
        "settings_store.view",
    },
    ROLE_OBSERVER: {
        "home.view",
        "operations.view",
        "stores.view",
        "products.view",
        "settings_store.view",
        "audit.view",
        "techlog.view",
    },
}


@transaction.atomic
def seed_identity_access() -> dict[str, int]:
    stats = {
        "roles": 0,
        "permissions": 0,
        "sections": 0,
        "role_permissions": 0,
        "role_sections": 0,
    }

    with system_dictionary_mutation():
        roles = {}
        for code, name in ROLE_DEFINITIONS.items():
            role, created = Role.objects.update_or_create(
                code=code,
                defaults={"name": name, "status": Role.Status.ACTIVE, "is_system": True},
            )
            roles[code] = role
            stats["roles"] += int(created)

        permissions = {}
        for code, (name, scope_type) in PERMISSION_DEFINITIONS.items():
            permission, created = Permission.objects.update_or_create(
                code=code,
                defaults={"name": name, "scope_type": scope_type, "is_system": True},
            )
            permissions[code] = permission
            stats["permissions"] += int(created)

        sections = {}
        for code, (section, mode, name) in SECTION_DEFINITIONS.items():
            section_access, created = SectionAccess.objects.update_or_create(
                code=code,
                defaults={
                    "section": section,
                    "mode": mode,
                    "name": name,
                    "is_system": True,
                },
            )
            sections[code] = section_access
            stats["sections"] += int(created)

        for role_code, permission_codes in ROLE_PERMISSION_CODES.items():
            role = roles[role_code]
            for permission_code in permission_codes:
                _, created = RolePermission.objects.get_or_create(
                    role=role,
                    permission=permissions[permission_code],
                )
                stats["role_permissions"] += int(created)

        for role_code, section_codes in ROLE_SECTION_CODES.items():
            role = roles[role_code]
            for section_code in section_codes:
                _, created = RoleSectionAccess.objects.get_or_create(
                    role=role,
                    section_access=sections[section_code],
                )
                stats["role_sections"] += int(created)

    return stats
