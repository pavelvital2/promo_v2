"""Service layer for operation/run creation and execution shell."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Iterable

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.files.models import FileVersion
from apps.identity_access.services import has_permission

from .models import (
    AppliedParameterSnapshot,
    CheckResult,
    CheckStatus,
    LaunchMethod,
    MessageLevel,
    Operation,
    OperationInputFile,
    OperationMode,
    OperationModule,
    OperationOutputFile,
    OperationType,
    OutputKind,
    ProcessResult,
    ProcessStatus,
    Run,
    RunStatus,
    SUCCESSFUL_CHECK_STATUSES,
    WarningConfirmation,
)


SCENARIO_BY_CONTEXT = {
    ("wb", OperationModule.DISCOUNTS_EXCEL, OperationMode.EXCEL): "wb_discounts_excel",
    ("ozon", OperationModule.DISCOUNTS_EXCEL, OperationMode.EXCEL): "ozon_discounts_excel",
}


@dataclass(frozen=True)
class InputFileSpec:
    file_version: FileVersion
    role_in_operation: str
    ordinal_no: int = 1


@dataclass(frozen=True)
class ParameterSnapshotSpec:
    parameter_code: str
    applied_value: object
    source: str
    parameter_version: str = ""
    effective_at: object | None = None


@dataclass(frozen=True)
class ShellExecutionResult:
    summary: dict
    error_count: int = 0
    warning_count: int = 0
    output_file_version: FileVersion | None = None


@dataclass(frozen=True)
class PressProcessResult:
    check_operation: Operation
    process_operation: Operation
    check_was_created: bool


def scenario_code(*, marketplace: str, module: str, mode: str) -> str:
    try:
        return SCENARIO_BY_CONTEXT[(marketplace, module, mode)]
    except KeyError as exc:
        raise ValidationError("Unsupported operation scenario.") from exc


def assert_can_run_operation(user, *, marketplace: str, module: str, mode: str, action: str, store) -> None:
    scenario = scenario_code(marketplace=marketplace, module=module, mode=mode)
    if not has_permission(user, f"{scenario}.{action}", store):
        raise PermissionDenied("No permission or object access for this operation.")


def _normalize_input_specs(input_files: Iterable[InputFileSpec | dict]) -> list[InputFileSpec]:
    normalized = []
    for item in input_files:
        if isinstance(item, InputFileSpec):
            normalized.append(item)
            continue
        normalized.append(
            InputFileSpec(
                file_version=item["file_version"],
                role_in_operation=item.get("role_in_operation", "input"),
                ordinal_no=item.get("ordinal_no", 1),
            )
        )
    return normalized


def _normalize_parameter_specs(
    parameters: Iterable[ParameterSnapshotSpec | dict],
) -> list[ParameterSnapshotSpec]:
    normalized = []
    for item in parameters:
        if isinstance(item, ParameterSnapshotSpec):
            normalized.append(item)
            continue
        normalized.append(
            ParameterSnapshotSpec(
                parameter_code=item["parameter_code"],
                applied_value=item["applied_value"],
                source=item["source"],
                parameter_version=item.get("parameter_version", ""),
                effective_at=item.get("effective_at"),
            )
        )
    return normalized


def _input_metadata_from_specs(input_files: Iterable[InputFileSpec | dict]) -> tuple[tuple, ...]:
    specs = _normalize_input_specs(input_files)
    return tuple(
        sorted(
            (
                spec.role_in_operation,
                spec.ordinal_no,
                spec.file_version.pk,
            )
            for spec in specs
        )
    )


def _stable_value(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _parameter_metadata_from_specs(parameters: Iterable[ParameterSnapshotSpec | dict]) -> tuple[tuple, ...]:
    specs = _normalize_parameter_specs(parameters)
    return tuple(
        sorted(
            (
                spec.parameter_code,
                _stable_value(spec.applied_value),
                spec.source,
                spec.parameter_version,
                spec.effective_at.isoformat() if spec.effective_at else "",
            )
            for spec in specs
        )
    )


def operation_actuality_metadata(operation: Operation) -> dict:
    """Return the documented shell-level metadata used to match check basis."""

    input_files = tuple(
        operation.input_files.order_by("role_in_operation", "ordinal_no", "file_version_id").values_list(
            "role_in_operation",
            "ordinal_no",
            "file_version_id",
        )
    )
    parameters = tuple(
        (
            snapshot.parameter_code,
            _stable_value(snapshot.applied_value),
            snapshot.source,
            snapshot.parameter_version,
            snapshot.effective_at.isoformat() if snapshot.effective_at else "",
        )
        for snapshot in operation.parameter_snapshots.order_by("parameter_code", "id")
    )
    return {
        "marketplace": operation.marketplace,
        "module": operation.module,
        "mode": operation.mode,
        "store_id": operation.store_id,
        "input_files": input_files,
        "parameters": parameters,
        "logic_version": operation.logic_version,
    }


def requested_actuality_metadata(
    *,
    marketplace: str,
    store,
    module: str = OperationModule.DISCOUNTS_EXCEL,
    mode: str = OperationMode.EXCEL,
    input_files: Iterable[InputFileSpec | dict],
    parameters: Iterable[ParameterSnapshotSpec | dict],
    logic_version: str,
) -> dict:
    return {
        "marketplace": marketplace,
        "module": module,
        "mode": mode,
        "store_id": store.pk,
        "input_files": _input_metadata_from_specs(input_files),
        "parameters": _parameter_metadata_from_specs(parameters),
        "logic_version": logic_version,
    }


def is_check_actual_for_request(
    check_operation: Operation,
    *,
    marketplace: str,
    store,
    module: str = OperationModule.DISCOUNTS_EXCEL,
    mode: str = OperationMode.EXCEL,
    input_files: Iterable[InputFileSpec | dict],
    parameters: Iterable[ParameterSnapshotSpec | dict],
    logic_version: str,
) -> bool:
    if not check_operation.is_successful_check:
        return False
    return operation_actuality_metadata(check_operation) == requested_actuality_metadata(
        marketplace=marketplace,
        module=module,
        mode=mode,
        store=store,
        input_files=input_files,
        parameters=parameters,
        logic_version=logic_version,
    )


def find_actual_successful_check(
    *,
    marketplace: str,
    module: str,
    mode: str,
    store,
    input_files: Iterable[InputFileSpec | dict],
    parameters: Iterable[ParameterSnapshotSpec | dict],
    logic_version: str,
) -> Operation | None:
    candidates = (
        Operation.objects.filter(
            marketplace=marketplace,
            module=module,
            mode=mode,
            store=store,
            operation_type=OperationType.CHECK,
            status__in=SUCCESSFUL_CHECK_STATUSES,
            error_count=0,
            logic_version=logic_version,
        )
        .prefetch_related("input_files", "parameter_snapshots")
        .order_by("-created_at", "-id")
    )
    for candidate in candidates:
        if is_check_actual_for_request(
            candidate,
            marketplace=marketplace,
            module=module,
            mode=mode,
            store=store,
            input_files=input_files,
            parameters=parameters,
            logic_version=logic_version,
        ):
            return candidate
    return None


@transaction.atomic
def create_run(
    *,
    marketplace: str,
    store,
    initiated_by,
    module: str = OperationModule.DISCOUNTS_EXCEL,
    mode: str = OperationMode.EXCEL,
    execution_context: dict | None = None,
    launch_method: str = LaunchMethod.MANUAL,
) -> Run:
    return Run.objects.create(
        marketplace=marketplace,
        module=module,
        mode=mode,
        store=store,
        initiated_by=initiated_by,
        execution_context=execution_context or {},
        launch_method=launch_method,
    )


def _attach_inputs(operation: Operation, input_files: Iterable[InputFileSpec | dict]) -> None:
    for spec in _normalize_input_specs(input_files):
        OperationInputFile.objects.create(
            operation=operation,
            file_version=spec.file_version,
            role_in_operation=spec.role_in_operation,
            ordinal_no=spec.ordinal_no,
        )


def _attach_parameters(operation: Operation, parameters: Iterable[ParameterSnapshotSpec | dict]) -> None:
    for spec in _normalize_parameter_specs(parameters):
        AppliedParameterSnapshot.objects.create(
            operation=operation,
            parameter_code=spec.parameter_code,
            applied_value=spec.applied_value,
            source=spec.source,
            parameter_version=spec.parameter_version,
            effective_at=spec.effective_at,
        )


def check_requires_warning_confirmation(check_operation: Operation) -> bool:
    if not check_operation.warning_count:
        return False
    warning_rows = check_operation.detail_rows.filter(
        message_level__in=[
            MessageLevel.WARNING_CONFIRMABLE,
            MessageLevel.WARNING_INFO,
        ],
    )
    if not warning_rows.exists():
        return True
    return warning_rows.filter(message_level=MessageLevel.WARNING_CONFIRMABLE).exists()


def _validate_output_file_version_is_new(output_file_version: FileVersion | None) -> None:
    if output_file_version is None:
        return
    if OperationOutputFile.objects.filter(file_version=output_file_version).exists():
        raise ValidationError("Output file version is already linked to an operation output.")
    if ProcessResult.objects.filter(output_file_version=output_file_version).exists():
        raise ValidationError("Output file version is already used by another process result.")


@transaction.atomic
def create_check_operation(
    *,
    marketplace: str,
    store,
    initiator_user,
    input_files: Iterable[InputFileSpec | dict],
    parameters: Iterable[ParameterSnapshotSpec | dict],
    logic_version: str,
    run: Run | None = None,
    module: str = OperationModule.DISCOUNTS_EXCEL,
    mode: str = OperationMode.EXCEL,
    execution_context: dict | None = None,
    launch_method: str = LaunchMethod.MANUAL,
    enforce_permissions: bool = False,
) -> Operation:
    if enforce_permissions:
        assert_can_run_operation(
            initiator_user,
            marketplace=marketplace,
            module=module,
            mode=mode,
            action="run_check",
            store=store,
        )
    run = run or create_run(
        marketplace=marketplace,
        module=module,
        mode=mode,
        store=store,
        initiated_by=initiator_user,
        execution_context=execution_context,
        launch_method=launch_method,
    )
    operation = Operation.objects.create(
        marketplace=marketplace,
        module=module,
        mode=mode,
        operation_type=OperationType.CHECK,
        status=CheckStatus.CREATED,
        run=run,
        store=store,
        initiator_user=initiator_user,
        execution_context=execution_context or run.execution_context,
        launch_method=launch_method,
        logic_version=logic_version,
    )
    _attach_inputs(operation, input_files)
    _attach_parameters(operation, parameters)
    return operation


@transaction.atomic
def create_process_operation(
    *,
    marketplace: str,
    store,
    initiator_user,
    input_files: Iterable[InputFileSpec | dict],
    parameters: Iterable[ParameterSnapshotSpec | dict],
    logic_version: str,
    check_basis_operation: Operation,
    run: Run | None = None,
    module: str = OperationModule.DISCOUNTS_EXCEL,
    mode: str = OperationMode.EXCEL,
    execution_context: dict | None = None,
    launch_method: str = LaunchMethod.MANUAL,
    confirmed_warning_codes: list[str] | None = None,
    enforce_permissions: bool = False,
) -> Operation:
    if enforce_permissions:
        assert_can_run_operation(
            initiator_user,
            marketplace=marketplace,
            module=module,
            mode=mode,
            action="run_process",
            store=store,
        )
    if not is_check_actual_for_request(
        check_basis_operation,
        marketplace=marketplace,
        module=module,
        mode=mode,
        store=store,
        input_files=input_files,
        parameters=parameters,
        logic_version=logic_version,
    ):
        raise ValidationError("Check basis is not actual for requested process.")
    if check_requires_warning_confirmation(check_basis_operation) and confirmed_warning_codes is None:
        raise ValidationError("Process requires explicit warning confirmation.")
    if enforce_permissions and confirmed_warning_codes is not None:
        assert_can_run_operation(
            initiator_user,
            marketplace=marketplace,
            module=module,
            mode=mode,
            action="confirm_warnings",
            store=store,
        )

    run = run or check_basis_operation.run
    operation = Operation.objects.create(
        marketplace=marketplace,
        module=module,
        mode=mode,
        operation_type=OperationType.PROCESS,
        status=ProcessStatus.CREATED,
        run=run,
        store=store,
        initiator_user=initiator_user,
        execution_context=execution_context or run.execution_context,
        launch_method=launch_method,
        logic_version=logic_version,
        check_basis_operation=check_basis_operation,
    )
    _attach_inputs(operation, input_files)
    _attach_parameters(operation, parameters)
    if confirmed_warning_codes is not None:
        WarningConfirmation.objects.create(
            check_operation=check_basis_operation,
            process_operation=operation,
            user=initiator_user,
            warning_codes=confirmed_warning_codes,
        )
    return operation


@transaction.atomic
def start_operation(operation: Operation) -> Operation:
    operation = Operation.objects.select_for_update().get(pk=operation.pk)
    if operation.operation_type == OperationType.CHECK:
        running_status = CheckStatus.RUNNING
    else:
        running_status = ProcessStatus.RUNNING
    operation.status = running_status
    operation.started_at = timezone.now()
    operation.save(update_fields=["status", "started_at", "updated_at"])
    Run.objects.filter(pk=operation.run_id).update(status=RunStatus.RUNNING)
    operation.run.refresh_from_db()
    return operation


@transaction.atomic
def complete_check_operation(
    operation: Operation,
    *,
    result: ShellExecutionResult,
) -> Operation:
    operation = Operation.objects.select_for_update().get(pk=operation.pk)
    if operation.operation_type != OperationType.CHECK:
        raise ValidationError("Only check operations can be completed as check.")
    operation.summary = result.summary
    operation.error_count = result.error_count
    operation.warning_count = result.warning_count
    CheckResult.objects.create(
        operation=operation,
        summary=result.summary,
        error_count=result.error_count,
        warning_count=result.warning_count,
    )
    if result.error_count:
        operation.status = CheckStatus.COMPLETED_WITH_ERRORS
    elif result.warning_count:
        operation.status = CheckStatus.COMPLETED_WITH_WARNINGS
    else:
        operation.status = CheckStatus.COMPLETED_NO_ERRORS
    operation.finished_at = timezone.now()
    operation.save(
        update_fields=[
            "summary",
            "error_count",
            "warning_count",
            "status",
            "finished_at",
            "updated_at",
        ]
    )
    _close_run_if_all_operations_terminal(operation.run)
    return operation


@transaction.atomic
def complete_process_operation(
    operation: Operation,
    *,
    result: ShellExecutionResult,
) -> Operation:
    operation = Operation.objects.select_for_update().get(pk=operation.pk)
    if operation.operation_type != OperationType.PROCESS:
        raise ValidationError("Only process operations can be completed as process.")
    _validate_output_file_version_is_new(result.output_file_version)
    operation.summary = result.summary
    operation.error_count = result.error_count
    operation.warning_count = result.warning_count
    ProcessResult.objects.create(
        operation=operation,
        output_file_version=result.output_file_version,
        summary=result.summary,
    )
    if result.output_file_version:
        OperationOutputFile.objects.create(
            operation=operation,
            file_version=result.output_file_version,
            output_kind=OutputKind.OUTPUT_WORKBOOK,
        )
    if result.error_count:
        operation.status = ProcessStatus.COMPLETED_WITH_ERROR
    elif result.warning_count:
        operation.status = ProcessStatus.COMPLETED_WITH_WARNINGS
    else:
        operation.status = ProcessStatus.COMPLETED_SUCCESS
    operation.finished_at = timezone.now()
    operation.save(
        update_fields=[
            "summary",
            "error_count",
            "warning_count",
            "status",
            "finished_at",
            "updated_at",
        ]
    )
    _close_run_if_all_operations_terminal(operation.run)
    return operation


@transaction.atomic
def mark_operation_interrupted_failed(operation: Operation, *, summary: dict | None = None) -> Operation:
    operation = Operation.objects.select_for_update().get(pk=operation.pk)
    operation.status = CheckStatus.INTERRUPTED_FAILED if operation.operation_type == OperationType.CHECK else ProcessStatus.INTERRUPTED_FAILED
    operation.summary = summary or operation.summary
    operation.finished_at = timezone.now()
    operation.save(update_fields=["status", "summary", "finished_at", "updated_at"])
    Run.objects.filter(pk=operation.run_id).update(status=RunStatus.INTERRUPTED_FAILED)
    operation.run.refresh_from_db()
    return operation


def _close_run_if_all_operations_terminal(run: Run) -> None:
    operations = list(run.operations.all())
    if operations and all(operation.is_terminal for operation in operations):
        Run.objects.filter(pk=run.pk).update(status=RunStatus.COMPLETED)


def run_check_sync(
    operation: Operation,
    executor: Callable[[Operation], ShellExecutionResult],
) -> Operation:
    operation = start_operation(operation)
    try:
        return complete_check_operation(operation, result=executor(operation))
    except Exception:
        mark_operation_interrupted_failed(operation, summary={"failure": "interrupted_failed"})
        raise


def run_process_sync(
    operation: Operation,
    executor: Callable[[Operation], ShellExecutionResult],
) -> Operation:
    operation = start_operation(operation)
    try:
        return complete_process_operation(operation, result=executor(operation))
    except Exception:
        mark_operation_interrupted_failed(operation, summary={"failure": "interrupted_failed"})
        raise


def press_process_sync(
    *,
    marketplace: str,
    store,
    initiator_user,
    input_files: Iterable[InputFileSpec | dict],
    parameters: Iterable[ParameterSnapshotSpec | dict],
    logic_version: str,
    check_executor: Callable[[Operation], ShellExecutionResult],
    process_executor: Callable[[Operation], ShellExecutionResult],
    module: str = OperationModule.DISCOUNTS_EXCEL,
    mode: str = OperationMode.EXCEL,
    execution_context: dict | None = None,
    launch_method: str = LaunchMethod.MANUAL,
    confirmed_warning_codes: list[str] | None = None,
    enforce_permissions: bool = False,
) -> PressProcessResult:
    if enforce_permissions:
        assert_can_run_operation(
            initiator_user,
            marketplace=marketplace,
            module=module,
            mode=mode,
            action="run_process",
            store=store,
        )

    check_operation = find_actual_successful_check(
        marketplace=marketplace,
        module=module,
        mode=mode,
        store=store,
        input_files=input_files,
        parameters=parameters,
        logic_version=logic_version,
    )
    check_was_created = check_operation is None

    if check_operation is None:
        check_operation = create_check_operation(
            marketplace=marketplace,
            module=module,
            mode=mode,
            store=store,
            initiator_user=initiator_user,
            input_files=input_files,
            parameters=parameters,
            logic_version=logic_version,
            execution_context=execution_context,
            launch_method=launch_method,
            enforce_permissions=False,
        )
        check_operation = run_check_sync(check_operation, check_executor)
        if not is_check_actual_for_request(
            check_operation,
            marketplace=marketplace,
            module=module,
            mode=mode,
            store=store,
            input_files=input_files,
            parameters=parameters,
            logic_version=logic_version,
        ):
            raise ValidationError("Auto-created check is not acceptable for requested process.")

    process_operation = create_process_operation(
        marketplace=marketplace,
        module=module,
        mode=mode,
        store=store,
        initiator_user=initiator_user,
        input_files=input_files,
        parameters=parameters,
        logic_version=logic_version,
        check_basis_operation=check_operation,
        run=check_operation.run,
        execution_context=execution_context,
        launch_method=launch_method,
        confirmed_warning_codes=confirmed_warning_codes,
        enforce_permissions=enforce_permissions,
    )
    process_operation = run_process_sync(process_operation, process_executor)
    return PressProcessResult(
        check_operation=check_operation,
        process_operation=process_operation,
        check_was_created=check_was_created,
    )
