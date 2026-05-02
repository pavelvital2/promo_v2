"""Tests for TASK-006 techlog behavior."""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from apps.identity_access.models import AccessEffect, Role, StoreAccess
from apps.identity_access.seeds import ROLE_GLOBAL_ADMIN, ROLE_OBSERVER, seed_identity_access
from apps.operations.services import create_check_operation
from apps.stores.models import StoreAccount
from apps.techlog.models import (
    SystemNotification,
    TECHLOG_EVENT_SEVERITY_BASELINE,
    TechLogEventType,
    TechLogHandledStatus,
    TechLogRecord,
    TechLogSeverity,
)
from apps.techlog.services import (
    cleanup_expired_techlog_records,
    create_techlog_record,
    sensitive_details_for,
    techlog_records_visible_to,
)


class TechLogTask006Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_identity_access()
        user_model = get_user_model()
        full_role = Role.objects.get(code=ROLE_GLOBAL_ADMIN)
        observer_role = Role.objects.get(code=ROLE_OBSERVER)
        cls.full_user = user_model.objects.create_user(
            login="full-techlog",
            password="test",
            display_name="Full Techlog",
            primary_role=full_role,
        )
        cls.limited_user = user_model.objects.create_user(
            login="limited-techlog",
            password="test",
            display_name="Limited Techlog",
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

    def test_techlog_record_links_operation_and_is_immutable(self):
        record = create_techlog_record(
            severity=TechLogSeverity.ERROR,
            event_type=TechLogEventType.OPERATION_EXECUTION_FAILED,
            source_component="apps.operations",
            operation=self.operation,
            user=self.full_user,
            safe_message="Operation failed.",
            sensitive_details_ref="secret-diagnostics-ref",
        )

        self.assertEqual(record.store, self.store)
        self.assertEqual(record.retention_until, record.occurred_at + timedelta(days=90))
        self.assertEqual(list(self.operation.techlog_records.all()), [record])

        record.safe_message = "mutated"
        with self.assertRaises(ValidationError):
            record.save()
        with self.assertRaises(ValidationError):
            TechLogRecord.objects.filter(pk=record.pk).update(safe_message="mutated")
        with self.assertRaises(ProtectedError):
            record.delete()
        with self.assertRaises(ProtectedError):
            TechLogRecord.objects.filter(pk=record.pk).delete()

    def test_marketplace_sync_data_integrity_event_uses_error_baseline(self):
        self.assertEqual(
            TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR,
            "marketplace_sync.data_integrity_error",
        )
        self.assertEqual(
            TECHLOG_EVENT_SEVERITY_BASELINE[
                TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR
            ],
            TechLogSeverity.ERROR,
        )

        record = create_techlog_record(
            severity=TechLogSeverity.WARNING,
            event_type=TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR,
            source_component="tests",
            operation=self.operation,
            safe_message="Source data integrity warning.",
        )

        self.assertEqual(record.event_type, TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR)
        self.assertEqual(record.severity, TechLogSeverity.ERROR)

    def test_core2_pc2_008_techlog_events_use_required_baselines(self):
        expected = {
            TechLogEventType.MARKETPLACE_SYNC_API_ERROR: TechLogSeverity.ERROR,
            TechLogEventType.MARKETPLACE_SNAPSHOT_WRITE_ERROR: TechLogSeverity.ERROR,
            TechLogEventType.MARKETPLACE_MAPPING_CONFLICT: TechLogSeverity.WARNING,
            TechLogEventType.OPERATION_DETAIL_ROW_ENRICHMENT_ERROR: TechLogSeverity.WARNING,
            TechLogEventType.PRODUCT_VARIANT_AUTO_CREATE_ERROR: TechLogSeverity.ERROR,
        }
        for event_type, baseline in expected.items():
            with self.subTest(event_type=event_type):
                self.assertEqual(TECHLOG_EVENT_SEVERITY_BASELINE[event_type], baseline)
                record = create_techlog_record(
                    severity=TechLogSeverity.INFO,
                    event_type=event_type,
                    source_component="tests",
                    operation=self.operation,
                    safe_message="Core 2 techlog event recorded.",
                )
                self.assertEqual(record.severity, baseline)

    def test_techlog_rejects_ozon_client_id_safe_contour(self):
        with self.assertRaises(ValueError):
            create_techlog_record(
                severity=TechLogSeverity.ERROR,
                event_type=TechLogEventType.OZON_API_SECRET_REDACTION_VIOLATION,
                source_component="tests",
                operation=self.operation,
                safe_message="client_id=123456",
            )

        with self.assertRaises(ValueError):
            create_techlog_record(
                severity=TechLogSeverity.ERROR,
                event_type=TechLogEventType.OZON_API_SECRET_REDACTION_VIOLATION,
                source_component="tests",
                operation=self.operation,
                safe_message="Safe message.",
                sensitive_details_ref="Client-Id: 123456",
            )

    def test_limited_full_and_sensitive_techlog_visibility_scopes(self):
        visible_record = create_techlog_record(
            severity=TechLogSeverity.ERROR,
            event_type=TechLogEventType.APPLICATION_EXCEPTION,
            source_component="tests",
            operation=self.operation,
            safe_message="Visible.",
            sensitive_details_ref="visible-sensitive-ref",
        )
        hidden_record = create_techlog_record(
            severity=TechLogSeverity.ERROR,
            event_type=TechLogEventType.APPLICATION_EXCEPTION,
            source_component="tests",
            operation=self.other_operation,
            safe_message="Hidden.",
            sensitive_details_ref="hidden-sensitive-ref",
        )
        hidden_own_store_record = create_techlog_record(
            severity=TechLogSeverity.ERROR,
            event_type=TechLogEventType.APPLICATION_EXCEPTION,
            source_component="tests",
            store=self.other_store,
            user=self.limited_user,
            safe_message="Own inaccessible store techlog.",
            sensitive_details_ref="own-hidden-store-sensitive-ref",
        )
        hidden_own_operation_record = create_techlog_record(
            severity=TechLogSeverity.ERROR,
            event_type=TechLogEventType.APPLICATION_EXCEPTION,
            source_component="tests",
            operation=self.other_operation,
            user=self.limited_user,
            safe_message="Own inaccessible operation techlog.",
            sensitive_details_ref="own-hidden-operation-sensitive-ref",
        )
        own_global_record = create_techlog_record(
            severity=TechLogSeverity.INFO,
            event_type=TechLogEventType.NOTIFICATION_CRITICAL_CREATED,
            source_component="tests",
            user=self.limited_user,
            safe_message="Own global techlog.",
            sensitive_details_ref="own-global-sensitive-ref",
        )

        limited_ids = set(techlog_records_visible_to(self.limited_user).values_list("id", flat=True))
        full_ids = set(techlog_records_visible_to(self.full_user).values_list("id", flat=True))

        self.assertIn(visible_record.pk, limited_ids)
        self.assertNotIn(hidden_record.pk, limited_ids)
        self.assertNotIn(hidden_own_store_record.pk, limited_ids)
        self.assertNotIn(hidden_own_operation_record.pk, limited_ids)
        self.assertIn(own_global_record.pk, limited_ids)
        self.assertIn(visible_record.pk, full_ids)
        self.assertIn(hidden_record.pk, full_ids)
        self.assertIn(hidden_own_store_record.pk, full_ids)
        self.assertIn(hidden_own_operation_record.pk, full_ids)
        self.assertIn(own_global_record.pk, full_ids)
        self.assertEqual(sensitive_details_for(self.limited_user, visible_record), "")
        self.assertEqual(sensitive_details_for(self.limited_user, hidden_own_store_record), "")
        self.assertEqual(
            sensitive_details_for(self.full_user, visible_record),
            "visible-sensitive-ref",
        )

    def test_critical_techlog_creates_system_notification(self):
        record = create_techlog_record(
            severity=TechLogSeverity.CRITICAL,
            event_type=TechLogEventType.FILE_STORAGE_SAVE_ERROR,
            source_component="apps.files.storage",
            operation=self.operation,
            user=self.full_user,
            safe_message="Storage save failed.",
            sensitive_details_ref="storage-secret-ref",
            notification_topic="Storage failure",
        )

        notification = SystemNotification.objects.get(related_techlog_record=record)
        self.assertEqual(record.handled_status, TechLogHandledStatus.NOTIFICATION_CREATED)
        self.assertEqual(notification.topic, "Storage failure")
        self.assertEqual(notification.message, "Storage save failed.")
        self.assertEqual(notification.related_operation, self.operation)
        self.assertEqual(notification.related_store, self.store)

    def test_critical_baseline_normalizes_lower_severity_and_creates_notification(self):
        record = create_techlog_record(
            severity=TechLogSeverity.INFO,
            event_type=TechLogEventType.OPERATION_EXECUTION_FAILED,
            source_component="apps.operations",
            operation=self.operation,
            user=self.full_user,
            safe_message="Operation failed.",
            create_notification_for_critical=False,
        )

        notification = SystemNotification.objects.get(related_techlog_record=record)
        self.assertEqual(record.severity, TechLogSeverity.CRITICAL)
        self.assertEqual(record.handled_status, TechLogHandledStatus.NOTIFICATION_CREATED)
        self.assertEqual(notification.severity, TechLogSeverity.CRITICAL)

    def test_non_critical_baseline_does_not_create_critical_notification_without_grounds(self):
        record = create_techlog_record(
            severity=TechLogSeverity.INFO,
            event_type=TechLogEventType.APPLICATION_EXCEPTION,
            source_component="tests",
            operation=self.operation,
            user=self.full_user,
            safe_message="Application exception.",
        )

        self.assertEqual(record.severity, TechLogSeverity.ERROR)
        self.assertEqual(record.handled_status, TechLogHandledStatus.RECORDED)
        self.assertFalse(SystemNotification.objects.filter(related_techlog_record=record).exists())

    def test_retention_cleanup_is_regulated_non_ui_and_preserves_operation(self):
        old_record = create_techlog_record(
            severity=TechLogSeverity.ERROR,
            event_type=TechLogEventType.APPLICATION_EXCEPTION,
            source_component="tests",
            operation=self.operation,
            safe_message="Old techlog.",
            occurred_at=timezone.now() - timedelta(days=91),
        )
        fresh_record = create_techlog_record(
            severity=TechLogSeverity.ERROR,
            event_type=TechLogEventType.APPLICATION_EXCEPTION,
            source_component="tests",
            operation=self.operation,
            safe_message="Fresh techlog.",
        )

        result = cleanup_expired_techlog_records(now=timezone.now())

        self.assertEqual(result.deleted_count, 1)
        self.assertFalse(TechLogRecord.objects.filter(pk=old_record.pk).exists())
        self.assertTrue(TechLogRecord.objects.filter(pk=fresh_record.pk).exists())
        self.assertTrue(type(self.operation).objects.filter(pk=self.operation.pk).exists())

    def test_techlog_rejects_secret_like_safe_contour(self):
        with self.assertRaises(ValueError):
            create_techlog_record(
                severity=TechLogSeverity.ERROR,
                event_type=TechLogEventType.WB_API_AUTH_FAILED,
                source_component="tests",
                store=self.store,
                safe_message="token=abcdef123456",
            )

        with self.assertRaises(ValueError):
            create_techlog_record(
                severity=TechLogSeverity.ERROR,
                event_type=TechLogEventType.WB_API_AUTH_FAILED,
                source_component="tests",
                store=self.store,
                safe_message="Auth failed.",
                sensitive_details_ref="Bearer abcdefghijklmnopqrstuvwxyz1234567890",
            )

        with self.assertRaises(ValueError):
            create_techlog_record(
                severity=TechLogSeverity.ERROR,
                event_type=TechLogEventType.OZON_API_AUTH_FAILED,
                source_component="tests",
                store=self.store,
                safe_message='{"client-id": "123456", "api_key": "ozon-api-key-abcdef"}',
            )

        with self.assertRaises(ValueError):
            create_techlog_record(
                severity=TechLogSeverity.ERROR,
                event_type=TechLogEventType.OZON_API_AUTH_FAILED,
                source_component="tests",
                store=self.store,
                safe_message="Auth failed.",
                sensitive_details_ref='{"Client-Id": "123456", "Api-Key": "ozon-api-key-abcdef"}',
            )
