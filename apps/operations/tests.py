from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from apps.files.models import FileObject, FileVersion
from apps.identity_access.models import (
    AccessEffect,
    Permission,
    StoreAccess,
    User,
    UserPermissionOverride,
)
from apps.identity_access.seeds import seed_identity_access
from apps.stores.models import StoreAccount

from .models import (
    CheckStatus,
    MessageLevel,
    OZON_REASON_CODES,
    Operation,
    OperationDetailRow,
    OperationType,
    ProcessStatus,
    RunStatus,
    WarningConfirmation,
)
from .services import (
    InputFileSpec,
    ParameterSnapshotSpec,
    ShellExecutionResult,
    complete_check_operation,
    complete_process_operation,
    create_check_operation,
    create_process_operation,
    find_actual_successful_check,
    press_process_sync,
    run_check_sync,
    start_operation,
)


class OperationsShellTests(TestCase):
    def setUp(self):
        seed_identity_access()
        self.user = User.objects.create_user(
            login="manager",
            password="pass",
            display_name="Marketplace manager",
        )
        self.store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
        )
        self.file_version = self._create_file_version("a" * 64)
        self.input_specs = [
            InputFileSpec(
                file_version=self.file_version,
                role_in_operation="prices_workbook",
                ordinal_no=1,
            )
        ]
        self.parameters = [
            ParameterSnapshotSpec(
                parameter_code="wb_threshold_percent",
                applied_value=70,
                source="system",
                parameter_version="defaults-v1",
            )
        ]

    def _create_file_version(self, checksum, *, kind=FileObject.Kind.INPUT):
        file_object = FileObject.objects.create(
            store=self.store,
            kind=kind,
            scenario=FileObject.Scenario.WB_DISCOUNTS_EXCEL,
            marketplace=FileObject.Marketplace.WB,
            module="discounts_excel",
            logical_name="prices" if kind == FileObject.Kind.INPUT else "output",
            original_name="prices.xlsx" if kind == FileObject.Kind.INPUT else "output.xlsx",
            created_by=self.user,
        )
        return FileVersion.objects.create(
            file=file_object,
            version_no=1,
            original_name=file_object.original_name,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            storage_path=f"test/{checksum}.xlsx",
            size=10,
            checksum_sha256=checksum,
            uploaded_by=self.user,
            retention_until=timezone.now() + timedelta(days=3),
        )

    def _create_completed_check(self, *, errors=0, warnings=0):
        operation = create_check_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=self.input_specs,
            parameters=self.parameters,
            logic_version="logic-v1",
        )
        return complete_check_operation(
            operation,
            result=ShellExecutionResult(
                summary={"rows": 1},
                error_count=errors,
                warning_count=warnings,
            ),
        )

    def _grant_permission(self, user, permission_code):
        UserPermissionOverride.objects.create(
            user=user,
            permission=Permission.objects.get(code=permission_code),
            effect=AccessEffect.ALLOW,
            store=self.store,
        )

    def test_create_check_operation_visible_ids_file_links_and_snapshots(self):
        operation = create_check_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=self.input_specs,
            parameters=self.parameters,
            logic_version="logic-v1",
        )

        self.assertRegex(operation.visible_id, r"^OP-\d{4}-\d{6}$")
        self.assertRegex(operation.run.visible_id, r"^RUN-\d{4}-\d{6}$")
        self.assertEqual(operation.operation_type, OperationType.CHECK)
        self.assertEqual(operation.status, CheckStatus.CREATED)
        self.assertEqual(operation.input_files.count(), 1)
        self.assertEqual(operation.parameter_snapshots.count(), 1)

        self.file_version.refresh_from_db()
        self.assertEqual(self.file_version.operation_ref, operation.visible_id)
        self.assertEqual(self.file_version.run_ref, operation.run.visible_id)

    def test_actual_check_allows_process_and_metadata_changes_require_new_check(self):
        check = self._create_completed_check()

        actual = find_actual_successful_check(
            marketplace="wb",
            module="discounts_excel",
            mode="excel",
            store=self.store,
            input_files=self.input_specs,
            parameters=self.parameters,
            logic_version="logic-v1",
        )
        self.assertEqual(actual, check)

        process = create_process_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=self.input_specs,
            parameters=self.parameters,
            logic_version="logic-v1",
            check_basis_operation=check,
        )
        self.assertEqual(process.operation_type, OperationType.PROCESS)
        self.assertEqual(process.status, ProcessStatus.CREATED)
        self.assertEqual(process.check_basis_operation, check)

        changed_parameters = [
            ParameterSnapshotSpec(
                parameter_code="wb_threshold_percent",
                applied_value=71,
                source="system",
                parameter_version="defaults-v2",
            )
        ]
        self.assertIsNone(
            find_actual_successful_check(
                marketplace="wb",
                module="discounts_excel",
                mode="excel",
                store=self.store,
                input_files=self.input_specs,
                parameters=changed_parameters,
                logic_version="logic-v1",
            )
        )
        with self.assertRaises(ValidationError):
            create_process_operation(
                marketplace="wb",
                store=self.store,
                initiator_user=self.user,
                input_files=self.input_specs,
                parameters=changed_parameters,
                logic_version="logic-v1",
                check_basis_operation=check,
            )

    def test_process_with_warning_basis_requires_confirmation_fact(self):
        check = self._create_completed_check(warnings=1)

        with self.assertRaises(ValidationError):
            create_process_operation(
                marketplace="wb",
                store=self.store,
                initiator_user=self.user,
                input_files=self.input_specs,
                parameters=self.parameters,
                logic_version="logic-v1",
                check_basis_operation=check,
            )

        process = create_process_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=self.input_specs,
            parameters=self.parameters,
            logic_version="logic-v1",
            check_basis_operation=check,
            confirmed_warning_codes=["threshold_warning"],
        )

        confirmation = WarningConfirmation.objects.get(process_operation=process)
        self.assertEqual(confirmation.check_operation, check)
        self.assertEqual(confirmation.warning_codes, ["threshold_warning"])

    def test_check_with_errors_cannot_be_process_basis(self):
        check = self._create_completed_check(errors=1)

        with self.assertRaises(ValidationError):
            create_process_operation(
                marketplace="wb",
                store=self.store,
                initiator_user=self.user,
                input_files=self.input_specs,
                parameters=self.parameters,
                logic_version="logic-v1",
                check_basis_operation=check,
            )

    def test_terminal_operation_and_related_records_are_immutable(self):
        operation = create_check_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=self.input_specs,
            parameters=self.parameters,
            logic_version="logic-v1",
        )
        OperationDetailRow.objects.create(
            operation=operation,
            row_no=1,
            row_status="valid",
            reason_code="wb_valid_calculated",
            message_level=MessageLevel.INFO,
            message="",
        )
        operation = complete_check_operation(
            operation,
            result=ShellExecutionResult(summary={"rows": 1}),
        )

        operation.summary = {"changed": True}
        with self.assertRaises(ValidationError):
            operation.save(update_fields=["summary", "updated_at"])
        with self.assertRaises(ValidationError):
            type(operation).objects.filter(pk=operation.pk).update(summary={"changed": True})
        with self.assertRaises(ValidationError):
            OperationDetailRow.objects.filter(operation=operation).update(message="changed")
        with self.assertRaises(ProtectedError):
            operation.delete()
        with self.assertRaises(ValidationError):
            OperationDetailRow.objects.create(
                operation=operation,
                row_no=2,
                row_status="valid",
                reason_code="wb_valid_calculated",
                message_level=MessageLevel.INFO,
                message="",
            )

    def test_interrupted_failed_is_terminal_and_does_not_auto_resume(self):
        operation = create_check_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=self.input_specs,
            parameters=self.parameters,
            logic_version="logic-v1",
        )

        def failing_executor(_operation):
            raise RuntimeError("executor failed")

        with self.assertRaises(RuntimeError):
            run_check_sync(operation, failing_executor)

        operation.refresh_from_db()
        operation.run.refresh_from_db()
        self.assertEqual(operation.status, CheckStatus.INTERRUPTED_FAILED)
        self.assertEqual(operation.run.status, RunStatus.INTERRUPTED_FAILED)

        with self.assertRaises(ValidationError):
            start_operation(operation)

    def test_press_process_without_actual_check_creates_check_then_process(self):
        calls = []

        def check_executor(operation):
            calls.append(("check", operation.operation_type, operation.status))
            return ShellExecutionResult(summary={"checked": True})

        def process_executor(operation):
            calls.append(("process", operation.operation_type, operation.status))
            return ShellExecutionResult(summary={"processed": True})

        result = press_process_sync(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=self.input_specs,
            parameters=self.parameters,
            logic_version="logic-v1",
            check_executor=check_executor,
            process_executor=process_executor,
        )

        self.assertTrue(result.check_was_created)
        self.assertNotEqual(result.check_operation, result.process_operation)
        self.assertEqual(result.check_operation.operation_type, OperationType.CHECK)
        self.assertEqual(result.process_operation.operation_type, OperationType.PROCESS)
        self.assertEqual(result.check_operation.status, CheckStatus.COMPLETED_NO_ERRORS)
        self.assertEqual(result.process_operation.status, ProcessStatus.COMPLETED_SUCCESS)
        self.assertEqual(result.process_operation.check_basis_operation, result.check_operation)
        self.assertEqual(
            calls,
            [
                ("check", OperationType.CHECK, CheckStatus.RUNNING),
                ("process", OperationType.PROCESS, ProcessStatus.RUNNING),
            ],
        )

    def test_press_process_reuses_existing_actual_check(self):
        check = self._create_completed_check()
        calls = []

        def check_executor(_operation):
            raise AssertionError("Existing actual check should be reused.")

        def process_executor(operation):
            calls.append(operation.pk)
            return ShellExecutionResult(summary={"processed": True})

        result = press_process_sync(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=self.input_specs,
            parameters=self.parameters,
            logic_version="logic-v1",
            check_executor=check_executor,
            process_executor=process_executor,
        )

        self.assertFalse(result.check_was_created)
        self.assertEqual(result.check_operation, check)
        self.assertEqual(result.process_operation.check_basis_operation, check)
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            Operation.objects.filter(operation_type=OperationType.CHECK).count(),
            1,
        )

    def test_press_process_does_not_create_process_when_auto_check_has_errors(self):
        def check_executor(_operation):
            return ShellExecutionResult(summary={"checked": True}, error_count=1)

        def process_executor(_operation):
            raise AssertionError("Process executor must not be called after check errors.")

        with self.assertRaises(ValidationError):
            press_process_sync(
                marketplace="wb",
                store=self.store,
                initiator_user=self.user,
                input_files=self.input_specs,
                parameters=self.parameters,
                logic_version="logic-v1",
                check_executor=check_executor,
                process_executor=process_executor,
            )

        self.assertEqual(
            Operation.objects.filter(operation_type=OperationType.CHECK).count(),
            1,
        )
        self.assertFalse(Operation.objects.filter(operation_type=OperationType.PROCESS).exists())

    def test_confirm_warnings_permission_required_when_enforced(self):
        restricted_user = User.objects.create_user(
            login="restricted",
            password="pass",
            display_name="Restricted",
        )
        StoreAccess.objects.create(
            user=restricted_user,
            store=self.store,
            access_level=StoreAccess.AccessLevel.WORK,
        )
        self._grant_permission(restricted_user, "wb_discounts_excel.run_process")
        check = self._create_completed_check(warnings=1)

        with self.assertRaises(PermissionDenied):
            create_process_operation(
                marketplace="wb",
                store=self.store,
                initiator_user=restricted_user,
                input_files=self.input_specs,
                parameters=self.parameters,
                logic_version="logic-v1",
                check_basis_operation=check,
                confirmed_warning_codes=["threshold_warning"],
                enforce_permissions=True,
            )

    def test_warning_confirmation_is_immutable_after_creation(self):
        check = self._create_completed_check(warnings=1)
        process = create_process_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=self.input_specs,
            parameters=self.parameters,
            logic_version="logic-v1",
            check_basis_operation=check,
            confirmed_warning_codes=["threshold_warning"],
        )

        confirmation = WarningConfirmation.objects.get(process_operation=process)
        confirmation.warning_codes = ["changed"]
        with self.assertRaises(ValidationError):
            confirmation.save(update_fields=["warning_codes"])

    def test_output_file_version_cannot_be_reused_across_process_operations(self):
        check = self._create_completed_check()
        first_process = create_process_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=self.input_specs,
            parameters=self.parameters,
            logic_version="logic-v1",
            check_basis_operation=check,
        )
        second_process = create_process_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=self.input_specs,
            parameters=self.parameters,
            logic_version="logic-v1",
            check_basis_operation=check,
        )
        output_version = self._create_file_version("b" * 64, kind=FileObject.Kind.OUTPUT)

        complete_process_operation(
            first_process,
            result=ShellExecutionResult(
                summary={"processed": True},
                output_file_version=output_version,
            ),
        )

        with self.assertRaises(ValidationError):
            complete_process_operation(
                second_process,
                result=ShellExecutionResult(
                    summary={"processed": True},
                    output_file_version=output_version,
                ),
            )

    def test_explicit_check_basis_mode_mismatch_is_rejected(self):
        check = self._create_completed_check()

        with self.assertRaises(ValidationError):
            create_process_operation(
                marketplace="wb",
                store=self.store,
                initiator_user=self.user,
                input_files=self.input_specs,
                parameters=self.parameters,
                logic_version="logic-v1",
                check_basis_operation=check,
                mode="api",
            )

    def test_invalid_status_bulk_update_is_rejected(self):
        operation = create_check_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=self.input_specs,
            parameters=self.parameters,
            logic_version="logic-v1",
        )

        with self.assertRaises(ValidationError):
            Operation.objects.filter(pk=operation.pk).update(status="not_a_status")
        with self.assertRaises(ValidationError):
            Operation.objects.filter(pk=operation.pk).update(status=ProcessStatus.COMPLETED_SUCCESS)

    def test_ozon_detail_reason_codes_are_centrally_validated(self):
        ozon_store = StoreAccount.objects.create(
            name="Ozon Store",
            marketplace=StoreAccount.Marketplace.OZON,
        )
        operation = create_check_operation(
            marketplace="ozon",
            store=ozon_store,
            initiator_user=self.user,
            input_files=[],
            parameters=[],
            logic_version="ozon_discounts_excel_v1",
        )

        self.assertEqual(
            OZON_REASON_CODES,
            {
                "missing_min_price",
                "no_stock",
                "no_boost_prices",
                "use_max_boost_price",
                "use_min_price",
                "below_min_price_threshold",
                "insufficient_ozon_input_data",
            },
        )
        for row_no, reason_code in enumerate(sorted(OZON_REASON_CODES), start=1):
            OperationDetailRow.objects.create(
                operation=operation,
                row_no=row_no,
                row_status="ok",
                reason_code=reason_code,
                message_level=MessageLevel.INFO,
                message="",
            )

        with self.assertRaises(ValidationError):
            OperationDetailRow.objects.create(
                operation=operation,
                row_no=99,
                row_status="ok",
                reason_code="unapproved_ozon_code",
                message_level=MessageLevel.INFO,
                message="",
            )

    def test_wb_detail_reason_code_validation_still_rejects_unknown_wb_prefix(self):
        operation = create_check_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=[],
            parameters=[],
            logic_version="logic-v1",
        )

        with self.assertRaises(ValidationError):
            OperationDetailRow.objects.create(
                operation=operation,
                row_no=1,
                row_status="ok",
                reason_code="wb_unknown_code",
                message_level=MessageLevel.INFO,
                message="",
            )
