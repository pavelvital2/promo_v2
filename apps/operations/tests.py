from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from apps.audit.models import AuditActionCode, AuditRecord
from apps.files.models import FileObject, FileVersion
from apps.identity_access.models import (
    AccessEffect,
    Permission,
    StoreAccess,
    User,
    UserPermissionOverride,
)
from apps.identity_access.seeds import seed_identity_access
from apps.product_core.models import ListingSource, MarketplaceListing
from apps.stores.models import StoreAccount
from apps.techlog.models import TechLogEventType, TechLogRecord, TechLogSeverity

from .models import (
    CheckStatus,
    MessageLevel,
    OZON_REASON_CODES,
    Operation,
    OperationDetailRow,
    OperationModule,
    OperationStepCode,
    OperationType,
    ProcessStatus,
    RunStatus,
    WarningConfirmation,
    allow_operation_detail_listing_fk_enrichment_update,
)
from .listing_enrichment import (
    CONFLICT_API_DATA_INTEGRITY_DUPLICATE,
    CONFLICT_MULTIPLE_LISTING_MATCHES,
    CONFLICT_NO_LISTING_MATCH,
    CONFLICT_ROW_NOT_PRODUCT_IDENTIFIER,
    backfill_operation_detail_listing_fk,
    enrich_detail_row_marketplace_listing,
    operation_detail_product_ref_checksum,
    resolve_listing_for_detail_row,
)
from .services import (
    InputFileSpec,
    ParameterSnapshotSpec,
    ShellExecutionResult,
    complete_check_operation,
    create_api_operation,
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
                "ozon_api_action_not_elastic",
                "ozon_api_action_not_found",
                "ozon_api_missing_elastic_fields",
                "ozon_api_missing_product_info",
                "ozon_api_missing_stock_info",
                "ozon_api_product_not_eligible",
                "ozon_api_upload_blocked_by_drift",
                "ozon_api_upload_blocked_deactivate_unconfirmed",
                "ozon_api_upload_ready",
                "ozon_api_upload_rejected",
                "ozon_api_upload_partial_rejected",
                "ozon_api_upload_success",
                "ozon_api_deactivate_required",
                "ozon_api_deactivate_group_confirmed",
                "ozon_api_auth_failed",
                "ozon_api_response_invalid",
                "ozon_api_rate_limited",
                "ozon_api_timeout",
                "ozon_api_secret_redaction_violation",
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

    def test_detail_row_marketplace_listing_fk_is_nullable_and_preserves_product_ref(self):
        operation = create_check_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=[],
            parameters=[],
            logic_version="logic-v1",
        )
        row = OperationDetailRow.objects.create(
            operation=operation,
            row_no=1,
            product_ref="RAW-ARTICLE-001",
            row_status="ok",
            reason_code="wb_valid_calculated",
            message_level=MessageLevel.INFO,
            message="",
        )

        self.assertIsNone(row.marketplace_listing_id)

        listing = MarketplaceListing.objects.create(
            marketplace="wb",
            store=self.store,
            external_primary_id="nm-fk-1",
            seller_article="RAW-ARTICLE-001",
            last_source=ListingSource.MIGRATION,
        )
        row.marketplace_listing = listing
        row.save(update_fields=["marketplace_listing"])
        row.refresh_from_db()

        self.assertEqual(row.marketplace_listing, listing)
        self.assertEqual(row.product_ref, "RAW-ARTICLE-001")

    def test_detail_row_marketplace_listing_fk_requires_same_store_and_marketplace(self):
        operation = create_check_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=[],
            parameters=[],
            logic_version="logic-v1",
        )
        ozon_store = StoreAccount.objects.create(
            name="Ozon Store For Listing FK",
            marketplace=StoreAccount.Marketplace.OZON,
        )
        listing = MarketplaceListing.objects.create(
            marketplace="ozon",
            store=ozon_store,
            external_primary_id="ozon-fk-1",
            last_source=ListingSource.MIGRATION,
        )

        with self.assertRaises(ValidationError):
            OperationDetailRow.objects.create(
                operation=operation,
                marketplace_listing=listing,
                row_no=1,
                product_ref="RAW-ARTICLE-001",
                row_status="ok",
                reason_code="wb_valid_calculated",
                message_level=MessageLevel.INFO,
                message="",
            )

    def test_detail_row_marketplace_listing_fk_protects_listing(self):
        operation = create_check_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=[],
            parameters=[],
            logic_version="logic-v1",
        )
        listing = MarketplaceListing.objects.create(
            marketplace="wb",
            store=self.store,
            external_primary_id="nm-protect-1",
            last_source=ListingSource.MIGRATION,
        )
        OperationDetailRow.objects.create(
            operation=operation,
            marketplace_listing=listing,
            row_no=1,
            product_ref="RAW-ARTICLE-001",
            row_status="ok",
            reason_code="wb_valid_calculated",
            message_level=MessageLevel.INFO,
            message="",
        )

        with self.assertRaises(ProtectedError):
            listing.delete()

    def _listing(self, *, store=None, marketplace="wb", external_primary_id="listing-1", **kwargs):
        return MarketplaceListing.objects.create(
            marketplace=marketplace,
            store=store or self.store,
            external_primary_id=external_primary_id,
            last_source=ListingSource.MIGRATION,
            **kwargs,
        )

    def _detail_row(self, *, operation=None, product_ref="SKU-1", reason_code="wb_valid_calculated", **kwargs):
        operation = operation or create_check_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=[],
            parameters=[],
            logic_version="logic-v1",
        )
        return OperationDetailRow.objects.create(
            operation=operation,
            row_no=kwargs.pop("row_no", 1),
            product_ref=product_ref,
            row_status=kwargs.pop("row_status", "ok"),
            reason_code=reason_code,
            message_level=kwargs.pop("message_level", MessageLevel.INFO),
            message=kwargs.pop("message", ""),
            **kwargs,
        )

    def _api_operation(self, *, marketplace="wb", store=None, step_code=None, module=None):
        store = store or self.store
        if step_code is None:
            step_code = OperationStepCode.WB_API_PRICES_DOWNLOAD
        if module is None:
            module = OperationModule.WB_API if marketplace == "wb" else OperationModule.OZON_API
        return create_api_operation(
            marketplace=marketplace,
            store=store,
            initiator_user=self.user,
            step_code=step_code,
            logic_version="logic-v1",
            module=module,
        )

    def test_listing_resolver_matches_external_primary_id_and_seller_article_in_same_scope(self):
        primary_listing = self._listing(external_primary_id=" 1001 ")
        primary_row = self._detail_row(product_ref="1001")
        self.assertEqual(resolve_listing_for_detail_row(primary_row).listing, primary_listing)

        article_listing = self._listing(
            external_primary_id="1002",
            seller_article="SELLER-ARTICLE-1",
        )
        article_row = self._detail_row(product_ref=" SELLER-ARTICLE-1 ", row_no=2)
        self.assertEqual(resolve_listing_for_detail_row(article_row).listing, article_listing)
        article_row.refresh_from_db()
        self.assertEqual(article_row.product_ref, " SELLER-ARTICLE-1 ")

    def test_listing_resolver_matches_wb_and_ozon_external_ids(self):
        wb_nm = self._listing(external_primary_id="wb-1", external_ids={"nmID": "501"})
        wb_vendor = self._listing(external_primary_id="wb-2", external_ids={"vendorCode": "vendor-501"})
        self.assertEqual(resolve_listing_for_detail_row(self._detail_row(product_ref="501")).listing, wb_nm)
        self.assertEqual(
            resolve_listing_for_detail_row(self._detail_row(product_ref="vendor-501", row_no=2)).listing,
            wb_vendor,
        )

        ozon_store = StoreAccount.objects.create(
            name="Ozon Store For Enrichment",
            marketplace=StoreAccount.Marketplace.OZON,
        )
        ozon_operation = self._api_operation(
            marketplace="ozon",
            store=ozon_store,
            step_code=OperationStepCode.OZON_API_ELASTIC_PRODUCT_DATA_DOWNLOAD,
        )
        ozon_product = self._listing(
            store=ozon_store,
            marketplace="ozon",
            external_primary_id="ozon-1",
            external_ids={"product_id": "7001"},
        )
        ozon_offer = self._listing(
            store=ozon_store,
            marketplace="ozon",
            external_primary_id="ozon-2",
            external_ids={"offer_id": "offer-7001"},
        )
        self.assertEqual(
            resolve_listing_for_detail_row(
                self._detail_row(operation=ozon_operation, product_ref="7001", reason_code="", row_no=1)
            ).listing,
            ozon_product,
        )
        self.assertEqual(
            resolve_listing_for_detail_row(
                self._detail_row(operation=ozon_operation, product_ref="offer-7001", reason_code="", row_no=2)
            ).listing,
            ozon_offer,
        )

    def test_listing_resolver_rejects_cross_scope_duplicate_blank_summary_and_fuzzy_matches(self):
        other_store = StoreAccount.objects.create(
            name="Other WB Store For Enrichment",
            marketplace=StoreAccount.Marketplace.WB,
        )
        self._listing(store=other_store, external_primary_id="CROSS-STORE")
        self.assertEqual(
            resolve_listing_for_detail_row(self._detail_row(product_ref="CROSS-STORE")).conflict_class,
            CONFLICT_NO_LISTING_MATCH,
        )

        self._listing(external_primary_id="dup-1", seller_article="DUP-ARTICLE")
        self._listing(external_primary_id="dup-2", seller_article="DUP-ARTICLE")
        duplicate = resolve_listing_for_detail_row(self._detail_row(product_ref="DUP-ARTICLE", row_no=2))
        self.assertEqual(duplicate.conflict_class, CONFLICT_API_DATA_INTEGRITY_DUPLICATE)

        self.assertEqual(
            resolve_listing_for_detail_row(self._detail_row(product_ref="   ", row_no=3)).conflict_class,
            CONFLICT_ROW_NOT_PRODUCT_IDENTIFIER,
        )

        promotion_operation = self._api_operation(step_code=OperationStepCode.WB_API_PROMOTIONS_DOWNLOAD)
        summary_row = self._detail_row(
            operation=promotion_operation,
            product_ref="12345",
            reason_code="wb_api_promotion_regular",
            row_no=1,
        )
        self.assertEqual(
            resolve_listing_for_detail_row(summary_row).conflict_class,
            CONFLICT_ROW_NOT_PRODUCT_IDENTIFIER,
        )

        self._listing(
            external_primary_id="Case-Sensitive-Article",
            seller_article="Partial Article",
            barcode="BARCODE-ONLY",
            title="Exact Title Match",
        )
        self.assertEqual(
            resolve_listing_for_detail_row(self._detail_row(product_ref="case-sensitive-article", row_no=4)).conflict_class,
            CONFLICT_NO_LISTING_MATCH,
        )
        self.assertEqual(
            resolve_listing_for_detail_row(self._detail_row(product_ref="Partial", row_no=5)).conflict_class,
            CONFLICT_NO_LISTING_MATCH,
        )
        self.assertEqual(
            resolve_listing_for_detail_row(self._detail_row(product_ref="BARCODE-ONLY", row_no=6)).conflict_class,
            CONFLICT_NO_LISTING_MATCH,
        )
        self.assertEqual(
            resolve_listing_for_detail_row(self._detail_row(product_ref="Exact Title Match", row_no=7)).conflict_class,
            CONFLICT_NO_LISTING_MATCH,
        )

    def test_terminal_operation_guard_allows_only_listing_fk_update(self):
        operation = create_check_operation(
            marketplace="wb",
            store=self.store,
            initiator_user=self.user,
            input_files=[],
            parameters=[],
            logic_version="logic-v1",
        )
        row = self._detail_row(operation=operation, product_ref="GUARD-ARTICLE")
        operation = complete_check_operation(operation, result=ShellExecutionResult(summary={"rows": 1}))
        listing = self._listing(external_primary_id="guard-listing", seller_article="GUARD-ARTICLE")

        with allow_operation_detail_listing_fk_enrichment_update():
            OperationDetailRow.objects.filter(pk=row.pk).update(marketplace_listing_id=listing.pk)
        row.refresh_from_db()
        self.assertEqual(row.marketplace_listing_id, listing.pk)
        self.assertEqual(row.product_ref, "GUARD-ARTICLE")

        blocked_updates = [
            {"product_ref": "changed"},
            {"row_status": "changed"},
            {"reason_code": "wb_missing_article"},
            {"message": "changed"},
            {"problem_field": "changed"},
            {"final_value": {"changed": True}},
            {"created_at": timezone.now()},
        ]
        for update_kwargs in blocked_updates:
            with self.subTest(update_kwargs=update_kwargs):
                with self.assertRaises(ValidationError):
                    with allow_operation_detail_listing_fk_enrichment_update():
                        OperationDetailRow.objects.filter(pk=row.pk).update(**update_kwargs)

        operation.summary = {"changed": True}
        with self.assertRaises(ValidationError):
            operation.save(update_fields=["summary"])

    def test_listing_fk_enrichment_writes_safe_audit_and_conflict_techlog(self):
        listing = self._listing(external_primary_id="audit-listing", seller_article="AUDIT-ARTICLE")
        row = self._detail_row(product_ref="AUDIT-ARTICLE")

        result = enrich_detail_row_marketplace_listing(row, dry_run=False)
        row.refresh_from_db()

        self.assertEqual(result.listing, listing)
        self.assertEqual(row.marketplace_listing_id, listing.pk)
        audit = AuditRecord.objects.get(
            action_code=AuditActionCode.OPERATION_DETAIL_ROW_LISTING_FK_ENRICHED,
            entity_id=str(row.pk),
        )
        self.assertEqual(audit.operation, row.operation)
        self.assertEqual(audit.store, self.store)
        self.assertEqual(audit.after_snapshot["listing_id"], listing.pk)
        self.assertEqual(audit.after_snapshot["matched_key_class"], "seller_article")
        self.assertNotIn("AUDIT-ARTICLE", str(audit.after_snapshot))

        missing_row = self._detail_row(product_ref="NO-LISTING-MATCH", row_no=2)
        enrich_detail_row_marketplace_listing(missing_row, dry_run=False)
        techlog = TechLogRecord.objects.get(
            event_type=TechLogEventType.OPERATION_DETAIL_ROW_ENRICHMENT_ERROR,
            entity_id=str(missing_row.pk),
        )
        self.assertEqual(techlog.severity, TechLogSeverity.WARNING)
        self.assertNotIn("NO-LISTING-MATCH", techlog.safe_message)

    def test_existing_different_fk_is_not_overwritten(self):
        existing = self._listing(external_primary_id="existing", seller_article="EXISTING")
        target = self._listing(external_primary_id="target", seller_article="TARGET")
        row = self._detail_row(product_ref="TARGET", marketplace_listing=existing)

        result = resolve_listing_for_detail_row(row)
        self.assertEqual(result.conflict_class, CONFLICT_MULTIPLE_LISTING_MATCHES)
        backfill_operation_detail_listing_fk(dry_run=False, limit=10)
        row.refresh_from_db()
        self.assertEqual(row.marketplace_listing_id, existing.pk)
        self.assertNotEqual(row.marketplace_listing_id, target.pk)

    def test_backfill_command_dry_run_write_idempotency_and_checksum_stability(self):
        listing = self._listing(external_primary_id="backfill-listing", seller_article="BACKFILL-ARTICLE")
        row = self._detail_row(product_ref="BACKFILL-ARTICLE")
        ozon_store = StoreAccount.objects.create(
            name="Ozon Excel Backfill Store",
            marketplace=StoreAccount.Marketplace.OZON,
        )
        ozon_listing = self._listing(
            store=ozon_store,
            marketplace="ozon",
            external_primary_id="OZON-BACKFILL-1",
            external_ids={"product_id": "OZON-BACKFILL-1", "offer_id": "OFFER-BACKFILL-1"},
        )
        ozon_operation = create_check_operation(
            marketplace="ozon",
            store=ozon_store,
            initiator_user=self.user,
            input_files=[],
            parameters=[],
            logic_version="logic-v1",
        )
        ozon_row = self._detail_row(
            operation=ozon_operation,
            product_ref="OFFER-BACKFILL-1",
            reason_code="use_max_boost_price",
            row_no=2,
        )
        before_count, before_checksum = operation_detail_product_ref_checksum()

        dry_run = backfill_operation_detail_listing_fk(dry_run=True, limit=10)
        row.refresh_from_db()
        self.assertIsNone(row.marketplace_listing_id)
        self.assertEqual(dry_run.row_count_before, before_count)
        self.assertEqual(dry_run.checksum_before, before_checksum)
        self.assertEqual(dry_run.checksum_after, before_checksum)

        out = StringIO()
        call_command("backfill_operation_detail_listing_fk", "--write", "--limit", "10", stdout=out)
        row.refresh_from_db()
        ozon_row.refresh_from_db()
        self.assertEqual(row.marketplace_listing_id, listing.pk)
        self.assertEqual(ozon_row.marketplace_listing_id, ozon_listing.pk)
        after_count, after_checksum = operation_detail_product_ref_checksum()
        self.assertEqual(after_count, before_count)
        self.assertEqual(after_checksum, before_checksum)
        self.assertIn('"changed_product_ref_count": 0', out.getvalue())

        second = backfill_operation_detail_listing_fk(dry_run=False, limit=10)
        row.refresh_from_db()
        self.assertEqual(row.marketplace_listing_id, listing.pk)
        self.assertGreaterEqual(second.idempotent_count, 1)
        self.assertEqual(second.checksum_after, before_checksum)
