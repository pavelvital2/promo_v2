from django.db import migrations


OZON_API_TASK_019_020_PERMISSIONS = {
    "ozon.api.connection.view": ("Ozon API: просмотр подключения", "store"),
    "ozon.api.connection.manage": ("Ozon API: управление подключением", "store"),
    "ozon.api.actions.view": ("Ozon API: просмотр actions/Elastic workflow", "store"),
    "ozon.api.actions.download": ("Ozon API: скачать доступные акции", "store"),
    "ozon.api.operation.view": ("Ozon API: просмотр операций", "store"),
}

OZON_API_SECTION = {
    "ozon_discounts_api.view": ("ozon_discounts_api", "view", "Ozon API"),
}

OZON_API_TASK_019_020_ROLE_PERMISSIONS = {
    "owner": set(OZON_API_TASK_019_020_PERMISSIONS),
    "global_admin": set(OZON_API_TASK_019_020_PERMISSIONS),
    "local_admin": {
        "ozon.api.connection.view",
        "ozon.api.connection.manage",
        "ozon.api.operation.view",
    },
    "marketplace_manager": {
        "ozon.api.actions.view",
        "ozon.api.actions.download",
        "ozon.api.operation.view",
    },
}

OZON_API_ROLE_SECTIONS = {
    "owner": {"ozon_discounts_api.view"},
    "global_admin": {"ozon_discounts_api.view"},
    "local_admin": {"ozon_discounts_api.view"},
    "marketplace_manager": {"ozon_discounts_api.view"},
}


def seed_ozon_api_permissions(apps, schema_editor):
    Permission = apps.get_model("identity_access", "Permission")
    Role = apps.get_model("identity_access", "Role")
    RolePermission = apps.get_model("identity_access", "RolePermission")
    SectionAccess = apps.get_model("identity_access", "SectionAccess")
    RoleSectionAccess = apps.get_model("identity_access", "RoleSectionAccess")

    permissions = {}
    for code, (name, scope_type) in OZON_API_TASK_019_020_PERMISSIONS.items():
        permission, _ = Permission.objects.update_or_create(
            code=code,
            defaults={"name": name, "scope_type": scope_type, "is_system": True},
        )
        permissions[code] = permission

    sections = {}
    for code, (section, mode, name) in OZON_API_SECTION.items():
        section_access, _ = SectionAccess.objects.update_or_create(
            code=code,
            defaults={"section": section, "mode": mode, "name": name, "is_system": True},
        )
        sections[code] = section_access

    roles = {
        role.code: role
        for role in Role.objects.filter(
            code__in=set(OZON_API_TASK_019_020_ROLE_PERMISSIONS) | set(OZON_API_ROLE_SECTIONS),
        )
    }
    for role_code, permission_codes in OZON_API_TASK_019_020_ROLE_PERMISSIONS.items():
        role = roles.get(role_code)
        if role is None:
            continue
        for permission_code in permission_codes:
            RolePermission.objects.get_or_create(role=role, permission=permissions[permission_code])

    for role_code, section_codes in OZON_API_ROLE_SECTIONS.items():
        role = roles.get(role_code)
        if role is None:
            continue
        for section_code in section_codes:
            RoleSectionAccess.objects.get_or_create(role=role, section_access=sections[section_code])


class Migration(migrations.Migration):

    dependencies = [
        ("identity_access", "0004_seed_wb_api_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_ozon_api_permissions, reverse_code=migrations.RunPython.noop),
    ]
