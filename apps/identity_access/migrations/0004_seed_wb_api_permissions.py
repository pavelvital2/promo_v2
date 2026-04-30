from django.db import migrations


WB_API_PERMISSIONS = {
    "wb.api.connection.view": ("WB API: просмотр подключения", "store"),
    "wb.api.connection.manage": ("WB API: управление подключением", "store"),
    "wb.api.prices.download": ("WB API: скачать цены", "store"),
    "wb.api.prices.file.download": ("WB API: скачать Excel цен", "store"),
    "wb.api.promotions.download": ("WB API: скачать текущие акции", "store"),
    "wb.api.promotions.file.download": ("WB API: скачать Excel акций", "store"),
    "wb.api.discounts.calculate": ("WB API: рассчитать скидки", "store"),
    "wb.api.discounts.result.download": ("WB API: скачать итоговый Excel/detail", "store"),
    "wb.api.discounts.upload": ("WB API: выполнить upload скидок", "store"),
    "wb.api.discounts.upload.confirm": ("WB API: подтвердить upload скидок", "store"),
    "wb.api.operation.view": ("WB API: просмотр операций", "store"),
}

WB_API_SECTION = {
    "wb_discounts_api.view": ("wb_discounts_api", "view", "WB API"),
}

WB_API_CONNECTION_CODES = {
    "wb.api.connection.view",
    "wb.api.connection.manage",
    "wb.api.operation.view",
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

WB_API_ROLE_PERMISSIONS = {
    "owner": set(WB_API_PERMISSIONS),
    "global_admin": set(WB_API_PERMISSIONS),
    "local_admin": WB_API_CONNECTION_CODES,
    "marketplace_manager": WB_API_MANAGER_CODES,
}

WB_API_ROLE_SECTIONS = {
    "owner": {"wb_discounts_api.view"},
    "global_admin": {"wb_discounts_api.view"},
    "local_admin": {"wb_discounts_api.view"},
    "marketplace_manager": {"wb_discounts_api.view"},
}


def seed_wb_api_permissions(apps, schema_editor):
    Permission = apps.get_model("identity_access", "Permission")
    Role = apps.get_model("identity_access", "Role")
    RolePermission = apps.get_model("identity_access", "RolePermission")
    SectionAccess = apps.get_model("identity_access", "SectionAccess")
    RoleSectionAccess = apps.get_model("identity_access", "RoleSectionAccess")

    permissions = {}
    for code, (name, scope_type) in WB_API_PERMISSIONS.items():
        permission, _ = Permission.objects.update_or_create(
            code=code,
            defaults={"name": name, "scope_type": scope_type, "is_system": True},
        )
        permissions[code] = permission

    sections = {}
    for code, (section, mode, name) in WB_API_SECTION.items():
        section_access, _ = SectionAccess.objects.update_or_create(
            code=code,
            defaults={"section": section, "mode": mode, "name": name, "is_system": True},
        )
        sections[code] = section_access

    roles = {role.code: role for role in Role.objects.filter(code__in=set(WB_API_ROLE_PERMISSIONS) | set(WB_API_ROLE_SECTIONS))}
    for role_code, permission_codes in WB_API_ROLE_PERMISSIONS.items():
        role = roles.get(role_code)
        if role is None:
            continue
        for permission_code in permission_codes:
            RolePermission.objects.get_or_create(role=role, permission=permissions[permission_code])

    for role_code, section_codes in WB_API_ROLE_SECTIONS.items():
        role = roles.get(role_code)
        if role is None:
            continue
        for section_code in section_codes:
            RoleSectionAccess.objects.get_or_create(role=role, section_access=sections[section_code])


class Migration(migrations.Migration):

    dependencies = [
        ("identity_access", "0003_alter_storeaccess_store_alter_storeaccess_user_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_wb_api_permissions, reverse_code=migrations.RunPython.noop),
    ]
