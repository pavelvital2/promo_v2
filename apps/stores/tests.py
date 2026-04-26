from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from apps.identity_access.models import AccessEffect, Role, StoreAccess, User
from apps.identity_access.seeds import (
    ROLE_GLOBAL_ADMIN,
    ROLE_MARKETPLACE_MANAGER,
    ROLE_OBSERVER,
    seed_identity_access,
)

from .models import BusinessGroup, ConnectionBlock, StoreAccount, StoreAccountChangeHistory
from .services import (
    API_STAGE_2_NOTICE,
    connection_metadata_display,
    save_connection_block,
    update_store_account,
    visible_stores_queryset,
)


class StoreTask003Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_identity_access()
        cls.global_admin_role = Role.objects.get(code=ROLE_GLOBAL_ADMIN)
        cls.manager_role = Role.objects.get(code=ROLE_MARKETPLACE_MANAGER)
        cls.observer_role = Role.objects.get(code=ROLE_OBSERVER)

        cls.group = BusinessGroup.objects.create(name="Brand group")
        cls.wb_store = StoreAccount.objects.create(
            name="WB visible store",
            group=cls.group,
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.CABINET,
            comments="initial comment",
        )
        cls.ozon_store = StoreAccount.objects.create(
            name="Ozon hidden store",
            marketplace=StoreAccount.Marketplace.OZON,
        )
        cls.global_admin = User.objects.create_user(
            login="global-admin",
            password="admin-pass-123",
            display_name="Global Admin",
            primary_role=cls.global_admin_role,
            is_staff=True,
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
        cls.no_access_user = User.objects.create_user(
            login="no-access",
            password="no-access-pass-123",
            display_name="No Access",
            primary_role=cls.observer_role,
        )
        StoreAccess.objects.create(
            user=cls.manager,
            store=cls.wb_store,
            access_level=StoreAccess.AccessLevel.WORK,
        )
        StoreAccess.objects.create(
            user=cls.observer,
            store=cls.wb_store,
            access_level=StoreAccess.AccessLevel.VIEW,
        )

    def test_visible_store_ids_follow_approved_format(self):
        self.assertRegex(self.wb_store.visible_id, r"^STORE-\d{6}$")
        self.assertRegex(self.ozon_store.visible_id, r"^STORE-\d{6}$")

    def test_visible_store_id_is_immutable_after_creation(self):
        stable_visible_id = self.wb_store.visible_id
        self.wb_store.visible_id = "STORE-999999"

        with self.assertRaises(ValidationError):
            self.wb_store.save()

        self.wb_store.refresh_from_db()
        self.assertEqual(self.wb_store.visible_id, stable_visible_id)

        with self.assertRaises(ValidationError):
            StoreAccount.objects.filter(pk=self.wb_store.pk).update(visible_id="STORE-999998")

        self.wb_store.refresh_from_db()
        self.assertEqual(self.wb_store.visible_id, stable_visible_id)

    def test_visible_stores_queryset_respects_object_access_and_direct_deny(self):
        manager_ids = set(visible_stores_queryset(self.manager).values_list("id", flat=True))
        self.assertEqual(manager_ids, {self.wb_store.id})

        no_access_ids = set(visible_stores_queryset(self.no_access_user).values_list("id", flat=True))
        self.assertEqual(no_access_ids, set())

        self.assertEqual(set(visible_stores_queryset(self.global_admin)), {self.wb_store, self.ozon_store})
        StoreAccess.objects.create(
            user=self.global_admin,
            store=self.wb_store,
            access_level=StoreAccess.AccessLevel.VIEW,
            effect=AccessEffect.DENY,
        )
        self.assertEqual(set(visible_stores_queryset(self.global_admin)), {self.ozon_store})

    def test_update_store_account_records_significant_field_history(self):
        update_store_account(
            self.global_admin,
            self.wb_store,
            name="WB renamed store",
            group=self.group,
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.CABINET,
            status=StoreAccount.Status.INACTIVE,
            comments="changed comment",
        )

        records = StoreAccountChangeHistory.objects.filter(store=self.wb_store, source="service")
        self.assertTrue(
            records.filter(
                field_code="name",
                old_value="WB visible store",
                new_value="WB renamed store",
                changed_by=self.global_admin,
            ).exists(),
        )
        self.assertTrue(
            records.filter(
                field_code="status",
                old_value=StoreAccount.Status.ACTIVE,
                new_value=StoreAccount.Status.INACTIVE,
            ).exists(),
        )
        self.assertTrue(records.filter(field_code="comments", new_value="changed comment").exists())

    def test_connection_block_is_stage_2_only_and_records_redacted_history(self):
        connection = ConnectionBlock(store=self.wb_store)
        save_connection_block(
            self.global_admin,
            connection,
            module="future_api",
            connection_type="protected_reference",
            status=ConnectionBlock.Status.PREPARED,
            protected_secret_ref="vault://stores/wb-visible-store",
            metadata={"owner": "integration-team"},
        )

        connection.refresh_from_db()
        self.assertFalse(connection.is_stage1_used)
        self.assertEqual(connection.protected_secret_ref, "vault://stores/wb-visible-store")
        self.assertTrue(
            StoreAccountChangeHistory.objects.filter(
                store=self.wb_store,
                field_code="connection.protected_secret_ref",
                old_value="[empty]",
                new_value="[ref-set]",
            ).exists(),
        )
        self.assertTrue(
            StoreAccountChangeHistory.objects.filter(
                store=self.wb_store,
                field_code="connection.stage",
                new_value=API_STAGE_2_NOTICE,
            ).exists(),
        )

        connection.is_stage1_used = True
        with self.assertRaises(ValidationError):
            connection.save()

        connection.metadata = {"api_token": "must-not-be-stored"}
        connection.is_stage1_used = False
        with self.assertRaises(ValidationError):
            connection.save()

    def test_connection_block_rejects_nested_secret_like_metadata_keys(self):
        nested_cases = (
            {"integration": {"api_token": "must-not-be-stored"}},
            {"integration": [{"privateKey": "must-not-be-stored"}]},
            [{"auth": {"password": "must-not-be-stored"}}],
        )

        for index, metadata in enumerate(nested_cases):
            connection = ConnectionBlock(
                store=self.wb_store,
                module=f"future_api_{index}",
                connection_type="protected_reference",
                metadata=metadata,
            )
            with self.subTest(metadata=metadata), self.assertRaises(ValidationError):
                connection.save()

    def test_connection_metadata_display_redacts_nested_secret_like_values(self):
        display = connection_metadata_display(
            {
                "integration": [
                    {
                        "owner": "integration-team",
                        "apiToken": "nested-secret-value",
                        "config": {"password": "nested-password-value"},
                    },
                ],
                "public": {"label": "safe label"},
            },
        )

        self.assertIn("[redacted]", display)
        self.assertIn("safe label", display)
        self.assertNotIn("nested-secret-value", display)
        self.assertNotIn("nested-password-value", display)

    def test_connection_secret_ref_requires_secret_edit_permission(self):
        connection = ConnectionBlock(
            store=self.wb_store,
            module="future_api",
            connection_type="protected_reference",
        )
        with self.assertRaises(PermissionDenied):
            save_connection_block(
                self.manager,
                connection,
                module="future_api",
                connection_type="protected_reference",
                status=ConnectionBlock.Status.PREPARED,
                protected_secret_ref="vault://forbidden",
                metadata={},
            )

    def test_store_access_changes_are_recorded_without_identity_model_rewrite(self):
        access = StoreAccess.objects.get(user=self.manager, store=self.wb_store)
        access.access_level = StoreAccess.AccessLevel.ADMIN
        access.save()

        self.assertTrue(
            StoreAccountChangeHistory.objects.filter(
                store=self.wb_store,
                field_code="access.user",
                old_value__contains="level=work",
                new_value__contains="level=admin",
                source="model",
            ).exists(),
        )

    def test_archive_delete_policy_blocks_used_store_connection_and_history(self):
        unused_store = StoreAccount.objects.create(
            name="Mistaken unused",
            marketplace=StoreAccount.Marketplace.WB,
        )
        unused_pk = unused_store.pk
        unused_store.delete()
        self.assertFalse(StoreAccount.objects.filter(pk=unused_pk).exists())

        with self.assertRaises(ProtectedError):
            self.wb_store.delete()
        with self.assertRaises(ProtectedError):
            StoreAccount.objects.filter(pk=self.wb_store.pk).delete()

        unused_connection = ConnectionBlock.objects.create(
            store=self.ozon_store,
            module="unused_future_api",
            connection_type="protected_reference",
        )
        unused_connection_pk = unused_connection.pk
        unused_connection.delete()
        self.assertFalse(ConnectionBlock.objects.filter(pk=unused_connection_pk).exists())

        connection = save_connection_block(
            self.global_admin,
            ConnectionBlock(store=self.wb_store),
            module="future_api_delete_policy",
            connection_type="protected_reference",
            status=ConnectionBlock.Status.PREPARED,
            protected_secret_ref="vault://stores/delete-policy",
            metadata={},
        )
        with self.assertRaises(ProtectedError):
            connection.delete()

        history = StoreAccountChangeHistory.objects.create(
            store=self.wb_store,
            field_code="status",
            old_value="active",
            new_value="inactive",
            source="test",
        )
        with self.assertRaises(ProtectedError):
            history.delete()
        with self.assertRaises(ProtectedError):
            StoreAccountChangeHistory.objects.filter(pk=history.pk).delete()

    def test_store_views_hide_inaccessible_stores_and_render_card_history_connection(self):
        self.client.force_login(self.manager)
        list_response = self.client.get(reverse("stores:store_list"), HTTP_HOST="localhost")
        self.assertContains(list_response, self.wb_store.visible_id)
        self.assertNotContains(list_response, self.ozon_store.visible_id)

        card_response = self.client.get(
            reverse("stores:store_card", args=[self.wb_store.visible_id]),
            HTTP_HOST="localhost",
        )
        self.assertContains(card_response, self.wb_store.name)
        self.assertContains(card_response, API_STAGE_2_NOTICE)

        hidden_response = self.client.get(
            reverse("stores:store_card", args=[self.ozon_store.visible_id]),
            HTTP_HOST="localhost",
        )
        self.assertEqual(hidden_response.status_code, 403)

        self.client.force_login(self.global_admin)
        history_response = self.client.get(
            reverse("stores:store_history", args=[self.wb_store.visible_id]),
            HTTP_HOST="localhost",
        )
        self.assertContains(history_response, "access.user")

        self.client.force_login(self.manager)
        connection_response = self.client.get(
            reverse("stores:connection_create", args=[self.wb_store.visible_id]),
            HTTP_HOST="localhost",
        )
        self.assertEqual(connection_response.status_code, 403)

    def test_store_card_redacts_nested_metadata_from_legacy_rows(self):
        connection = ConnectionBlock.objects.create(
            store=self.wb_store,
            module="legacy_future_api",
            connection_type="protected_reference",
            metadata={"owner": "integration-team"},
        )
        ConnectionBlock.objects.filter(pk=connection.pk).update(
            metadata={
                "integration": {
                    "api_token": "legacy-nested-secret",
                    "owner": "integration-team",
                },
            },
        )

        self.client.force_login(self.global_admin)
        response = self.client.get(
            reverse("stores:store_card", args=[self.wb_store.visible_id]),
            HTTP_HOST="localhost",
        )

        self.assertContains(response, "[redacted]")
        self.assertContains(response, "integration-team")
        self.assertNotContains(response, "legacy-nested-secret")
