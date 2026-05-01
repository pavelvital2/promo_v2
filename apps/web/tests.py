import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.audit.models import AuditActionCode, AuditRecord
from apps.discounts.ozon_api.actions import SELECTED_ACTION_METADATA_KEY
from apps.discounts.wb_api.client import WBApiInvalidResponseError
from apps.identity_access.models import AccessEffect, Permission, Role, StoreAccess, UserPermissionOverride
from apps.identity_access.seeds import ROLE_LOCAL_ADMIN, ROLE_OBSERVER, ROLE_OWNER, seed_identity_access
from apps.files.models import FileObject, FileVersion
from apps.files.services import create_file_version
from apps.marketplace_products.models import MarketplaceProduct
from apps.operations.models import (
    CheckStatus,
    Operation,
    OperationDetailRow,
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
