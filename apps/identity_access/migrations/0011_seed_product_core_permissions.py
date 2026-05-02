from django.db import migrations


NEW_PERMISSIONS = {
    "product_core.view": ("Product Core: просмотр внутренних товаров", "global"),
    "product_core.create": ("Product Core: создание внутренних товаров", "global"),
    "product_core.update": ("Product Core: изменение внутренних товаров", "global"),
    "product_core.archive": ("Product Core: архивирование внутренних товаров", "global"),
    "product_core.export": ("Product Core: экспорт внутренних товаров", "global"),
    "product_variant.view": ("Product Core: просмотр вариантов", "global"),
    "product_variant.create": ("Product Core: создание вариантов", "global"),
    "product_variant.update": ("Product Core: изменение вариантов", "global"),
    "product_variant.archive": ("Product Core: архивирование вариантов", "global"),
    "marketplace_listing.view": ("Product Core: просмотр marketplace listings", "store"),
    "marketplace_listing.sync": ("Product Core: запуск sync listings", "store"),
    "marketplace_listing.export": ("Product Core: экспорт listings", "store"),
    "marketplace_listing.map": ("Product Core: связать listing с variant", "store"),
    "marketplace_listing.unmap": ("Product Core: снять связь listing с variant", "store"),
    "marketplace_listing.archive": ("Product Core: архивировать listing", "store"),
    "marketplace_snapshot.view": ("Product Core: просмотр snapshots", "store"),
    "marketplace_snapshot.technical_view": (
        "Product Core: просмотр технических деталей snapshots",
        "store",
    ),
}

NEW_SECTIONS = {
    "product_core.view": ("product_core", "view", "Product Core"),
    "marketplace_listings.view": ("marketplace_listings", "view", "Marketplace listings"),
}

OWNER_ROLE_CODE = "owner"
GLOBAL_ADMIN_ROLE_CODE = "global_admin"
LOCAL_ADMIN_ROLE_CODE = "local_admin"
MANAGER_ROLE_CODE = "marketplace_manager"
OBSERVER_ROLE_CODE = "observer"

LOCAL_ADMIN_PERMISSIONS = {
    "product_core.view",
    "product_variant.view",
    "marketplace_listing.view",
    "marketplace_listing.sync",
    "marketplace_listing.export",
    "marketplace_listing.map",
    "marketplace_listing.unmap",
    "marketplace_snapshot.view",
}
MANAGER_PERMISSIONS = {
    "product_core.view",
    "product_variant.view",
    "marketplace_listing.view",
    "marketplace_listing.export",
    "marketplace_snapshot.view",
}
OBSERVER_PERMISSIONS = {
    "product_core.view",
    "product_variant.view",
    "marketplace_listing.view",
    "marketplace_snapshot.view",
}


def seed_product_core_permissions(apps, schema_editor):
    Permission = apps.get_model("identity_access", "Permission")
    Role = apps.get_model("identity_access", "Role")
    RolePermission = apps.get_model("identity_access", "RolePermission")
    SectionAccess = apps.get_model("identity_access", "SectionAccess")
    RoleSectionAccess = apps.get_model("identity_access", "RoleSectionAccess")

    permissions = {}
    for code, (name, scope_type) in NEW_PERMISSIONS.items():
        permission, _ = Permission.objects.update_or_create(
            code=code,
            defaults={"name": name, "scope_type": scope_type, "is_system": True},
        )
        permissions[code] = permission

    sections = {}
    for code, (section, mode, name) in NEW_SECTIONS.items():
        section_access, _ = SectionAccess.objects.update_or_create(
            code=code,
            defaults={"section": section, "mode": mode, "name": name, "is_system": True},
        )
        sections[code] = section_access

    role_permission_codes = {
        OWNER_ROLE_CODE: set(NEW_PERMISSIONS),
        GLOBAL_ADMIN_ROLE_CODE: set(NEW_PERMISSIONS),
        LOCAL_ADMIN_ROLE_CODE: LOCAL_ADMIN_PERMISSIONS,
        MANAGER_ROLE_CODE: MANAGER_PERMISSIONS,
        OBSERVER_ROLE_CODE: OBSERVER_PERMISSIONS,
    }
    role_section_codes = {
        OWNER_ROLE_CODE: set(NEW_SECTIONS),
        GLOBAL_ADMIN_ROLE_CODE: set(NEW_SECTIONS),
        LOCAL_ADMIN_ROLE_CODE: {"marketplace_listings.view"},
        MANAGER_ROLE_CODE: set(NEW_SECTIONS),
        OBSERVER_ROLE_CODE: set(NEW_SECTIONS),
    }

    for role_code, permission_codes in role_permission_codes.items():
        role = Role.objects.filter(code=role_code).first()
        if not role:
            continue
        for permission_code in permission_codes:
            RolePermission.objects.get_or_create(
                role=role,
                permission=permissions[permission_code],
            )

    for role_code, section_codes in role_section_codes.items():
        role = Role.objects.filter(code=role_code).first()
        if not role:
            continue
        for section_code in section_codes:
            RoleSectionAccess.objects.get_or_create(
                role=role,
                section_access=sections[section_code],
            )


class Migration(migrations.Migration):
    dependencies = [
        ("identity_access", "0010_seed_ozon_elastic_upload_permissions"),
    ]

    operations = [
        migrations.RunPython(
            seed_product_core_permissions,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
