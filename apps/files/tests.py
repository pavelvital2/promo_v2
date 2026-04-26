"""Tests for TASK-004 files/storage behavior."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.identity_access.models import AccessEffect, StoreAccess, UserPermissionOverride
from apps.identity_access.seeds import (
    ROLE_MARKETPLACE_MANAGER,
    ROLE_OBSERVER,
    seed_identity_access,
)
from apps.stores.models import StoreAccount

from .models import FileObject, FileVersion
from .services import (
    FileRetentionExpired,
    FileUnavailable,
    assert_can_download_file_version,
    cleanup_expired_physical_files,
    create_file_version,
    delete_pre_operation_file_upload,
    delete_pre_operation_file_version,
    open_file_version_for_download,
)


class FileStorageTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_root = tempfile.mkdtemp(prefix="promo-v2-files-tests-")
        cls.override = override_settings(MEDIA_ROOT=cls._media_root)
        cls.override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.override.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        seed_identity_access()
        role_manager = cls._role(ROLE_MARKETPLACE_MANAGER)
        role_observer = cls._role(ROLE_OBSERVER)
        User = get_user_model()
        cls.manager = User.objects.create_user(
            login="manager",
            password="password",
            display_name="Manager",
            primary_role=role_manager,
        )
        cls.observer = User.objects.create_user(
            login="observer",
            password="password",
            display_name="Observer",
            primary_role=role_observer,
        )
        cls.store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        StoreAccess.objects.create(
            user=cls.manager,
            store=cls.store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        StoreAccess.objects.create(
            user=cls.observer,
            store=cls.store,
            access_level=StoreAccess.AccessLevel.VIEW,
            effect=AccessEffect.ALLOW,
        )

    @staticmethod
    def _role(code):
        from apps.identity_access.models import Role

        return Role.objects.get(code=code)

    @staticmethod
    def upload(name: str, content: bytes, content_type: str = "application/vnd.ms-excel"):
        return SimpleUploadedFile(name, content, content_type=content_type)

    def create_output_version(self, content: bytes = b"result"):
        return create_file_version(
            store=self.store,
            uploaded_by=self.manager,
            uploaded_file=self.upload("result.xlsx", content),
            scenario=FileObject.Scenario.WB_DISCOUNTS_EXCEL,
            kind=FileObject.Kind.OUTPUT,
            logical_name="wb output",
        )

    def test_upload_creates_metadata_version_checksum_and_safe_path(self):
        content = b"wb input workbook bytes"
        version = create_file_version(
            store=self.store,
            uploaded_by=self.manager,
            uploaded_file=self.upload("../unsafe/name.xlsx", content),
            scenario=FileObject.Scenario.WB_DISCOUNTS_EXCEL,
            kind=FileObject.Kind.INPUT,
            logical_name="price upload",
        )

        self.assertEqual(version.version_no, 1)
        self.assertEqual(version.original_name, "name.xlsx")
        self.assertEqual(version.file.visible_id[:10], f"FILE-{timezone.localtime().year}-")
        self.assertEqual(version.checksum_sha256, hashlib.sha256(content).hexdigest())
        self.assertEqual(version.size, len(content))
        self.assertTrue(default_storage.exists(version.storage_path))
        self.assertIn(f"/{version.file.visible_id}/v000001/", version.storage_path)
        self.assertNotIn("..", version.storage_path)
        self.assertGreater(version.retention_until, timezone.now() + timedelta(days=2, hours=23))

    def test_repeated_upload_same_logical_file_creates_new_version(self):
        first = create_file_version(
            store=self.store,
            uploaded_by=self.manager,
            uploaded_file=self.upload("same.xlsx", b"first"),
            scenario=FileObject.Scenario.WB_DISCOUNTS_EXCEL,
            kind=FileObject.Kind.INPUT,
            logical_name="same logical input",
            operation_ref="OP-2026-000001",
        )
        second = create_file_version(
            store=self.store,
            uploaded_by=self.manager,
            uploaded_file=self.upload("same.xlsx", b"second"),
            scenario=FileObject.Scenario.WB_DISCOUNTS_EXCEL,
            kind=FileObject.Kind.INPUT,
            logical_name="same logical input",
            file_object=first.file,
        )

        first.refresh_from_db()
        self.assertEqual(second.file_id, first.file_id)
        self.assertEqual(second.version_no, 2)
        self.assertNotEqual(first.storage_path, second.storage_path)
        self.assertNotEqual(first.checksum_sha256, second.checksum_sha256)
        self.assertEqual(first.operation_ref, "OP-2026-000001")
        self.assertEqual(first.file.versions.count(), 2)

    def test_download_requires_scenario_permission_and_store_access(self):
        version = self.create_output_version()
        detail_version = create_file_version(
            store=self.store,
            uploaded_by=self.manager,
            uploaded_file=self.upload("details.xlsx", b"details"),
            scenario=FileObject.Scenario.WB_DISCOUNTS_EXCEL,
            kind=FileObject.Kind.DETAIL_REPORT,
            logical_name="wb detail report",
        )

        assert_can_download_file_version(self.manager, version)
        assert_can_download_file_version(self.manager, detail_version)
        with self.assertRaises(PermissionDenied):
            assert_can_download_file_version(self.observer, version)
        with self.assertRaises(PermissionDenied):
            assert_can_download_file_version(self.observer, detail_version)

        no_access_user = get_user_model().objects.create_user(
            login="no-access",
            password="password",
            display_name="No access",
            primary_role=self._role(ROLE_MARKETPLACE_MANAGER),
        )
        with self.assertRaises(PermissionDenied):
            assert_can_download_file_version(no_access_user, version)

    def test_individual_download_deny_overrides_role_permission(self):
        version = self.create_output_version(b"blocked")
        permission = version.file.scenario + ".download_output"
        from apps.identity_access.models import Permission

        UserPermissionOverride.objects.create(
            user=self.manager,
            permission=Permission.objects.get(code=permission),
            effect=AccessEffect.DENY,
            store=self.store,
        )

        with self.assertRaises(PermissionDenied):
            assert_can_download_file_version(self.manager, version)

    def test_expired_or_deleted_physical_file_is_unavailable_but_metadata_remains(self):
        version = self.create_output_version(b"expired")
        expired_at = timezone.now() - timedelta(minutes=1)
        FileVersion.objects.filter(pk=version.pk).update(retention_until=expired_at)
        version.refresh_from_db()

        with self.assertRaises(FileRetentionExpired):
            assert_can_download_file_version(self.manager, version)

        result = cleanup_expired_physical_files(now=timezone.now())
        version.refresh_from_db()
        self.assertEqual(result.scanned, 1)
        self.assertEqual(result.deleted, 1)
        self.assertFalse(default_storage.exists(version.storage_path))
        self.assertEqual(version.physical_status, FileVersion.PhysicalStatus.RETENTION_DELETED)
        self.assertTrue(FileObject.objects.filter(pk=version.file_id).exists())
        self.assertTrue(FileVersion.objects.filter(pk=version.pk).exists())

        with self.assertRaises(FileUnavailable):
            open_file_version_for_download(self.manager, version)

    def test_cleanup_dry_run_preserves_physical_file_and_status(self):
        version = self.create_output_version(b"dry-run")
        FileVersion.objects.filter(pk=version.pk).update(
            retention_until=timezone.now() - timedelta(days=1),
        )
        version.refresh_from_db()

        result = cleanup_expired_physical_files(dry_run=True)
        version.refresh_from_db()
        self.assertEqual(result.scanned, 1)
        self.assertEqual(result.deleted, 1)
        self.assertTrue(default_storage.exists(version.storage_path))
        self.assertEqual(version.physical_status, FileVersion.PhysicalStatus.AVAILABLE)

    def test_pre_operation_delete_removes_input_physical_file_and_metadata(self):
        version = create_file_version(
            store=self.store,
            uploaded_by=self.manager,
            uploaded_file=self.upload("wrong.xlsx", b"wrong upload"),
            scenario=FileObject.Scenario.WB_DISCOUNTS_EXCEL,
            kind=FileObject.Kind.INPUT,
            logical_name="wrong input",
        )
        file_object_id = version.file_id
        version_id = version.pk
        storage_path = version.storage_path

        result = delete_pre_operation_file_upload(version.file)

        self.assertEqual(result.file_object_id, file_object_id)
        self.assertEqual(result.version_ids, (version_id,))
        self.assertEqual(result.physical_deleted, 1)
        self.assertEqual(result.physical_missing, 0)
        self.assertFalse(default_storage.exists(storage_path))
        self.assertFalse(FileVersion.objects.filter(pk=version_id).exists())
        self.assertFalse(FileObject.objects.filter(pk=file_object_id).exists())

    def test_pre_operation_delete_can_remove_one_unused_version(self):
        first = create_file_version(
            store=self.store,
            uploaded_by=self.manager,
            uploaded_file=self.upload("first.xlsx", b"first"),
            scenario=FileObject.Scenario.WB_DISCOUNTS_EXCEL,
            kind=FileObject.Kind.INPUT,
            logical_name="draft input",
        )
        second = create_file_version(
            store=self.store,
            uploaded_by=self.manager,
            uploaded_file=self.upload("second.xlsx", b"second"),
            scenario=FileObject.Scenario.WB_DISCOUNTS_EXCEL,
            kind=FileObject.Kind.INPUT,
            logical_name="draft input",
            file_object=first.file,
        )
        second_path = second.storage_path

        result = delete_pre_operation_file_version(second)

        self.assertEqual(result.version_ids, (second.pk,))
        self.assertEqual(result.physical_deleted, 1)
        self.assertFalse(default_storage.exists(second_path))
        self.assertTrue(FileObject.objects.filter(pk=first.file_id).exists())
        self.assertTrue(FileVersion.objects.filter(pk=first.pk).exists())
        self.assertFalse(FileVersion.objects.filter(pk=second.pk).exists())

    def test_pre_operation_delete_rejects_operation_linked_or_generated_files(self):
        linked = create_file_version(
            store=self.store,
            uploaded_by=self.manager,
            uploaded_file=self.upload("linked.xlsx", b"linked"),
            scenario=FileObject.Scenario.WB_DISCOUNTS_EXCEL,
            kind=FileObject.Kind.INPUT,
            logical_name="linked input",
            operation_ref="OP-2026-000001",
        )
        output = self.create_output_version(b"generated")

        with self.assertRaises(ValidationError):
            delete_pre_operation_file_upload(linked.file)
        with self.assertRaises(ValidationError):
            delete_pre_operation_file_upload(output.file)

        self.assertTrue(default_storage.exists(linked.storage_path))
        self.assertTrue(default_storage.exists(output.storage_path))
        self.assertTrue(FileVersion.objects.filter(pk=linked.pk).exists())
        self.assertTrue(FileVersion.objects.filter(pk=output.pk).exists())
