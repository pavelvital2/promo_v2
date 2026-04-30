"""Tests for TASK-006 audit behavior."""

from __future__ import annotations

from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from apps.audit.models import AuditActionCode, AuditRecord, AuditVisibleScope
from apps.audit.services import (
    audit_records_visible_to,
    cleanup_expired_audit_records,
    create_audit_record,
)
from apps.identity_access.models import AccessEffect, Role, StoreAccess
from apps.identity_access.seeds import ROLE_GLOBAL_ADMIN, ROLE_OBSERVER, seed_identity_access
from apps.operations.models import OperationType
from apps.operations.services import create_check_operation
from apps.stores.models import StoreAccount
from apps.techlog.models import TechLogEventType, TechLogRecord, TechLogSeverity
from apps.techlog.services import create_techlog_record


class AuditTask006Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_identity_access()
        user_model = get_user_model()
        full_role = Role.objects.get(code=ROLE_GLOBAL_ADMIN)
        observer_role = Role.objects.get(code=ROLE_OBSERVER)
        cls.full_user = user_model.objects.create_user(
            login="full-audit",
            password="test",
            display_name="Full Audit",
            primary_role=full_role,
        )
        cls.limited_user = user_model.objects.create_user(
            login="limited-audit",
            password="test",
            display_name="Limited Audit",
            primary_role=observer_role,
        )
        cls.store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
        )
        cls.other_store = StoreAccount.objects.create(
            name="Other WB Store",
            marketplace=StoreAccount.Marketplace.WB,
        )
        StoreAccess.objects.create(
            user=cls.limited_user,
            store=cls.store,
            access_level=StoreAccess.AccessLevel.VIEW,
            effect=AccessEffect.ALLOW,
        )
        cls.operation = create_check_operation(
            marketplace=cls.store.marketplace,
            store=cls.store,
            initiator_user=cls.full_user,
            input_files=[],
            parameters=[],
            logic_version="task-006",
        )
        cls.other_operation = create_check_operation(
            marketplace=cls.other_store.marketplace,
            store=cls.other_store,
            initiator_user=cls.full_user,
            input_files=[],
            parameters=[],
            logic_version="task-006",
        )

    def test_audit_record_links_operation_and_is_immutable(self):
        record = create_audit_record(
            action_code=AuditActionCode.OPERATION_CHECK_STARTED,
            entity_type="Operation",
            entity_id=self.operation.visible_id,
            user=self.full_user,
            operation=self.operation,
            safe_message="Check started.",
        )

        self.assertEqual(record.store, self.store)
        self.assertEqual(record.operation.operation_type, OperationType.CHECK)
        self.assertEqual(record.retention_until, record.occurred_at + timedelta(days=90))
        self.assertEqual(list(self.operation.audit_records.all()), [record])

        record.safe_message = "mutated"
        with self.assertRaises(ValidationError):
            record.save()
        with self.assertRaises(ValidationError):
            AuditRecord.objects.filter(pk=record.pk).update(safe_message="mutated")
        with self.assertRaises(ProtectedError):
            record.delete()
        with self.assertRaises(ProtectedError):
            AuditRecord.objects.filter(pk=record.pk).delete()

    def test_limited_and_full_audit_visibility_scopes(self):
        visible_record = create_audit_record(
            action_code=AuditActionCode.STORE_CHANGED,
            entity_type="StoreAccount",
            entity_id=self.store.visible_id,
            user=self.full_user,
            store=self.store,
            safe_message="Store changed.",
        )
        hidden_record = create_audit_record(
            action_code=AuditActionCode.STORE_CHANGED,
            entity_type="StoreAccount",
            entity_id=self.other_store.visible_id,
            user=self.full_user,
            store=self.other_store,
            safe_message="Other store changed.",
        )
        hidden_own_store_record = create_audit_record(
            action_code=AuditActionCode.STORE_CHANGED,
            entity_type="StoreAccount",
            entity_id=self.other_store.visible_id,
            user=self.limited_user,
            store=self.other_store,
            safe_message="Own inaccessible store changed.",
        )
        hidden_own_operation_record = create_audit_record(
            action_code=AuditActionCode.OPERATION_CHECK_STARTED,
            entity_type="Operation",
            entity_id=self.other_operation.visible_id,
            user=self.limited_user,
            operation=self.other_operation,
            safe_message="Own inaccessible operation changed.",
        )
        own_global_record = create_audit_record(
            action_code=AuditActionCode.USER_CHANGED,
            entity_type="User",
            entity_id=str(self.limited_user.pk),
            user=self.limited_user,
            safe_message="Own global audit.",
        )
        full_scope_record = create_audit_record(
            action_code=AuditActionCode.STORE_CHANGED,
            entity_type="StoreAccount",
            entity_id=self.store.visible_id,
            user=self.full_user,
            store=self.store,
            safe_message="Full-scope audit.",
            visible_scope=AuditVisibleScope.FULL,
        )

        limited_ids = set(audit_records_visible_to(self.limited_user).values_list("id", flat=True))
        full_ids = set(audit_records_visible_to(self.full_user).values_list("id", flat=True))

        self.assertIn(visible_record.pk, limited_ids)
        self.assertNotIn(hidden_record.pk, limited_ids)
        self.assertNotIn(hidden_own_store_record.pk, limited_ids)
        self.assertNotIn(hidden_own_operation_record.pk, limited_ids)
        self.assertIn(own_global_record.pk, limited_ids)
        self.assertNotIn(full_scope_record.pk, limited_ids)
        self.assertIn(visible_record.pk, full_ids)
        self.assertIn(hidden_record.pk, full_ids)
        self.assertIn(hidden_own_store_record.pk, full_ids)
        self.assertIn(hidden_own_operation_record.pk, full_ids)
        self.assertIn(own_global_record.pk, full_ids)
        self.assertIn(full_scope_record.pk, full_ids)

    def test_retention_cleanup_is_regulated_non_ui_and_preserves_operation(self):
        old_record = create_audit_record(
            action_code=AuditActionCode.OPERATION_CHECK_STARTED,
            entity_type="Operation",
            entity_id=self.operation.visible_id,
            user=self.full_user,
            operation=self.operation,
            safe_message="Old audit.",
            occurred_at=timezone.now() - timedelta(days=91),
        )
        fresh_record = create_audit_record(
            action_code=AuditActionCode.OPERATION_CHECK_STARTED,
            entity_type="Operation",
            entity_id=self.operation.visible_id,
            user=self.full_user,
            operation=self.operation,
            safe_message="Fresh audit.",
        )

        result = cleanup_expired_audit_records(now=timezone.now())

        self.assertEqual(result.deleted_count, 1)
        self.assertFalse(AuditRecord.objects.filter(pk=old_record.pk).exists())
        self.assertTrue(AuditRecord.objects.filter(pk=fresh_record.pk).exists())
        self.assertTrue(type(self.operation).objects.filter(pk=self.operation.pk).exists())

    def test_cleanup_management_command_cleans_audit_and_techlog(self):
        create_audit_record(
            action_code=AuditActionCode.OPERATION_CHECK_STARTED,
            entity_type="Operation",
            entity_id=self.operation.visible_id,
            user=self.full_user,
            operation=self.operation,
            safe_message="Old audit.",
            occurred_at=timezone.now() - timedelta(days=91),
        )
        old_techlog = create_techlog_record(
            severity=TechLogSeverity.ERROR,
            event_type=TechLogEventType.APPLICATION_EXCEPTION,
            source_component="tests",
            operation=self.operation,
            safe_message="Old techlog.",
            occurred_at=timezone.now() - timedelta(days=91),
        )

        stdout = StringIO()
        call_command("cleanup_audit_techlog", stdout=stdout)

        self.assertIn("cleanup_audit_techlog completed", stdout.getvalue())
        self.assertEqual(AuditRecord.objects.count(), 0)
        self.assertFalse(TechLogRecord.objects.filter(pk=old_techlog.pk).exists())

    def test_audit_rejects_secret_like_safe_contour(self):
        with self.assertRaises(ValueError):
            create_audit_record(
                action_code=AuditActionCode.WB_API_CONNECTION_CHECKED,
                entity_type="ConnectionBlock",
                entity_id="1",
                user=self.full_user,
                store=self.store,
                safe_message="Authorization: Bearer abcdefghijklmnopqrstuvwxyz1234567890",
            )

        with self.assertRaises(ValueError):
            create_audit_record(
                action_code=AuditActionCode.WB_API_CONNECTION_UPDATED,
                entity_type="ConnectionBlock",
                entity_id="1",
                user=self.full_user,
                store=self.store,
                after_snapshot={"api_key": "abcdef123456"},
            )

        with self.assertRaises(ValueError):
            create_audit_record(
                action_code=AuditActionCode.OZON_API_CONNECTION_CHECKED,
                entity_type="ConnectionBlock",
                entity_id="1",
                user=self.full_user,
                store=self.store,
                safe_message="Client-Id: 123456",
            )

        with self.assertRaises(ValueError):
            create_audit_record(
                action_code=AuditActionCode.OZON_API_CONNECTION_UPDATED,
                entity_type="ConnectionBlock",
                entity_id="1",
                user=self.full_user,
                store=self.store,
                after_snapshot={"Client-Id": "123456"},
            )

        with self.assertRaises(ValueError):
            create_audit_record(
                action_code=AuditActionCode.OZON_API_CONNECTION_CHECKED,
                entity_type="ConnectionBlock",
                entity_id="1",
                user=self.full_user,
                store=self.store,
                safe_message='{"client_id": "123456", "api_key": "ozon-api-key-abcdef"}',
            )

        with self.assertRaises(ValueError):
            create_audit_record(
                action_code=AuditActionCode.OZON_API_CONNECTION_UPDATED,
                entity_type="ConnectionBlock",
                entity_id="1",
                user=self.full_user,
                store=self.store,
                after_snapshot={
                    "payload": '{"Client-Id": "123456", "Api-Key": "ozon-api-key-abcdef"}',
                },
            )
