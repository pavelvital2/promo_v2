"""Operations/run execution shell for TASK-005."""

from __future__ import annotations

import re
from contextlib import contextmanager
from contextvars import ContextVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Max
from django.db.models.deletion import ProtectedError
from django.utils import timezone


_operation_visible_id_service_update_allowed = ContextVar(
    "operation_visible_id_service_update_allowed",
    default=False,
)
_run_visible_id_service_update_allowed = ContextVar(
    "run_visible_id_service_update_allowed",
    default=False,
)


@contextmanager
def allow_operation_visible_id_service_update():
    token = _operation_visible_id_service_update_allowed.set(True)
    try:
        yield
    finally:
        _operation_visible_id_service_update_allowed.reset(token)


@contextmanager
def allow_run_visible_id_service_update():
    token = _run_visible_id_service_update_allowed.set(True)
    try:
        yield
    finally:
        _run_visible_id_service_update_allowed.reset(token)


def _operation_visible_id_update_allowed() -> bool:
    return _operation_visible_id_service_update_allowed.get()


def _run_visible_id_update_allowed() -> bool:
    return _run_visible_id_service_update_allowed.get()


class GuardedDeleteQuerySet(models.QuerySet):
    def delete(self):
        count = 0
        with transaction.atomic():
            for obj in self:
                obj.delete()
                count += 1
        return count, {self.model._meta.label: count}


class Marketplace(models.TextChoices):
    WB = "wb", "WB"
    OZON = "ozon", "Ozon"


class OperationModule(models.TextChoices):
    DISCOUNTS_EXCEL = "discounts_excel", "Discounts Excel"
    WB_API = "wb_api", "WB API"


class OperationMode(models.TextChoices):
    EXCEL = "excel", "Excel"
    API = "api", "API"


class LaunchMethod(models.TextChoices):
    MANUAL = "manual", "Manual"
    AUTOMATIC = "automatic", "Automatic"
    SERVICE = "service", "Service"
    API = "api", "API"


class OperationType(models.TextChoices):
    CHECK = "check", "Check"
    PROCESS = "process", "Process"
    NOT_APPLICABLE = "not_applicable", "Not applicable"


class OperationStepCode(models.TextChoices):
    WB_API_PRICES_DOWNLOAD = "wb_api_prices_download", "WB API prices download"
    WB_API_PROMOTIONS_DOWNLOAD = "wb_api_promotions_download", "WB API promotions download"
    WB_API_DISCOUNT_CALCULATION = "wb_api_discount_calculation", "WB API discount calculation"
    WB_API_DISCOUNT_UPLOAD = "wb_api_discount_upload", "WB API discount upload"


class CheckStatus(models.TextChoices):
    CREATED = "created", "Created"
    RUNNING = "running", "Running"
    COMPLETED_NO_ERRORS = "completed_no_errors", "Completed without errors"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings", "Completed with warnings"
    COMPLETED_WITH_ERRORS = "completed_with_errors", "Completed with errors"
    INTERRUPTED_FAILED = "interrupted_failed", "Interrupted / failed"


class ProcessStatus(models.TextChoices):
    CREATED = "created", "Created"
    RUNNING = "running", "Running"
    COMPLETED_SUCCESS = "completed_success", "Completed successfully"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings", "Completed with warnings"
    COMPLETED_WITH_ERROR = "completed_with_error", "Completed with error"
    INTERRUPTED_FAILED = "interrupted_failed", "Interrupted / failed"


CHECK_STATUS_VALUES = tuple(choice.value for choice in CheckStatus)
PROCESS_STATUS_VALUES = tuple(choice.value for choice in ProcessStatus)
API_OPERATION_STATUS_VALUES = PROCESS_STATUS_VALUES
OPERATION_STATUS_CHOICES = (
    tuple(CheckStatus.choices)
    + tuple(
        choice
        for choice in ProcessStatus.choices
        if choice[0] not in CHECK_STATUS_VALUES
    )
)


class RunStatus(models.TextChoices):
    CREATED = "created", "Created"
    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    INTERRUPTED_FAILED = "interrupted_failed", "Interrupted / failed"


class MessageLevel(models.TextChoices):
    INFO = "info", "Info"
    WARNING_CONFIRMABLE = "warning_confirmable", "Confirmable warning"
    WARNING_INFO = "warning_info", "Informational warning"
    ERROR = "error", "Error"
    CRITICAL = "critical", "Critical"


class ParameterSource(models.TextChoices):
    STORE = "store", "Store"
    SYSTEM = "system", "System"


class OutputKind(models.TextChoices):
    OUTPUT_WORKBOOK = "output_workbook", "Output workbook"
    DETAIL_REPORT = "detail_report", "Detail report"


CHECK_TERMINAL_STATUSES = {
    CheckStatus.COMPLETED_NO_ERRORS,
    CheckStatus.COMPLETED_WITH_WARNINGS,
    CheckStatus.COMPLETED_WITH_ERRORS,
    CheckStatus.INTERRUPTED_FAILED,
}
PROCESS_TERMINAL_STATUSES = {
    ProcessStatus.COMPLETED_SUCCESS,
    ProcessStatus.COMPLETED_WITH_WARNINGS,
    ProcessStatus.COMPLETED_WITH_ERROR,
    ProcessStatus.INTERRUPTED_FAILED,
}
SUCCESSFUL_CHECK_STATUSES = {
    CheckStatus.COMPLETED_NO_ERRORS,
    CheckStatus.COMPLETED_WITH_WARNINGS,
}
WB_REASON_CODES = {
    "wb_valid_calculated",
    "wb_no_promo_item",
    "wb_over_threshold",
    "wb_missing_article",
    "wb_invalid_current_price",
    "wb_duplicate_price_article",
    "wb_missing_required_column",
    "wb_invalid_promo_row",
    "wb_invalid_workbook",
    "wb_output_write_error",
    "wb_discount_out_of_range",
}
WB_API_REASON_CODES = {
    "wb_api_price_download_success",
    "wb_api_price_download_failed",
    "wb_api_price_row_valid",
    "wb_api_price_row_size_conflict",
    "wb_api_price_row_invalid",
    "wb_api_promotion_current",
    "wb_api_promotion_not_current_filtered",
    "wb_api_promotion_regular",
    "wb_api_promotion_auto_no_nomenclatures",
    "wb_api_promotion_product_valid",
    "wb_api_promotion_product_invalid",
    "wb_api_calculated_from_api_sources",
    "wb_api_upload_ready",
    "wb_api_upload_blocked_by_drift",
    "wb_api_upload_sent",
    "wb_api_upload_success",
    "wb_api_upload_partial_error",
    "wb_api_upload_all_error",
    "wb_api_upload_canceled",
    "wb_api_upload_quarantine",
    "wb_api_upload_status_unknown",
}
WB_ALL_REASON_CODES = WB_REASON_CODES | WB_API_REASON_CODES
WB_API_STEP_CODES = tuple(choice.value for choice in OperationStepCode)
OZON_REASON_CODES = {
    "missing_min_price",
    "no_stock",
    "no_boost_prices",
    "use_max_boost_price",
    "use_min_price",
    "below_min_price_threshold",
    "insufficient_ozon_input_data",
}


def is_terminal_status(operation_type: str, status: str) -> bool:
    if operation_type == OperationType.CHECK:
        return status in CHECK_TERMINAL_STATUSES
    if operation_type == OperationType.PROCESS:
        return status in PROCESS_TERMINAL_STATUSES
    if operation_type == OperationType.NOT_APPLICABLE:
        return status in PROCESS_TERMINAL_STATUSES
    return False


def is_valid_operation_status(operation_type: str, status: str) -> bool:
    if operation_type == OperationType.CHECK:
        return status in CHECK_STATUS_VALUES
    if operation_type == OperationType.PROCESS:
        return status in PROCESS_STATUS_VALUES
    if operation_type == OperationType.NOT_APPLICABLE:
        return status in API_OPERATION_STATUS_VALUES
    return False


class RunQuerySet(GuardedDeleteQuerySet):
    def update(self, **kwargs):
        if "visible_id" in kwargs and not _run_visible_id_update_allowed():
            raise ValidationError("Run.visible_id is immutable after creation.")
        return super().update(**kwargs)


RunManager = models.Manager.from_queryset(RunQuerySet)


class OperationQuerySet(GuardedDeleteQuerySet):
    def update(self, **kwargs):
        if "visible_id" in kwargs and not _operation_visible_id_update_allowed():
            raise ValidationError("Operation.visible_id is immutable after creation.")
        if "status" in kwargs:
            status = kwargs["status"]
            if status not in {*CHECK_STATUS_VALUES, *PROCESS_STATUS_VALUES}:
                raise ValidationError("Operation status does not match operation type.")
            operation_type = kwargs.get("operation_type")
            if operation_type is not None:
                if not is_valid_operation_status(operation_type, status):
                    raise ValidationError("Operation status does not match operation type.")
            else:
                if status not in CHECK_STATUS_VALUES and self.filter(
                    operation_type=OperationType.CHECK,
                ).exists():
                    raise ValidationError("Operation status does not match operation type.")
                if status not in PROCESS_STATUS_VALUES and self.filter(
                    operation_type=OperationType.PROCESS,
                ).exists():
                    raise ValidationError("Operation status does not match operation type.")
                if status not in API_OPERATION_STATUS_VALUES and self.filter(
                    operation_type=OperationType.NOT_APPLICABLE,
                ).exists():
                    raise ValidationError("Operation status does not match operation type.")
        if self.filter(
            models.Q(operation_type=OperationType.CHECK, status__in=CHECK_TERMINAL_STATUSES)
            | models.Q(operation_type=OperationType.PROCESS, status__in=PROCESS_TERMINAL_STATUSES)
            | models.Q(
                operation_type=OperationType.NOT_APPLICABLE,
                status__in=PROCESS_TERMINAL_STATUSES,
            )
        ).exists():
            raise ValidationError("Terminal operations are immutable.")
        return super().update(**kwargs)


OperationManager = models.Manager.from_queryset(OperationQuerySet)


class OperationRelatedQuerySet(GuardedDeleteQuerySet):
    def update(self, **kwargs):
        if self.filter(
            models.Q(operation__operation_type=OperationType.CHECK, operation__status__in=CHECK_TERMINAL_STATUSES)
            | models.Q(
                operation__operation_type=OperationType.PROCESS,
                operation__status__in=PROCESS_TERMINAL_STATUSES,
            )
            | models.Q(
                operation__operation_type=OperationType.NOT_APPLICABLE,
                operation__status__in=PROCESS_TERMINAL_STATUSES,
            )
        ).exists():
            raise ValidationError("Terminal operation related records are immutable.")
        return super().update(**kwargs)


OperationRelatedManager = models.Manager.from_queryset(OperationRelatedQuerySet)


class WarningConfirmationQuerySet(GuardedDeleteQuerySet):
    def update(self, **kwargs):
        if self.exists():
            raise ValidationError("Warning confirmations are immutable.")
        return super().update(**kwargs)


WarningConfirmationManager = models.Manager.from_queryset(WarningConfirmationQuerySet)


class Run(models.Model):
    visible_id = models.CharField(max_length=32, unique=True, null=True, blank=True)
    marketplace = models.CharField(max_length=16, choices=Marketplace.choices)
    module = models.CharField(
        max_length=64,
        choices=OperationModule.choices,
        default=OperationModule.DISCOUNTS_EXCEL,
    )
    mode = models.CharField(max_length=16, choices=OperationMode.choices, default=OperationMode.EXCEL)
    store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        related_name="operation_runs",
    )
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="initiated_runs",
    )
    status = models.CharField(
        max_length=32,
        choices=RunStatus.choices,
        default=RunStatus.CREATED,
    )
    execution_context = models.JSONField(default=dict, blank=True)
    launch_method = models.CharField(
        max_length=16,
        choices=LaunchMethod.choices,
        default=LaunchMethod.MANUAL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RunManager()

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.visible_id or 'RUN-new'} {self.marketplace}/{self.module}/{self.mode}"

    def clean(self):
        super().clean()
        if self.store_id and self.marketplace != self.store.marketplace:
            raise ValidationError("Run marketplace must match store/cabinet marketplace.")

    def _next_visible_id(self) -> str:
        year = timezone.localtime(self.created_at or timezone.now()).year
        prefix = f"RUN-{year}-"
        max_visible_id = (
            type(self)
            .objects.filter(visible_id__startswith=prefix)
            .aggregate(max_visible_id=Max("visible_id"))["max_visible_id"]
        )
        next_no = 1
        if max_visible_id:
            match = re.match(rf"^{re.escape(prefix)}(\d{{6}})$", max_visible_id)
            if match:
                next_no = int(match.group(1)) + 1
        return f"{prefix}{next_no:06d}"

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        visible_id_may_be_written = update_fields is None or "visible_id" in update_fields
        if (
            self.pk
            and not self._state.adding
            and visible_id_may_be_written
            and not _run_visible_id_update_allowed()
        ):
            current_visible_id = (
                type(self).objects.filter(pk=self.pk).values_list("visible_id", flat=True).first()
            )
            if current_visible_id != self.visible_id:
                raise ValidationError("Run.visible_id is immutable after creation.")

        self.full_clean()
        super().save(*args, **kwargs)
        if not self.visible_id:
            self.visible_id = self._next_visible_id()
            with allow_run_visible_id_service_update():
                super().save(update_fields=["visible_id"])

    def delete(self, using=None, keep_parents=False):
        if self.operations.exists():
            raise ProtectedError("Runs with operations are historical and are not deleted.", [self])
        return super().delete(using=using, keep_parents=keep_parents)


class Operation(models.Model):
    visible_id = models.CharField(max_length=32, unique=True, null=True, blank=True)
    marketplace = models.CharField(max_length=16, choices=Marketplace.choices)
    module = models.CharField(
        max_length=64,
        choices=OperationModule.choices,
        default=OperationModule.DISCOUNTS_EXCEL,
    )
    mode = models.CharField(max_length=16, choices=OperationMode.choices, default=OperationMode.EXCEL)
    operation_type = models.CharField(max_length=16, choices=OperationType.choices)
    step_code = models.CharField(
        max_length=64,
        choices=OperationStepCode.choices,
        blank=True,
        db_index=True,
    )
    status = models.CharField(max_length=64, choices=OPERATION_STATUS_CHOICES)
    run = models.ForeignKey(Run, on_delete=models.PROTECT, related_name="operations")
    store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        related_name="operations",
    )
    initiator_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="initiated_operations",
    )
    execution_context = models.JSONField(default=dict, blank=True)
    launch_method = models.CharField(
        max_length=16,
        choices=LaunchMethod.choices,
        default=LaunchMethod.MANUAL,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    logic_version = models.CharField(max_length=128)
    check_basis_operation = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="process_operations",
    )
    summary = models.JSONField(default=dict, blank=True)
    error_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OperationManager()

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["marketplace", "module", "mode", "store", "operation_type"]),
            models.Index(fields=["marketplace", "mode", "step_code"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(operation_type=OperationType.CHECK, status__in=CHECK_STATUS_VALUES)
                    | models.Q(operation_type=OperationType.PROCESS, status__in=PROCESS_STATUS_VALUES)
                    | models.Q(
                        operation_type=OperationType.NOT_APPLICABLE,
                        status__in=API_OPERATION_STATUS_VALUES,
                    )
                ),
                name="operation_status_matches_type",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        marketplace=Marketplace.WB,
                        mode=OperationMode.API,
                        step_code__in=WB_API_STEP_CODES,
                        operation_type=OperationType.NOT_APPLICABLE,
                    )
                    | ~models.Q(marketplace=Marketplace.WB, mode=OperationMode.API)
                ),
                name="wb_api_operation_has_step_and_non_check_type",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.visible_id or 'OP-new'} {self.operation_type}/{self.status}"

    @property
    def is_terminal(self) -> bool:
        return is_terminal_status(self.operation_type, self.status)

    @property
    def is_successful_check(self) -> bool:
        return (
            self.operation_type == OperationType.CHECK
            and self.status in SUCCESSFUL_CHECK_STATUSES
            and self.error_count == 0
        )

    def clean(self):
        super().clean()
        if not is_valid_operation_status(self.operation_type, self.status):
            raise ValidationError("Operation status does not match operation type.")
        if self.store_id and self.marketplace != self.store.marketplace:
            raise ValidationError("Operation marketplace must match store/cabinet marketplace.")
        if self.run_id:
            if self.run.store_id != self.store_id:
                raise ValidationError("Operation store/cabinet must match run.")
            if (
                self.run.marketplace != self.marketplace
                or self.run.module != self.module
                or self.run.mode != self.mode
            ):
                raise ValidationError("Operation scenario must match run scenario.")
        if self.operation_type == OperationType.CHECK and self.check_basis_operation_id:
            raise ValidationError("Check operation cannot have check basis.")
        if self.marketplace == Marketplace.WB and self.mode == OperationMode.API:
            if self.step_code not in WB_API_STEP_CODES:
                raise ValidationError("WB API operation requires a supported step code.")
            if self.operation_type in {OperationType.CHECK, OperationType.PROCESS}:
                raise ValidationError("WB API operation must not use check/process type.")
        elif self.step_code:
            raise ValidationError("Step code is reserved for documented API operations.")
        if self.operation_type == OperationType.NOT_APPLICABLE and not (
            self.marketplace == Marketplace.WB and self.mode == OperationMode.API
        ):
            raise ValidationError("Not applicable operation type is reserved for documented API operations.")
        if self.operation_type == OperationType.PROCESS:
            if not self.check_basis_operation_id:
                raise ValidationError("Process operation must reference a check basis.")
            basis = self.check_basis_operation
            if basis.operation_type != OperationType.CHECK:
                raise ValidationError("Process basis must be a check operation.")
            if not basis.is_successful_check:
                raise ValidationError("Process basis must be a successful check.")

    def _next_visible_id(self) -> str:
        year = timezone.localtime(self.created_at or timezone.now()).year
        prefix = f"OP-{year}-"
        max_visible_id = (
            type(self)
            .objects.filter(visible_id__startswith=prefix)
            .aggregate(max_visible_id=Max("visible_id"))["max_visible_id"]
        )
        next_no = 1
        if max_visible_id:
            match = re.match(rf"^{re.escape(prefix)}(\d{{6}})$", max_visible_id)
            if match:
                next_no = int(match.group(1)) + 1
        return f"{prefix}{next_no:06d}"

    def _raise_if_terminal_mutation(self):
        if not self.pk or self._state.adding:
            return
        previous = type(self).objects.filter(pk=self.pk).values("operation_type", "status").first()
        if previous and is_terminal_status(previous["operation_type"], previous["status"]):
            raise ValidationError("Terminal operations are immutable.")

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        visible_id_may_be_written = update_fields is None or "visible_id" in update_fields
        if (
            self.pk
            and not self._state.adding
            and visible_id_may_be_written
            and not _operation_visible_id_update_allowed()
        ):
            current_visible_id = (
                type(self).objects.filter(pk=self.pk).values_list("visible_id", flat=True).first()
            )
            if current_visible_id != self.visible_id:
                raise ValidationError("Operation.visible_id is immutable after creation.")

        self._raise_if_terminal_mutation()
        self.full_clean()
        super().save(*args, **kwargs)
        if not self.visible_id:
            self.visible_id = self._next_visible_id()
            with allow_operation_visible_id_service_update():
                super().save(update_fields=["visible_id"])

    def delete(self, using=None, keep_parents=False):
        raise ProtectedError("Operations are historical and are not deleted.", [self])


class OperationLinkGuardMixin:
    operation_field_name = "operation"

    @property
    def guarded_operation(self):
        return getattr(self, self.operation_field_name)

    def _raise_if_terminal_operation_mutation(self):
        if self.guarded_operation.is_terminal:
            raise ValidationError("Terminal operation related records are immutable.")

    def delete(self, using=None, keep_parents=False):
        raise ProtectedError("Operation related records are historical and are not deleted.", [self])


class OperationInputFile(OperationLinkGuardMixin, models.Model):
    operation = models.ForeignKey(Operation, on_delete=models.PROTECT, related_name="input_files")
    file_version = models.ForeignKey(
        "files.FileVersion",
        on_delete=models.PROTECT,
        related_name="operation_input_links",
    )
    role_in_operation = models.CharField(max_length=64)
    ordinal_no = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = OperationRelatedManager()

    class Meta:
        ordering = ["operation_id", "ordinal_no", "role_in_operation", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["operation", "role_in_operation", "ordinal_no"],
                name="uniq_operation_input_role_ordinal",
            ),
        ]

    def clean(self):
        super().clean()
        file_object = self.file_version.file
        if file_object.store_id != self.operation.store_id:
            raise ValidationError("Input file store/cabinet must match operation.")
        if file_object.marketplace != self.operation.marketplace:
            raise ValidationError("Input file marketplace must match operation.")
        if file_object.module != self.operation.module:
            raise ValidationError("Input file module must match operation.")

    def save(self, *args, **kwargs):
        self._raise_if_terminal_operation_mutation()
        self.full_clean()
        super().save(*args, **kwargs)
        self._mark_file_version_used()

    def _mark_file_version_used(self):
        updates = {}
        if not self.file_version.operation_ref:
            updates["operation_ref"] = self.operation.visible_id
        if not self.file_version.run_ref:
            updates["run_ref"] = self.operation.run.visible_id
        if updates:
            type(self.file_version).objects.filter(pk=self.file_version_id).update(**updates)


class OperationOutputFile(OperationLinkGuardMixin, models.Model):
    operation = models.ForeignKey(Operation, on_delete=models.PROTECT, related_name="output_files")
    file_version = models.ForeignKey(
        "files.FileVersion",
        on_delete=models.PROTECT,
        related_name="operation_output_links",
    )
    output_kind = models.CharField(
        max_length=32,
        choices=OutputKind.choices,
        default=OutputKind.OUTPUT_WORKBOOK,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = OperationRelatedManager()

    class Meta:
        ordering = ["operation_id", "output_kind", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["operation", "output_kind"],
                name="uniq_operation_output_kind",
            ),
            models.UniqueConstraint(
                fields=["file_version"],
                name="uniq_operation_output_file_version",
            ),
        ]

    def clean(self):
        super().clean()
        file_object = self.file_version.file
        if file_object.store_id != self.operation.store_id:
            raise ValidationError("Output file store/cabinet must match operation.")
        if file_object.marketplace != self.operation.marketplace:
            raise ValidationError("Output file marketplace must match operation.")
        if file_object.module != self.operation.module:
            raise ValidationError("Output file module must match operation.")
        existing = type(self).objects.filter(file_version_id=self.file_version_id)
        if self.pk:
            existing = existing.exclude(pk=self.pk)
        if existing.exists():
            raise ValidationError("Output file version is already linked to an operation output.")
        existing_result = ProcessResult.objects.filter(
            output_file_version_id=self.file_version_id,
        ).exclude(operation_id=self.operation_id)
        if existing_result.exists():
            raise ValidationError("Output file version is already used by another process result.")

    def save(self, *args, **kwargs):
        self._raise_if_terminal_operation_mutation()
        self.full_clean()
        super().save(*args, **kwargs)
        self._mark_file_version_used()

    def _mark_file_version_used(self):
        updates = {}
        if not self.file_version.operation_ref:
            updates["operation_ref"] = self.operation.visible_id
        if not self.file_version.run_ref:
            updates["run_ref"] = self.operation.run.visible_id
        if updates:
            type(self.file_version).objects.filter(pk=self.file_version_id).update(**updates)


class AppliedParameterSnapshot(OperationLinkGuardMixin, models.Model):
    operation = models.ForeignKey(
        Operation,
        on_delete=models.PROTECT,
        related_name="parameter_snapshots",
    )
    parameter_code = models.CharField(max_length=128)
    applied_value = models.JSONField()
    source = models.CharField(max_length=16, choices=ParameterSource.choices)
    parameter_version = models.CharField(max_length=128, blank=True)
    effective_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = OperationRelatedManager()

    class Meta:
        ordering = ["operation_id", "parameter_code", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["operation", "parameter_code"],
                name="uniq_operation_parameter_snapshot",
            ),
        ]

    def save(self, *args, **kwargs):
        self._raise_if_terminal_operation_mutation()
        self.full_clean()
        return super().save(*args, **kwargs)


class CheckResult(OperationLinkGuardMixin, models.Model):
    operation = models.OneToOneField(
        Operation,
        on_delete=models.PROTECT,
        related_name="check_result",
    )
    summary = models.JSONField(default=dict, blank=True)
    error_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = OperationRelatedManager()

    def clean(self):
        super().clean()
        if self.operation.operation_type != OperationType.CHECK:
            raise ValidationError("CheckResult can be attached only to check operation.")

    def save(self, *args, **kwargs):
        self._raise_if_terminal_operation_mutation()
        self.full_clean()
        return super().save(*args, **kwargs)


class ProcessResult(OperationLinkGuardMixin, models.Model):
    operation = models.OneToOneField(
        Operation,
        on_delete=models.PROTECT,
        related_name="process_result",
    )
    output_file_version = models.ForeignKey(
        "files.FileVersion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="process_results",
    )
    summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = OperationRelatedManager()

    def clean(self):
        super().clean()
        if self.operation.operation_type != OperationType.PROCESS:
            raise ValidationError("ProcessResult can be attached only to process operation.")
        if self.output_file_version_id:
            linked_output = OperationOutputFile.objects.filter(
                file_version_id=self.output_file_version_id,
            ).exclude(operation_id=self.operation_id)
            if linked_output.exists():
                raise ValidationError("Output file version is already linked to another process operation.")
            existing_result = type(self).objects.filter(
                output_file_version_id=self.output_file_version_id,
            )
            if self.pk:
                existing_result = existing_result.exclude(pk=self.pk)
            if existing_result.exists():
                raise ValidationError("Output file version is already used by another process result.")

    def save(self, *args, **kwargs):
        self._raise_if_terminal_operation_mutation()
        self.full_clean()
        return super().save(*args, **kwargs)


class OperationDetailRow(OperationLinkGuardMixin, models.Model):
    operation = models.ForeignKey(Operation, on_delete=models.PROTECT, related_name="detail_rows")
    row_no = models.PositiveIntegerField()
    product_ref = models.CharField(max_length=255, blank=True)
    row_status = models.CharField(max_length=64)
    reason_code = models.CharField(max_length=128, blank=True)
    message_level = models.CharField(max_length=32, choices=MessageLevel.choices)
    message = models.TextField(blank=True)
    problem_field = models.CharField(max_length=128, blank=True)
    final_value = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = OperationRelatedManager()

    class Meta:
        ordering = ["operation_id", "row_no", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["operation", "row_no", "reason_code", "problem_field"],
                name="uniq_operation_detail_row_problem",
            ),
        ]

    def clean(self):
        super().clean()
        if self.reason_code and self.reason_code.startswith("wb_") and self.reason_code not in WB_ALL_REASON_CODES:
            raise ValidationError("Unsupported WB reason/result code.")
        if (
            self.reason_code
            and self.operation.marketplace == Marketplace.OZON
            and self.reason_code not in OZON_REASON_CODES
        ):
            raise ValidationError("Unsupported Ozon reason/result code.")

    def save(self, *args, **kwargs):
        self._raise_if_terminal_operation_mutation()
        self.full_clean()
        return super().save(*args, **kwargs)


class WarningConfirmation(models.Model):
    check_operation = models.ForeignKey(
        Operation,
        on_delete=models.PROTECT,
        related_name="warning_confirmations_as_check",
    )
    process_operation = models.ForeignKey(
        Operation,
        on_delete=models.PROTECT,
        related_name="warning_confirmations_as_process",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="operation_warning_confirmations",
    )
    confirmed_at = models.DateTimeField(auto_now_add=True)
    warning_codes = models.JSONField(default=list, blank=True)

    objects = WarningConfirmationManager()

    class Meta:
        ordering = ["-confirmed_at", "-id"]

    def clean(self):
        super().clean()
        if self.check_operation.operation_type != OperationType.CHECK:
            raise ValidationError("Warning confirmation check side must be a check operation.")
        if self.process_operation.operation_type != OperationType.PROCESS:
            raise ValidationError("Warning confirmation process side must be a process operation.")
        if self.process_operation.check_basis_operation_id != self.check_operation_id:
            raise ValidationError("Warning confirmation must match process check basis.")

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Warning confirmations are immutable.")
        if not self.pk and self.process_operation.is_terminal:
            raise ValidationError("Warning confirmation must be recorded before process completion.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        raise ProtectedError("Warning confirmations are historical and are not deleted.", [self])
