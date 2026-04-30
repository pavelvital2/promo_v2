from django.db import migrations


TASK_021_PERMISSIONS = {
    "ozon.api.elastic.active_products.download": (
        "Ozon API: скачать товары участвующие в акции",
        "store",
    ),
    "ozon.api.elastic.candidates.download": (
        "Ozon API: скачать кандидаты в акцию",
        "store",
    ),
}

TASK_021_ROLE_PERMISSIONS = {
    "owner": set(TASK_021_PERMISSIONS),
    "global_admin": set(TASK_021_PERMISSIONS),
    "marketplace_manager": set(TASK_021_PERMISSIONS),
}


def seed_task_021_permissions(apps, schema_editor):
    Permission = apps.get_model("identity_access", "Permission")
    Role = apps.get_model("identity_access", "Role")
    RolePermission = apps.get_model("identity_access", "RolePermission")

    permissions = {}
    for code, (name, scope_type) in TASK_021_PERMISSIONS.items():
        permission, _ = Permission.objects.update_or_create(
            code=code,
            defaults={"name": name, "scope_type": scope_type, "is_system": True},
        )
        permissions[code] = permission

    roles = Role.objects.filter(code__in=TASK_021_ROLE_PERMISSIONS)
    roles_by_code = {role.code: role for role in roles}
    for role_code, permission_codes in TASK_021_ROLE_PERMISSIONS.items():
        role = roles_by_code.get(role_code)
        if role is None:
            continue
        for permission_code in permission_codes:
            RolePermission.objects.get_or_create(role=role, permission=permissions[permission_code])


class Migration(migrations.Migration):

    dependencies = [
        ("identity_access", "0005_seed_ozon_api_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_task_021_permissions, reverse_code=migrations.RunPython.noop),
    ]
