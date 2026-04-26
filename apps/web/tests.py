import re
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.audit.models import AuditActionCode, AuditRecord
from apps.identity_access.models import AccessEffect, Permission, Role, StoreAccess, UserPermissionOverride
from apps.identity_access.seeds import ROLE_LOCAL_ADMIN, ROLE_OBSERVER, ROLE_OWNER, seed_identity_access
from apps.files.models import FileObject, FileVersion
from apps.files.services import create_file_version
from apps.marketplace_products.models import MarketplaceProduct
from apps.operations.models import (
    CheckStatus,
    Operation,
    OperationDetailRow,
    OperationOutputFile,
    OperationType,
    OutputKind,
    Run,
)
from apps.platform_settings.models import StoreParameterChangeHistory, StoreParameterValue
from apps.stores.models import StoreAccount


class BootstrapSmokeTests(SimpleTestCase):
    def test_health_route_returns_ok(self) -> None:
        response = self.client.get(reverse("web:health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class DeploymentReadinessTests(SimpleTestCase):
    repo_root = Path(__file__).resolve().parents[2]

    def read_text(self, relative_path: str) -> str:
        return (self.repo_root / relative_path).read_text(encoding="utf-8")

    def test_nginx_and_systemd_examples_match_stage_1_deployment_decisions(self) -> None:
        nginx_conf = self.read_text("deploy/nginx/promo_v2.conf.example")
        systemd_service = self.read_text("deploy/systemd/promo_v2.service.example")

        self.assertIn("listen 8080;", nginx_conf)
        self.assertNotIn("listen 80;", nginx_conf)
        self.assertIn("proxy_pass http://127.0.0.1:8000;", nginx_conf)
        upload_limit_match = re.search(r"client_max_body_size\s+(\d+)m;", nginx_conf)
        self.assertIsNotNone(upload_limit_match)
        self.assertGreaterEqual(int(upload_limit_match.group(1)), 128)
        self.assertIn("gunicorn config.wsgi:application", systemd_service)
        self.assertIn("--bind 127.0.0.1:8000", systemd_service)

    def test_task_010_operational_scripts_are_executable_and_policy_aligned(self) -> None:
        expected_scripts = [
            "scripts/backup_postgres.sh",
            "scripts/backup_media.sh",
            "scripts/pre_update_backup.sh",
            "scripts/restore_check.sh",
            "scripts/deployment_smoke_check.sh",
            "scripts/audit_techlog_retention_check.sh",
        ]
        for script_path in expected_scripts:
            with self.subTest(script_path=script_path):
                path = self.repo_root / script_path
                self.assertTrue(path.exists())
                self.assertTrue(path.stat().st_mode & 0o111)

        postgres_backup = self.read_text("scripts/backup_postgres.sh")
        media_backup = self.read_text("scripts/backup_media.sh")
        restore_check = self.read_text("scripts/restore_check.sh")
        retention_check = self.read_text("scripts/audit_techlog_retention_check.sh")
        daily_backup_service = self.read_text("deploy/systemd/promo_v2-daily-backup.service.example")
        daily_backup_timer = self.read_text("deploy/systemd/promo_v2-daily-backup.timer.example")
        runbook = self.read_text("docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md")

        self.assertIn('BACKUP_RETENTION_DAYS:-14', postgres_backup)
        self.assertIn('pg_dump', postgres_backup)
        self.assertIn('BACKUP_RETENTION_DAYS:-14', media_backup)
        self.assertIn('RESTORE_DB must not be the production POSTGRES_DB', restore_check)
        self.assertIn('cleanup_audit_techlog --dry-run', retention_check)
        self.assertIn("ExecStart=/opt/promo_v2/scripts/backup_postgres.sh", daily_backup_service)
        self.assertIn("ExecStart=/opt/promo_v2/scripts/backup_media.sh", daily_backup_service)
        self.assertIn("OnCalendar=*-*-* 02:15:00", daily_backup_timer)
        self.assertIn("systemctl enable --now promo_v2-daily-backup.timer", runbook)
        self.assertIn("find /var/backups/promo_v2/postgres", runbook)
        self.assertIn("find /var/backups/promo_v2/media", runbook)

    def test_acceptance_registry_keeps_customer_artifacts_gated(self) -> None:
        registry = self.read_text("docs/testing/CONTROL_FILE_REGISTRY.md")
        plan = self.read_text("docs/testing/STAGE_1_ACCEPTANCE_EXECUTION_PLAN.md")

        self.assertIn("blocked_by_artifact_gate", registry)
        self.assertIn("pending customer delivery", registry)
        self.assertIn("Агенты не создают фиктивные customer files", registry)
        self.assertIn("WB formal comparison", plan)
        self.assertIn("Ozon formal comparison", plan)
        self.assertIn("blocked_by_artifact_gate", plan)


class HomeSmokeTests(TestCase):
    def setUp(self) -> None:
        seed_identity_access()

    def _owner(self):
        owner_role = Role.objects.get(code=ROLE_OWNER)
        return get_user_model().objects.create_user(
            login="owner",
            password="password",
            display_name="Owner",
            primary_role=owner_role,
        )

    def test_home_route_renders_template_shell(self) -> None:
        user = self._owner()
        self.client.force_login(user)
        response = self.client.get(reverse("web:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/home.html")
        self.assertContains(response, "Главная")

    def test_stage_1_owner_screens_smoke(self) -> None:
        user = self._owner()
        StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        StoreAccount.objects.create(
            name="Ozon Store",
            marketplace=StoreAccount.Marketplace.OZON,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        self.client.force_login(user)

        route_names = [
            "web:marketplaces",
            "web:wb_excel",
            "web:ozon_excel",
            "web:operation_list",
            "web:reference_index",
            "web:product_list",
            "web:settings_index",
            "web:admin_index",
            "web:user_list",
            "web:role_list",
            "web:permission_list",
            "web:store_access_list",
            "web:logs_index",
            "web:audit_list",
            "web:techlog_list",
            "web:notification_list",
            "stores:store_list",
        ]
        for route_name in route_names:
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)

    def test_anonymous_home_redirects_to_login(self) -> None:
        response = self.client.get(reverse("web:home"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_product_list_and_card_are_store_access_aware(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        product = MarketplaceProduct.objects.create(
            marketplace="wb",
            store=store,
            sku="WB-1",
            external_ids={"wb": "WB-1"},
            last_values={"last_reason_code": "wb_valid_calculated"},
        )
        self.client.force_login(user)

        response = self.client.get(reverse("web:product_list"))
        self.assertContains(response, "WB-1")
        response = self.client.get(reverse("web:product_card", args=[product.pk]))
        self.assertContains(response, "last_reason_code")

    def test_reference_index_allows_store_scoped_store_list_access(self) -> None:
        local_admin_role = Role.objects.get(code=ROLE_LOCAL_ADMIN)
        user = get_user_model().objects.create_user(
            login="local-admin",
            password="password",
            display_name="Local Admin",
            primary_role=local_admin_role,
        )
        allowed_store = StoreAccount.objects.create(
            name="Allowed WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        denied_store = StoreAccount.objects.create(
            name="Denied Ozon Store",
            marketplace=StoreAccount.Marketplace.OZON,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        StoreAccess.objects.create(
            user=user,
            store=allowed_store,
            access_level=StoreAccess.AccessLevel.ADMIN,
            effect=AccessEffect.ALLOW,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("web:reference_index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("stores:store_list"))
        self.assertNotContains(response, reverse("web:product_list"))

        response = self.client.get(reverse("stores:store_list"))
        self.assertContains(response, allowed_store.name)
        self.assertNotContains(response, denied_store.name)

    def test_product_card_related_operations_match_store_and_marketplace(self) -> None:
        user = self._owner()
        wb_store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        other_store = StoreAccount.objects.create(
            name="Other WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        product = MarketplaceProduct.objects.create(
            marketplace="wb",
            store=wb_store,
            sku="SKU-1",
            external_ids={"wb": "SKU-1"},
        )
        matching_run = Run.objects.create(marketplace="wb", store=wb_store, initiated_by=user)
        matching_operation = Operation.objects.create(
            marketplace="wb",
            operation_type=OperationType.CHECK,
            status=CheckStatus.CREATED,
            run=matching_run,
            store=wb_store,
            initiator_user=user,
            logic_version="test",
        )
        other_run = Run.objects.create(marketplace="wb", store=other_store, initiated_by=user)
        other_operation = Operation.objects.create(
            marketplace="wb",
            operation_type=OperationType.CHECK,
            status=CheckStatus.CREATED,
            run=other_run,
            store=other_store,
            initiator_user=user,
            logic_version="test",
        )
        for operation in (matching_operation, other_operation):
            OperationDetailRow.objects.create(
                operation=operation,
                row_no=1,
                product_ref="SKU-1",
                row_status="ok",
                reason_code="wb_valid_calculated",
                message_level="info",
            )
        self.client.force_login(user)

        response = self.client.get(reverse("web:product_card", args=[product.pk]))

        self.assertContains(response, matching_operation.visible_id)
        self.assertNotContains(response, other_operation.visible_id)

    def test_operation_card_uses_separate_output_and_detail_download_permissions(self) -> None:
        observer_role = Role.objects.get(code=ROLE_OBSERVER)
        user = get_user_model().objects.create_user(
            login="detail-only",
            password="password",
            display_name="Detail Only",
            primary_role=observer_role,
        )
        store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        StoreAccess.objects.create(
            user=user,
            store=store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        for code in (
            "wb_discounts_excel.view_check_result",
            "wb_discounts_excel.download_detail_report",
        ):
            UserPermissionOverride.objects.create(
                user=user,
                permission=Permission.objects.get(code=code),
                effect=AccessEffect.ALLOW,
                store=store,
            )
        run = Run.objects.create(marketplace="wb", store=store, initiated_by=user)
        operation = Operation.objects.create(
            marketplace="wb",
            operation_type=OperationType.CHECK,
            status=CheckStatus.CREATED,
            run=run,
            store=store,
            initiator_user=user,
            logic_version="test",
        )
        output_version = create_file_version(
            store=store,
            uploaded_by=user,
            uploaded_file=SimpleUploadedFile("output.xlsx", b"output"),
            scenario=FileObject.Scenario.WB_DISCOUNTS_EXCEL,
            kind=FileObject.Kind.OUTPUT,
            logical_name="wb output",
        )
        detail_version = create_file_version(
            store=store,
            uploaded_by=user,
            uploaded_file=SimpleUploadedFile("detail.xlsx", b"detail"),
            scenario=FileObject.Scenario.WB_DISCOUNTS_EXCEL,
            kind=FileObject.Kind.DETAIL_REPORT,
            logical_name="wb detail report",
        )
        OperationOutputFile.objects.create(
            operation=operation,
            file_version=output_version,
            output_kind=OutputKind.OUTPUT_WORKBOOK,
        )
        OperationOutputFile.objects.create(
            operation=operation,
            file_version=detail_version,
            output_kind=OutputKind.DETAIL_REPORT,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("web:operation_card", args=[operation.visible_id]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("web:download_file", args=[output_version.pk]))
        self.assertContains(response, reverse("web:download_file", args=[detail_version.pk]))
        direct_detail_download = self.client.get(reverse("web:download_file", args=[detail_version.pk]))
        self.assertEqual(direct_detail_download.status_code, 200)

        UserPermissionOverride.objects.filter(
            user=user,
            permission__code="wb_discounts_excel.download_detail_report",
        ).update(is_active=False)
        UserPermissionOverride.objects.create(
            user=user,
            permission=Permission.objects.get(code="wb_discounts_excel.download_output"),
            effect=AccessEffect.ALLOW,
            store=store,
        )

        response = self.client.get(reverse("web:operation_card", args=[operation.visible_id]))

        self.assertContains(response, reverse("web:download_file", args=[output_version.pk]))
        self.assertNotContains(response, reverse("web:download_file", args=[detail_version.pk]))

    def test_wb_store_parameter_write_creates_history_and_audit(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("web:settings_index"),
            {"store": store.pk, "wb_threshold_percent": "71"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            StoreParameterValue.objects.filter(
                store=store,
                parameter_code="wb_threshold_percent",
                value=71,
                is_active=True,
            ).exists()
        )
        self.assertEqual(StoreParameterChangeHistory.objects.filter(store=store).count(), 1)
        self.assertTrue(AuditRecord.objects.filter(action_code="settings.wb_parameter_changed").exists())

    def test_admin_can_create_user_from_ui(self) -> None:
        user = self._owner()
        observer_role = Role.objects.get(code=ROLE_OBSERVER)
        self.client.force_login(user)

        response = self.client.post(
            reverse("web:user_list"),
            {
                "login": "new-user",
                "display_name": "New User",
                "password": "password",
                "primary_role": observer_role.pk,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(login="new-user").exists())
        self.assertTrue(AuditRecord.objects.filter(action_code="user.created").exists())

    def test_draft_replace_preserves_file_chain_and_creates_audit(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        self.client.force_login(user)

        for name, content in (("prices-v1.xlsx", b"first"), ("prices-v2.xlsx", b"second")):
            response = self.client.post(
                reverse("web:wb_excel"),
                {
                    "store": store.pk,
                    "action": "upload_price",
                    "price_file": SimpleUploadedFile(name, content),
                },
            )
            self.assertEqual(response.status_code, 302)

        file_object = FileObject.objects.get()
        versions = list(FileVersion.objects.filter(file=file_object).order_by("version_no"))
        self.assertEqual([version.version_no for version in versions], [1, 2])
        self.assertEqual(versions[0].original_name, "prices-v1.xlsx")
        self.assertEqual(versions[1].original_name, "prices-v2.xlsx")
        self.assertTrue(
            AuditRecord.objects.filter(action_code=AuditActionCode.FILE_INPUT_UPLOADED).exists()
        )
        replaced = AuditRecord.objects.get(action_code=AuditActionCode.FILE_INPUT_REPLACED)
        self.assertEqual(replaced.before_snapshot["version_id"], versions[0].pk)
        self.assertEqual(replaced.after_snapshot["version_id"], versions[1].pk)
        self.assertNotIn("files/", replaced.safe_message)
        self.assertNotIn("storage_path", replaced.after_snapshot)

        response = self.client.get(f"{reverse('web:wb_excel')}?store={store.pk}")
        self.assertContains(response, "v1")
        self.assertContains(response, "v2")

    def test_admin_user_actions_require_distinct_permissions(self) -> None:
        observer_role = Role.objects.get(code=ROLE_OBSERVER)
        actor = get_user_model().objects.create_user(
            login="status-admin",
            password="password",
            display_name="Status Admin",
            primary_role=observer_role,
        )
        target = get_user_model().objects.create_user(
            login="target-user",
            password="password",
            display_name="Target",
            primary_role=observer_role,
        )
        store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        for user in (actor, target):
            StoreAccess.objects.create(
                user=user,
                store=store,
                access_level=StoreAccess.AccessLevel.ADMIN,
                effect=AccessEffect.ALLOW,
            )
        for code in ("users.card.view", "users.status.change"):
            UserPermissionOverride.objects.create(
                user=actor,
                permission=Permission.objects.get(code=code),
                effect=AccessEffect.ALLOW,
                store=store,
            )
        self.client.force_login(actor)

        response = self.client.post(
            reverse("web:user_card", args=[target.visible_id]),
            {"action": "save_user", "display_name": "Changed", "primary_role": observer_role.pk},
        )
        target.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(target.display_name, "Target")

        response = self.client.post(
            reverse("web:user_card", args=[target.visible_id]),
            {"action": "archive", "reason": "test"},
        )
        target.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(target.status, get_user_model().Status.ARCHIVED)

        response = self.client.post(
            reverse("web:user_card", args=[target.visible_id]),
            {"action": "block", "reason": "test"},
        )
        target.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(target.status, get_user_model().Status.BLOCKED)

    def test_launch_post_denies_run_before_creating_files(self) -> None:
        observer_role = Role.objects.get(code=ROLE_OBSERVER)
        user = get_user_model().objects.create_user(
            login="uploader",
            password="password",
            display_name="Uploader",
            primary_role=observer_role,
        )
        store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        StoreAccess.objects.create(
            user=user,
            store=store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        UserPermissionOverride.objects.create(
            user=user,
            permission=Permission.objects.get(code="wb_discounts_excel.upload_input"),
            effect=AccessEffect.ALLOW,
            store=store,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("web:wb_excel"),
            {
                "store": store.pk,
                "action": "check",
                "price_file": SimpleUploadedFile("prices.xlsx", b"not-xlsx"),
                "promo_files": SimpleUploadedFile("promo.xlsx", b"not-xlsx"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(FileObject.objects.exists())
