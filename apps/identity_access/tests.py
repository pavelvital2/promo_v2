from django.contrib import admin
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.db.models.deletion import ProtectedError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.identity_access.admin import RolePermissionInline, RoleSectionAccessInline, UserRoleInline
from apps.identity_access.models import (
    AccessEffect,
    Permission,
    Role,
    RolePermission,
    RoleSectionAccess,
    SectionAccess,
    StoreAccess,
    User,
    UserBlockHistory,
    UserChangeHistory,
    UserPermissionOverride,
    UserRole,
    system_dictionary_mutation,
)
from apps.identity_access.seeds import (
    PERMISSION_DEFINITIONS,
    ROLE_GLOBAL_ADMIN,
    ROLE_LOCAL_ADMIN,
    ROLE_MARKETPLACE_MANAGER,
    ROLE_OBSERVER,
    ROLE_OWNER,
    ROLE_PERMISSION_CODES,
    seed_identity_access,
)
from apps.identity_access.services import can_manage_user, change_user_status, has_permission, is_owner
from apps.stores.models import StoreAccount


class IdentityAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_identity_access()
        cls.owner_role = Role.objects.get(code=ROLE_OWNER)
        cls.global_admin_role = Role.objects.get(code=ROLE_GLOBAL_ADMIN)
        cls.local_admin_role = Role.objects.get(code=ROLE_LOCAL_ADMIN)
        cls.manager_role = Role.objects.get(code=ROLE_MARKETPLACE_MANAGER)
        cls.observer_role = Role.objects.get(code=ROLE_OBSERVER)

        cls.wb_store = StoreAccount.objects.create(
            name="WB test store",
            marketplace=StoreAccount.Marketplace.WB,
        )
        cls.ozon_store = StoreAccount.objects.create(
            name="Ozon test store",
            marketplace=StoreAccount.Marketplace.OZON,
        )
        cls.owner = User.objects.create_user(
            login="owner",
            password="owner-pass-123",
            display_name="Owner",
            primary_role=cls.owner_role,
            is_staff=True,
        )
        cls.global_admin = User.objects.create_user(
            login="global-admin",
            password="admin-pass-123",
            display_name="Global Admin",
            primary_role=cls.global_admin_role,
            is_staff=True,
        )
        cls.local_admin = User.objects.create_user(
            login="local-admin",
            password="local-pass-123",
            display_name="Local Admin",
            primary_role=cls.local_admin_role,
        )
        cls.manager = User.objects.create_user(
            login="manager",
            password="manager-pass-123",
            display_name="Manager",
            primary_role=cls.manager_role,
        )
        cls.observer = User.objects.create_user(
            login="observer",
            password="observer-pass-123",
            display_name="Observer",
            primary_role=cls.observer_role,
        )
        StoreAccess.objects.create(
            user=cls.local_admin,
            store=cls.wb_store,
            access_level=StoreAccess.AccessLevel.ADMIN,
        )
        StoreAccess.objects.create(
            user=cls.manager,
            store=cls.wb_store,
            access_level=StoreAccess.AccessLevel.WORK,
        )
        StoreAccess.objects.create(
            user=cls.manager,
            store=cls.ozon_store,
            access_level=StoreAccess.AccessLevel.WORK,
        )
        StoreAccess.objects.create(
            user=cls.observer,
            store=cls.wb_store,
            access_level=StoreAccess.AccessLevel.VIEW,
        )

    def test_seed_roles_and_permissions_match_approved_catalog(self):
        self.assertEqual(Permission.objects.count(), len(PERMISSION_DEFINITIONS))
        self.assertEqual(
            set(
                self.global_admin_role.role_permissions.values_list(
                    "permission__code",
                    flat=True,
                ),
            ),
            ROLE_PERMISSION_CODES[ROLE_GLOBAL_ADMIN],
        )
        self.assertNotIn(
            "users.owner.manage",
            ROLE_PERMISSION_CODES[ROLE_GLOBAL_ADMIN],
        )
        self.assertNotIn("roles.edit", ROLE_PERMISSION_CODES[ROLE_LOCAL_ADMIN])
        self.assertNotIn(
            "wb_discounts_excel.download_output",
            ROLE_PERMISSION_CODES[ROLE_OBSERVER],
        )
        self.assertIn("ozon.api.connection.view", PERMISSION_DEFINITIONS)
        self.assertIn("ozon.api.connection.manage", ROLE_PERMISSION_CODES[ROLE_LOCAL_ADMIN])
        self.assertIn("ozon.api.actions.download", ROLE_PERMISSION_CODES[ROLE_MARKETPLACE_MANAGER])
        self.assertNotIn("ozon.api.connection.manage", ROLE_PERMISSION_CODES[ROLE_MARKETPLACE_MANAGER])
        self.assertIn("ozon.api.elastic.active_products.download", PERMISSION_DEFINITIONS)
        self.assertIn("ozon.api.elastic.candidates.download", PERMISSION_DEFINITIONS)
        self.assertIn(
            "ozon.api.elastic.active_products.download",
            ROLE_PERMISSION_CODES[ROLE_MARKETPLACE_MANAGER],
        )
        self.assertIn(
            "ozon.api.elastic.candidates.download",
            ROLE_PERMISSION_CODES[ROLE_MARKETPLACE_MANAGER],
        )
        self.assertIn("ozon.api.elastic.product_data.download", PERMISSION_DEFINITIONS)
        self.assertIn(
            "ozon.api.elastic.product_data.download",
            ROLE_PERMISSION_CODES[ROLE_MARKETPLACE_MANAGER],
        )
        self.assertNotIn(
            "ozon.api.elastic.active_products.download",
            ROLE_PERMISSION_CODES[ROLE_LOCAL_ADMIN],
        )
        self.assertNotIn(
            "ozon.api.elastic.product_data.download",
            ROLE_PERMISSION_CODES[ROLE_LOCAL_ADMIN],
        )
        self.assertNotIn(
            "ozon.api.elastic.candidates.download",
            ROLE_PERMISSION_CODES[ROLE_OBSERVER],
        )
        self.assertNotIn(
            "ozon.api.elastic.product_data.download",
            ROLE_PERMISSION_CODES[ROLE_OBSERVER],
        )
        self.assertTrue(has_permission(self.owner, "ozon.api.actions.download", self.ozon_store))
        self.assertTrue(has_permission(self.global_admin, "ozon.api.actions.download", self.ozon_store))
        self.assertIn("ozon.api.elastic.calculate", PERMISSION_DEFINITIONS)
        self.assertIn(
            "ozon.api.elastic.calculate",
            ROLE_PERMISSION_CODES[ROLE_MARKETPLACE_MANAGER],
        )
        self.assertNotIn(
            "ozon.api.elastic.calculate",
            ROLE_PERMISSION_CODES[ROLE_LOCAL_ADMIN],
        )
        self.assertNotIn(
            "ozon.api.elastic.calculate",
            ROLE_PERMISSION_CODES[ROLE_OBSERVER],
        )
        self.assertTrue(has_permission(self.owner, "ozon.api.elastic.calculate", self.ozon_store))
        self.assertTrue(has_permission(self.global_admin, "ozon.api.elastic.calculate", self.ozon_store))
        self.assertIn("ozon.api.elastic.files.download", PERMISSION_DEFINITIONS)
        self.assertIn(
            "ozon.api.elastic.files.download",
            ROLE_PERMISSION_CODES[ROLE_MARKETPLACE_MANAGER],
        )
        self.assertNotIn(
            "ozon.api.elastic.files.download",
            ROLE_PERMISSION_CODES[ROLE_LOCAL_ADMIN],
        )
        self.assertNotIn(
            "ozon.api.elastic.files.download",
            ROLE_PERMISSION_CODES[ROLE_OBSERVER],
        )
        self.assertTrue(has_permission(self.owner, "ozon.api.elastic.files.download", self.ozon_store))
        self.assertTrue(has_permission(self.global_admin, "ozon.api.elastic.files.download", self.ozon_store))
        self.assertTrue(has_permission(self.manager, "ozon.api.elastic.files.download", self.ozon_store))
        self.assertIn("ozon.api.elastic.review", PERMISSION_DEFINITIONS)
        self.assertIn(
            "ozon.api.elastic.review",
            ROLE_PERMISSION_CODES[ROLE_MARKETPLACE_MANAGER],
        )
        self.assertNotIn(
            "ozon.api.elastic.review",
            ROLE_PERMISSION_CODES[ROLE_LOCAL_ADMIN],
        )
        self.assertNotIn(
            "ozon.api.elastic.review",
            ROLE_PERMISSION_CODES[ROLE_OBSERVER],
        )
        self.assertTrue(has_permission(self.owner, "ozon.api.elastic.review", self.ozon_store))
        self.assertTrue(has_permission(self.global_admin, "ozon.api.elastic.review", self.ozon_store))
        self.assertTrue(has_permission(self.manager, "ozon.api.elastic.review", self.ozon_store))
        upload_ozon_permissions = {
            "ozon.api.elastic.upload",
            "ozon.api.elastic.upload.confirm",
            "ozon.api.elastic.deactivate.confirm",
        }
        self.assertTrue(upload_ozon_permissions <= set(PERMISSION_DEFINITIONS))
        self.assertTrue(upload_ozon_permissions <= ROLE_PERMISSION_CODES[ROLE_OWNER])
        self.assertTrue(upload_ozon_permissions <= ROLE_PERMISSION_CODES[ROLE_GLOBAL_ADMIN])
        self.assertFalse(upload_ozon_permissions & ROLE_PERMISSION_CODES[ROLE_MARKETPLACE_MANAGER])
        self.assertFalse(upload_ozon_permissions & ROLE_PERMISSION_CODES[ROLE_LOCAL_ADMIN])
        self.assertFalse(upload_ozon_permissions & ROLE_PERMISSION_CODES[ROLE_OBSERVER])
        product_core_permissions = {
            "product_core.view",
            "product_core.create",
            "product_core.update",
            "product_core.archive",
            "product_core.export",
            "product_variant.view",
            "product_variant.create",
            "product_variant.update",
            "product_variant.archive",
            "marketplace_listing.view",
            "marketplace_listing.sync",
            "marketplace_listing.export",
            "marketplace_listing.map",
            "marketplace_listing.unmap",
            "marketplace_listing.archive",
            "marketplace_snapshot.view",
            "marketplace_snapshot.technical_view",
        }
        self.assertTrue(product_core_permissions <= set(PERMISSION_DEFINITIONS))
        self.assertTrue(product_core_permissions <= ROLE_PERMISSION_CODES[ROLE_OWNER])
        self.assertTrue(product_core_permissions <= ROLE_PERMISSION_CODES[ROLE_GLOBAL_ADMIN])
        self.assertIn("marketplace_listing.map", ROLE_PERMISSION_CODES[ROLE_LOCAL_ADMIN])
        self.assertIn("marketplace_listing.unmap", ROLE_PERMISSION_CODES[ROLE_LOCAL_ADMIN])
        self.assertNotIn("marketplace_listing.archive", ROLE_PERMISSION_CODES[ROLE_LOCAL_ADMIN])
        self.assertNotIn("product_core.create", ROLE_PERMISSION_CODES[ROLE_LOCAL_ADMIN])
        self.assertNotIn("marketplace_listing.map", ROLE_PERMISSION_CODES[ROLE_MARKETPLACE_MANAGER])
        self.assertNotIn("marketplace_listing.unmap", ROLE_PERMISSION_CODES[ROLE_MARKETPLACE_MANAGER])
        self.assertNotIn("marketplace_listing.export", ROLE_PERMISSION_CODES[ROLE_OBSERVER])
        self.assertNotIn("marketplace_snapshot.technical_view", ROLE_PERMISSION_CODES[ROLE_OBSERVER])
        self.assertFalse(has_permission(self.local_admin, "marketplace_listing.archive", self.wb_store))
        self.assertTrue(has_permission(self.manager, "product_core.view"))
        self.assertTrue(has_permission(self.manager, "marketplace_listing.view", self.wb_store))
        self.assertFalse(has_permission(self.manager, "marketplace_listing.map", self.wb_store))
        self.assertFalse(has_permission(self.observer, "marketplace_listing.export", self.wb_store))

    def test_seed_command_is_idempotent(self):
        before = {
            "roles": Role.objects.count(),
            "permissions": Permission.objects.count(),
        }
        call_command("seed_identity_access", verbosity=0)
        call_command("seed_identity_access", verbosity=0)
        after = {
            "roles": Role.objects.count(),
            "permissions": Permission.objects.count(),
        }

        self.assertEqual(after, before)

    def test_seed_service_can_restore_system_dictionary_through_service_context(self):
        official_name = PERMISSION_DEFINITIONS["roles.edit"][0]
        with system_dictionary_mutation():
            Permission.objects.filter(code="roles.edit").update(name="Temporary seed test name")

        seed_identity_access()

        self.assertEqual(Permission.objects.get(code="roles.edit").name, official_name)
        self.assertEqual(
            seed_identity_access(),
            {
                "roles": 0,
                "permissions": 0,
                "sections": 0,
                "role_permissions": 0,
                "role_sections": 0,
            },
        )

    def test_auth_login_uses_secure_password_storage(self):
        self.assertNotEqual(self.manager.password, "manager-pass-123")
        self.assertTrue(self.manager.check_password("manager-pass-123"))

        response = self.client.post(
            reverse("login"),
            {"username": "manager", "password": "manager-pass-123"},
        )

        self.assertEqual(response.status_code, 302)

    def test_owner_has_full_known_permissions_and_cannot_be_managed_by_admin(self):
        self.assertTrue(has_permission(self.owner, "users.owner.manage"))
        self.assertTrue(has_permission(self.owner, "wb_discounts_excel.run_process", self.wb_store))
        self.assertTrue(
            has_permission(self.global_admin, "wb_discounts_excel.run_process", self.wb_store),
        )
        self.assertFalse(has_permission(self.global_admin, "users.owner.manage"))
        self.assertFalse(can_manage_user(self.global_admin, self.owner))

    def test_owner_cannot_be_blocked_deleted_or_denied(self):
        self.owner.status = User.Status.BLOCKED
        with self.assertRaises(ValidationError):
            self.owner.save()

        with self.assertRaises(ProtectedError):
            self.owner.delete()

        with self.assertRaises(ValidationError):
            UserPermissionOverride.objects.create(
                user=self.owner,
                permission=Permission.objects.get(code="roles.edit"),
                effect=AccessEffect.DENY,
            )

    def test_owner_detection_is_consistent_for_primary_and_assigned_roles(self):
        m2m_owner = User.objects.create_user(
            login="m2m-owner",
            password="owner-pass-123",
            display_name="M2M Owner",
        )
        UserRole.objects.create(user=m2m_owner, role=self.owner_role)

        self.assertTrue(m2m_owner.is_owner)
        self.assertTrue(is_owner(m2m_owner))
        with self.assertRaises(ProtectedError):
            m2m_owner.delete()
        with self.assertRaises(ValidationError):
            UserPermissionOverride.objects.create(
                user=m2m_owner,
                permission=Permission.objects.get(code="roles.edit"),
                effect=AccessEffect.DENY,
            )

    def test_system_dictionaries_and_system_role_composition_are_immutable(self):
        self.global_admin_role.name = "Changed"
        with self.assertRaises(ValidationError):
            self.global_admin_role.save()

        permission = Permission.objects.get(code="roles.edit")
        permission.name = "Changed"
        with self.assertRaises(ValidationError):
            permission.save()

        section = SectionAccess.objects.get(code="users.view")
        section.name = "Changed"
        with self.assertRaises(ValidationError):
            section.save()

        with self.assertRaises(ValidationError):
            RolePermission.objects.create(role=self.local_admin_role, permission=permission)

        with self.assertRaises(ValidationError):
            RoleSectionAccess.objects.create(
                role=self.local_admin_role,
                section_access=SectionAccess.objects.get(code="roles.view"),
            )

        with self.assertRaises(ProtectedError):
            self.local_admin_role.role_permissions.first().delete()
        with self.assertRaises(ProtectedError):
            self.local_admin_role.role_sections.first().delete()
        with self.assertRaises(ProtectedError):
            Permission.objects.filter(code="roles.edit").delete()

    def test_queryset_update_cannot_mutate_system_dictionaries_or_role_composition(self):
        with self.assertRaises(ValidationError):
            Role.objects.filter(code=ROLE_GLOBAL_ADMIN).update(name="Changed by update")
        self.assertEqual(Role.objects.get(code=ROLE_GLOBAL_ADMIN).name, "Глобальный администратор")

        with self.assertRaises(ValidationError):
            Permission.objects.filter(code="roles.edit").update(name="Changed by update")
        self.assertEqual(
            Permission.objects.get(code="roles.edit").name,
            PERMISSION_DEFINITIONS["roles.edit"][0],
        )

        with self.assertRaises(ValidationError):
            SectionAccess.objects.filter(code="users.view").update(name="Changed by update")
        self.assertEqual(SectionAccess.objects.get(code="users.view").name, "Пользователи")

        custom_role = Role.objects.create(code="custom", name="Custom")
        with self.assertRaises(ValidationError):
            Role.objects.filter(pk=custom_role.pk).update(is_system=True)
        custom_role.refresh_from_db()
        self.assertFalse(custom_role.is_system)

        role_permission = RolePermission.objects.get(
            role=self.global_admin_role,
            permission_id="roles.edit",
        )
        with self.assertRaises(ValidationError):
            RolePermission.objects.filter(pk=role_permission.pk).update(
                permission_id="users.owner.manage",
            )
        role_permission.refresh_from_db()
        self.assertEqual(role_permission.permission_id, "roles.edit")

        role_section = RoleSectionAccess.objects.get(
            role=self.global_admin_role,
            section_access_id="roles.view",
        )
        with self.assertRaises(ValidationError):
            RoleSectionAccess.objects.filter(pk=role_section.pk).update(
                role=self.manager_role,
            )
        role_section.refresh_from_db()
        self.assertEqual(role_section.role, self.global_admin_role)

    def test_system_dictionaries_are_readonly_in_admin(self):
        request = RequestFactory().get("/admin/")
        request.user = self.global_admin

        role_admin = admin.site._registry[Role]
        permission_admin = admin.site._registry[Permission]
        section_admin = admin.site._registry[SectionAccess]
        role_permission_inline = RolePermissionInline(Role, admin.site)
        role_section_inline = RoleSectionAccessInline(Role, admin.site)
        user_role_inline = UserRoleInline(User, admin.site)

        self.assertIn("name", role_admin.get_readonly_fields(request, self.global_admin_role))
        self.assertIn("name", permission_admin.get_readonly_fields(request, Permission.objects.first()))
        self.assertIn(
            "name",
            section_admin.get_readonly_fields(request, SectionAccess.objects.first()),
        )
        self.assertFalse(role_admin.has_delete_permission(request, self.global_admin_role))
        self.assertFalse(role_permission_inline.has_add_permission(request, self.global_admin_role))
        self.assertFalse(role_permission_inline.has_change_permission(request, self.global_admin_role))
        self.assertFalse(role_permission_inline.has_delete_permission(request, self.global_admin_role))
        self.assertFalse(role_section_inline.has_add_permission(request, self.global_admin_role))
        self.assertFalse(role_section_inline.has_change_permission(request, self.global_admin_role))
        self.assertFalse(role_section_inline.has_delete_permission(request, self.global_admin_role))
        self.assertFalse(user_role_inline.can_delete)

    def test_user_delete_policy_preserves_used_access_and_history_rows(self):
        unused = User.objects.create_user(
            login="unused",
            password="unused-pass-123",
            display_name="Unused",
        )
        unused_pk = unused.pk
        unused.delete()
        self.assertFalse(User.objects.filter(pk=unused_pk).exists())

        with self.assertRaises(ProtectedError):
            self.manager.delete()
        with self.assertRaises(ProtectedError):
            User.objects.filter(pk=self.global_admin.pk).delete()

        assigned_user = User.objects.create_user(
            login="assigned-user",
            password="assigned-pass-123",
            display_name="Assigned User",
        )
        assigned_role = UserRole.objects.create(user=assigned_user, role=self.manager_role)
        self.assertTrue(assigned_user.has_physical_delete_usage())
        with self.assertRaises(ProtectedError):
            assigned_role.delete()
        with self.assertRaises(ProtectedError):
            UserRole.objects.filter(pk=assigned_role.pk).delete()
        with self.assertRaises(ProtectedError):
            assigned_user.delete()
        self.assertTrue(User.objects.filter(pk=assigned_user.pk).exists())
        self.assertTrue(UserRole.objects.filter(pk=assigned_role.pk).exists())

        override = UserPermissionOverride.objects.create(
            user=self.manager,
            permission=Permission.objects.get(code="wb_discounts_excel.run_check"),
            effect=AccessEffect.DENY,
            store=self.wb_store,
        )
        with self.assertRaises(ProtectedError):
            override.delete()
        with self.assertRaises(ProtectedError):
            UserPermissionOverride.objects.filter(pk=override.pk).delete()

        access = StoreAccess.objects.get(user=self.manager, store=self.wb_store)
        with self.assertRaises(ProtectedError):
            access.delete()

        history = UserChangeHistory.objects.create(
            user=self.manager,
            changed_by=self.global_admin,
            field_code="display_name",
            old_value="Manager",
            new_value="Manager 2",
            source="test",
        )
        with self.assertRaises(ProtectedError):
            history.delete()
        with self.assertRaises(ProtectedError):
            UserChangeHistory.objects.filter(pk=history.pk).delete()

    def test_direct_deny_overrides_role_allow(self):
        self.assertTrue(
            has_permission(self.manager, "wb_discounts_excel.run_check", self.wb_store),
        )

        UserPermissionOverride.objects.create(
            user=self.manager,
            permission=Permission.objects.get(code="wb_discounts_excel.run_check"),
            effect=AccessEffect.DENY,
            store=self.wb_store,
        )

        self.assertFalse(
            has_permission(self.manager, "wb_discounts_excel.run_check", self.wb_store),
        )
        self.assertTrue(has_permission(self.manager, "marketplace_listing.view", self.ozon_store))

        UserPermissionOverride.objects.create(
            user=self.manager,
            permission=Permission.objects.get(code="marketplace_listing.view"),
            effect=AccessEffect.DENY,
            store=self.ozon_store,
        )

        self.assertFalse(has_permission(self.manager, "marketplace_listing.view", self.ozon_store))

    def test_store_deny_overrides_full_object_scope(self):
        self.assertTrue(
            has_permission(self.global_admin, "stores.card.view", self.wb_store),
        )
        StoreAccess.objects.create(
            user=self.global_admin,
            store=self.wb_store,
            access_level=StoreAccess.AccessLevel.VIEW,
            effect=AccessEffect.DENY,
        )

        self.assertFalse(
            has_permission(self.global_admin, "stores.card.view", self.wb_store),
        )

    def test_local_admin_is_limited_to_object_scope(self):
        self.assertTrue(has_permission(self.local_admin, "users.edit", self.wb_store))
        self.assertFalse(has_permission(self.local_admin, "users.edit", self.ozon_store))
        self.assertFalse(has_permission(self.local_admin, "users.edit"))

    def test_can_manage_user_respects_store_scope_and_system_roles(self):
        ozon_manager = User.objects.create_user(
            login="ozon-manager",
            password="manager-pass-123",
            display_name="Ozon Manager",
            primary_role=self.manager_role,
        )
        StoreAccess.objects.create(
            user=ozon_manager,
            store=self.ozon_store,
            access_level=StoreAccess.AccessLevel.WORK,
        )

        self.assertTrue(can_manage_user(self.global_admin, self.manager))
        self.assertTrue(can_manage_user(self.local_admin, self.manager))
        self.assertTrue(can_manage_user(self.local_admin, self.manager, self.wb_store))
        self.assertFalse(can_manage_user(self.local_admin, self.manager, self.ozon_store))
        self.assertFalse(can_manage_user(self.local_admin, ozon_manager))
        self.assertFalse(can_manage_user(self.local_admin, self.global_admin))
        self.assertFalse(can_manage_user(self.local_admin, self.owner))

    def test_status_change_service_records_history_and_protects_owner(self):
        change_user_status(
            self.global_admin,
            self.manager,
            User.Status.BLOCKED,
            reason="test block",
            source="test",
        )
        self.manager.refresh_from_db()

        self.assertEqual(self.manager.status, User.Status.BLOCKED)
        self.assertTrue(
            UserBlockHistory.objects.filter(
                user=self.manager,
                changed_by=self.global_admin,
                old_status=User.Status.ACTIVE,
                new_status=User.Status.BLOCKED,
                reason="test block",
                source="test",
            ).exists(),
        )

        with self.assertRaises(PermissionDenied):
            change_user_status(
                self.global_admin,
                self.owner,
                User.Status.BLOCKED,
                reason="forbidden",
                source="test",
            )

    def test_manager_and_observer_role_limits(self):
        self.assertFalse(has_permission(self.manager, "roles.edit"))
        self.assertTrue(has_permission(self.manager, "wb_discounts_excel.run_process", self.wb_store))
        self.assertFalse(
            has_permission(self.observer, "wb_discounts_excel.download_output", self.wb_store),
        )
        self.assertFalse(
            has_permission(self.observer, "wb_discounts_excel.run_process", self.wb_store),
        )
        self.assertTrue(
            has_permission(self.observer, "wb_discounts_excel.view_check_result", self.wb_store),
        )

    def test_visible_user_ids_follow_usr_format(self):
        self.assertRegex(self.manager.visible_id, r"^USR-\d{6}$")
