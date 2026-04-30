import os
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
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
from apps.operations.models import (
    LaunchMethod,
    Marketplace,
    Operation,
    OperationMode,
    OperationModule,
    OperationStepCode,
    OperationType,
    ProcessStatus,
    Run,
    RunStatus,
)
from apps.audit.models import AuditActionCode, AuditRecord
from apps.techlog.models import TechLogEventType, TechLogRecord
from apps.stores.admin import ConnectionBlockAdmin
from apps.discounts.ozon_api.client import (
    OzonApiAuthError,
    OzonApiCredentials,
    OzonApiInvalidResponseError,
    OzonApiRateLimitError,
    OzonApiTemporaryError,
)
from apps.discounts.wb_api.client import (
    WBApiAuthError,
    WBApiInvalidResponseError,
    WBApiRateLimitError,
    WBApiTimeoutError,
)

from .models import BusinessGroup, ConnectionBlock, StoreAccount, StoreAccountChangeHistory
from .services import (
    API_STAGE_2_NOTICE,
    OZON_API_CONNECTION_TYPE,
    OZON_API_MODULE,
    WB_API_CONNECTION_TYPE,
    WB_API_MODULE,
    check_ozon_api_connection,
    check_wb_api_connection,
    connection_metadata_display,
    default_ozon_secret_resolver,
    default_secret_resolver,
    save_connection_block,
    update_store_account,
    visible_stores_queryset,
)


SENTINEL_TOKEN = "Bearer abcdefghijklmnopqrstuvwxyz1234567890"
SENTINEL_OZON_CLIENT_ID = "123456"
SENTINEL_OZON_API_KEY = "ozon-api-key-abcdefghijklmnopqrstuvwxyz"


class FakeWBApiClient:
    error = None
    token_seen = None
    store_scope_seen = None

    def __init__(self, *, token, store_scope, **kwargs):
        type(self).token_seen = token
        type(self).store_scope_seen = store_scope

    def check_connection(self):
        if type(self).error:
            raise type(self).error(type(self).error.safe_message)
        return {"data": {"listGoods": []}}


class FakeOzonApiClient:
    error = None
    credentials_seen = None
    store_scope_seen = None

    def __init__(self, *, credentials, store_scope, **kwargs):
        type(self).credentials_seen = credentials
        type(self).store_scope_seen = store_scope

    def check_connection(self):
        if type(self).error:
            raise type(self).error(type(self).error.safe_message)
        return {"result": []}


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
            status=ConnectionBlock.Status.NOT_CONFIGURED,
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
                        "Client-Id": "123456",
                        "config": {"password": "nested-password-value"},
                    },
                ],
                "public": {
                    "label": "safe label",
                    "note": "Bearer abcdefghijklmnopqrstuvwxyz1234567890",
                },
            },
        )

        self.assertIn("[redacted]", display)
        self.assertIn("safe label", display)
        self.assertNotIn("nested-secret-value", display)
        self.assertNotIn("nested-password-value", display)
        self.assertNotIn("Client-Id", display)
        self.assertNotIn("123456", display)
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz", display)

    def test_connection_metadata_display_redacts_scalar_json_secret_payloads(self):
        display = connection_metadata_display(
            {
                "owner": "integration-team",
                "payload": '{"client_id": "123456", "api_key": "ozon-api-key-abcdef"}',
                "jsonish": '"Client-Id": "123456", "Api-Key": "ozon-api-key-abcdef"',
            },
        )

        self.assertIn("integration-team", display)
        self.assertIn("[redacted]", display)
        self.assertNotIn("client_id", display)
        self.assertNotIn("Client-Id", display)
        self.assertNotIn("Api-Key", display)
        self.assertNotIn("123456", display)
        self.assertNotIn("ozon-api-key", display)

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
                status=ConnectionBlock.Status.NOT_CONFIGURED,
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
            status=ConnectionBlock.Status.NOT_CONFIGURED,
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

    def test_history_display_redacts_legacy_secret_like_metadata_values(self):
        StoreAccountChangeHistory.objects.create(
            store=self.wb_store,
            field_code="connection.metadata",
            old_value='{"public": "{\\"Client-Id\\": \\"123456\\"}"}',
            new_value=(
                '{"public": "{\\"client_id\\": \\"123456\\", '
                '\\"Api-Key\\": \\"ozon-api-key-abcdef\\"}"}'
            ),
            source="bulk",
        )

        self.client.force_login(self.global_admin)
        response = self.client.get(
            reverse("stores:store_history", args=[self.wb_store.visible_id]),
            HTTP_HOST="localhost",
        )

        self.assertContains(response, "[redacted]")
        self.assertNotContains(response, "Client-Id")
        self.assertNotContains(response, "client_id")
        self.assertNotContains(response, "Api-Key")
        self.assertNotContains(response, "123456")
        self.assertNotContains(response, "ozon-api-key")


class StoreTask011WBApiConnectionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_identity_access()
        cls.global_admin_role = Role.objects.get(code=ROLE_GLOBAL_ADMIN)
        cls.manager_role = Role.objects.get(code=ROLE_MARKETPLACE_MANAGER)
        cls.observer_role = Role.objects.get(code=ROLE_OBSERVER)
        cls.store = StoreAccount.objects.create(
            name="WB API Store",
            marketplace=StoreAccount.Marketplace.WB,
        )
        cls.other_store = StoreAccount.objects.create(
            name="Other WB API Store",
            marketplace=StoreAccount.Marketplace.WB,
        )
        cls.ozon_store = StoreAccount.objects.create(
            name="Ozon API Store",
            marketplace=StoreAccount.Marketplace.OZON,
        )
        cls.global_admin = User.objects.create_user(
            login="global-admin-task011",
            password="test",
            display_name="Global Admin TASK-011",
            primary_role=cls.global_admin_role,
        )
        cls.manager = User.objects.create_user(
            login="manager-task011",
            password="test",
            display_name="Manager TASK-011",
            primary_role=cls.manager_role,
        )
        cls.observer = User.objects.create_user(
            login="observer-task011",
            password="test",
            display_name="Observer TASK-011",
            primary_role=cls.observer_role,
        )
        StoreAccess.objects.create(
            user=cls.manager,
            store=cls.store,
            access_level=StoreAccess.AccessLevel.WORK,
        )
        StoreAccess.objects.create(
            user=cls.observer,
            store=cls.store,
            access_level=StoreAccess.AccessLevel.VIEW,
        )

    def setUp(self):
        FakeWBApiClient.error = None
        FakeWBApiClient.token_seen = None
        FakeWBApiClient.store_scope_seen = None
        FakeOzonApiClient.error = None
        FakeOzonApiClient.credentials_seen = None
        FakeOzonApiClient.store_scope_seen = None

    def _create_connection(self):
        return save_connection_block(
            self.global_admin,
            ConnectionBlock(store=self.store),
            module=WB_API_MODULE,
            connection_type=WB_API_CONNECTION_TYPE,
            protected_secret_ref="vault://wb-api/store-001",
            metadata={"label": "read-only check"},
        )

    def _resolve_secret(self, protected_secret_ref):
        self.assertEqual(protected_secret_ref, "vault://wb-api/store-001")
        return SENTINEL_TOKEN

    def test_wb_api_connection_save_uses_protected_ref_status_and_audit(self):
        connection = self._create_connection()

        self.assertEqual(connection.status, ConnectionBlock.Status.CONFIGURED)
        self.assertTrue(connection.is_stage2_1_used)
        self.assertEqual(connection.protected_secret_ref, "vault://wb-api/store-001")
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.WB_API_CONNECTION_CREATED,
                entity_type="ConnectionBlock",
                entity_id=str(connection.pk),
                store=self.store,
            ).exists(),
        )
        persisted_text = " ".join(
            [
                str(connection.metadata),
                *AuditRecord.objects.values_list("safe_message", flat=True),
            ],
        )
        self.assertNotIn(SENTINEL_TOKEN, persisted_text)

    def test_metadata_rejects_secret_like_keys_and_values(self):
        secret_cases = (
            {"authorization": "safe-looking"},
            {"client_id": "123456"},
            {"client-id": "123456"},
            {"Client-Id": "123456"},
            {"public_note": SENTINEL_TOKEN},
            {"public_note": "Client-Id: 123456"},
            {
                "public_note": (
                    '{"client_id": "123456", "api_key": "ozon-api-key-abcdef"}'
                ),
            },
            {"public_note": '"Client-Id": "123456", "Api-Key": "ozon-api-key-abcdef"'},
            {"nested": [{"label": "token=abcdef123456"}]},
        )
        for index, metadata in enumerate(secret_cases):
            connection = ConnectionBlock(
                store=self.store,
                module=f"{WB_API_MODULE}_{index}",
                connection_type=WB_API_CONNECTION_TYPE,
                metadata=metadata,
            )
            with self.subTest(metadata=metadata), self.assertRaises(ValidationError):
                connection.save()

    def test_connection_check_success_sets_active_and_keeps_token_outside_db(self):
        connection = self._create_connection()

        result = check_wb_api_connection(
            self.global_admin,
            connection,
            client_factory=FakeWBApiClient,
            secret_resolver=self._resolve_secret,
        )

        self.assertEqual(result.status, ConnectionBlock.Status.ACTIVE)
        self.assertEqual(result.last_check_status, "success")
        self.assertEqual(FakeWBApiClient.token_seen, SENTINEL_TOKEN)
        self.assertEqual(FakeWBApiClient.store_scope_seen, self.store.visible_id)
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.WB_API_CONNECTION_CHECKED,
                entity_id=str(connection.pk),
            ).exists(),
        )
        self.assertFalse(TechLogRecord.objects.exists())
        all_db_text = " ".join(
            [
                str(ConnectionBlock.objects.values_list("protected_secret_ref", "metadata")),
                str(AuditRecord.objects.values_list("safe_message", "before_snapshot", "after_snapshot")),
                str(TechLogRecord.objects.values_list("safe_message", "sensitive_details_ref")),
            ],
        )
        self.assertNotIn(SENTINEL_TOKEN, all_db_text)
        self.assertIn("vault://wb-api/store-001", all_db_text)

    def test_default_secret_resolver_uses_documented_env_ref_without_persisting_secret(self):
        env_ref = "env://PROMO_V2_TASK011_WB_SECRET"
        connection = save_connection_block(
            self.global_admin,
            ConnectionBlock(store=self.store),
            module=WB_API_MODULE,
            connection_type=WB_API_CONNECTION_TYPE,
            protected_secret_ref=env_ref,
            metadata={"label": "local env resolver"},
        )

        with patch.dict(os.environ, {"PROMO_V2_TASK011_WB_SECRET": SENTINEL_TOKEN}, clear=False):
            self.assertEqual(default_secret_resolver(env_ref), SENTINEL_TOKEN)
            with patch("apps.stores.services.WBApiClient", FakeWBApiClient):
                result = check_wb_api_connection(self.global_admin, connection)

        self.assertEqual(result.status, ConnectionBlock.Status.ACTIVE)
        self.assertEqual(FakeWBApiClient.token_seen, SENTINEL_TOKEN)
        all_db_text = " ".join(
            [
                str(ConnectionBlock.objects.values_list("protected_secret_ref", "metadata")),
                str(AuditRecord.objects.values_list("safe_message", "before_snapshot", "after_snapshot")),
                str(TechLogRecord.objects.values_list("safe_message", "sensitive_details_ref")),
            ],
        )
        self.assertNotIn(SENTINEL_TOKEN, all_db_text)
        self.assertIn(env_ref, all_db_text)

    def test_default_secret_resolver_rejects_unsupported_or_missing_refs_safely(self):
        for ref in ("vault://wb-api/store-001", "env://invalid-name", "env://PROMO_V2_MISSING_SECRET"):
            with self.subTest(ref=ref), self.assertRaises(WBApiInvalidResponseError):
                default_secret_resolver(ref)

    def test_connection_check_auth_rate_and_timeout_fail_safely(self):
        connection = self._create_connection()
        cases = (
            (WBApiAuthError, TechLogEventType.WB_API_AUTH_FAILED),
            (WBApiRateLimitError, TechLogEventType.WB_API_RATE_LIMITED),
            (WBApiTimeoutError, TechLogEventType.WB_API_TIMEOUT),
        )
        for error_class, event_type in cases:
            FakeWBApiClient.error = error_class

            result = check_wb_api_connection(
                self.global_admin,
                connection,
                client_factory=FakeWBApiClient,
                secret_resolver=self._resolve_secret,
            )

            self.assertEqual(result.status, ConnectionBlock.Status.CHECK_FAILED)
            self.assertEqual(result.last_check_status, "failed")
            self.assertTrue(
                TechLogRecord.objects.filter(
                    event_type=event_type,
                    entity_type="ConnectionBlock",
                    entity_id=str(connection.pk),
                ).exists(),
            )
            self.assertNotIn(
                SENTINEL_TOKEN,
                str(TechLogRecord.objects.values_list("safe_message", "sensitive_details_ref")),
            )

    def test_connection_view_manage_and_object_access_are_enforced(self):
        connection = self._create_connection()

        self.assertEqual(
            self.client.get(
                reverse("stores:store_card", args=[self.other_store.visible_id]),
                HTTP_HOST="localhost",
            ).status_code,
            302,
        )
        self.client.force_login(self.manager)
        response = self.client.get(
            reverse("stores:store_card", args=[self.store.visible_id]),
            HTTP_HOST="localhost",
        )
        self.assertNotContains(response, "vault://wb-api/store-001")

        response = self.client.get(
            reverse("stores:connection_edit", args=[self.store.visible_id, connection.pk]),
            HTTP_HOST="localhost",
        )
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.global_admin)
        response = self.client.get(
            reverse("stores:store_card", args=[self.store.visible_id]),
            HTTP_HOST="localhost",
        )
        self.assertContains(response, "[ref-set]")
        self.assertNotContains(response, "vault://wb-api/store-001")

    def test_connection_edit_form_does_not_render_saved_secret_ref_or_status_control(self):
        connection = save_connection_block(
            self.global_admin,
            ConnectionBlock(store=self.store),
            module=WB_API_MODULE,
            connection_type=WB_API_CONNECTION_TYPE,
            protected_secret_ref="env://PROMO_V2_TASK011_WB_SECRET",
            metadata={"label": "edit leak check"},
        )

        self.client.force_login(self.global_admin)
        response = self.client.get(
            reverse("stores:connection_edit", args=[self.store.visible_id, connection.pk]),
            HTTP_HOST="localhost",
        )

        self.assertContains(response, "edit leak check")
        self.assertContains(response, "name=\"protected_secret_ref\"")
        self.assertNotContains(response, "env://PROMO_V2_TASK011_WB_SECRET")
        self.assertNotContains(response, "name=\"status\"")
        self.assertNotContains(response, "value=\"active\"")

    def test_blank_secret_input_keeps_existing_ref_and_new_input_replaces_it(self):
        connection = save_connection_block(
            self.global_admin,
            ConnectionBlock(store=self.store),
            module=WB_API_MODULE,
            connection_type=WB_API_CONNECTION_TYPE,
            protected_secret_ref="env://PROMO_V2_TASK011_WB_SECRET",
            metadata={"label": "original"},
        )

        self.client.force_login(self.global_admin)
        response = self.client.post(
            reverse("stores:connection_edit", args=[self.store.visible_id, connection.pk]),
            {"metadata": '{"label": "kept"}', "protected_secret_ref": ""},
            HTTP_HOST="localhost",
        )
        self.assertEqual(response.status_code, 302)
        connection.refresh_from_db()
        self.assertEqual(connection.protected_secret_ref, "env://PROMO_V2_TASK011_WB_SECRET")
        self.assertEqual(connection.metadata, {"label": "kept"})

        response = self.client.post(
            reverse("stores:connection_edit", args=[self.store.visible_id, connection.pk]),
            {
                "metadata": '{"label": "replaced"}',
                "protected_secret_ref": "env://PROMO_V2_TASK011_WB_SECRET_REPLACEMENT",
            },
            HTTP_HOST="localhost",
        )
        self.assertEqual(response.status_code, 302)
        connection.refresh_from_db()
        self.assertEqual(
            connection.protected_secret_ref,
            "env://PROMO_V2_TASK011_WB_SECRET_REPLACEMENT",
        )
        self.assertEqual(connection.status, ConnectionBlock.Status.CONFIGURED)

    def test_posted_active_status_cannot_bypass_connection_check(self):
        connection = self._create_connection()

        self.client.force_login(self.global_admin)
        response = self.client.post(
            reverse("stores:connection_edit", args=[self.store.visible_id, connection.pk]),
            {
                "metadata": '{"label": "manual active attempt"}',
                "protected_secret_ref": "",
                "status": ConnectionBlock.Status.ACTIVE,
            },
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 302)
        connection.refresh_from_db()
        self.assertEqual(connection.status, ConnectionBlock.Status.CONFIGURED)
        self.assertEqual(connection.last_check_status, "")

        with self.assertRaises(ValidationError):
            save_connection_block(
                self.global_admin,
                connection,
                module=WB_API_MODULE,
                connection_type=WB_API_CONNECTION_TYPE,
                status=ConnectionBlock.Status.ACTIVE,
                metadata={},
            )

    def _create_ozon_connection(self):
        return save_connection_block(
            self.global_admin,
            ConnectionBlock(store=self.ozon_store),
            module=OZON_API_MODULE,
            connection_type=OZON_API_CONNECTION_TYPE,
            protected_secret_ref="vault://ozon-api/store-001",
            metadata={"label": "actions check"},
        )

    def _resolve_ozon_secret(self, protected_secret_ref):
        self.assertEqual(protected_secret_ref, "vault://ozon-api/store-001")
        return OzonApiCredentials(
            client_id=SENTINEL_OZON_CLIENT_ID,
            api_key=SENTINEL_OZON_API_KEY,
        )

    def test_ozon_api_connection_save_check_and_redaction(self):
        connection = self._create_ozon_connection()

        self.assertEqual(connection.status, ConnectionBlock.Status.CONFIGURED)
        self.assertEqual(connection.module, OZON_API_MODULE)
        self.assertEqual(connection.connection_type, OZON_API_CONNECTION_TYPE)
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.OZON_API_CONNECTION_CREATED,
                entity_type="ConnectionBlock",
                entity_id=str(connection.pk),
                store=self.ozon_store,
            ).exists(),
        )

        result = check_ozon_api_connection(
            self.global_admin,
            connection,
            client_factory=FakeOzonApiClient,
            secret_resolver=self._resolve_ozon_secret,
        )

        self.assertEqual(result.status, ConnectionBlock.Status.ACTIVE)
        self.assertEqual(result.last_check_status, "success")
        self.assertEqual(FakeOzonApiClient.credentials_seen.client_id, SENTINEL_OZON_CLIENT_ID)
        self.assertEqual(FakeOzonApiClient.credentials_seen.api_key, SENTINEL_OZON_API_KEY)
        self.assertEqual(FakeOzonApiClient.store_scope_seen, self.ozon_store.visible_id)
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.OZON_API_CONNECTION_CHECKED,
                entity_id=str(connection.pk),
                operation__marketplace=Marketplace.OZON,
                operation__mode=OperationMode.API,
                operation__module=OperationModule.OZON_API,
                operation__operation_type=OperationType.NOT_APPLICABLE,
                operation__step_code=OperationStepCode.OZON_API_CONNECTION_CHECK,
                operation__status=ProcessStatus.COMPLETED_SUCCESS,
            ).exists(),
        )
        operation = Operation.objects.get(
            marketplace=Marketplace.OZON,
            mode=OperationMode.API,
            module=OperationModule.OZON_API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.OZON_API_CONNECTION_CHECK,
            store=self.ozon_store,
        )
        self.assertEqual(operation.summary["last_check_status"], "success")
        all_db_text = " ".join(
            [
                str(ConnectionBlock.objects.values_list("protected_secret_ref", "metadata")),
                str(AuditRecord.objects.values_list("safe_message", "before_snapshot", "after_snapshot")),
                str(TechLogRecord.objects.values_list("safe_message", "sensitive_details_ref")),
            ],
        )
        self.assertNotIn(SENTINEL_OZON_CLIENT_ID, all_db_text)
        self.assertNotIn(SENTINEL_OZON_API_KEY, all_db_text)
        self.assertIn("vault://ozon-api/store-001", all_db_text)

    def test_ozon_default_secret_resolver_reads_single_protected_env_ref(self):
        env_ref = "env://PROMO_V2_TASK019_OZON_SECRET"
        payload = (
            '{"client_id": "'
            + SENTINEL_OZON_CLIENT_ID
            + '", "api_key": "'
            + SENTINEL_OZON_API_KEY
            + '"}'
        )

        with patch.dict(os.environ, {"PROMO_V2_TASK019_OZON_SECRET": payload}, clear=False):
            credentials = default_ozon_secret_resolver(env_ref)

        self.assertEqual(credentials.client_id, SENTINEL_OZON_CLIENT_ID)
        self.assertEqual(credentials.api_key, SENTINEL_OZON_API_KEY)

        for ref in ("vault://ozon/store-001", "env://invalid-name", "env://PROMO_V2_MISSING_SECRET"):
            with self.subTest(ref=ref), self.assertRaises(OzonApiInvalidResponseError):
                default_ozon_secret_resolver(ref)

    def test_ozon_connection_check_failure_mapping_and_safe_techlog(self):
        connection = self._create_ozon_connection()
        cases = (
            (OzonApiAuthError, "auth_failed", TechLogEventType.OZON_API_AUTH_FAILED),
            (OzonApiRateLimitError, "rate_limited", TechLogEventType.OZON_API_RATE_LIMITED),
            (OzonApiTemporaryError, "temporary", TechLogEventType.OZON_API_TIMEOUT),
            (OzonApiInvalidResponseError, "invalid_response", TechLogEventType.OZON_API_RESPONSE_INVALID),
        )
        for error_class, check_status, event_type in cases:
            FakeOzonApiClient.error = error_class

            result = check_ozon_api_connection(
                self.global_admin,
                connection,
                client_factory=FakeOzonApiClient,
                secret_resolver=self._resolve_ozon_secret,
            )

            self.assertEqual(result.status, ConnectionBlock.Status.CHECK_FAILED)
            self.assertEqual(result.last_check_status, check_status)
            operation = Operation.objects.filter(
                marketplace=Marketplace.OZON,
                mode=OperationMode.API,
                module=OperationModule.OZON_API,
                operation_type=OperationType.NOT_APPLICABLE,
                step_code=OperationStepCode.OZON_API_CONNECTION_CHECK,
                store=self.ozon_store,
            ).latest("id")
            self.assertEqual(operation.status, ProcessStatus.COMPLETED_WITH_ERROR)
            self.assertEqual(operation.error_count, 1)
            self.assertTrue(
                TechLogRecord.objects.filter(
                    event_type=event_type,
                    entity_type="ConnectionBlock",
                    entity_id=str(connection.pk),
                    operation=operation,
                ).exists(),
            )
            persisted = str(
                TechLogRecord.objects.values_list("safe_message", "sensitive_details_ref"),
            )
            self.assertNotIn(SENTINEL_OZON_CLIENT_ID, persisted)
            self.assertNotIn(SENTINEL_OZON_API_KEY, persisted)

    def test_ozon_connection_check_without_secret_still_completes_operation(self):
        connection = save_connection_block(
            self.global_admin,
            ConnectionBlock(store=self.ozon_store),
            module=OZON_API_MODULE,
            connection_type=OZON_API_CONNECTION_TYPE,
            metadata={"label": "missing secret"},
        )

        result = check_ozon_api_connection(self.global_admin, connection)

        self.assertEqual(result.status, ConnectionBlock.Status.NOT_CONFIGURED)
        operation = Operation.objects.get(
            marketplace=Marketplace.OZON,
            mode=OperationMode.API,
            module=OperationModule.OZON_API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.OZON_API_CONNECTION_CHECK,
            store=self.ozon_store,
        )
        self.assertEqual(operation.status, ProcessStatus.COMPLETED_WITH_ERROR)
        self.assertEqual(operation.summary["last_check_status"], "not_configured")
        self.assertTrue(AuditRecord.objects.filter(operation=operation).exists())

    def test_ozon_connection_view_manage_and_object_access_are_enforced(self):
        connection = self._create_ozon_connection()

        self.client.force_login(self.manager)
        response = self.client.get(
            reverse("stores:store_card", args=[self.ozon_store.visible_id]),
            HTTP_HOST="localhost",
        )
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.global_admin)
        response = self.client.get(
            reverse("stores:store_card", args=[self.ozon_store.visible_id]),
            HTTP_HOST="localhost",
        )
        self.assertContains(response, "[ref-set]")
        self.assertNotContains(response, "vault://ozon-api/store-001")

        response = self.client.get(
            reverse("stores:connection_edit", args=[self.ozon_store.visible_id, connection.pk]),
            HTTP_HOST="localhost",
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "vault://ozon-api/store-001")

    def test_ozon_api_operation_classifier_accepts_connection_check_and_actions_download(self):
        run = Run.objects.create(
            marketplace=Marketplace.OZON,
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            store=self.ozon_store,
            initiated_by=self.global_admin,
            status=RunStatus.CREATED,
            launch_method=LaunchMethod.MANUAL,
        )

        operation = Operation.objects.create(
            marketplace=Marketplace.OZON,
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.OZON_API_CONNECTION_CHECK,
            status=ProcessStatus.CREATED,
            run=run,
            store=self.ozon_store,
            initiator_user=self.global_admin,
            launch_method=LaunchMethod.MANUAL,
            logic_version="task-019",
        )

        self.assertEqual(operation.marketplace, Marketplace.OZON)
        self.assertEqual(operation.mode, OperationMode.API)
        self.assertEqual(operation.step_code, OperationStepCode.OZON_API_CONNECTION_CHECK)
        self.assertEqual(operation.operation_type, OperationType.NOT_APPLICABLE)

        operation = Operation.objects.create(
            marketplace=Marketplace.OZON,
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.OZON_API_ACTIONS_DOWNLOAD,
            status=ProcessStatus.CREATED,
            run=run,
            store=self.ozon_store,
            initiator_user=self.global_admin,
            launch_method=LaunchMethod.MANUAL,
            logic_version="task-020",
        )

        self.assertEqual(operation.step_code, OperationStepCode.OZON_API_ACTIONS_DOWNLOAD)
        self.assertEqual(operation.operation_type, OperationType.NOT_APPLICABLE)

        with self.assertRaises(ValidationError):
            Operation(
                marketplace=Marketplace.OZON,
                module=OperationModule.OZON_API,
                mode=OperationMode.API,
                operation_type=OperationType.CHECK,
                step_code=OperationStepCode.OZON_API_CONNECTION_CHECK,
                status=ProcessStatus.CREATED,
                run=run,
                store=self.ozon_store,
                initiator_user=self.global_admin,
                launch_method=LaunchMethod.MANUAL,
                logic_version="task-019",
            ).full_clean()

    def test_wb_api_connection_ui_and_service_are_denied_for_ozon_store(self):
        self.client.force_login(self.global_admin)

        card_response = self.client.get(
            reverse("stores:store_card", args=[self.ozon_store.visible_id]),
            HTTP_HOST="localhost",
        )
        self.assertContains(card_response, "Connection blocks")

        with self.assertRaises(PermissionDenied):
            save_connection_block(
                self.global_admin,
                ConnectionBlock(store=self.ozon_store),
                module=WB_API_MODULE,
                connection_type=WB_API_CONNECTION_TYPE,
                protected_secret_ref="env://PROMO_V2_TASK011_WB_SECRET",
                metadata={},
            )

        with self.assertRaises(ValidationError):
            ConnectionBlock.objects.create(
                store=self.ozon_store,
                module=WB_API_MODULE,
                connection_type=WB_API_CONNECTION_TYPE,
                protected_secret_ref="env://PROMO_V2_TASK011_WB_SECRET",
                metadata={},
            )
        with self.assertRaises(ValidationError):
            ConnectionBlock.objects.create(
                store=self.store,
                module=OZON_API_MODULE,
                connection_type=OZON_API_CONNECTION_TYPE,
                protected_secret_ref="env://PROMO_V2_TASK019_OZON_SECRET",
                metadata={},
            )
        with self.assertRaises(PermissionDenied):
            ConnectionBlockAdmin(ConnectionBlock, AdminSite()).save_model(
                SimpleNamespace(user=self.global_admin),
                ConnectionBlock(
                    store=self.ozon_store,
                    module=WB_API_MODULE,
                    connection_type=WB_API_CONNECTION_TYPE,
                    protected_secret_ref="env://PROMO_V2_TASK011_WB_SECRET",
                    metadata={},
                ),
                None,
                False,
            )

        legacy_connection = ConnectionBlock.objects.create(
            store=self.ozon_store,
            module="future_api_legacy",
            connection_type="protected_reference",
            protected_secret_ref="env://PROMO_V2_TASK011_WB_SECRET",
            metadata={},
        )
        ConnectionBlock.objects.filter(pk=legacy_connection.pk).update(
            module=WB_API_MODULE,
            connection_type=WB_API_CONNECTION_TYPE,
        )
        legacy_connection.refresh_from_db()
        edit_response = self.client.get(
            reverse("stores:connection_edit", args=[self.ozon_store.visible_id, legacy_connection.pk]),
            HTTP_HOST="localhost",
        )
        self.assertEqual(edit_response.status_code, 403)

        check_response = self.client.post(
            reverse("stores:connection_check", args=[self.ozon_store.visible_id, legacy_connection.pk]),
            HTTP_HOST="localhost",
        )
        self.assertEqual(check_response.status_code, 403)
        with self.assertRaises(PermissionDenied):
            check_wb_api_connection(self.global_admin, legacy_connection, secret_resolver=self._resolve_secret)
