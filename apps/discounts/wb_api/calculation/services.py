"""Use case for TASK-014 WB API discount calculation and result Excel."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditActionCode, AuditSourceContext
from apps.audit.services import create_audit_record
from apps.discounts.wb_api.promotions.models import WBPromotionExportFile, WBPromotionSnapshot
from apps.discounts.wb_api.redaction import assert_no_secret_like_values
from apps.discounts.wb_excel import services as wb_excel_services
from apps.files.models import FileObject, FileVersion
from apps.identity_access.services import has_permission
from apps.operations.models import (
    AppliedParameterSnapshot,
    LaunchMethod,
    Marketplace,
    Operation,
    OperationDetailRow,
    OperationInputFile,
    OperationMode,
    OperationModule,
    OperationOutputFile,
    OperationStepCode,
    OperationType,
    OutputKind,
    ProcessStatus,
    RunStatus,
)
from apps.operations.listing_enrichment import enrich_detail_row_marketplace_listing
from apps.operations.services import (
    ApiOperationResult,
    ParameterSnapshotSpec,
    complete_api_operation,
    create_api_operation,
    start_operation,
)
from apps.stores.models import StoreAccount
from apps.stores.services import require_wb_store_for_wb_api
from apps.techlog.models import TechLogSeverity
from apps.techlog.services import create_techlog_record


LOGIC_VERSION = "wb-api-discount-calculation-v1"
PRICE_INPUT_ROLE = "api_price_export"
PROMOTION_INPUT_ROLE = "api_promotion_export"
RESULT_LOGICAL_NAME = "wb_api_discount_result.xlsx"
SUCCESSFUL_SOURCE_STATUSES = (
    ProcessStatus.COMPLETED_SUCCESS,
    ProcessStatus.COMPLETED_WITH_WARNINGS,
)


def _latest_price_export_operation(store: StoreAccount) -> Operation | None:
    return (
        Operation.objects.filter(
            marketplace=Marketplace.WB,
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.WB_API_PRICES_DOWNLOAD,
            store=store,
            status__in=SUCCESSFUL_SOURCE_STATUSES,
            output_files__file_version__file__scenario=FileObject.Scenario.WB_DISCOUNTS_API_PRICE_EXPORT,
        )
        .order_by("-finished_at", "-id")
        .first()
    )


def _latest_promotion_export_operation(store: StoreAccount) -> Operation | None:
    return (
        Operation.objects.filter(
            marketplace=Marketplace.WB,
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.WB_API_PROMOTIONS_DOWNLOAD,
            store=store,
            status__in=SUCCESSFUL_SOURCE_STATUSES,
            wb_promotion_snapshot__isnull=False,
        )
        .order_by("-finished_at", "-id")
        .first()
    )


def _output_file(operation: Operation, *, scenario: str) -> FileVersion:
    link = (
        OperationOutputFile.objects.select_related("file_version", "file_version__file")
        .filter(operation=operation, file_version__file__scenario=scenario)
        .order_by("file_version_id")
        .first()
    )
    if link is None:
        raise ValidationError("Selected WB API source operation has no required output file.")
    return link.file_version


def _promotion_file_versions(operation: Operation) -> list[FileVersion]:
    return [
        export_file.file_version
        for export_file in WBPromotionExportFile.objects.select_related("file_version", "file_version__file")
        .filter(operation=operation)
        .order_by("promotion__wb_promotion_id", "id")
    ]


def _operation_checksum(operation: Operation, file_version: FileVersion | None = None) -> dict:
    safe_snapshot = operation.summary.get("safe_snapshot", {}) if isinstance(operation.summary, dict) else {}
    checksum = safe_snapshot.get("source_checksum") if isinstance(safe_snapshot, dict) else None
    payload = {
        "operation_id": operation.pk,
        "operation_visible_id": operation.visible_id,
        "finished_at": operation.finished_at.isoformat() if operation.finished_at else "",
        "summary_source_checksum": checksum,
    }
    if file_version is not None:
        payload.update(
            {
                "file_version_id": file_version.pk,
                "file_checksum_sha256": file_version.checksum_sha256,
            },
        )
    return payload


def _basis_payload(
    *,
    price_operation: Operation,
    price_file: FileVersion,
    promo_operation: Operation,
    promo_files: list[FileVersion],
    promotion_snapshot: WBPromotionSnapshot,
    parameters: wb_excel_services.WbParameters,
) -> dict:
    payload = {
        "store_id": price_operation.store_id,
        "price_basis": _operation_checksum(price_operation, price_file),
        "promotion_basis": {
            **_operation_checksum(promo_operation),
            "wb_promotion_snapshot_id": promotion_snapshot.pk,
            "current_filter_timestamp": promotion_snapshot.current_filter_timestamp.isoformat(),
            "safe_snapshot_checksum": (
                promotion_snapshot.raw_response_safe_snapshot.get("source_checksum")
                if isinstance(promotion_snapshot.raw_response_safe_snapshot, dict)
                else None
            ),
            "promotion_file_versions": [
                {
                    "file_version_id": file_version.pk,
                    "checksum_sha256": file_version.checksum_sha256,
                }
                for file_version in promo_files
            ],
        },
        "parameters": {
            snapshot.code: {
                "value": wb_excel_services.decimal_to_json(snapshot.value),
                "source": snapshot.source,
                "parameter_version": snapshot.parameter_version,
                "effective_at": snapshot.effective_at.isoformat() if snapshot.effective_at else "",
            }
            for snapshot in parameters.snapshots
        },
        "calculation_logic_version": LOGIC_VERSION,
        "stage1_logic_version": wb_excel_services.LOGIC_VERSION,
    }
    assert_no_secret_like_values(payload, field_name="WB API calculation basis")
    return payload


def _parameter_specs(parameters: wb_excel_services.WbParameters) -> list[ParameterSnapshotSpec]:
    return wb_excel_services.build_parameter_specs(parameters)


def _attach_operation_inputs(operation: Operation, *, price_file: FileVersion, promo_files: list[FileVersion]) -> None:
    OperationInputFile.objects.create(
        operation=operation,
        file_version=price_file,
        role_in_operation=PRICE_INPUT_ROLE,
        ordinal_no=1,
    )
    for index, file_version in enumerate(promo_files, start=1):
        OperationInputFile.objects.create(
            operation=operation,
            file_version=file_version,
            role_in_operation=PROMOTION_INPUT_ROLE,
            ordinal_no=index,
        )


def _attach_parameter_snapshots(
    operation: Operation,
    specs: list[ParameterSnapshotSpec],
) -> None:
    for spec in specs:
        AppliedParameterSnapshot.objects.create(
            operation=operation,
            parameter_code=spec.parameter_code,
            applied_value=spec.applied_value,
            source=spec.source,
            parameter_version=spec.parameter_version,
            effective_at=spec.effective_at,
        )


def _persist_api_details(operation: Operation, result: wb_excel_services.CalculationResult) -> None:
    for detail in result.details:
        reason_code = detail.reason_code
        final_value = detail.final_value_payload() or {}
        if detail.row_status == "ok":
            final_value = {
                **final_value,
                "source_stage1_reason_code": detail.reason_code,
                "upload_ready": True,
            }
            reason_code = "wb_api_calculated_from_api_sources"
        elif detail.reason_code == "wb_discount_out_of_range":
            final_value = {
                **final_value,
                "source_stage1_reason_code": detail.reason_code,
                "upload_ready": False,
            }
        detail_row = OperationDetailRow.objects.create(
            operation=operation,
            row_no=detail.row_no,
            product_ref=detail.article,
            row_status=detail.row_status,
            reason_code=reason_code,
            message_level=detail.message_level,
            message=detail.message,
            problem_field=detail.problem_field,
            final_value=final_value or None,
        )
        enrich_detail_row_marketplace_listing(detail_row)


def _record_failure(operation: Operation, actor, store, exc: Exception) -> None:
    safe_message = getattr(exc, "safe_message", "WB API discount calculation failed.")
    create_techlog_record(
        severity=TechLogSeverity.ERROR,
        event_type="operation.execution_failed",
        source_component="apps.discounts.wb_api.calculation",
        operation=operation,
        store=store,
        user=actor,
        entity_type="Operation",
        entity_id=operation.pk,
        safe_message=safe_message,
        sensitive_details_ref="redacted:wb-api-discount-calculation",
    )


def _source_operations(
    *,
    store: StoreAccount,
    price_operation: Operation | None,
    promotion_operation: Operation | None,
) -> tuple[Operation, Operation]:
    price_operation = price_operation or _latest_price_export_operation(store)
    promotion_operation = promotion_operation or _latest_promotion_export_operation(store)
    if price_operation is None:
        raise ValidationError("Successful WB API price export is required for discount calculation.")
    if promotion_operation is None:
        raise ValidationError("Successful WB API current promotions export is required for discount calculation.")
    if price_operation.store_id != store.pk or promotion_operation.store_id != store.pk:
        raise ValidationError("WB API price and promotion basis must belong to the same store.")
    if (
        price_operation.step_code != OperationStepCode.WB_API_PRICES_DOWNLOAD
        or price_operation.status not in SUCCESSFUL_SOURCE_STATUSES
    ):
        raise ValidationError("Selected price basis is not a successful WB API price export.")
    if (
        promotion_operation.step_code != OperationStepCode.WB_API_PROMOTIONS_DOWNLOAD
        or promotion_operation.status not in SUCCESSFUL_SOURCE_STATUSES
    ):
        raise ValidationError("Selected promotion basis is not a successful WB API promotions export.")
    return price_operation, promotion_operation


@transaction.atomic
def calculate_wb_api_discounts(
    *,
    actor,
    store: StoreAccount,
    price_operation: Operation | None = None,
    promotion_operation: Operation | None = None,
    enforce_permissions: bool = True,
) -> Operation:
    if enforce_permissions and not has_permission(actor, "wb.api.discounts.calculate", store):
        raise PermissionDenied("No permission or object access for WB API discount calculation.")
    require_wb_store_for_wb_api(store)
    price_operation, promotion_operation = _source_operations(
        store=store,
        price_operation=price_operation,
        promotion_operation=promotion_operation,
    )
    price_file = _output_file(
        price_operation,
        scenario=FileObject.Scenario.WB_DISCOUNTS_API_PRICE_EXPORT,
    )
    promo_files = _promotion_file_versions(promotion_operation)
    if not promo_files:
        raise ValidationError("WB API current promotions export has no regular promotion Excel files.")
    promotion_snapshot = promotion_operation.wb_promotion_snapshot
    parameters = wb_excel_services.resolve_wb_parameters(store)
    basis = _basis_payload(
        price_operation=price_operation,
        price_file=price_file,
        promo_operation=promotion_operation,
        promo_files=promo_files,
        promotion_snapshot=promotion_snapshot,
        parameters=parameters,
    )

    operation = create_api_operation(
        marketplace=Marketplace.WB,
        store=store,
        initiator_user=actor,
        step_code=OperationStepCode.WB_API_DISCOUNT_CALCULATION,
        logic_version=LOGIC_VERSION,
        module=OperationModule.WB_API,
        execution_context={
            "mode": OperationMode.API,
            "step_code": OperationStepCode.WB_API_DISCOUNT_CALCULATION,
            "basis": basis,
        },
        launch_method=LaunchMethod.MANUAL,
        enforce_permissions=False,
    )
    _attach_operation_inputs(operation, price_file=price_file, promo_files=promo_files)
    _attach_parameter_snapshots(operation, _parameter_specs(parameters))
    create_audit_record(
        action_code=AuditActionCode.WB_API_DISCOUNT_CALCULATION_STARTED,
        entity_type="Operation",
        entity_id=operation.pk,
        user=actor,
        store=store,
        operation=operation,
        safe_message="WB API discount calculation started.",
        after_snapshot={
            "mode": OperationMode.API,
            "marketplace": Marketplace.WB,
            "step_code": OperationStepCode.WB_API_DISCOUNT_CALCULATION,
            "basis": basis,
        },
        source_context=AuditSourceContext.SERVICE,
    )
    operation = start_operation(operation)
    try:
        result = wb_excel_services.calculate(price_file, promo_files, parameters)
        _persist_api_details(operation, result)
        summary = {
            **result.summary,
            "result_code": "wb_api_calculated_from_api_sources",
            "basis": basis,
            "output_created": False,
            "upload_blocked": bool(result.error_count),
        }
        output_file = None
        if not result.error_count:
            output_file = wb_excel_services._write_output_workbook(
                price_version=price_file,
                final_discounts_by_row=result.final_discounts_by_row,
                store=store,
                user=actor,
                operation_ref=operation.visible_id,
                run_ref=operation.run.visible_id,
                scenario=FileObject.Scenario.WB_DISCOUNTS_API_RESULT_EXCEL,
                module=OperationModule.WB_API,
                logical_name=RESULT_LOGICAL_NAME,
            )
            summary["output_created"] = True
            summary["output_file_version_id"] = output_file.pk
        assert_no_secret_like_values(summary, field_name="WB API calculation summary")
        completed = complete_api_operation(
            operation,
            result=ApiOperationResult(
                summary=summary,
                status=(
                    ProcessStatus.COMPLETED_WITH_ERROR
                    if result.error_count
                    else ProcessStatus.COMPLETED_WITH_WARNINGS
                    if result.warning_count
                    else ProcessStatus.COMPLETED_SUCCESS
                ),
                error_count=result.error_count,
                warning_count=result.warning_count,
                output_file_version=output_file,
                output_kind=OutputKind.OUTPUT_WORKBOOK,
            ),
        )
        create_audit_record(
            action_code=AuditActionCode.WB_API_DISCOUNT_CALCULATION_COMPLETED,
            entity_type="Operation",
            entity_id=completed.pk,
            user=actor,
            store=store,
            operation=completed,
            safe_message="WB API discount calculation completed.",
            after_snapshot={
                "status": completed.status,
                "output_file_version_id": output_file.pk if output_file else None,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
            },
            source_context=AuditSourceContext.SERVICE,
        )
        return completed
    except Exception as exc:
        _record_failure(operation, actor, store, exc)
        operation.status = ProcessStatus.INTERRUPTED_FAILED
        operation.summary = {
            "result_code": "wb_api_calculated_from_api_sources",
            "failure": "WB API discount calculation failed.",
            "basis": basis,
        }
        operation.finished_at = timezone.now()
        operation.save(update_fields=["status", "summary", "finished_at", "updated_at"])
        operation.run.status = RunStatus.INTERRUPTED_FAILED
        operation.run.save(update_fields=["status", "updated_at"])
        raise
