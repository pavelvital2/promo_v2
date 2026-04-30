from django.db import migrations


NEW_PERMISSIONS = {
    "ozon.api.elastic.upload": (
        "Ozon API: выполнить API upload add/update",
        "store",
    ),
    "ozon.api.elastic.upload.confirm": (
        "Ozon API: подтвердить API upload add/update",
        "store",
    ),
    "ozon.api.elastic.deactivate.confirm": (
        "Ozon API: подтвердить группу deactivate",
        "store",
    ),
}

OWNER_ROLE_CODE = "owner"
GLOBAL_ADMIN_ROLE_CODE = "global_admin"


def seed_ozon_elastic_upload_permissions(apps, schema_editor):
    Permission = apps.get_model("identity_access", "Permission")
    Role = apps.get_model("identity_access", "Role")
    RolePermission = apps.get_model("identity_access", "RolePermission")

    permissions = {}
    for code, (name, scope_type) in NEW_PERMISSIONS.items():
        permission, _ = Permission.objects.update_or_create(
            code=code,
            defaults={"name": name, "scope_type": scope_type, "is_system": True},
        )
        permissions[code] = permission

    for role_code in (OWNER_ROLE_CODE, GLOBAL_ADMIN_ROLE_CODE):
        role = Role.objects.filter(code=role_code).first()
        if role:
            for permission in permissions.values():
                RolePermission.objects.get_or_create(role=role, permission=permission)


class Migration(migrations.Migration):
    dependencies = [
        ("identity_access", "0009_seed_ozon_elastic_review_permission"),
    ]

    operations = [
        migrations.RunPython(
            seed_ozon_elastic_upload_permissions,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
