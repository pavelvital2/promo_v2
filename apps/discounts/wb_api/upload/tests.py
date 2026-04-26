from __future__ import annotations

import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase, override_settings
from openpyxl import Workbook

from apps.audit.models import AuditRecord
from apps.discounts.wb_api.client import WBApiAlreadyExistsError, WBApiInvalidResponseError
from apps.discounts.wb_api.redaction import contains_secret_like
from apps.files.models import FileObject
from apps.files.services import create_file_version
from apps.identity_access.models import AccessEffect, Role, StoreAccess
from apps.identity_access.seeds import ROLE_MARKETPLACE_MANAGER, ROLE_OWNER, seed_identity_access
from apps.operations.models import (
    Marketplace,
    MessageLevel,
    Operation,
    OperationDetailRow,
    OperationMode,
    OperationStepCode,
    OperationType,
    OutputKind,
    ProcessStatus,
)
from apps.operations.services import ApiOperationResult, complete_api_operation, create_api_operation, start_operation
from apps.stores.models import ConnectionBlock, StoreAccount
from apps.stores.services import WB_API_CONNECTION_TYPE, WB_API_MODULE
from apps.techlog.models import TechLogRecord

from .services import CONFIRMATION_PHRASE, UPLOAD_BATCH_SIZE, upload_wb_api_discounts


class FakeUploadClient:
    def __init__(
        self,
        *,
        token,
        store_scope,
        drift_goods=None,
        upload_responses=None,
        statuses=None,
        details=None,
        quarantines=None,
        upload_error=None,
    ):
        self.token = token
        self.store_scope = store_scope
        self.drift_goods = list(drift_goods or [])
        self.upload_responses = list(upload_responses or [])
        self.statuses = list(statuses or [])
        self.details = list(details or [])
        self.quarantines = list(quarantines or [])
        self.upload_error = upload_error
        self.drift_calls = []
        self.upload_payloads = []
        self.history_calls = []
        self.buffer_calls = []

    def list_goods_filter_by_nm_list(self, *, nm_list):
        self.drift_calls.append(list(nm_list))
        goods = self.drift_goods.pop(0) if self.drift_goods else [
            self._good(nm_id, price=1000) for nm_id in nm_list
        ]
        return {"data": {"listGoods": goods}}

    def upload_discount_task(self, *, data):
        self.upload_payloads.append(data)
        if self.upload_error:
            raise self.upload_error
        if self.upload_responses:
            response = self.upload_responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response
        return {"data": {"uploadID": f"upload-{len(self.upload_payloads)}"}}

    def history_tasks(self, *, upload_id):
        self.history_calls.append(upload_id)
        status = self.statuses.pop(0) if self.statuses else 3
        return {"data": {"tasks": [{"uploadID": upload_id, "status": status}]}}

    def buffer_tasks(self, *, upload_id):
        self.buffer_calls.append(upload_id)
        return {"data": {"tasks": [{"uploadID": upload_id, "status": 2}]}}

    def history_goods_task(self, *, upload_id):
        return {"data": {"goods": self.details.pop(0) if self.details else []}}

    def buffer_goods_task(self, *, upload_id):
        return {"data": {"goods": []}}

    def quarantine_goods(self, *, nm_list):
        return {"data": {"goods": self.quarantines.pop(0) if self.quarantines else []}}

    @staticmethod
    def _good(nm_id, *, price):
        return {
            "nmID": int(nm_id),
            "vendorCode": f"v-{nm_id}",
            "sizes": [
                {"sizeID": 1, "price": price, "discountedPrice": price, "techSizeName": "0"},
                {"sizeID": 2, "price": price, "discountedPrice": price, "techSizeName": "1"},
            ],
            "currencyIsoCode4217": "RUB",
            "discount": 10,
            "editableSizePrice": False,
            "isBadTurnover": False,
        }


class FakeClientFactory:
    def __init__(self, client_kwargs=None):
        self.client_kwargs = client_kwargs or {}
        self.client = None

    def __call__(self, *, token, store_scope):
        self.client = FakeUploadClient(token=token, store_scope=store_scope, **self.client_kwargs)
        return self.client


class WBApiUploadTask015Tests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_root = tempfile.mkdtemp(prefix="promo-v2-wb-api-upload-")
        cls.override = override_settings(MEDIA_ROOT=cls._media_root)
        cls.override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.override.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        seed_identity_access()
        User = get_user_model()
        self.user = User.objects.create_user(
            login=f"owner-{self._testMethodName}",
            password="password",
            display_name="Owner",
            primary_role=Role.objects.get(code=ROLE_OWNER),
        )
        self.store = StoreAccount.objects.create(
            name=f"WB Upload Store {self._testMethodName}",
            marketplace=StoreAccount.Marketplace.WB,
        )
        StoreAccess.objects.create(
            user=self.user,
            store=self.store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        self.connection = ConnectionBlock.objects.create(
            store=self.store,
            module=WB_API_MODULE,
            connection_type=WB_API_CONNECTION_TYPE,
            status=ConnectionBlock.Status.ACTIVE,
            protected_secret_ref="env://TASK015_WB_TOKEN",
            metadata={"label": "safe"},
            is_stage2_1_used=True,
        )

    @staticmethod
    def _secret_resolver(protected_secret_ref):
        assert protected_secret_ref == "env://TASK015_WB_TOKEN"
        return "Bearer task015-local-token-value"

    def _result_file(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Цены"
        sheet.append(["Артикул WB", "Текущая цена", "Новая скидка"])
        sheet.append(["101", "9999", "88"])
        buffer = BytesIO()
        workbook.save(buffer)
        workbook.close()
        return create_file_version(
            store=self.store,
            uploaded_by=self.user,
            uploaded_file=ContentFile(buffer.getvalue(), name="wb-api-result.xlsx"),
            scenario=FileObject.Scenario.WB_DISCOUNTS_API_RESULT_EXCEL,
            kind=FileObject.Kind.OUTPUT,
            logical_name="wb_api_result",
            module="wb_api",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def _calculation(self, rows=None, *, status=ProcessStatus.COMPLETED_SUCCESS, error_count=0):
        rows = rows or [("101", 1000, 30)]
        operation = create_api_operation(
            marketplace=Marketplace.WB,
            store=self.store,
            initiator_user=self.user,
            step_code=OperationStepCode.WB_API_DISCOUNT_CALCULATION,
            logic_version="calc-test",
            execution_context={"step_code": OperationStepCode.WB_API_DISCOUNT_CALCULATION},
        )
        operation = start_operation(operation)
        for index, (nm_id, price, discount) in enumerate(rows, start=2):
            OperationDetailRow.objects.create(
                operation=operation,
                row_no=index,
                product_ref=str(nm_id),
                row_status="ok",
                reason_code="wb_api_calculated_from_api_sources",
                message_level=MessageLevel.INFO,
                message="calculated",
                final_value={
                    "current_price": str(price),
                    "final_discount": discount,
                    "upload_ready": True,
                    "excel_price_must_not_be_used": "9999",
                },
            )
        return complete_api_operation(
            operation,
            result=ApiOperationResult(
                summary={"result_code": "wb_api_calculated_from_api_sources"},
                status=status,
                error_count=error_count,
                output_file_version=self._result_file(),
                output_kind=OutputKind.OUTPUT_WORKBOOK,
            ),
        )

    def test_confirmation_permissions_and_successful_calculation_are_required(self):
        calculation = self._calculation()
        with self.assertRaises(ValidationError):
            upload_wb_api_discounts(
                actor=self.user,
                store=self.store,
                calculation_operation=calculation,
                confirmation_phrase="wrong",
                client_factory=FakeClientFactory(),
                secret_resolver=self._secret_resolver,
            )
        self.assertFalse(Operation.objects.filter(step_code=OperationStepCode.WB_API_DISCOUNT_UPLOAD).exists())

        outsider = get_user_model().objects.create_user(
            login=f"outsider-{self._testMethodName}",
            password="password",
            display_name="Outsider",
            primary_role=Role.objects.get(code=ROLE_MARKETPLACE_MANAGER),
        )
        with self.assertRaises(PermissionDenied):
            upload_wb_api_discounts(
                actor=outsider,
                store=self.store,
                calculation_operation=calculation,
                confirmation_phrase=CONFIRMATION_PHRASE,
                client_factory=FakeClientFactory(),
                secret_resolver=self._secret_resolver,
            )

        failed_calc = self._calculation(rows=[("102", 1000, 30)], status=ProcessStatus.COMPLETED_WITH_ERROR, error_count=1)
        with self.assertRaises(ValidationError):
            upload_wb_api_discounts(
                actor=self.user,
                store=self.store,
                calculation_operation=failed_calc,
                confirmation_phrase=CONFIRMATION_PHRASE,
                client_factory=FakeClientFactory(),
                secret_resolver=self._secret_resolver,
            )

    def test_drift_check_blocks_upload_before_post(self):
        calculation = self._calculation()
        factory = FakeClientFactory(
            {
                "drift_goods": [[FakeUploadClient._good("101", price=1001)]],
            }
        )

        operation = upload_wb_api_discounts(
            actor=self.user,
            store=self.store,
            calculation_operation=calculation,
            confirmation_phrase=CONFIRMATION_PHRASE,
            client_factory=factory,
            secret_resolver=self._secret_resolver,
        )

        self.assertEqual(operation.status, ProcessStatus.COMPLETED_WITH_ERROR)
        self.assertEqual(operation.summary["result_code"], "wb_api_upload_blocked_by_drift")
        self.assertEqual(factory.client.upload_payloads, [])
        self.assertEqual(
            operation.detail_rows.get(product_ref="101").reason_code,
            "wb_api_upload_blocked_by_drift",
        )

    def test_normal_payload_has_only_nmid_discount_and_never_uses_excel_or_old_price(self):
        calculation = self._calculation()
        factory = FakeClientFactory()

        operation = upload_wb_api_discounts(
            actor=self.user,
            store=self.store,
            calculation_operation=calculation,
            confirmation_phrase=CONFIRMATION_PHRASE,
            client_factory=factory,
            secret_resolver=self._secret_resolver,
        )

        self.assertEqual(operation.status, ProcessStatus.COMPLETED_SUCCESS)
        self.assertEqual(factory.client.upload_payloads, [[{"nmID": 101, "discount": 30}]])
        self.assertNotIn("price", factory.client.upload_payloads[0][0])
        combined = str({"summary": operation.summary, "payloads": factory.client.upload_payloads})
        self.assertNotIn("9999", combined)
        self.assertNotIn("current_price", combined)
        self.assertTrue(factory.client.history_calls)

    def test_discount_only_rejection_stops_safely_without_fallback_price(self):
        calculation = self._calculation()
        factory = FakeClientFactory({"upload_error": WBApiInvalidResponseError("discount-only rejected")})

        operation = upload_wb_api_discounts(
            actor=self.user,
            store=self.store,
            calculation_operation=calculation,
            confirmation_phrase=CONFIRMATION_PHRASE,
            client_factory=factory,
            secret_resolver=self._secret_resolver,
        )

        self.assertEqual(operation.status, ProcessStatus.INTERRUPTED_FAILED)
        self.assertEqual(factory.client.upload_payloads, [[{"nmID": 101, "discount": 30}]])
        self.assertEqual(len(factory.client.upload_payloads), 1)
        self.assertNotIn("price", str(factory.client.upload_payloads))
        self.assertTrue(TechLogRecord.objects.filter(operation=operation, event_type="wb_api_response_invalid").exists())

    def test_batching_status_mapping_partial_quarantine_and_208(self):
        rows = [(str(100000 + index), 1000, 20) for index in range(UPLOAD_BATCH_SIZE + 1)]
        calculation = self._calculation(rows=rows)
        first_goods = [FakeUploadClient._good(nm_id, price=1000) for nm_id, _price, _discount in rows[:UPLOAD_BATCH_SIZE]]
        second_goods = [FakeUploadClient._good(rows[-1][0], price=1000)]
        factory = FakeClientFactory(
            {
                "drift_goods": [first_goods, second_goods],
                "upload_responses": [
                    {"data": {"uploadID": "u-1"}},
                    WBApiAlreadyExistsError(response={"data": {"uploadID": "u-2"}}),
                ],
                "statuses": [3, 5],
                "details": [[], [{"nmID": int(rows[-1][0]), "errorText": "safe partial error"}]],
                "quarantines": [[], [{"nmID": int(rows[-1][0]), "reason": "quarantine"}]],
            }
        )

        operation = upload_wb_api_discounts(
            actor=self.user,
            store=self.store,
            calculation_operation=calculation,
            confirmation_phrase=CONFIRMATION_PHRASE,
            client_factory=factory,
            secret_resolver=self._secret_resolver,
        )

        self.assertEqual(operation.status, ProcessStatus.COMPLETED_WITH_WARNINGS)
        self.assertEqual(len(factory.client.upload_payloads), 2)
        self.assertLessEqual(len(factory.client.upload_payloads[0]), UPLOAD_BATCH_SIZE)
        self.assertEqual([batch["uploadID"] for batch in operation.summary["batches"]], ["u-1", "u-2"])
        self.assertTrue(
            operation.detail_rows.filter(reason_code="wb_api_upload_quarantine", product_ref=rows[-1][0]).exists()
        )
        self.assertTrue(TechLogRecord.objects.filter(operation=operation, event_type="wb_api_upload_partial_errors").exists())
        self.assertTrue(TechLogRecord.objects.filter(operation=operation, event_type="wb_api_quarantine_detected").exists())

    def test_mixed_status_3_quarantine_does_not_leak_to_success_rows(self):
        calculation = self._calculation(rows=[("501", 1000, 20), ("502", 1000, 20)])
        factory = FakeClientFactory(
            {
                "statuses": [3],
                "quarantines": [[{"nmID": 502, "reason": "quarantine"}]],
            }
        )

        operation = upload_wb_api_discounts(
            actor=self.user,
            store=self.store,
            calculation_operation=calculation,
            confirmation_phrase=CONFIRMATION_PHRASE,
            client_factory=factory,
            secret_resolver=self._secret_resolver,
        )

        success_row = operation.detail_rows.get(product_ref="501")
        quarantine_row = operation.detail_rows.get(product_ref="502")
        self.assertEqual(success_row.row_status, "ok")
        self.assertEqual(success_row.reason_code, "wb_api_upload_success")
        self.assertEqual(quarantine_row.row_status, "warning")
        self.assertEqual(quarantine_row.reason_code, "wb_api_upload_quarantine")
        self.assertEqual(operation.summary["batches"][0]["result_code"], "wb_api_upload_quarantine")

    def test_mixed_status_5_partial_and_quarantine_keep_row_level_codes(self):
        calculation = self._calculation(rows=[("601", 1000, 20), ("602", 1000, 20), ("603", 1000, 20)])
        factory = FakeClientFactory(
            {
                "statuses": [5],
                "details": [[{"nmID": 601, "errorText": "safe partial error"}]],
                "quarantines": [[{"nmID": 602, "reason": "quarantine"}]],
            }
        )

        operation = upload_wb_api_discounts(
            actor=self.user,
            store=self.store,
            calculation_operation=calculation,
            confirmation_phrase=CONFIRMATION_PHRASE,
            client_factory=factory,
            secret_resolver=self._secret_resolver,
        )

        partial_row = operation.detail_rows.get(product_ref="601")
        quarantine_row = operation.detail_rows.get(product_ref="602")
        success_row = operation.detail_rows.get(product_ref="603")
        self.assertEqual(partial_row.row_status, "warning")
        self.assertEqual(partial_row.reason_code, "wb_api_upload_partial_error")
        self.assertEqual(quarantine_row.row_status, "warning")
        self.assertEqual(quarantine_row.reason_code, "wb_api_upload_quarantine")
        self.assertEqual(success_row.row_status, "ok")
        self.assertEqual(success_row.reason_code, "wb_api_upload_success")

    def test_wb_status_4_and_6_map_to_completed_with_error(self):
        for status in (4, 6):
            with self.subTest(status=status):
                calculation = self._calculation(rows=[(f"90{status}", 1000, 20)])
                factory = FakeClientFactory({"statuses": [status]})

                operation = upload_wb_api_discounts(
                    actor=self.user,
                    store=self.store,
                    calculation_operation=calculation,
                    confirmation_phrase=CONFIRMATION_PHRASE,
                    client_factory=factory,
                    secret_resolver=self._secret_resolver,
                )

                self.assertEqual(operation.status, ProcessStatus.COMPLETED_WITH_ERROR)

    def test_operation_classifier_and_secret_redaction(self):
        calculation = self._calculation(rows=[("301", 1000, 20)])
        operation = upload_wb_api_discounts(
            actor=self.user,
            store=self.store,
            calculation_operation=calculation,
            confirmation_phrase=CONFIRMATION_PHRASE,
            client_factory=FakeClientFactory(),
            secret_resolver=self._secret_resolver,
        )

        self.assertEqual(operation.marketplace, Marketplace.WB)
        self.assertEqual(operation.mode, OperationMode.API)
        self.assertEqual(operation.step_code, OperationStepCode.WB_API_DISCOUNT_UPLOAD)
        self.assertEqual(operation.operation_type, OperationType.NOT_APPLICABLE)
        combined = str(
            {
                "operation": Operation.objects.filter(pk=operation.pk).values("execution_context", "summary").get(),
                "audit": list(
                    AuditRecord.objects.filter(operation=operation).values(
                        "safe_message",
                        "after_snapshot",
                    )
                ),
                "techlog": list(TechLogRecord.objects.filter(operation=operation).values("safe_message", "sensitive_details_ref")),
            }
        )
        self.assertFalse(contains_secret_like(combined))
        self.assertNotIn("task015-local-token-value", combined)

    def test_goods_error_text_is_redacted_before_detail_summary_report_audit_and_techlog(self):
        calculation = self._calculation(rows=[("701", 1000, 20)])
        leaked_secret = "wb-leaked-token-value-1234567890"
        factory = FakeClientFactory(
            {
                "statuses": [5],
                "details": [
                    [
                        {
                            "nmID": 701,
                            "errorText": f"WB rejected Authorization: Bearer {leaked_secret}",
                            "error": f"token={leaked_secret}",
                        }
                    ]
                ],
            }
        )

        operation = upload_wb_api_discounts(
            actor=self.user,
            store=self.store,
            calculation_operation=calculation,
            confirmation_phrase=CONFIRMATION_PHRASE,
            client_factory=factory,
            secret_resolver=self._secret_resolver,
        )

        detail = operation.detail_rows.get(product_ref="701")
        report_version = operation.output_files.get(output_kind=OutputKind.DETAIL_REPORT).file_version
        with default_storage.open(report_version.storage_path, "rb") as report_file:
            report_text = report_file.read().decode("utf-8")
        combined = str(
            {
                "details": list(
                    OperationDetailRow.objects.filter(operation=operation).values(
                        "final_value",
                        "reason_code",
                        "row_status",
                    )
                ),
                "summary": Operation.objects.filter(pk=operation.pk).values("summary").get(),
                "report": report_text,
                "audit": list(
                    AuditRecord.objects.filter(operation=operation).values(
                        "safe_message",
                        "after_snapshot",
                    )
                ),
                "techlog": list(
                    TechLogRecord.objects.filter(operation=operation).values(
                        "safe_message",
                        "sensitive_details_ref",
                    )
                ),
            }
        )

        self.assertEqual(detail.reason_code, "wb_api_upload_partial_error")
        self.assertEqual(detail.final_value["errorText_safe"], "[redacted]")
        self.assertFalse(contains_secret_like(combined))
        self.assertNotIn(leaked_secret, combined)
        self.assertNotIn("Authorization: Bearer", combined)
