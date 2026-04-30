from django.db import migrations


TASK_022_PERMISSIONS = {
    "ozon.api.elastic.product_data.download": (
        "Ozon API: скачать product info/stocks",
        "store",
    ),
}

TASK_022_ROLE_PERMISSIONS = {
    "owner": set(TASK_022_PERMISSIONS),
    "global_admin": set(TASK_022_PERMISSIONS),
    "marketplace_manager": set(TASK_022_PERMISSIONS),
}


def seed_task_022_permissions(apps, schema_editor):
    Permission = apps.get_model("identity_access", "Permission")
    Role = apps.get_model("identity_access", "Role")
    RolePermission = apps.get_model("identity_access", "RolePermission")

    permissions = {}
    for code, (name, scope_type) in TASK_022_PERMISSIONS.items():
        permission, _ = Permission.objects.update_or_create(
            code=code,
            defaults={"name": name, "scope_type": scope_type, "is_system": True},
        )
        permissions[code] = permission

    roles_by_code = {
        role.code: role
        for role in Role.objects.filter(code__in=TASK_022_ROLE_PERMISSIONS)
    }
    for role_code, permission_codes in TASK_022_ROLE_PERMISSIONS.items():
        role = roles_by_code.get(role_code)
        if role is None:
            continue
        for permission_code in permission_codes:
            RolePermission.objects.get_or_create(role=role, permission=permissions[permission_code])


class Migration(migrations.Migration):

    dependencies = [
        ("identity_access", "0006_seed_ozon_elastic_product_download_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_task_022_permissions, reverse_code=migrations.RunPython.noop),
    ]
