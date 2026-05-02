import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.audit.models import AuditActionCode, AuditRecord
from apps.discounts.ozon_api.actions import SELECTED_ACTION_METADATA_KEY
from apps.discounts.wb_api.client import WBApiInvalidResponseError
from apps.identity_access.models import AccessEffect, Permission, Role, StoreAccess, UserPermissionOverride
from apps.identity_access.seeds import (
    ROLE_LOCAL_ADMIN,
    ROLE_MARKETPLACE_MANAGER,
    ROLE_OBSERVER,
    ROLE_OWNER,
    seed_identity_access,
)
from apps.files.models import FileObject, FileVersion
from apps.files.services import create_file_version
from apps.marketplace_products.models import MarketplaceProduct
from apps.operations.models import (
    CheckStatus,
    Operation,
    OperationDetailRow,
    MessageLevel,
    OperationMode,
    OperationModule,
    OperationOutputFile,
    OperationStepCode,
    OperationType,
    OutputKind,
    ProcessStatus,
    Run,
)
from apps.platform_settings.models import StoreParameterChangeHistory, StoreParameterValue
from apps.product_core.models import (
    InternalProduct,
    ListingSource,
    Marketplace,
    MarketplaceListing,
    MarketplaceSyncRun,
    PriceSnapshot,
    ProductIdentifier,
    ProductMappingHistory,
    ProductStatus,
    ProductVariant,
    StockSnapshot,
)
from apps.stores.models import ConnectionBlock, StoreAccount
from apps.web.views import _summary_items


class BootstrapSmokeTests(SimpleTestCase):
    def test_health_route_returns_ok(self) -> None:
        response = self.client.get(reverse("web:health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_summary_items_hide_safe_snapshot_from_user_summary(self) -> None:
        self.assertEqual(
            _summary_items({"result_code": "ok", "safe_snapshot": {"technical": "payload"}}),
            [],
        )

    def test_summary_items_hide_large_operation_payloads_from_user_summary(self) -> None:
        self.assertEqual(
            _summary_items(
                {
                    "products_count": 484,
                    "products": [{"product_id": "1"}],
                    "canonical_rows": [{"product_id": "1"}],
                    "calculation_rows": [{"product_id": "1"}],
                    "accepted_calculation_snapshot": {"rows": [{"product_id": "1"}]},
                    "accepted_basis_candidate": {"add_to_action": [{"product_id": "1"}]},
                }
            ),
            [("products_count", 484)],
        )


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

        self.assertRegex(registry, r"\| WB-REAL-001 \| WB \| .* \| accepted \|")
        self.assertRegex(registry, r"\| OZ-REAL-001 \| Ozon \| .* \| accepted \|")
        self.assertIn("Status: accepted.", registry)
        self.assertIn("Для будущих новых обязательных customer artifacts", registry)
        self.assertIn("blocked_by_artifact_gate", registry)
        self.assertIn("Агенты не создают фиктивные customer files", registry)
        self.assertIn("WB formal comparison", plan)
        self.assertIn("Ozon formal comparison", plan)
        self.assertIn("WB-REAL-001` registered and compared", plan)
        self.assertIn("OZ-REAL-001` registered and compared", plan)
        self.assertIn("accepted", plan)
        self.assertIn("Formal acceptance for `WB-REAL-001` and `OZ-REAL-001` is complete", plan)


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
            "web:internal_product_list",
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

    def test_ozon_elastic_master_page_renders_hierarchy_and_button_order(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="Ozon Store",
            marketplace=StoreAccount.Marketplace.OZON,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        ConnectionBlock.objects.create(
            store=store,
            module="ozon_api",
            connection_type="ozon_client_id_api_key",
            status=ConnectionBlock.Status.ACTIVE,
            protected_secret_ref="env://OZON_TEST_SECRET",
        )
        run = Run.objects.create(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            store=store,
            initiated_by=user,
        )
        Operation.objects.create(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.OZON_API_ACTIONS_DOWNLOAD,
            status=ProcessStatus.COMPLETED_SUCCESS,
            run=run,
            store=store,
            initiator_user=user,
            logic_version="test",
            summary={
                "actions_count": 2,
                "elastic_actions_count": 1,
                "elastic_actions": [
                    {
                        "action_id": "101",
                        "title": "Эластичный бустинг",
                        "action_type": "MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT",
                    }
                ],
            },
        )
        self.client.force_login(user)

        response = self.client.get(reverse("web:ozon_elastic"), {"store": store.pk})

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Маркетплейсы / Ozon / Акции / API / Эластичный бустинг", html)
        expected_order = [
            "Скачать доступные акции",
            "Выбрать акцию",
            "Скачать товары и данные по ним",
            "Обработать",
            "Принять / не принять результат",
            "Скачать Excel для ручной загрузки",
            "Загрузить в Ozon",
        ]
        position = -1
        for text in expected_order:
            next_position = html.find(text, position + 1)
            self.assertGreater(next_position, position, text)
            position = next_position
        self.assertIn("101 Эластичный бустинг", html)

    def test_ozon_elastic_select_action_saves_basis_and_stays_on_master_page(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="Ozon Store",
            marketplace=StoreAccount.Marketplace.OZON,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        connection = ConnectionBlock.objects.create(
            store=store,
            module="ozon_api",
            connection_type="ozon_client_id_api_key",
            status=ConnectionBlock.Status.ACTIVE,
            protected_secret_ref="env://OZON_TEST_SECRET",
        )
        run = Run.objects.create(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            store=store,
            initiated_by=user,
        )
        Operation.objects.create(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.OZON_API_ACTIONS_DOWNLOAD,
            status=ProcessStatus.COMPLETED_SUCCESS,
            run=run,
            store=store,
            initiator_user=user,
            logic_version="test",
            summary={
                "elastic_actions": [
                    {
                        "action_id": "101",
                        "title": "Эластичный бустинг",
                        "action_type": "MARKETPLACE_MULTI_LEVEL_DISCOUNT_ON_AMOUNT",
                    }
                ],
            },
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("web:ozon_elastic"),
            {"store": store.pk, "action": "select_action", "action_id": "101"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], f"{reverse('web:ozon_elastic')}?store={store.pk}")
        connection.refresh_from_db()
        selected = connection.metadata[SELECTED_ACTION_METADATA_KEY]
        self.assertEqual(selected["action_id"], "101")

    def test_ozon_elastic_requires_actions_view_not_operation_view_only(self) -> None:
        observer_role = Role.objects.get(code=ROLE_OBSERVER)
        user = get_user_model().objects.create_user(
            login="op-view-only",
            password="password",
            display_name="Operation View Only",
            primary_role=observer_role,
        )
        store = StoreAccount.objects.create(
            name="Ozon Store",
            marketplace=StoreAccount.Marketplace.OZON,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        StoreAccess.objects.create(
            user=user,
            store=store,
            effect=AccessEffect.ALLOW,
            access_level=StoreAccess.AccessLevel.VIEW,
        )
        UserPermissionOverride.objects.create(
            user=user,
            store=store,
            permission=Permission.objects.get(code="ozon.api.operation.view"),
            effect=AccessEffect.ALLOW,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("web:ozon_elastic"), {"store": store.pk})

        self.assertEqual(response.status_code, 403)

    def test_ozon_elastic_review_and_deactivate_rows_are_visible(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="Ozon Store",
            marketplace=StoreAccount.Marketplace.OZON,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        ConnectionBlock.objects.create(
            store=store,
            module="ozon_api",
            connection_type="ozon_client_id_api_key",
            status=ConnectionBlock.Status.ACTIVE,
            protected_secret_ref="env://OZON_TEST_SECRET",
        )
        rows = [
            {
                "product_id": f"20{index:02d}",
                "offer_id": f"OFFER-{index}",
                "name": f"Product {index}",
                "source_group": "active",
                "J_min_price": "",
                "O_price_min_elastic": "100",
                "P_price_max_elastic": "120",
                "R_stock_present": "5",
                "current_action_price": "110",
                "calculated_action_price": "",
                "reason_code": "missing_min_price",
                "reason": "Missing minimum price.",
                "planned_action": "deactivate_from_action",
                "upload_ready": False,
                "deactivate_required": True,
                "deactivate_reason_code": "missing_min_price",
                "deactivate_reason": "Missing minimum price.",
            }
            for index in range(1, 12)
        ]
        run = Run.objects.create(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            store=store,
            initiated_by=user,
        )
        Operation.objects.create(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.OZON_API_ELASTIC_CALCULATION,
            status=ProcessStatus.COMPLETED_SUCCESS,
            run=run,
            store=store,
            initiator_user=user,
            logic_version="test",
            summary={
                "review_state": "review_pending_deactivate_confirmation",
                "deactivate_confirmation_status": "pending",
                "groups_count": {"deactivate_from_action": len(rows)},
                "calculation_rows": rows,
                "accepted_basis_checksum": "checksum",
                "accepted_calculation_snapshot": {
                    "action_id": "101",
                    "calculation_rows": rows,
                },
            },
        )
        self.client.force_login(user)

        response = self.client.get(reverse("web:ozon_elastic"), {"store": store.pk, "tab": "result"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Будет снято с акции")
        self.assertContains(response, "Не проходит расчёт сейчас")
        self.assertContains(response, "Ошибки")
        self.assertContains(response, "2001")
        deactivate_group = next(group for group in response.context["result_groups"] if group["key"] == "deactivate")
        self.assertEqual(deactivate_group["count"], 11)
        self.assertEqual(len(deactivate_group["rows"]), 10)

        workflow_response = self.client.get(reverse("web:ozon_elastic"), {"store": store.pk})
        workflow_html = workflow_response.content.decode()
        self.assertNotIn("accepted_basis_checksum", workflow_html)
        self.assertNotIn("deactivate_from_action", workflow_html)
        self.assertContains(workflow_response, "Подтвердить снятие с акции")

    def test_ozon_elastic_statuses_are_human_readable(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="Ozon Store",
            marketplace=StoreAccount.Marketplace.OZON,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        ConnectionBlock.objects.create(
            store=store,
            module="ozon_api",
            connection_type="ozon_client_id_api_key",
            status=ConnectionBlock.Status.ACTIVE,
            protected_secret_ref="env://OZON_TEST_SECRET",
        )
        run = Run.objects.create(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            store=store,
            initiated_by=user,
        )
        Operation.objects.create(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.OZON_API_ELASTIC_CALCULATION,
            status=ProcessStatus.COMPLETED_SUCCESS,
            run=run,
            store=store,
            initiator_user=user,
            logic_version="test",
            summary={
                "review_state": "review_pending_deactivate_confirmation",
                "groups_count": {"add_to_action": 1},
                "calculation_rows": [],
            },
        )
        self.client.force_login(user)

        response = self.client.get(reverse("web:ozon_elastic"), {"store": store.pk})

        self.assertContains(response, "Требуется подтверждение снятия с акции")
        self.assertContains(response, "Выполнено")
        self.assertNotContains(response, "review_pending_deactivate_confirmation")
        self.assertNotContains(response, "completed_success")

    def test_ozon_elastic_connection_status_is_human_readable_in_header_and_workflow(self) -> None:
        user = self._owner()
        self.client.force_login(user)
        cases = [
            (ConnectionBlock.Status.ACTIVE, "Активно"),
            (ConnectionBlock.Status.CHECK_FAILED, "Проверка не пройдена"),
            (None, "Не настроено"),
        ]

        for index, (status, expected_label) in enumerate(cases, start=1):
            with self.subTest(status=status or ConnectionBlock.Status.NOT_CONFIGURED):
                store = StoreAccount.objects.create(
                    name=f"Ozon Store {index}",
                    marketplace=StoreAccount.Marketplace.OZON,
                    cabinet_type=StoreAccount.CabinetType.STORE,
                )
                if status is not None:
                    ConnectionBlock.objects.create(
                        store=store,
                        module="ozon_api",
                        connection_type="ozon_client_id_api_key",
                        status=status,
                        protected_secret_ref="env://OZON_TEST_SECRET",
                    )

                response = self.client.get(reverse("web:ozon_elastic"), {"store": store.pk})

                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                match = re.search(
                    r"Подключение Ozon API</strong><span><span class=\"badge[^\"]*\">([^<]+)</span>",
                    html,
                )
                self.assertIsNotNone(match)
                self.assertEqual(match.group(1), expected_label)
                self.assertNotIn(status or ConnectionBlock.Status.NOT_CONFIGURED, match.group(1))
                self.assertNotIn("active Ozon API connection", html)
                self.assertNotIn("check_failed", html)
                self.assertNotIn("not_configured", html)

    def test_ozon_elastic_filters_upload_report_and_completion_block(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="Ozon Store",
            marketplace=StoreAccount.Marketplace.OZON,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        ConnectionBlock.objects.create(
            store=store,
            module="ozon_api",
            connection_type="ozon_client_id_api_key",
            status=ConnectionBlock.Status.ACTIVE,
            protected_secret_ref="env://OZON_TEST_SECRET",
        )
        run = Run.objects.create(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            store=store,
            initiated_by=user,
        )
        manual_version = create_file_version(
            store=store,
            uploaded_by=user,
            uploaded_file=SimpleUploadedFile("manual.xlsx", b"manual"),
            scenario=FileObject.Scenario.OZON_API_ELASTIC_MANUAL_UPLOAD_EXCEL,
            kind=FileObject.Kind.OUTPUT,
            logical_name="ozon_api_elastic_manual_upload_excel.xlsx",
        )
        upload_report_version = create_file_version(
            store=store,
            uploaded_by=user,
            uploaded_file=SimpleUploadedFile("upload.xlsx", b"upload"),
            scenario=FileObject.Scenario.OZON_API_ELASTIC_UPLOAD_REPORT,
            kind=FileObject.Kind.OUTPUT,
            logical_name="ozon_api_elastic_upload_report.xlsx",
        )
        rows = [
            {
                "product_id": "1001",
                "offer_id": "SKU-1001",
                "name": "Needle filter product",
                "source_group": "candidate",
                "planned_action": "add_to_action",
                "reason": "Ready.",
                "upload_ready": True,
                "upload_status": "success",
            },
            {
                "product_id": "1002",
                "offer_id": "SKU-1002",
                "name": "Other product",
                "source_group": "candidate",
                "planned_action": "add_to_action",
                "reason": "Rejected.",
                "upload_ready": True,
                "upload_status": "rejected",
                "reason_code": "ozon_api_upload_rejected",
            },
        ]
        calculation = Operation.objects.create(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.OZON_API_ELASTIC_CALCULATION,
            status=ProcessStatus.COMPLETED_SUCCESS,
            run=run,
            store=store,
            initiator_user=user,
            logic_version="test",
            summary={
                "review_state": "accepted",
                "groups_count": {"add_to_action": 2},
                "manual_upload_file_version_id": manual_version.pk,
                "calculation_rows": rows,
            },
        )
        Operation.objects.create(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.OZON_API_ELASTIC_UPLOAD,
            status=ProcessStatus.COMPLETED_WITH_WARNINGS,
            run=run,
            store=store,
            initiator_user=user,
            check_basis_operation=calculation,
            logic_version="test",
            summary={
                "success_count": 1,
                "rejected_count": 1,
                "upload_report_file_version_id": upload_report_version.pk,
            },
        )
        self.client.force_login(user)

        result_response = self.client.get(
            reverse("web:ozon_elastic"),
            {"store": store.pk, "tab": "result", "q": "Needle", "upload_status": "success", "upload_ready": "true"},
        )
        workflow_response = self.client.get(reverse("web:ozon_elastic"), {"store": store.pk})

        self.assertContains(result_response, "Поиск товара")
        self.assertContains(result_response, "Статус загрузки")
        self.assertContains(result_response, "Готово к загрузке")
        self.assertContains(result_response, "Needle filter product")
        self.assertNotContains(result_response, "Other product")
        self.assertContains(result_response, "ozon_api_elastic_upload_report")
        self.assertContains(workflow_response, "Загрузка завершена")
        self.assertContains(workflow_response, "Отправлено строк")
        self.assertContains(workflow_response, "Принято Ozon")
        self.assertContains(workflow_response, "Отклонено Ozon")
        self.assertContains(workflow_response, "Stage 1-compatible template")

    def test_ozon_elastic_diagnostics_requires_logs_permissions_and_redacts_secrets(self) -> None:
        owner = self._owner()
        manager_role = Role.objects.get(code="marketplace_manager")
        manager = get_user_model().objects.create_user(
            login="manager",
            password="password",
            display_name="Manager",
            primary_role=manager_role,
        )
        store = StoreAccount.objects.create(
            name="Ozon Store",
            marketplace=StoreAccount.Marketplace.OZON,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        StoreAccess.objects.create(
            user=manager,
            store=store,
            effect=AccessEffect.ALLOW,
            access_level=StoreAccess.AccessLevel.WORK,
        )
        ConnectionBlock.objects.create(
            store=store,
            module="ozon_api",
            connection_type="ozon_client_id_api_key",
            status=ConnectionBlock.Status.ACTIVE,
            protected_secret_ref="env://OZON_TEST_SECRET",
        )
        run = Run.objects.create(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            store=store,
            initiated_by=owner,
        )
        Operation.objects.create(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.OZON_API_ELASTIC_CALCULATION,
            status=ProcessStatus.COMPLETED_SUCCESS,
            run=run,
            store=store,
            initiator_user=owner,
            logic_version="test",
            summary={
                "basis": {"Client-Id": "secret-client", "Authorization": "Bearer secret-token"},
                "accepted_basis_checksum": "checksum",
                "groups_count": {"add_to_action": 1},
                "calculation_rows": [],
            },
        )

        self.client.force_login(manager)
        manager_response = self.client.get(reverse("web:ozon_elastic"), {"store": store.pk})
        self.assertNotContains(manager_response, "Диагностика")
        for code in (
            "audit.list.view",
            "audit.card.view",
            "techlog.list.view",
            "techlog.card.view",
            "logs.scope.limited",
        ):
            UserPermissionOverride.objects.create(
                user=manager,
                store=store,
                permission=Permission.objects.get(code=code),
                effect=AccessEffect.ALLOW,
            )
        manager_diag_response = self.client.get(
            reverse("web:ozon_elastic"),
            {"store": store.pk, "tab": "diagnostics"},
        )
        self.assertNotContains(manager_diag_response, "Операционные доказательства")

        self.client.force_login(owner)
        owner_response = self.client.get(
            reverse("web:ozon_elastic"),
            {"store": store.pk, "tab": "diagnostics"},
        )
        self.assertContains(owner_response, "Диагностика")
        self.assertContains(owner_response, "Операционные доказательства")
        self.assertContains(owner_response, "Основание расчёта")
        self.assertContains(owner_response, "Снимки, checksums и source operations")
        self.assertContains(owner_response, "API metadata")
        self.assertContains(owner_response, "Audit / Techlog")
        self.assertContains(owner_response, "Технические коды")
        self.assertContains(owner_response, "[redacted]")
        self.assertNotContains(owner_response, "secret-client")
        self.assertNotContains(owner_response, "secret-token")

    def test_operation_card_keeps_raw_structures_out_of_short_summary(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="Ozon Store",
            marketplace=StoreAccount.Marketplace.OZON,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        run = Run.objects.create(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            store=store,
            initiated_by=user,
        )
        operation = Operation.objects.create(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.OZON_API_ELASTIC_CALCULATION,
            status=ProcessStatus.RUNNING,
            run=run,
            store=store,
            initiator_user=user,
            logic_version="test",
            summary={
                "rows_count": 2,
                "groups_count": {"add_to_action": 1},
                "basis": {"action_id": "101"},
                "result_code": "ozon_api_calculation_completed",
            },
        )
        OperationDetailRow.objects.create(
            operation=operation,
            row_no=1,
            product_ref="1001",
            row_status="ok",
            reason_code="",
            message_level="info",
            message="ok",
            final_value={"long": "x" * 120},
        )
        self.client.force_login(user)

        response = self.client.get(reverse("web:operation_card", args=[operation.visible_id]))

        html = response.content.decode()
        short_block = html.split("Технические блоки", 1)[0]
        self.assertIn("rows_count", short_block)
        self.assertNotIn("groups_count", short_block)
        self.assertNotIn("result_code", short_block)
        self.assertContains(response, "groups_count")
        self.assertContains(response, "table-scroll")

    def test_anonymous_home_redirects_to_login(self) -> None:
        response = self.client.get(reverse("web:home"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_legacy_product_list_and_card_keep_stage_1_route_compatibility(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Legacy Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        legacy_product = MarketplaceProduct.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            sku="LEGACY-SKU-1",
            barcode="4600000000101",
            title="Legacy marketplace product",
            external_ids={"nmID": "LEGACY-SKU-1"},
            last_values={"price": "999"},
        )
        InternalProduct.objects.create(pk=legacy_product.pk, internal_code="IP-COLLISION", name="Collision")
        self.client.force_login(user)

        response = self.client.get(reverse("web:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LEGACY-SKU-1")
        self.assertNotContains(response, "IP-COLLISION")

        response = self.client.get(reverse("web:product_card", args=[legacy_product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Legacy marketplace product")
        self.assertContains(response, "LEGACY-SKU-1")
        self.assertNotContains(response, "IP-COLLISION")

    def test_internal_product_list_and_card_are_store_access_aware(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        product = InternalProduct.objects.create(internal_code="IP-001", name="Needle")
        variant = ProductVariant.objects.create(
            product=product,
            internal_sku="SKU-1",
            name="Default",
        )
        MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            internal_variant=variant,
            external_primary_id="WB-1",
            seller_article="WB-ART-1",
            mapping_status=MarketplaceListing.MappingStatus.MATCHED,
            last_source=ListingSource.MANUAL_IMPORT,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("web:internal_product_list"))
        self.assertContains(response, "IP-001")
        self.assertContains(response, "Needle")
        response = self.client.get(reverse("web:internal_product_card", args=[product.pk]))
        self.assertContains(response, "SKU-1")
        self.assertContains(response, "WB-ART-1")

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
        self.assertNotContains(response, reverse("web:internal_product_list"))

        response = self.client.get(reverse("stores:store_list"))
        self.assertContains(response, allowed_store.name)
        self.assertNotContains(response, denied_store.name)

    def test_product_card_hides_inaccessible_listing_counts_and_details(self) -> None:
        manager_role = Role.objects.get(code="marketplace_manager")
        manager = get_user_model().objects.create_user(
            login="pc-manager",
            password="password",
            display_name="PC Manager",
            primary_role=manager_role,
        )
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
        StoreAccess.objects.create(
            user=manager,
            store=wb_store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        product = InternalProduct.objects.create(internal_code="IP-002", name="Private counts")
        variant = ProductVariant.objects.create(
            product=product,
            internal_sku="SKU-PRIVATE",
            name="Default",
        )
        MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=wb_store,
            internal_variant=variant,
            external_primary_id="VISIBLE-LISTING",
            seller_article="VISIBLE-ART",
            mapping_status=MarketplaceListing.MappingStatus.MATCHED,
            last_source=ListingSource.MANUAL_IMPORT,
        )
        MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=other_store,
            internal_variant=variant,
            external_primary_id="HIDDEN-LISTING",
            seller_article="HIDDEN-ART",
            mapping_status=MarketplaceListing.MappingStatus.MATCHED,
            last_source=ListingSource.MANUAL_IMPORT,
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("web:internal_product_card", args=[product.pk]))

        self.assertContains(response, "VISIBLE-ART")
        self.assertNotContains(response, "HIDDEN-ART")
        self.assertContains(response, "<dt>WB</dt><dd>1</dd>", html=True)

    def test_marketplace_listing_list_filters_and_enforces_store_access(self) -> None:
        manager = get_user_model().objects.create_user(
            login="listing-manager",
            password="password",
            display_name="Listing Manager",
            primary_role=Role.objects.get(code=ROLE_MARKETPLACE_MANAGER),
        )
        allowed_store = StoreAccount.objects.create(
            name="Allowed WB Listing Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        hidden_store = StoreAccount.objects.create(
            name="Hidden WB Listing Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        StoreAccess.objects.create(
            user=manager,
            store=allowed_store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        visible_listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=allowed_store,
            external_primary_id="VISIBLE-NM",
            seller_article="VISIBLE-ART",
            barcode="460000000001",
            title="Visible listing",
            brand="Visible brand",
            category_name="Visible category",
            mapping_status=MarketplaceListing.MappingStatus.UNMATCHED,
            last_values={"price": "100.00", "currency": "RUB", "total_stock": 5},
            last_source=ListingSource.MANUAL_IMPORT,
        )
        hidden_listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=hidden_store,
            external_primary_id="HIDDEN-NM",
            seller_article="HIDDEN-ART",
            last_source=ListingSource.MANUAL_IMPORT,
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("web:marketplace_listing_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VISIBLE-ART")
        self.assertContains(response, "100.00")
        self.assertNotContains(response, "HIDDEN-ART")

        response = self.client.get(
            reverse("web:marketplace_listing_list"),
            {"q": "VISIBLE", "stock": "present"},
        )
        self.assertContains(response, "VISIBLE-NM")

        response = self.client.get(reverse("web:unmatched_listing_list"))
        self.assertContains(response, "VISIBLE-ART")

        response = self.client.get(reverse("web:marketplace_listing_card", args=[hidden_listing.pk]))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("web:marketplace_listing_card", args=[visible_listing.pk]))
        self.assertEqual(response.status_code, 200)

    def test_product_core_exports_apply_access_and_do_not_leak_hidden_listing_details(self) -> None:
        manager = get_user_model().objects.create_user(
            login="export-manager",
            password="password",
            display_name="Export Manager",
            primary_role=Role.objects.get(code=ROLE_MARKETPLACE_MANAGER),
        )
        allowed_store = StoreAccount.objects.create(
            name="Allowed Export Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        hidden_store = StoreAccount.objects.create(
            name="Hidden Export Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        StoreAccess.objects.create(
            user=manager,
            store=allowed_store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        UserPermissionOverride.objects.create(
            user=manager,
            permission=Permission.objects.get(code="product_core.export"),
            effect=AccessEffect.ALLOW,
        )
        product = InternalProduct.objects.create(internal_code="IP-EXPORT", name="Export product")
        variant = ProductVariant.objects.create(product=product, internal_sku="SKU-EXPORT", name="Default")
        MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=allowed_store,
            internal_variant=variant,
            external_primary_id="VISIBLE-EXPORT-NM",
            seller_article="VISIBLE-EXPORT-ART",
            mapping_status=MarketplaceListing.MappingStatus.MATCHED,
            last_source=ListingSource.MANUAL_IMPORT,
        )
        MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=hidden_store,
            internal_variant=variant,
            external_primary_id="HIDDEN-EXPORT-NM",
            seller_article="HIDDEN-EXPORT-ART",
            mapping_status=MarketplaceListing.MappingStatus.MATCHED,
            last_source=ListingSource.MANUAL_IMPORT,
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("web:internal_product_export"))

        body = response.content.decode("utf-8-sig")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("IP-EXPORT", body)
        self.assertIn(",1,0,", body)
        self.assertNotIn("VISIBLE-EXPORT-ART", body)
        self.assertNotIn("HIDDEN-EXPORT-ART", body)
        self.assertNotIn("Hidden Export Store", body)
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.PRODUCT_CORE_EXPORT_GENERATED,
                entity_id="internal_products",
                user=manager,
            ).exists(),
        )

        response = self.client.get(reverse("web:marketplace_listing_export"))
        body = response.content.decode("utf-8-sig")
        self.assertIn("VISIBLE-EXPORT-ART", body)
        self.assertNotIn("HIDDEN-EXPORT-ART", body)
        self.assertNotIn("Hidden Export Store", body)
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.PRODUCT_CORE_EXPORT_GENERATED,
                entity_id="marketplace_listings",
                user=manager,
            ).exists(),
        )

    def test_listing_export_blanks_internal_identifiers_without_product_core_view(self) -> None:
        manager = get_user_model().objects.create_user(
            login="listing-export-no-product-view",
            password="password",
            display_name="Listing Export No Product View",
            primary_role=Role.objects.get(code=ROLE_MARKETPLACE_MANAGER),
        )
        store = StoreAccount.objects.create(
            name="Identifier Gate Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        StoreAccess.objects.create(
            user=manager,
            store=store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        for code in ("product_core.view", "product_variant.view"):
            UserPermissionOverride.objects.create(
                user=manager,
                permission=Permission.objects.get(code=code),
                effect=AccessEffect.DENY,
            )
        product = InternalProduct.objects.create(internal_code="IP-HIDDEN-EXPORT", name="Hidden product")
        variant = ProductVariant.objects.create(product=product, internal_sku="SKU-HIDDEN-EXPORT", name="Hidden variant")
        MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            internal_variant=variant,
            external_primary_id="VISIBLE-LINKED-NM",
            seller_article="VISIBLE-LINKED-ART",
            mapping_status=MarketplaceListing.MappingStatus.MATCHED,
            last_source=ListingSource.MANUAL_IMPORT,
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("web:marketplace_listing_export"))

        body = response.content.decode("utf-8-sig")
        self.assertEqual(response.status_code, 200)
        self.assertIn("VISIBLE-LINKED-ART", body)
        self.assertNotIn("IP-HIDDEN-EXPORT", body)
        self.assertNotIn("Hidden product", body)
        self.assertNotIn("SKU-HIDDEN-EXPORT", body)
        self.assertNotIn("Hidden variant", body)

    def test_listing_related_exports_blank_internal_identifiers_without_variant_view(self) -> None:
        manager = get_user_model().objects.create_user(
            login="listing-export-no-variant-view",
            password="password",
            display_name="Listing Export No Variant View",
            primary_role=Role.objects.get(code=ROLE_MARKETPLACE_MANAGER),
        )
        store = StoreAccount.objects.create(
            name="Variant Gate Export Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        StoreAccess.objects.create(
            user=manager,
            store=store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        UserPermissionOverride.objects.create(
            user=manager,
            permission=Permission.objects.get(code="product_variant.view"),
            effect=AccessEffect.DENY,
        )
        product = InternalProduct.objects.create(
            internal_code="IP-VARIANT-GATED",
            name="Variant gated product",
        )
        variant = ProductVariant.objects.create(
            product=product,
            internal_sku="SKU-VARIANT-GATED",
            name="Variant gated variant",
        )
        listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            internal_variant=variant,
            external_primary_id="VARIANT-GATED-NM",
            seller_article="VARIANT-GATED-ART",
            last_values={"price": "101.00", "total_stock": 5},
            mapping_status=MarketplaceListing.MappingStatus.MATCHED,
            last_source=ListingSource.MANUAL_IMPORT,
        )
        run = Run.objects.create(
            marketplace=Marketplace.WB,
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            store=store,
            initiated_by=manager,
        )
        operation = Operation.objects.create(
            marketplace=Marketplace.WB,
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.WB_API_PRICES_DOWNLOAD,
            status=ProcessStatus.CREATED,
            run=run,
            store=store,
            initiator_user=manager,
            logic_version="test",
        )
        OperationDetailRow.objects.create(
            operation=operation,
            marketplace_listing=listing,
            row_no=1,
            product_ref="VARIANT-GATED-NM",
            row_status="ok",
            reason_code="wb_api_price_row_valid",
            message_level=MessageLevel.INFO,
        )
        self.client.force_login(manager)

        export_names = [
            "marketplace_listing_export",
            "listing_latest_values_export",
            "listing_mapping_report_export",
            "operation_link_report_export",
        ]
        for export_name in export_names:
            with self.subTest(export_name=export_name):
                response = self.client.get(reverse(f"web:{export_name}"))
                body = response.content.decode("utf-8-sig")

                self.assertEqual(response.status_code, 200)
                self.assertIn("VARIANT-GATED-ART", body)
                self.assertNotIn("IP-VARIANT-GATED", body)
                self.assertNotIn("Variant gated product", body)
                self.assertNotIn("SKU-VARIANT-GATED", body)
                self.assertNotIn("Variant gated variant", body)

    def test_listing_latest_values_export_redacts_secret_like_values_and_raw_safe(self) -> None:
        manager = get_user_model().objects.create_user(
            login="latest-export-manager",
            password="password",
            display_name="Latest Export Manager",
            primary_role=Role.objects.get(code=ROLE_MARKETPLACE_MANAGER),
        )
        store = StoreAccount.objects.create(
            name="Latest Export Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        StoreAccess.objects.create(
            user=manager,
            store=store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        run = MarketplaceSyncRun.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            sync_type=MarketplaceSyncRun.SyncType.PRICES,
            source=ListingSource.WB_API_PRICES,
            status=MarketplaceSyncRun.SyncStatus.COMPLETED_SUCCESS,
            started_at=timezone.now(),
            finished_at=timezone.now(),
        )
        listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            external_primary_id="LATEST-NM",
            seller_article="LATEST-ART",
            last_values={
                "price": "100.00",
                "currency": "RUB",
                "api_key": "SECRET-VALUE-123456",
                "nested": {"Authorization": "Bearer abcdefghijklmnop"},
                "raw_safe": {"debug_marker": "LATEST-RAW-SAFE-SHOULD-NOT-EXPORT"},
                "request_headers": {"X-Debug": "LATEST-REQUEST-HEADER-SHOULD-NOT-EXPORT"},
                "stack_trace": "LATEST-STACK-SHOULD-NOT-EXPORT",
            },
            last_source=ListingSource.WB_API_PRICES,
        )
        PriceSnapshot.objects.create(
            listing=listing,
            sync_run=run,
            snapshot_at=timezone.now(),
            price="100.00",
            currency="RUB",
            raw_safe={"debug_marker": "RAW-SAFE-SHOULD-NOT-EXPORT"},
            source_endpoint="wb_prices_list_goods_filter",
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("web:listing_latest_values_export"))

        body = response.content.decode("utf-8-sig")
        self.assertContains(response, "LATEST-ART")
        self.assertIn("100.00", body)
        self.assertIn("[redacted]", body)
        self.assertNotIn("api_key", body)
        self.assertNotIn("SECRET-VALUE-123456", body)
        self.assertNotIn("Authorization", body)
        self.assertNotIn("LATEST-RAW-SAFE-SHOULD-NOT-EXPORT", body)
        self.assertNotIn("LATEST-REQUEST-HEADER-SHOULD-NOT-EXPORT", body)
        self.assertNotIn("LATEST-STACK-SHOULD-NOT-EXPORT", body)
        self.assertNotIn("RAW-SAFE-SHOULD-NOT-EXPORT", body)

    def test_listing_latest_values_export_denies_when_snapshot_scope_is_absent(self) -> None:
        manager = get_user_model().objects.create_user(
            login="latest-export-no-snapshot",
            password="password",
            display_name="Latest Export No Snapshot",
            primary_role=Role.objects.get(code=ROLE_MARKETPLACE_MANAGER),
        )
        store = StoreAccount.objects.create(
            name="No Snapshot Export Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        StoreAccess.objects.create(
            user=manager,
            store=store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        UserPermissionOverride.objects.create(
            user=manager,
            permission=Permission.objects.get(code="marketplace_snapshot.view"),
            store=store,
            effect=AccessEffect.DENY,
        )
        MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            external_primary_id="NO-SNAPSHOT-NM",
            seller_article="NO-SNAPSHOT-ART",
            last_values={"price": "100.00"},
            last_source=ListingSource.MANUAL_IMPORT,
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("web:listing_latest_values_export"))

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.PRODUCT_CORE_EXPORT_GENERATED,
                entity_id="listing_latest_values",
                user=manager,
            ).exists(),
        )

    def test_unmatched_and_mapping_report_exports_use_visible_rows(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Mapping Export Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        product = InternalProduct.objects.create(internal_code="IP-MAPPING-EXPORT", name="Mapped")
        variant = ProductVariant.objects.create(product=product, internal_sku="SKU-MAPPING-EXPORT", name="Default")
        MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            internal_variant=variant,
            external_primary_id="MAPPED-EXPORT-NM",
            seller_article="MAPPED-EXPORT-ART",
            mapping_status=MarketplaceListing.MappingStatus.MATCHED,
            last_source=ListingSource.MANUAL_IMPORT,
        )
        MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            external_primary_id="UNMATCHED-EXPORT-NM",
            seller_article="UNMATCHED-EXPORT-ART",
            mapping_status=MarketplaceListing.MappingStatus.UNMATCHED,
            last_source=ListingSource.MANUAL_IMPORT,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("web:unmatched_listing_export"))
        body = response.content.decode("utf-8-sig")
        self.assertIn("UNMATCHED-EXPORT-ART", body)
        self.assertNotIn("MAPPED-EXPORT-ART", body)

        response = self.client.get(reverse("web:listing_mapping_report_export"))
        body = response.content.decode("utf-8-sig")
        self.assertIn("MAPPED-EXPORT-ART", body)
        self.assertIn("SKU-MAPPING-EXPORT", body)
        self.assertIn("UNMATCHED-EXPORT-ART", body)

    def test_operation_link_report_exports_visible_rows_and_blanks_variant_without_permission(self) -> None:
        manager = get_user_model().objects.create_user(
            login="operation-link-export-manager",
            password="password",
            display_name="Operation Link Export Manager",
            primary_role=Role.objects.get(code=ROLE_MARKETPLACE_MANAGER),
        )
        store = StoreAccount.objects.create(
            name="Operation Link Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        StoreAccess.objects.create(
            user=manager,
            store=store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        for code in ("product_core.view", "product_variant.view"):
            UserPermissionOverride.objects.create(
                user=manager,
                permission=Permission.objects.get(code=code),
                effect=AccessEffect.DENY,
            )
        product = InternalProduct.objects.create(internal_code="IP-OP-LINK", name="Operation link product")
        variant = ProductVariant.objects.create(product=product, internal_sku="SKU-OP-LINK", name="Operation link variant")
        listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            internal_variant=variant,
            external_primary_id="OP-LINK-NM",
            seller_article="OP-LINK-ART",
            mapping_status=MarketplaceListing.MappingStatus.MATCHED,
            last_source=ListingSource.MANUAL_IMPORT,
        )
        run = Run.objects.create(
            marketplace=Marketplace.WB,
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            store=store,
            initiated_by=manager,
        )
        operation = Operation.objects.create(
            marketplace=Marketplace.WB,
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.WB_API_PRICES_DOWNLOAD,
            status=ProcessStatus.CREATED,
            run=run,
            store=store,
            initiator_user=manager,
            logic_version="test",
        )
        linked_row = OperationDetailRow.objects.create(
            operation=operation,
            marketplace_listing=listing,
            row_no=1,
            product_ref="OP-LINK-NM",
            row_status="ok",
            reason_code="wb_api_price_row_valid",
            message_level=MessageLevel.INFO,
        )
        unresolved_row = OperationDetailRow.objects.create(
            operation=operation,
            row_no=2,
            product_ref="OP-LINK-NM",
            row_status="ok",
            reason_code="wb_api_price_row_valid",
            message_level=MessageLevel.INFO,
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("web:operation_link_report_export"))

        body = response.content.decode("utf-8-sig")
        self.assertEqual(response.status_code, 200)
        self.assertIn(operation.visible_id, body)
        self.assertIn("OP-LINK-NM", body)
        self.assertIn("OP-LINK-ART", body)
        self.assertIn("linked", body)
        self.assertIn("not_linked", body)
        self.assertNotIn("SKU-OP-LINK", body)
        self.assertNotIn("IP-OP-LINK", body)
        unresolved_row.refresh_from_db()
        linked_row.refresh_from_db()
        self.assertIsNone(unresolved_row.marketplace_listing_id)
        self.assertEqual(linked_row.marketplace_listing_id, listing.pk)
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.PRODUCT_CORE_EXPORT_GENERATED,
                entity_id="operation_link_report",
                user=manager,
            ).exists(),
        )

    def test_marketplace_listing_card_hides_raw_safe_without_technical_permission(self) -> None:
        manager = get_user_model().objects.create_user(
            login="listing-snapshot-manager",
            password="password",
            display_name="Listing Snapshot Manager",
            primary_role=Role.objects.get(code=ROLE_MARKETPLACE_MANAGER),
        )
        store = StoreAccount.objects.create(
            name="WB Snapshot Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        StoreAccess.objects.create(
            user=manager,
            store=store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        run = Run.objects.create(
            marketplace="wb",
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            store=store,
            initiated_by=manager,
        )
        operation = Operation.objects.create(
            marketplace="wb",
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.WB_API_PRICES_DOWNLOAD,
            status=ProcessStatus.RUNNING,
            run=run,
            store=store,
            initiator_user=manager,
            logic_version="test",
        )
        output_version = create_file_version(
            store=store,
            uploaded_by=manager,
            uploaded_file=SimpleUploadedFile("prices.xlsx", b"prices"),
            scenario=FileObject.Scenario.WB_DISCOUNTS_API_PRICE_EXPORT,
            kind=FileObject.Kind.OUTPUT,
            logical_name="wb api prices",
            module=OperationModule.WB_API,
        )
        OperationOutputFile.objects.create(
            operation=operation,
            file_version=output_version,
            output_kind=OutputKind.PROMOTION_EXPORT,
        )
        Operation.objects.filter(pk=operation.pk).update(status=ProcessStatus.COMPLETED_SUCCESS)
        operation.refresh_from_db()
        sync_run = MarketplaceSyncRun.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            sync_type=MarketplaceSyncRun.SyncType.PRICES,
            source=ListingSource.WB_API_PRICES,
            status=MarketplaceSyncRun.SyncStatus.COMPLETED_SUCCESS,
            started_at=timezone.now(),
            finished_at=timezone.now(),
            requested_by=manager,
            operation=operation,
        )
        listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            external_primary_id="RAW-NM",
            external_ids={"nmID": "RAW-NM"},
            seller_article="RAW-ART",
            last_values={"price": "123.45", "currency": "RUB", "total_stock": 9},
            last_successful_sync_at=sync_run.finished_at,
            last_sync_run=sync_run,
            last_source=ListingSource.WB_API_PRICES,
        )
        PriceSnapshot.objects.create(
            listing=listing,
            sync_run=sync_run,
            operation=operation,
            snapshot_at=timezone.now(),
            price="123.45",
            currency="RUB",
            raw_safe={"debug_marker": "RAW-SAFE-MARKER"},
            source_endpoint="wb_prices_list_goods_filter",
        )
        StockSnapshot.objects.create(
            listing=listing,
            sync_run=sync_run,
            operation=operation,
            snapshot_at=timezone.now(),
            total_stock=9,
            raw_safe={"stock_marker": "RAW-STOCK-MARKER"},
            source_endpoint="wb_stock_summary",
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("web:marketplace_listing_card", args=[listing.pk]))

        self.assertContains(response, "RAW-ART")
        self.assertContains(response, operation.visible_id)
        self.assertContains(response, reverse("web:download_file", args=[output_version.pk]))
        self.assertContains(response, "Скрыто")
        self.assertNotContains(response, "RAW-SAFE-MARKER")
        self.assertNotContains(response, "RAW-STOCK-MARKER")

        UserPermissionOverride.objects.create(
            user=manager,
            permission=Permission.objects.get(code="marketplace_snapshot.technical_view"),
            effect=AccessEffect.ALLOW,
            store=store,
        )
        response = self.client.get(reverse("web:marketplace_listing_card", args=[listing.pk]))

        self.assertContains(response, "RAW-SAFE-MARKER")
        self.assertContains(response, "RAW-STOCK-MARKER")

    def test_mapping_workflow_requires_permission_and_does_not_auto_confirm_candidates(self) -> None:
        manager = get_user_model().objects.create_user(
            login="mapping-manager",
            password="password",
            display_name="Mapping Manager",
            primary_role=Role.objects.get(code=ROLE_MARKETPLACE_MANAGER),
        )
        local_admin = get_user_model().objects.create_user(
            login="mapping-local-admin",
            password="password",
            display_name="Mapping Local Admin",
            primary_role=Role.objects.get(code=ROLE_LOCAL_ADMIN),
        )
        store = StoreAccount.objects.create(
            name="WB Mapping Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        for user in (manager, local_admin):
            StoreAccess.objects.create(
                user=user,
                store=store,
                access_level=StoreAccess.AccessLevel.WORK,
                effect=AccessEffect.ALLOW,
            )
        product = InternalProduct.objects.create(internal_code="IP-MAP", name="Mapped product")
        variant = ProductVariant.objects.create(
            product=product,
            internal_sku="MAP-ART",
            name="Mapped variant",
        )
        listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            external_primary_id="WB-MAP-1",
            seller_article="MAP-ART",
            mapping_status=MarketplaceListing.MappingStatus.UNMATCHED,
            last_source=ListingSource.MANUAL_IMPORT,
        )

        self.client.force_login(manager)
        response = self.client.get(reverse("web:marketplace_listing_mapping", args=[listing.pk]))
        self.assertEqual(response.status_code, 403)

        self.client.force_login(local_admin)
        response = self.client.get(reverse("web:marketplace_listing_mapping", args=[listing.pk]))
        listing.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Подсказки не являются авторитетным решением")
        self.assertContains(response, "exact_seller_article")
        self.assertIsNone(listing.internal_variant)
        self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.NEEDS_REVIEW)
        self.assertTrue(
            ProductMappingHistory.objects.filter(
                listing=listing,
                action=ProductMappingHistory.MappingAction.NEEDS_REVIEW_MARKER,
            ).exists()
        )

        response = self.client.post(
            reverse("web:marketplace_listing_mapping", args=[listing.pk]),
            {
                "action": "link_existing",
                "variant": str(variant.pk),
                "reason_comment": "Explicitly confirmed by user.",
            },
        )
        listing.refresh_from_db()
        self.assertEqual(response["Location"], reverse("web:marketplace_listing_card", args=[listing.pk]))
        self.assertEqual(listing.internal_variant, variant)
        self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.MATCHED)
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.MARKETPLACE_LISTING_MAPPED,
                user=local_admin,
                store=store,
            ).exists()
        )

    def test_leave_unmatched_records_history_and_audit_for_already_unmatched_listing(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Already Unmatched Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            external_primary_id="WB-ALREADY-UNMATCHED",
            seller_article="NO-MATCH",
            mapping_status=MarketplaceListing.MappingStatus.UNMATCHED,
            last_source=ListingSource.MANUAL_IMPORT,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("web:marketplace_listing_mapping", args=[listing.pk]),
            {
                "action": "leave_unmatched",
                "reason_comment": "Explicitly keep unmatched.",
            },
        )

        listing.refresh_from_db()
        self.assertEqual(response["Location"], reverse("web:marketplace_listing_card", args=[listing.pk]))
        self.assertIsNone(listing.internal_variant)
        self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.UNMATCHED)
        history = ProductMappingHistory.objects.get(listing=listing)
        self.assertEqual(history.action, ProductMappingHistory.MappingAction.UNMAP)
        self.assertIsNone(history.previous_variant)
        self.assertIsNone(history.new_variant)
        self.assertEqual(history.mapping_status_after, MarketplaceListing.MappingStatus.UNMATCHED)
        self.assertEqual(history.reason_comment, "Explicitly keep unmatched.")
        self.assertEqual(history.source_context, {"basis": "manual_leave_unmatched"})
        audit = AuditRecord.objects.get(
            action_code=AuditActionCode.MARKETPLACE_LISTING_UNMAPPED,
            entity_type="ProductMappingHistory",
            entity_id=str(history.pk),
            user=user,
            store=store,
        )
        self.assertEqual(audit.source_context, "ui")
        self.assertEqual(audit.after_snapshot["mapping_status"], MarketplaceListing.MappingStatus.UNMATCHED)
        self.assertIsNone(audit.after_snapshot["variant_id"])
        self.assertEqual(audit.after_snapshot["mapping_action"], ProductMappingHistory.MappingAction.UNMAP)
        self.assertEqual(audit.after_snapshot["reason_comment"], "Explicitly keep unmatched.")
        self.assertEqual(audit.after_snapshot["mapping_source_context"], {"basis": "manual_leave_unmatched"})

    def test_mapping_workflow_conflict_unmap_and_create_product_variant(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Mapping Owner Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        product = InternalProduct.objects.create(internal_code="IP-CONFLICT", name="Conflict product")
        variant = ProductVariant.objects.create(product=product, internal_sku="DUP-WEB", name="First")
        other_variant = ProductVariant.objects.create(
            product=product,
            internal_sku="DUP-WEB-2",
            name="Second",
        )
        ProductIdentifier.objects.create(
            variant=other_variant,
            identifier_type=ProductIdentifier.IdentifierType.LEGACY_ARTICLE,
            value="DUP-WEB",
        )
        listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            external_primary_id="WB-CONFLICT",
            seller_article="DUP-WEB",
            last_source=ListingSource.MANUAL_IMPORT,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("web:marketplace_listing_mapping", args=[listing.pk]))
        listing.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.CONFLICT)
        self.assertIsNone(listing.internal_variant)

        self.client.post(
            reverse("web:marketplace_listing_mapping", args=[listing.pk]),
            {"action": "link_existing", "variant": str(variant.pk), "reason_comment": "Resolve."},
        )
        listing.refresh_from_db()
        self.assertEqual(listing.internal_variant, variant)

        self.client.post(
            reverse("web:marketplace_listing_mapping", args=[listing.pk]),
            {
                "action": "unmap",
                "mapping_status_after": MarketplaceListing.MappingStatus.CONFLICT,
                "reason_comment": "Still conflicting.",
            },
        )
        listing.refresh_from_db()
        self.assertIsNone(listing.internal_variant)
        self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.CONFLICT)
        self.assertTrue(
            ProductMappingHistory.objects.filter(
                listing=listing,
                action=ProductMappingHistory.MappingAction.UNMAP,
                previous_variant=variant,
                mapping_status_after=MarketplaceListing.MappingStatus.CONFLICT,
            ).exists()
        )

        new_listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=store,
            external_primary_id="WB-NEW",
            seller_article="NEW-WEB",
            last_source=ListingSource.MANUAL_IMPORT,
        )
        response = self.client.post(
            reverse("web:marketplace_listing_mapping", args=[new_listing.pk]),
            {
                "action": "create_product_variant",
                "product-internal_code": "IP-WEB-NEW",
                "product-name": "Web new product",
                "product-product_type": InternalProduct.ProductType.FINISHED_GOOD,
                "product-status": ProductStatus.ACTIVE,
                "product-comments": "",
                "product-attributes_json": "{}",
                "variant-internal_sku": "NEW-WEB",
                "variant-name": "Web new variant",
                "variant-barcode_internal": "",
                "variant-status": ProductStatus.ACTIVE,
                "variant-variant_attributes_json": "{}",
                "reason_comment": "Create from mapping workflow.",
            },
        )
        new_listing.refresh_from_db()
        self.assertEqual(response["Location"], reverse("web:marketplace_listing_card", args=[new_listing.pk]))
        self.assertIsNotNone(new_listing.internal_variant)
        self.assertEqual(new_listing.internal_variant.internal_sku, "NEW-WEB")
        self.assertEqual(new_listing.mapping_status, MarketplaceListing.MappingStatus.MATCHED)

    def test_internal_product_and_variant_create_update_archive_flows(self) -> None:
        user = self._owner()
        self.client.force_login(user)

        create_response = self.client.post(
            reverse("web:internal_product_create"),
            {
                "internal_code": "IP-FLOW",
                "name": "Flow product",
                "product_type": InternalProduct.ProductType.FINISHED_GOOD,
                "status": "active",
                "attributes_json": '{"color": "black"}',
                "comments": "created",
            },
        )
        product = InternalProduct.objects.get(internal_code="IP-FLOW")
        self.assertEqual(create_response["Location"], reverse("web:internal_product_card", args=[product.pk]))
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.PRODUCT_CORE_CREATED,
                entity_type="InternalProduct",
                entity_id=str(product.pk),
            ).exists()
        )

        update_response = self.client.post(
            reverse("web:internal_product_update", args=[product.pk]),
            {
                "internal_code": "IP-FLOW",
                "name": "Flow product updated",
                "product_type": InternalProduct.ProductType.MATERIAL,
                "status": "inactive",
                "attributes_json": '{"color": "white"}',
                "comments": "updated",
            },
        )
        product.refresh_from_db()
        self.assertEqual(update_response["Location"], reverse("web:internal_product_card", args=[product.pk]))
        self.assertEqual(product.name, "Flow product updated")
        self.assertEqual(product.attributes, {"color": "white"})

        variant_response = self.client.post(
            reverse("web:internal_variant_create", args=[product.pk]),
            {
                "internal_sku": "FLOW-SKU",
                "name": "Flow variant",
                "barcode_internal": "4600000000000",
                "status": "active",
                "variant_attributes_json": '{"size": "M"}',
            },
        )
        variant = ProductVariant.objects.get(product=product, internal_sku="FLOW-SKU")
        self.assertEqual(variant_response["Location"], reverse("web:internal_product_card", args=[product.pk]))

        variant_update_response = self.client.post(
            reverse("web:internal_variant_update", args=[product.pk, variant.pk]),
            {
                "internal_sku": "FLOW-SKU",
                "name": "Flow variant updated",
                "barcode_internal": "4600000000001",
                "status": "inactive",
                "variant_attributes_json": '{"size": "L"}',
            },
        )
        variant.refresh_from_db()
        self.assertEqual(variant_update_response["Location"], reverse("web:internal_product_card", args=[product.pk]))
        self.assertEqual(variant.name, "Flow variant updated")
        self.assertEqual(variant.variant_attributes, {"size": "L"})

        self.client.post(reverse("web:internal_variant_archive", args=[product.pk, variant.pk]))
        variant.refresh_from_db()
        self.assertEqual(variant.status, "archived")

        self.client.post(reverse("web:internal_product_archive", args=[product.pk]))
        product.refresh_from_db()
        self.assertEqual(product.status, "archived")

    def test_product_core_write_requires_permissions(self) -> None:
        observer_role = Role.objects.get(code=ROLE_OBSERVER)
        user = get_user_model().objects.create_user(
            login="pc-observer-web",
            password="password",
            display_name="PC Observer Web",
            primary_role=observer_role,
        )
        product = InternalProduct.objects.create(internal_code="IP-DENY", name="Deny")
        self.client.force_login(user)

        response = self.client.get(reverse("web:internal_product_create"))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("web:internal_product_update", args=[product.pk]))
        self.assertEqual(response.status_code, 403)

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

    def test_wb_api_master_requires_object_access_and_shows_active_connection(self) -> None:
        observer_role = Role.objects.get(code=ROLE_OBSERVER)
        user = get_user_model().objects.create_user(
            login="wb-api-viewer",
            password="password",
            display_name="WB API Viewer",
            primary_role=observer_role,
        )
        allowed_store = StoreAccount.objects.create(
            name="Allowed WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        hidden_store = StoreAccount.objects.create(
            name="Hidden WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        ConnectionBlock.objects.create(
            store=allowed_store,
            module="wb_api",
            connection_type="wb_header_api_key",
            status=ConnectionBlock.Status.ACTIVE,
            protected_secret_ref="env://WB_API_REF",
            is_stage2_1_used=True,
            metadata={"safe": "value"},
        )
        StoreAccess.objects.create(
            user=user,
            store=allowed_store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        for code in ("wb.api.operation.view", "wb.api.connection.view"):
            UserPermissionOverride.objects.create(
                user=user,
                permission=Permission.objects.get(code=code),
                effect=AccessEffect.ALLOW,
                store=allowed_store,
            )
        self.client.force_login(user)

        response = self.client.get(reverse("web:wb_api"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Allowed WB Store")
        self.assertNotContains(response, "Hidden WB Store")
        self.assertContains(response, "active")
        self.assertContains(response, "[ref-set]")
        self.assertNotContains(response, "env://WB_API_REF")

        StoreAccess.objects.create(
            user=user,
            store=hidden_store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.DENY,
        )
        response = self.client.get(f"{reverse('web:wb_api')}?store={hidden_store.pk}")
        self.assertEqual(response.status_code, 403)

    def test_wb_api_post_invokes_price_service_and_preserves_store_redirect(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        run = Run.objects.create(
            marketplace="wb",
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            store=store,
            initiated_by=user,
        )
        operation = Operation.objects.create(
            marketplace="wb",
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.WB_API_PRICES_DOWNLOAD,
            status=ProcessStatus.COMPLETED_SUCCESS,
            run=run,
            store=store,
            initiator_user=user,
            logic_version="test",
        )
        self.client.force_login(user)

        with patch("apps.web.views.wb_api_prices_services.download_wb_prices", return_value=operation) as service:
            response = self.client.post(
                reverse("web:wb_api"),
                {"store": store.pk, "action": "download_prices"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            f"{reverse('web:wb_api')}?store={store.pk}&operation={operation.visible_id}",
        )
        service.assert_called_once()

    def test_wb_api_post_shows_safe_message_when_wb_api_fails(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        self.client.force_login(user)

        with patch(
            "apps.web.views.wb_api_promotions_services.download_wb_current_promotions",
            side_effect=WBApiInvalidResponseError(WBApiInvalidResponseError.safe_message),
        ) as service:
            response = self.client.post(
                reverse("web:wb_api"),
                {"store": store.pk, "action": "download_promotions"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "WB API returned an invalid response.")
        service.assert_called_once()

    def test_wb_api_calculation_requires_active_connection_in_ui_and_dispatch(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        ConnectionBlock.objects.create(
            store=store,
            module="wb_api",
            connection_type="wb_header_api_key",
            status=ConnectionBlock.Status.CONFIGURED,
            is_stage2_1_used=True,
        )
        run = Run.objects.create(
            marketplace="wb",
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            store=store,
            initiated_by=user,
        )
        price_operation = Operation.objects.create(
            marketplace="wb",
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.WB_API_PRICES_DOWNLOAD,
            status=ProcessStatus.COMPLETED_SUCCESS,
            run=run,
            store=store,
            initiator_user=user,
            logic_version="test",
        )
        promotion_operation = Operation.objects.create(
            marketplace="wb",
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.WB_API_PROMOTIONS_DOWNLOAD,
            status=ProcessStatus.COMPLETED_SUCCESS,
            run=run,
            store=store,
            initiator_user=user,
            logic_version="test",
        )
        self.client.force_login(user)

        response = self.client.get(f"{reverse('web:wb_api')}?store={store.pk}")

        self.assertContains(response, "Действия Stage 2.1 заблокированы: требуется active connection.")
        self.assertRegex(
            response.content.decode(),
            r'<button[^>]+name="action"[^>]+value="calculate"[^>]+disabled',
        )

        with patch("apps.web.views.wb_api_calculation_services.calculate_wb_api_discounts") as service:
            response = self.client.post(
                reverse("web:wb_api"),
                {
                    "store": store.pk,
                    "action": "calculate",
                    "price_operation_id": price_operation.pk,
                    "promotion_operation_id": promotion_operation.pk,
                },
            )

        self.assertEqual(response.status_code, 200)
        service.assert_not_called()
        self.assertContains(response, "Действие заблокировано: требуется active connection.")

    def test_operation_list_and_card_classify_wb_api_by_step_code(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        run = Run.objects.create(
            marketplace="wb",
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            store=store,
            initiated_by=user,
        )
        operation = Operation.objects.create(
            marketplace="wb",
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.WB_API_DISCOUNT_UPLOAD,
            status=ProcessStatus.COMPLETED_WITH_WARNINGS,
            run=run,
            store=store,
            initiator_user=user,
            logic_version="test",
            warning_count=1,
        )
        self.client.force_login(user)

        response = self.client.get(
            f"{reverse('web:operation_list')}?mode=api&step_code={OperationStepCode.WB_API_DISCOUNT_UPLOAD}"
        )
        self.assertContains(response, "2.1.4 Загрузить по API")
        self.assertNotContains(response, "<td>not_applicable</td>", html=True)

        response = self.client.get(reverse("web:operation_card", args=[operation.visible_id]))
        self.assertContains(response, OperationStepCode.WB_API_DISCOUNT_UPLOAD)
        self.assertContains(response, "2.1.4 Загрузить по API")
        self.assertNotContains(response, "Подтверждение warnings")

    def test_wb_api_upload_confirmation_posts_exact_phrase_to_service(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        ConnectionBlock.objects.create(
            store=store,
            module="wb_api",
            connection_type="wb_header_api_key",
            status=ConnectionBlock.Status.ACTIVE,
            protected_secret_ref="env://WB_API_REF",
            is_stage2_1_used=True,
        )
        run = Run.objects.create(
            marketplace="wb",
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            store=store,
            initiated_by=user,
        )
        calculation = Operation.objects.create(
            marketplace="wb",
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.WB_API_DISCOUNT_CALCULATION,
            status=ProcessStatus.RUNNING,
            run=run,
            store=store,
            initiator_user=user,
            logic_version="test",
        )
        result_version = create_file_version(
            store=store,
            uploaded_by=user,
            uploaded_file=SimpleUploadedFile("result.xlsx", b"output"),
            scenario=FileObject.Scenario.WB_DISCOUNTS_API_RESULT_EXCEL,
            kind=FileObject.Kind.OUTPUT,
            logical_name="wb api result",
            module=OperationModule.WB_API,
        )
        OperationOutputFile.objects.create(
            operation=calculation,
            file_version=result_version,
            output_kind=OutputKind.OUTPUT_WORKBOOK,
        )
        OperationDetailRow.objects.create(
            operation=calculation,
            row_no=1,
            product_ref="123",
            row_status="ok",
            reason_code="wb_api_calculated_from_api_sources",
            message_level="info",
            final_value={"upload_ready": True, "final_discount": 20, "current_price": "100"},
        )
        Operation.objects.filter(pk=calculation.pk).update(status=ProcessStatus.COMPLETED_SUCCESS)
        calculation.refresh_from_db()
        upload_operation = Operation.objects.create(
            marketplace="wb",
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.WB_API_DISCOUNT_UPLOAD,
            status=ProcessStatus.COMPLETED_SUCCESS,
            run=run,
            store=store,
            initiator_user=user,
            logic_version="test",
        )
        self.client.force_login(user)

        phrase = "Я понимаю, что скидки будут отправлены в WB по API."
        with patch(
            "apps.web.views.wb_api_upload_services.upload_wb_api_discounts",
            return_value=upload_operation,
        ) as service:
            response = self.client.post(
                reverse("web:wb_api_upload_confirm"),
                {
                    "store": store.pk,
                    "calculation_operation_id": calculation.pk,
                    "confirmation_phrase": phrase,
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            f"{reverse('web:wb_api')}?store={store.pk}&operation={upload_operation.visible_id}",
        )
        self.assertEqual(service.call_args.kwargs["confirmation_phrase"], phrase)

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

    def test_wb_check_keeps_draft_files_for_process(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        self.client.force_login(user)
        self.client.post(
            reverse("web:wb_excel"),
            {
                "store": store.pk,
                "action": "upload_price",
                "price_file": SimpleUploadedFile("prices.xlsx", b"price"),
            },
        )
        self.client.post(
            reverse("web:wb_excel"),
            {
                "store": store.pk,
                "action": "upload_promo",
                "promo_files": SimpleUploadedFile("promo.xlsx", b"promo"),
            },
        )
        session_key = f"draft:wb:{store.pk}"
        before = self.client.session[session_key].copy()

        with patch(
            "apps.web.views.wb_services.run_wb_check",
            return_value=SimpleNamespace(visible_id="OP-2026-999001"),
        ):
            response = self.client.post(
                reverse("web:wb_excel"),
                {"store": store.pk, "action": "check"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            f"{reverse('web:wb_excel')}?store={store.pk}&operation=OP-2026-999001",
        )
        self.assertEqual(self.client.session[session_key], before)

    def test_owner_can_edit_wb_parameters_on_upload_page(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        self.client.force_login(user)

        response = self.client.get(f"{reverse('web:wb_excel')}?store={store.pk}")
        self.assertContains(response, "Сохранить параметры WB")
        self.assertContains(response, "wb_threshold_percent")

        response = self.client.post(
            reverse("web:wb_excel"),
            {
                "store": store.pk,
                "action": "save_wb_params",
                "wb_threshold_percent": "70",
                "wb_fallback_no_promo_percent": "55",
                "wb_fallback_over_threshold_percent": "55",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], f"{reverse('web:wb_excel')}?store={store.pk}")
        self.assertEqual(StoreParameterValue.objects.filter(store=store, is_active=True).count(), 3)
        self.assertTrue(AuditRecord.objects.filter(action_code="settings.wb_parameter_changed").exists())

    def test_ozon_check_keeps_draft_file_for_process(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="Ozon Store",
            marketplace=StoreAccount.Marketplace.OZON,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        self.client.force_login(user)
        self.client.post(
            reverse("web:ozon_excel"),
            {
                "store": store.pk,
                "action": "upload_input",
                "input_file": SimpleUploadedFile("ozon.xlsx", b"input"),
            },
        )
        session_key = f"draft:ozon:{store.pk}"
        before = self.client.session[session_key].copy()

        with patch(
            "apps.web.views.ozon_services.run_ozon_check",
            return_value=SimpleNamespace(visible_id="OP-2026-999002"),
        ):
            response = self.client.post(
                reverse("web:ozon_excel"),
                {"store": store.pk, "action": "check"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            f"{reverse('web:ozon_excel')}?store={store.pk}&operation=OP-2026-999002",
        )
        self.assertEqual(self.client.session[session_key], before)

    def test_excel_pages_show_product_core_boundary_and_uploads_do_not_create_core_records(self) -> None:
        user = self._owner()
        wb_store = StoreAccount.objects.create(
            name="WB Boundary Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        ozon_store = StoreAccount.objects.create(
            name="Ozon Boundary Store",
            marketplace=StoreAccount.Marketplace.OZON,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        self.client.force_login(user)

        response = self.client.get(f"{reverse('web:wb_excel')}?store={wb_store.pk}")
        self.assertContains(response, "не обновляет Product Core")
        response = self.client.get(f"{reverse('web:ozon_excel')}?store={ozon_store.pk}")
        self.assertContains(response, "не обновляет Product Core")

        self.client.post(
            reverse("web:wb_excel"),
            {
                "store": wb_store.pk,
                "action": "upload_price",
                "price_file": SimpleUploadedFile("prices.xlsx", b"price"),
            },
        )
        self.client.post(
            reverse("web:ozon_excel"),
            {
                "store": ozon_store.pk,
                "action": "upload_input",
                "input_file": SimpleUploadedFile("ozon.xlsx", b"input"),
            },
        )

        self.assertEqual(InternalProduct.objects.count(), 0)
        self.assertEqual(ProductVariant.objects.count(), 0)
        self.assertEqual(MarketplaceListing.objects.count(), 0)
        self.assertEqual(ProductMappingHistory.objects.count(), 0)

    def test_excel_page_shows_process_output_download_inline(self) -> None:
        user = self._owner()
        store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )
        run = Run.objects.create(marketplace="wb", store=store, initiated_by=user)
        check = Operation.objects.create(
            marketplace="wb",
            operation_type=OperationType.CHECK,
            status=CheckStatus.COMPLETED_NO_ERRORS,
            run=run,
            store=store,
            initiator_user=user,
            logic_version="test",
        )
        operation = Operation.objects.create(
            marketplace="wb",
            operation_type=OperationType.PROCESS,
            status="running",
            run=run,
            store=store,
            initiator_user=user,
            check_basis_operation=check,
            logic_version="test",
            summary={"output_created": True},
        )
        output_version = create_file_version(
            store=store,
            uploaded_by=user,
            uploaded_file=SimpleUploadedFile("result.xlsx", b"output"),
            scenario=FileObject.Scenario.WB_DISCOUNTS_EXCEL,
            kind=FileObject.Kind.OUTPUT,
            logical_name="wb output",
        )
        OperationOutputFile.objects.create(
            operation=operation,
            file_version=output_version,
            output_kind=OutputKind.OUTPUT_WORKBOOK,
        )
        self.client.force_login(user)

        response = self.client.get(
            f"{reverse('web:wb_excel')}?store={store.pk}&operation={operation.visible_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Результат {operation.visible_id}")
        self.assertContains(response, reverse("web:download_file", args=[output_version.pk]))

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
