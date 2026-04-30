from django.db import migrations


NEW_PERMISSION = {
    "ozon.api.elastic.calculate": (
        "Ozon API: рассчитать Elastic Boosting",
        "store",
    ),
    "ozon.api.elastic.files.download": (
        "Ozon API: скачать Stage 2.2 файлы",
        "store",
    ),
}

MANAGER_ROLE_CODE = "marketplace_manager"
OWNER_ROLE_CODE = "owner"
GLOBAL_ADMIN_ROLE_CODE = "global_admin"


def seed_ozon_elastic_calculation_permission(apps, schema_editor):
    Permission = apps.get_model("identity_access", "Permission")
    Role = apps.get_model("identity_access", "Role")
    RolePermission = apps.get_model("identity_access", "RolePermission")

    permissions = {}
    for code, (name, scope_type) in NEW_PERMISSION.items():
        permission, _ = Permission.objects.update_or_create(
            code=code,
            defaults={"name": name, "scope_type": scope_type, "is_system": True},
        )
        permissions[code] = permission

    permission_values = permissions.values()
    for role_code in (OWNER_ROLE_CODE, GLOBAL_ADMIN_ROLE_CODE, MANAGER_ROLE_CODE):
        role = Role.objects.filter(code=role_code).first()
        if role:
            for permission in permission_values:
                RolePermission.objects.get_or_create(role=role, permission=permission)


class Migration(migrations.Migration):
    dependencies = [
        ("identity_access", "0007_seed_ozon_elastic_product_data_permission"),
    ]

    operations = [
        migrations.RunPython(
            seed_ozon_elastic_calculation_permission,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
