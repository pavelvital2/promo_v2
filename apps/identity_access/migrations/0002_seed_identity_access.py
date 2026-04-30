from django.db import migrations


ROLE_DEFINITIONS = {
    "owner": "Владелец",
    "global_admin": "Глобальный администратор",
    "local_admin": "Локальный администратор",
    "marketplace_manager": "Менеджер маркетплейсов",
    "observer": "Наблюдатель",
}

PERMISSION_DEFINITIONS = {
    "users.list.view": ("просмотр пользователей", "global_store"),
    "users.card.view": ("просмотр карточки пользователя", "global_store"),
    "users.create": ("создание пользователя", "global_store"),
    "users.edit": ("изменение пользователя", "global_store"),
    "users.status.change": ("блокировка/разблокировка пользователя", "global_store"),
    "users.archive": ("архивирование пользователя", "global_store"),
    "users.owner.manage": ("управление владельцем", "owner_only"),
    "roles.list.view": ("просмотр ролей", "global"),
    "roles.card.view": ("просмотр карточки роли", "global"),
    "roles.edit": ("изменение ролей и состава прав", "global"),
    "permissions.assign": ("назначение ролей и индивидуальных прав", "global_store"),
    "section_access.view": ("просмотр разделов и доступов", "global_store"),
    "section_access.edit": ("изменение разделов и доступов", "global_store"),
    "wb_discounts_excel.view": ("WB: видеть сценарий", "store"),
    "wb_discounts_excel.upload_input": ("WB: загружать входной файл", "store"),
    "wb_discounts_excel.run_check": ("WB: запускать проверку", "store"),
    "wb_discounts_excel.view_check_result": ("WB: просматривать результат проверки", "store"),
    "wb_discounts_excel.view_details": ("WB: просматривать ошибки/предупреждения", "store"),
    "wb_discounts_excel.confirm_warnings": ("WB: подтверждать предупреждения", "store"),
    "wb_discounts_excel.run_process": ("WB: запускать обработку", "store"),
    "wb_discounts_excel.view_process_result": ("WB: просматривать результат обработки", "store"),
    "wb_discounts_excel.download_output": ("WB: скачивать выходной файл", "store"),
    "wb_discounts_excel.download_detail_report": ("WB: скачивать отчёт детализации", "store"),
    "wb_discounts_excel.view_related_operations": ("WB: просматривать связанные операции", "store"),
    "wb_discounts_excel.rerun_check": ("WB: запускать повторную проверку", "store"),
    "wb_discounts_excel.rerun_process": ("WB: запускать повторную обработку", "store"),
    "ozon_discounts_excel.view": ("Ozon: видеть сценарий", "store"),
    "ozon_discounts_excel.upload_input": ("Ozon: загружать входной файл", "store"),
    "ozon_discounts_excel.run_check": ("Ozon: запускать проверку", "store"),
    "ozon_discounts_excel.view_check_result": ("Ozon: просматривать результат проверки", "store"),
    "ozon_discounts_excel.view_details": ("Ozon: просматривать ошибки/предупреждения", "store"),
    "ozon_discounts_excel.confirm_warnings": ("Ozon: подтверждать предупреждения", "store"),
    "ozon_discounts_excel.run_process": ("Ozon: запускать обработку", "store"),
    "ozon_discounts_excel.view_process_result": ("Ozon: просматривать результат обработки", "store"),
    "ozon_discounts_excel.download_output": ("Ozon: скачивать выходной файл", "store"),
    "ozon_discounts_excel.download_detail_report": ("Ozon: скачивать отчёт детализации", "store"),
    "ozon_discounts_excel.view_related_operations": ("Ozon: просматривать связанные операции", "store"),
    "ozon_discounts_excel.rerun_check": ("Ozon: запускать повторную проверку", "store"),
    "ozon_discounts_excel.rerun_process": ("Ozon: запускать повторную обработку", "store"),
    "settings.system_params.view": ("просмотр системных параметров", "global"),
    "settings.system_params.edit": ("изменение системных параметров", "global"),
    "settings.store_params.view": ("просмотр параметров магазина", "store"),
    "settings.store_params.edit": ("изменение параметров магазина", "store"),
    "settings.param_history.view": ("просмотр истории параметров", "global_store"),
    "settings.param_source.view": ("просмотр источника значения", "global_store"),
    "settings.service.view": ("просмотр служебных настроек", "global"),
    "settings.service.edit": ("изменение служебных настроек", "global"),
    "stores.list.view": ("просмотр списка магазинов", "global_store"),
    "stores.card.view": ("просмотр карточки магазина", "global_store"),
    "stores.create": ("создание магазина", "global_store"),
    "stores.edit": ("изменение магазина", "global_store"),
    "stores.params.edit": ("изменение параметров магазина", "store"),
    "stores.connection.view": ("просмотр блока подключения", "store"),
    "stores.connection.edit": ("изменение блока подключения", "store"),
    "stores.connection.secret_edit": ("добавление/изменение API-ключей", "store"),
    "stores.access.assign": ("назначение доступов к магазину", "global_store"),
    "stores.operations.view": ("просмотр операций магазина", "store"),
    "stores.history.view": ("просмотр истории изменений магазина", "store"),
    "audit.list.view": ("просмотр списка аудита", "global_store"),
    "audit.card.view": ("просмотр карточки аудита", "global_store"),
    "techlog.list.view": ("просмотр списка техжурнала", "global_store"),
    "techlog.card.view": ("просмотр карточки техжурнала", "global_store"),
    "logs.scope.limited": ("ограниченный контур записей", "global_store"),
    "logs.scope.full": ("полный контур записей", "global"),
    "techlog.sensitive.view": ("чувствительные технические детали", "global"),
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
}

ADMIN_PERMISSION_CODES = {
    code for code in PERMISSION_DEFINITIONS if code.startswith(("users.", "roles.", "permissions.", "section_access."))
}
STORE_SETTINGS_CODES = {
    "settings.store_params.view",
    "settings.store_params.edit",
    "settings.param_history.view",
    "settings.param_source.view",
}
STORE_CODES = {code for code in PERMISSION_DEFINITIONS if code.startswith("stores.")}
AUDIT_TECHLOG_CODES = {
    "audit.list.view",
    "audit.card.view",
    "techlog.list.view",
    "techlog.card.view",
    "logs.scope.limited",
}
SCENARIO_CODES = {
    code
    for code in PERMISSION_DEFINITIONS
    if code.startswith(("wb_discounts_excel.", "ozon_discounts_excel."))
}

ROLE_PERMISSION_CODES = {
    "owner": set(PERMISSION_DEFINITIONS),
    "global_admin": set(PERMISSION_DEFINITIONS) - {"users.owner.manage"},
    "local_admin": (
        {code for code in ADMIN_PERMISSION_CODES if not code.startswith("roles.")}
        | STORE_CODES
        | STORE_SETTINGS_CODES
        | AUDIT_TECHLOG_CODES
    )
    - {
        "users.owner.manage",
        "roles.edit",
        "settings.system_params.edit",
        "techlog.sensitive.view",
    },
    "marketplace_manager": (
        SCENARIO_CODES
        | {
            "stores.list.view",
            "stores.card.view",
            "stores.operations.view",
            "settings.store_params.view",
            "settings.store_params.edit",
            "settings.param_history.view",
            "settings.param_source.view",
        }
    )
    - {
        "users.owner.manage",
        "settings.system_params.edit",
    },
    "observer": {
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
    },
}

ROLE_SECTION_CODES = {
    "owner": set(SECTION_DEFINITIONS),
    "global_admin": set(SECTION_DEFINITIONS),
    "local_admin": {
        "home.view",
        "stores.view",
        "settings_store.view",
        "users.view",
        "permissions.view",
        "store_access.view",
        "audit.view",
        "techlog.view",
    },
    "marketplace_manager": {
        "home.view",
        "wb_discounts_excel.view",
        "ozon_discounts_excel.view",
        "operations.view",
        "stores.view",
        "products.view",
        "settings_store.view",
    },
    "observer": {
        "home.view",
        "operations.view",
        "stores.view",
        "products.view",
        "settings_store.view",
        "audit.view",
        "techlog.view",
    },
}


def seed_identity_access(apps, schema_editor):
    Role = apps.get_model("identity_access", "Role")
    Permission = apps.get_model("identity_access", "Permission")
    SectionAccess = apps.get_model("identity_access", "SectionAccess")
    RolePermission = apps.get_model("identity_access", "RolePermission")
    RoleSectionAccess = apps.get_model("identity_access", "RoleSectionAccess")

    roles = {}
    for code, name in ROLE_DEFINITIONS.items():
        role, _ = Role.objects.update_or_create(
            code=code,
            defaults={"name": name, "status": "active", "is_system": True},
        )
        roles[code] = role

    permissions = {}
    for code, (name, scope_type) in PERMISSION_DEFINITIONS.items():
        permission, _ = Permission.objects.update_or_create(
            code=code,
            defaults={"name": name, "scope_type": scope_type, "is_system": True},
        )
        permissions[code] = permission

    sections = {}
    for code, (section, mode, name) in SECTION_DEFINITIONS.items():
        section_access, _ = SectionAccess.objects.update_or_create(
            code=code,
            defaults={"section": section, "mode": mode, "name": name, "is_system": True},
        )
        sections[code] = section_access

    for role_code, permission_codes in ROLE_PERMISSION_CODES.items():
        role = roles[role_code]
        for permission_code in permission_codes:
            RolePermission.objects.get_or_create(role=role, permission=permissions[permission_code])

    for role_code, section_codes in ROLE_SECTION_CODES.items():
        role = roles[role_code]
        for section_code in section_codes:
            RoleSectionAccess.objects.get_or_create(role=role, section_access=sections[section_code])


class Migration(migrations.Migration):

    dependencies = [
        ("identity_access", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_identity_access, reverse_code=migrations.RunPython.noop),
    ]
