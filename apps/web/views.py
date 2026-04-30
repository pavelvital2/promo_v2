from __future__ import annotations

from dataclasses import dataclass

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date

from apps.audit.models import AuditActionCode, AuditRecord, AuditSourceContext
from apps.audit.services import audit_records_visible_to, create_audit_record
from apps.discounts.ozon_api import actions as ozon_api_actions
from apps.discounts.ozon_api import calculation as ozon_api_calculation
from apps.discounts.ozon_api import product_data as ozon_api_product_data
from apps.discounts.ozon_api import products as ozon_api_products
from apps.discounts.ozon_api import review as ozon_api_review
from apps.discounts.ozon_api import upload as ozon_api_upload
from apps.discounts.ozon_api.client import OzonApiError
from apps.discounts.ozon_excel import services as ozon_services
from apps.discounts.wb_api.client import WBApiError
from apps.discounts.wb_api.calculation import services as wb_api_calculation_services
from apps.discounts.wb_api.prices import services as wb_api_prices_services
from apps.discounts.wb_api.promotions import services as wb_api_promotions_services
from apps.discounts.wb_api.upload import services as wb_api_upload_services
from apps.discounts.wb_excel import services as wb_services
from apps.files.models import FileObject, FileVersion
from apps.files.services import (
    delete_pre_operation_file_version,
    download_permission_code,
    open_file_version_for_download,
)
from apps.identity_access.models import (
    AccessEffect,
    Permission,
    Role,
    RolePermission,
    RoleSectionAccess,
    SectionAccess,
    StoreAccess,
    UserPermissionOverride,
)
from apps.identity_access.services import (
    can_manage_user,
    can_manage_user_action,
    change_user_status,
    has_permission,
    has_section_access,
    has_store_access,
    is_owner,
    record_user_change,
)
from apps.marketplace_products.services import products_visible_to
from apps.marketplace_products.models import MarketplaceProduct
from apps.operations.models import (
    MessageLevel,
    OperationMode,
    OperationModule,
    OperationStepCode,
    Operation,
    OperationType,
    OutputKind,
    ProcessStatus,
)
from apps.platform_settings.models import (
    StoreParameterChangeHistory,
    StoreParameterValue,
    SystemParameterValue,
    WB_PARAMETER_CODES,
)
from apps.platform_settings.services import effective_parameter_rows, save_wb_store_parameters
from apps.stores.models import ConnectionBlock, StoreAccount
from apps.stores.services import (
    API_STAGE_2_NOTICE,
    OZON_API_CONNECTION_TYPE,
    OZON_API_MODULE,
    WB_API_CONNECTION_TYPE,
    WB_API_MODULE,
    connection_metadata_display,
    visible_stores_queryset,
)
from apps.techlog.models import SystemNotification, TechLogRecord


PAGE_SIZE = 25


@dataclass(frozen=True)
class NavItem:
    label: str
    url_name: str
    section_codes: tuple[str, ...]


NAV_ITEMS = (
    NavItem("Главная", "web:home", ("home.view",)),
    NavItem(
        "Маркетплейсы",
        "web:marketplaces",
        (
            "wb_discounts_excel.view",
            "wb_discounts_api.view",
            "ozon_discounts_excel.view",
            "ozon_api.view",
        ),
    ),
    NavItem("Операции", "web:operation_list", ("operations.view",)),
    NavItem("Справочники", "web:reference_index", ("stores.view", "products.view")),
    NavItem("Настройки", "web:settings_index", ("settings_system.view", "settings_store.view")),
    NavItem(
        "Администрирование",
        "web:admin_index",
        ("users.view", "roles.view", "permissions.view", "store_access.view"),
    ),
    NavItem("Аудит и журналы", "web:logs_index", ("audit.view", "techlog.view")),
)


SCENARIO_VIEW_PERMISSION = {
    "wb": "wb_discounts_excel.view",
    "ozon": "ozon_discounts_excel.view",
}
SCENARIO_CHECK_RESULT_PERMISSION = {
    "wb": "wb_discounts_excel.view_check_result",
    "ozon": "ozon_discounts_excel.view_check_result",
}
SCENARIO_PROCESS_RESULT_PERMISSION = {
    "wb": "wb_discounts_excel.view_process_result",
    "ozon": "ozon_discounts_excel.view_process_result",
}
SCENARIO_FILE_OBJECT = {
    "wb": FileObject.Scenario.WB_DISCOUNTS_EXCEL,
    "ozon": FileObject.Scenario.OZON_DISCOUNTS_EXCEL,
}
WB_API_ACTION_PERMISSION_CODES = (
    "wb.api.operation.view",
    "wb.api.connection.view",
    "wb.api.connection.manage",
    "wb.api.prices.download",
    "wb.api.prices.file.download",
    "wb.api.promotions.download",
    "wb.api.promotions.file.download",
    "wb.api.discounts.calculate",
    "wb.api.discounts.result.download",
    "wb.api.discounts.upload",
    "wb.api.discounts.upload.confirm",
)
WB_API_STEP_LABELS = {
    OperationStepCode.WB_API_PRICES_DOWNLOAD: "2.1.1 Скачать цены",
    OperationStepCode.WB_API_PROMOTIONS_DOWNLOAD: "2.1.2 Скачать текущие акции",
    OperationStepCode.WB_API_DISCOUNT_CALCULATION: "2.1.3 Рассчитать итоговый Excel",
    OperationStepCode.WB_API_DISCOUNT_UPLOAD: "2.1.4 Загрузить по API",
}
WB_API_STEPS = tuple(WB_API_STEP_LABELS)
OZON_API_ACTION_PERMISSION_CODES = (
    "ozon.api.operation.view",
    "ozon.api.connection.view",
    "ozon.api.connection.manage",
    "ozon.api.actions.view",
    "ozon.api.actions.download",
    "ozon.api.elastic.active_products.download",
    "ozon.api.elastic.candidates.download",
    "ozon.api.elastic.product_data.download",
    "ozon.api.elastic.calculate",
    "ozon.api.elastic.review",
    "ozon.api.elastic.files.download",
    "ozon.api.elastic.upload",
    "ozon.api.elastic.upload.confirm",
    "ozon.api.elastic.deactivate.confirm",
)
OZON_API_STEP_LABELS = {
    OperationStepCode.OZON_API_ACTIONS_DOWNLOAD: "Скачать доступные акции",
    OperationStepCode.OZON_API_ELASTIC_ACTIVE_PRODUCTS_DOWNLOAD: "Скачать товары участвующие в акции",
    OperationStepCode.OZON_API_ELASTIC_CANDIDATE_PRODUCTS_DOWNLOAD: "Скачать товары кандидаты в акцию",
    OperationStepCode.OZON_API_ELASTIC_PRODUCT_DATA_DOWNLOAD: "Скачать данные по полученным товарам",
    OperationStepCode.OZON_API_ELASTIC_CALCULATION: "Обработать",
    OperationStepCode.OZON_API_ELASTIC_UPLOAD: "Загрузить в Ozon",
}
OZON_API_STEPS = tuple(OZON_API_STEP_LABELS)


def _common_context(request: HttpRequest, *, section: str = "") -> dict:
    nav_items = []
    if request.user.is_authenticated:
        for item in NAV_ITEMS:
            if any(has_section_access(request.user, code) for code in item.section_codes):
                nav_items.append(item)
    return {"nav_items": nav_items, "active_section": section}


def _render(request: HttpRequest, template: str, context: dict | None = None, *, section: str = ""):
    payload = _common_context(request, section=section)
    payload.update(context or {})
    return render(request, template, payload)


def _paginate(request: HttpRequest, queryset, per_page: int = PAGE_SIZE):
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))


def _visible_store_ids(user) -> list[int]:
    return list(visible_stores_queryset(user).values_list("id", flat=True))


def _stores_with_permission(user, permission_code: str):
    stores = visible_stores_queryset(user)
    allowed_ids = [store.pk for store in stores if has_permission(user, permission_code, store)]
    return StoreAccount.objects.filter(pk__in=allowed_ids)


def _has_permission_in_scope(user, permission_code: str) -> bool:
    return has_permission(user, permission_code) or _stores_with_permission(
        user,
        permission_code,
    ).exists()


def _user_queryset_for_permission(user, permission_code: str):
    queryset = get_user_model().objects.select_related("primary_role")
    if has_permission(user, permission_code):
        return queryset
    store_ids = list(_stores_with_permission(user, permission_code).values_list("id", flat=True))
    if not store_ids:
        return queryset.none()
    return queryset.filter(store_access__store_id__in=store_ids, store_access__is_active=True).distinct()


def _visible_operations_queryset(user):
    if not user.is_authenticated or not user.is_active:
        return Operation.objects.none()

    queryset = Operation.objects.select_related("store", "initiator_user", "check_basis_operation")
    queryset = queryset.filter(store_id__in=_visible_store_ids(user))
    allowed_ids = [operation.id for operation in queryset if _can_view_operation(user, operation)]
    return (
        Operation.objects.select_related("store", "initiator_user", "check_basis_operation")
        .filter(id__in=allowed_ids)
        .order_by("-created_at", "-id")
    )


def _require_operation_view(user, operation: Operation) -> None:
    if not _can_view_operation(user, operation):
        raise PermissionDenied("No permission or object access for this operation.")


def _scenario_stores(user, marketplace: str):
    permission_code = SCENARIO_VIEW_PERMISSION[marketplace]
    stores = visible_stores_queryset(user).filter(marketplace=marketplace)
    allowed_ids = [store.pk for store in stores if has_permission(user, permission_code, store)]
    return StoreAccount.objects.filter(pk__in=allowed_ids).select_related("group").order_by("name", "id")


def _selected_store(request: HttpRequest, marketplace: str) -> StoreAccount | None:
    store_id = request.POST.get("store") or request.GET.get("store")
    stores = _scenario_stores(request.user, marketplace)
    if not store_id:
        return stores.first()
    return stores.filter(pk=store_id).first()


def _draft_key(marketplace: str, store: StoreAccount) -> str:
    return f"draft:{marketplace}:{store.pk}"


def _draft_data(request: HttpRequest, marketplace: str, store: StoreAccount) -> dict:
    return request.session.setdefault(
        _draft_key(marketplace, store),
        {"price": None, "promo": [], "input": None},
    )


def _save_draft_data(request: HttpRequest, marketplace: str, store: StoreAccount, data: dict) -> None:
    request.session[_draft_key(marketplace, store)] = data
    request.session.modified = True


def _draft_versions(request: HttpRequest, marketplace: str, store: StoreAccount) -> dict:
    data = _draft_data(request, marketplace, store)
    ids = []
    if data.get("price"):
        ids.append(data["price"])
    if data.get("input"):
        ids.append(data["input"])
    ids.extend(data.get("promo") or [])
    versions = {
        version.pk: version
        for version in FileVersion.objects.select_related("file", "uploaded_by")
        .filter(pk__in=ids, file__store=store, file__scenario=SCENARIO_FILE_OBJECT[marketplace])
    }
    price = versions.get(data.get("price"))
    input_version = versions.get(data.get("input"))
    chain_file_ids = [version.file_id for version in (price, input_version) if version]
    chains = {}
    if chain_file_ids:
        for version in (
            FileVersion.objects.select_related("file", "uploaded_by")
            .filter(file_id__in=chain_file_ids)
            .order_by("file_id", "-version_no", "-id")
        ):
            chains.setdefault(version.file_id, []).append(version)
    return {
        "price": price,
        "input": input_version,
        "promo": [versions[item_id] for item_id in data.get("promo") or [] if item_id in versions],
        "all": [versions[item_id] for item_id in ids if item_id in versions],
        "price_chain": chains.get(price.file_id, []) if price else [],
        "input_chain": chains.get(input_version.file_id, []) if input_version else [],
    }


def _audit_input_version_upload(
    request: HttpRequest,
    *,
    store: StoreAccount,
    version: FileVersion,
    old_version: FileVersion | None = None,
) -> None:
    file_metadata = {
        "file_visible_id": version.file.visible_id,
        "version_id": version.pk,
        "version_no": version.version_no,
        "original_name": version.original_name,
        "logical_name": version.file.logical_name,
        "scenario": version.file.scenario,
        "size": version.size,
        "checksum_sha256": version.checksum_sha256,
    }
    before = {}
    if old_version is not None:
        before = {
            "file_visible_id": old_version.file.visible_id,
            "version_id": old_version.pk,
            "version_no": old_version.version_no,
            "original_name": old_version.original_name,
            "logical_name": old_version.file.logical_name,
            "scenario": old_version.file.scenario,
            "size": old_version.size,
            "checksum_sha256": old_version.checksum_sha256,
        }
    create_audit_record(
        action_code=(
            AuditActionCode.FILE_INPUT_REPLACED
            if old_version is not None
            else AuditActionCode.FILE_INPUT_UPLOADED
        ),
        entity_type="FileVersion",
        entity_id=version.pk,
        user=request.user,
        store=store,
        safe_message=(
            f"Input file replaced: {version.file.visible_id} v{version.version_no}"
            if old_version is not None
            else f"Input file uploaded: {version.file.visible_id} v{version.version_no}"
        ),
        before_snapshot=before,
        after_snapshot=file_metadata,
        source_context=AuditSourceContext.UI,
    )


def _replace_single_draft_file(
    request: HttpRequest,
    *,
    marketplace: str,
    store: StoreAccount,
    slot: str,
    uploaded_file,
    logical_name: str,
) -> None:
    data = _draft_data(request, marketplace, store)
    old_id = data.get(slot)
    old_version = None
    if old_id:
        old_version = FileVersion.objects.filter(
            pk=old_id,
            file__store=store,
            file__scenario=SCENARIO_FILE_OBJECT[marketplace],
        ).select_related("file").first()
    version = _create_input_version(
        request,
        store,
        uploaded_file,
        SCENARIO_FILE_OBJECT[marketplace],
        logical_name,
        file_object=old_version.file if old_version else None,
    )
    _audit_input_version_upload(request, store=store, version=version, old_version=old_version)
    data[slot] = version.pk
    _save_draft_data(request, marketplace, store, data)


def _delete_draft_version(request: HttpRequest, *, marketplace: str, store: StoreAccount, version_id: int) -> None:
    data = _draft_data(request, marketplace, store)
    version = get_object_or_404(
        FileVersion.objects.select_related("file"),
        pk=version_id,
        file__store=store,
        file__scenario=SCENARIO_FILE_OBJECT[marketplace],
    )
    delete_pre_operation_file_version(version)
    if data.get("price") == version_id:
        data["price"] = None
    if data.get("input") == version_id:
        data["input"] = None
    data["promo"] = [item_id for item_id in data.get("promo") or [] if item_id != version_id]
    _save_draft_data(request, marketplace, store, data)


def _summary_items(value) -> list[tuple[str, object]]:
    if not isinstance(value, dict):
        return []
    hidden_keys = {
        "safe_snapshot",
        "products",
        "canonical_rows",
        "calculation_rows",
        "accepted_calculation_snapshot",
    }
    return [(key, child) for key, child in value.items() if key not in hidden_keys]


def _operation_classifier(operation: Operation) -> str:
    if operation.marketplace == "wb" and operation.mode == OperationMode.API:
        return operation.step_code or OperationType.NOT_APPLICABLE
    if operation.marketplace == "ozon" and operation.mode == OperationMode.API:
        return operation.step_code or OperationType.NOT_APPLICABLE
    return operation.operation_type


def _operation_classifier_label(operation: Operation) -> str:
    if operation.marketplace == "wb" and operation.mode == OperationMode.API:
        return WB_API_STEP_LABELS.get(operation.step_code, operation.step_code or "api")
    if operation.marketplace == "ozon" and operation.mode == OperationMode.API:
        return OZON_API_STEP_LABELS.get(operation.step_code, operation.step_code or "api")
    return operation.operation_type


def _decorate_operations(operations):
    for operation in operations:
        operation.classifier = _operation_classifier(operation)
        operation.classifier_label = _operation_classifier_label(operation)
    return operations


def _can_view_operation(user, operation: Operation) -> bool:
    if operation.marketplace == "wb" and operation.mode == OperationMode.API:
        return (
            operation.module == OperationModule.WB_API
            and operation.step_code in WB_API_STEPS
            and has_permission(user, "wb.api.operation.view", operation.store)
        )
    if operation.marketplace == "ozon" and operation.mode == OperationMode.API:
        return (
            operation.module == OperationModule.OZON_API
            and operation.step_code in OZON_API_STEPS
            and has_permission(user, "ozon.api.operation.view", operation.store)
        )
    permission_map = (
        SCENARIO_CHECK_RESULT_PERMISSION
        if operation.operation_type == OperationType.CHECK
        else SCENARIO_PROCESS_RESULT_PERMISSION
    )
    permission_code = permission_map.get(operation.marketplace)
    return bool(permission_code and has_permission(user, permission_code, operation.store))


def _api_file_permission(link) -> str:
    return download_permission_code(link.file_version.file)


def _can_download_link(user, link) -> bool:
    return has_permission(user, _api_file_permission(link), link.file_version.file.store)


def _successful_wb_api_operations(store: StoreAccount, step_code: str):
    return (
        Operation.objects.filter(
            marketplace="wb",
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=step_code,
            store=store,
            status__in=[ProcessStatus.COMPLETED_SUCCESS, ProcessStatus.COMPLETED_WITH_WARNINGS],
        )
        .order_by("-finished_at", "-id")
    )


def _successful_wb_api_calculations(store: StoreAccount):
    return (
        Operation.objects.filter(
            marketplace="wb",
            module=OperationModule.WB_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.WB_API_DISCOUNT_CALCULATION,
            store=store,
            status=ProcessStatus.COMPLETED_SUCCESS,
            error_count=0,
            output_files__file_version__file__scenario=FileObject.Scenario.WB_DISCOUNTS_API_RESULT_EXCEL,
        )
        .distinct()
        .order_by("-finished_at", "-id")
    )


def _successful_ozon_api_operations(store: StoreAccount, step_code: str):
    return (
        Operation.objects.filter(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=step_code,
            store=store,
            status__in=[ProcessStatus.COMPLETED_SUCCESS, ProcessStatus.COMPLETED_WITH_WARNINGS],
        )
        .order_by("-finished_at", "-id")
    )


def _ozon_api_calculations(store: StoreAccount):
    return (
        Operation.objects.filter(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code=OperationStepCode.OZON_API_ELASTIC_CALCULATION,
            store=store,
            status__in=[
                ProcessStatus.COMPLETED_SUCCESS,
                ProcessStatus.COMPLETED_WITH_WARNINGS,
                ProcessStatus.COMPLETED_WITH_ERROR,
            ],
        )
        .order_by("-finished_at", "-id")
    )


def _wb_api_stores(user):
    stores = visible_stores_queryset(user).filter(marketplace=StoreAccount.Marketplace.WB)
    allowed_ids = [
        store.pk
        for store in stores
        if has_permission(user, "wb.api.operation.view", store)
        or any(has_permission(user, code, store) for code in WB_API_ACTION_PERMISSION_CODES)
    ]
    return StoreAccount.objects.filter(pk__in=allowed_ids).select_related("group").order_by("name", "id")


def _ozon_api_stores(user):
    stores = visible_stores_queryset(user).filter(marketplace=StoreAccount.Marketplace.OZON)
    allowed_ids = [
        store.pk
        for store in stores
        if has_permission(user, "ozon.api.operation.view", store)
        or any(has_permission(user, code, store) for code in OZON_API_ACTION_PERMISSION_CODES)
    ]
    return StoreAccount.objects.filter(pk__in=allowed_ids).select_related("group").order_by("name", "id")


def _selected_wb_api_store(request: HttpRequest) -> StoreAccount | None:
    store_id = request.POST.get("store") or request.GET.get("store")
    stores = _wb_api_stores(request.user)
    if not store_id:
        return stores.first()
    return stores.filter(pk=store_id).first()


def _selected_ozon_api_store(request: HttpRequest) -> StoreAccount | None:
    store_id = request.POST.get("store") or request.GET.get("store")
    stores = _ozon_api_stores(request.user)
    if not store_id:
        return stores.first()
    return stores.filter(pk=store_id).first()


def _active_connection_for_ui(store: StoreAccount | None):
    if store is None:
        return None
    return (
        ConnectionBlock.objects.filter(
            store=store,
            module=WB_API_MODULE,
            connection_type=WB_API_CONNECTION_TYPE,
            is_stage2_1_used=True,
        )
        .order_by("-updated_at", "-id")
        .first()
    )


def _ozon_active_connection_for_ui(store: StoreAccount | None):
    if store is None:
        return None
    return (
        ConnectionBlock.objects.filter(
            store=store,
            module=OZON_API_MODULE,
            connection_type=OZON_API_CONNECTION_TYPE,
        )
        .order_by("-updated_at", "-id")
        .first()
    )


def _connection_context(user, store: StoreAccount | None) -> dict:
    connection = _active_connection_for_ui(store)
    can_view = bool(store and has_permission(user, "wb.api.connection.view", store))
    can_manage = bool(store and has_permission(user, "wb.api.connection.manage", store))
    if connection and can_view:
        connection_info = {
            "last_checked_at": connection.last_checked_at,
            "last_check_status": connection.last_check_status,
            "has_protected_ref": bool(connection.protected_secret_ref),
            "metadata_display": connection_metadata_display(connection.metadata),
        }
    else:
        connection_info = None
    status = connection.status if connection else ConnectionBlock.Status.NOT_CONFIGURED
    return {
        "connection": connection_info,
        "connection_status": status,
        "connection_is_active": status == ConnectionBlock.Status.ACTIVE,
        "can_view_connection": can_view,
        "can_manage_connection": can_manage,
    }


def _ozon_connection_context(user, store: StoreAccount | None) -> dict:
    connection = _ozon_active_connection_for_ui(store)
    can_view = bool(store and has_permission(user, "ozon.api.connection.view", store))
    can_manage = bool(store and has_permission(user, "ozon.api.connection.manage", store))
    if connection and can_view:
        connection_info = {
            "last_checked_at": connection.last_checked_at,
            "last_check_status": connection.last_check_status,
            "has_protected_ref": bool(connection.protected_secret_ref),
            "metadata_display": connection_metadata_display(connection.metadata),
        }
    else:
        connection_info = None
    status = connection.status if connection else ConnectionBlock.Status.NOT_CONFIGURED
    return {
        "connection": connection_info,
        "connection_status": status,
        "connection_is_active": status == ConnectionBlock.Status.ACTIVE,
        "can_view_connection": can_view,
        "can_manage_connection": can_manage,
    }


def _operation_output_links(operation: Operation | None):
    if operation is None:
        return []
    return list(operation.output_files.select_related("file_version", "file_version__file"))


def _step_context(user, operation: Operation | None) -> dict:
    links = _operation_output_links(operation)
    return {
        "operation": operation,
        "summary_items": _summary_items(operation.summary if operation else None),
        "output_links": [
            {
                "link": link,
                "can_download": _can_download_link(user, link),
            }
            for link in links
        ],
    }


def _upload_ready_count(operation: Operation | None) -> int:
    if operation is None:
        return 0
    return operation.detail_rows.filter(
        row_status="ok",
        reason_code="wb_api_calculated_from_api_sources",
        final_value__upload_ready=True,
    ).count()


def _wb_api_redirect(store: StoreAccount, operation: Operation | None = None):
    url = f"{reverse('web:wb_api')}?store={store.pk}"
    if operation is not None:
        url = f"{url}&operation={operation.visible_id}"
    return redirect(url)


@login_required
def home(request: HttpRequest) -> HttpResponse:
    operations = _visible_operations_queryset(request.user)
    problem_operations = operations.filter(
        Q(error_count__gt=0)
        | Q(warning_count__gt=0)
        | Q(status__in=["interrupted_failed", "completed_with_error", "completed_with_errors"])
    )[:8]
    file_notifications = FileVersion.objects.select_related("file", "file__store").filter(
        file__store_id__in=_visible_store_ids(request.user),
    ).order_by("retention_until")[:8]
    system_notifications = (
        _visible_notifications_queryset(request.user)[:8]
        if has_section_access(request.user, "audit.view") or has_section_access(request.user, "techlog.view")
        else []
    )

    sections = [
        {"label": item.label, "url_name": item.url_name}
        for item in NAV_ITEMS
        if any(has_section_access(request.user, code) for code in item.section_codes)
    ]
    quick_actions = []
    for marketplace, label, route in (
        ("wb", "WB Excel", "web:wb_excel"),
        ("ozon", "Ozon Excel", "web:ozon_excel"),
    ):
        if _scenario_stores(request.user, marketplace).exists():
            quick_actions.append({"label": label, "url_name": route})
    if _wb_api_stores(request.user).exists():
        quick_actions.append({"label": "WB API", "url_name": "web:wb_api"})
    if _ozon_api_stores(request.user).exists():
        quick_actions.append({"label": "Ozon Elastic API", "url_name": "web:ozon_elastic"})

    return _render(
        request,
        "web/home.html",
        {
            "sections": sections,
            "quick_actions": quick_actions,
            "latest_operations": operations[:8],
            "problem_operations": problem_operations,
            "file_notifications": file_notifications,
            "system_notifications": system_notifications,
        },
        section="home",
    )


def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


@login_required
def marketplaces(request: HttpRequest) -> HttpResponse:
    wb_stores = _scenario_stores(request.user, "wb")
    ozon_stores = _scenario_stores(request.user, "ozon")
    wb_api_stores = _wb_api_stores(request.user)
    ozon_api_stores = _ozon_api_stores(request.user)
    return _render(
        request,
        "web/marketplaces.html",
        {
            "wb_stores": wb_stores,
            "ozon_stores": ozon_stores,
            "wb_api_stores": wb_api_stores,
            "ozon_api_stores": ozon_api_stores,
        },
        section="marketplaces",
    )


@login_required
def wb_excel(request: HttpRequest) -> HttpResponse:
    return _excel_screen(request, marketplace="wb")


@login_required
def ozon_excel(request: HttpRequest) -> HttpResponse:
    return _excel_screen(request, marketplace="ozon")


@login_required
def ozon_elastic(request: HttpRequest) -> HttpResponse:
    stores = _ozon_api_stores(request.user)
    store = _selected_ozon_api_store(request)
    if store is None and stores.exists():
        raise PermissionDenied("No object access for selected Ozon store.")
    if store and not (
        has_permission(request.user, "ozon.api.operation.view", store)
        or has_permission(request.user, "ozon.api.actions.view", store)
    ):
        raise PermissionDenied("No permission or object access for Ozon Elastic workflow.")

    if request.method == "POST":
        action = request.POST.get("action")
        if store is None:
            messages.error(request, "Не выбран доступный Ozon магазин/кабинет.")
        else:
            response = _handle_ozon_elastic_post(request, store, action)
            if response:
                return response

    context = _ozon_elastic_master_context(request, stores, store)
    return _render(request, "web/ozon_elastic.html", context, section="marketplaces")


@login_required
def wb_api(request: HttpRequest) -> HttpResponse:
    stores = _wb_api_stores(request.user)
    store = _selected_wb_api_store(request)
    if store is None and stores.exists():
        raise PermissionDenied("No object access for selected WB store.")
    if store and not has_permission(request.user, "wb.api.operation.view", store):
        raise PermissionDenied("No permission or object access for WB API operations.")

    if request.method == "POST":
        action = request.POST.get("action")
        if store is None:
            messages.error(request, "Не выбран доступный WB магазин/кабинет.")
        else:
            response = _handle_wb_api_post(request, store, action)
            if response:
                return response

    context = _wb_api_master_context(request, stores, store)
    return _render(request, "web/wb_api.html", context, section="marketplaces")


@login_required
def wb_api_upload_confirm(request: HttpRequest) -> HttpResponse:
    stores = _wb_api_stores(request.user)
    store = _selected_wb_api_store(request)
    if store is None:
        raise PermissionDenied("No object access for selected WB store.")
    if not (
        has_permission(request.user, "wb.api.operation.view", store)
        and has_permission(request.user, "wb.api.discounts.upload", store)
        and has_permission(request.user, "wb.api.discounts.upload.confirm", store)
    ):
        raise PermissionDenied("No permission or object access for WB API upload confirmation.")

    calculation = get_object_or_404(
        _successful_wb_api_calculations(store),
        pk=request.POST.get("calculation_operation_id") or request.GET.get("calculation_operation_id") or 0,
    )
    if request.method == "POST":
        try:
            operation = wb_api_upload_services.upload_wb_api_discounts(
                actor=request.user,
                store=store,
                calculation_operation=calculation,
                confirmation_phrase=request.POST.get("confirmation_phrase", ""),
            )
            return _wb_api_redirect(store, operation)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, _error_text(exc))

    result_link = (
        calculation.output_files.select_related("file_version", "file_version__file")
        .filter(file_version__file__scenario=FileObject.Scenario.WB_DISCOUNTS_API_RESULT_EXCEL)
        .first()
    )
    upload_ready_count = _upload_ready_count(calculation)
    excluded_count = calculation.detail_rows.exclude(
        row_status="ok",
        reason_code="wb_api_calculated_from_api_sources",
        final_value__upload_ready=True,
    ).count()
    return _render(
        request,
        "web/wb_api_upload_confirm.html",
        {
            "stores": stores,
            "selected_store": store,
            "calculation": calculation,
            "result_link": result_link,
            "upload_ready_count": upload_ready_count,
            "excluded_count": excluded_count,
            "confirmation_phrase": wb_api_upload_services.CONFIRMATION_PHRASE,
            **_connection_context(request.user, store),
        },
        section="marketplaces",
    )


def _handle_wb_api_post(request: HttpRequest, store: StoreAccount, action: str | None):
    if action not in {"download_prices", "download_promotions", "calculate"}:
        messages.error(request, "Неизвестное действие.")
        return None
    try:
        if action == "download_prices":
            operation = wb_api_prices_services.download_wb_prices(actor=request.user, store=store)
            return _wb_api_redirect(store, operation)
        if action == "download_promotions":
            operation = wb_api_promotions_services.download_wb_current_promotions(
                actor=request.user,
                store=store,
            )
            return _wb_api_redirect(store, operation)

        if not _connection_context(request.user, store)["connection_is_active"]:
            messages.error(request, "Действие заблокировано: требуется active connection.")
            return None
        price_operation = get_object_or_404(
            _successful_wb_api_operations(store, OperationStepCode.WB_API_PRICES_DOWNLOAD),
            pk=request.POST.get("price_operation_id") or 0,
        )
        promotion_operation = get_object_or_404(
            _successful_wb_api_operations(store, OperationStepCode.WB_API_PROMOTIONS_DOWNLOAD),
            pk=request.POST.get("promotion_operation_id") or 0,
        )
        operation = wb_api_calculation_services.calculate_wb_api_discounts(
            actor=request.user,
            store=store,
            price_operation=price_operation,
            promotion_operation=promotion_operation,
        )
        return _wb_api_redirect(store, operation)
    except (PermissionDenied, ValidationError, WBApiError) as exc:
        messages.error(request, _error_text(exc))
        return None


def _wb_api_master_context(request: HttpRequest, stores, store: StoreAccount | None) -> dict:
    latest_by_step = {}
    price_basis = []
    promotion_basis = []
    calculations = []
    if store:
        for operation in (
            Operation.objects.filter(
                marketplace="wb",
                module=OperationModule.WB_API,
                mode=OperationMode.API,
                operation_type=OperationType.NOT_APPLICABLE,
                step_code__in=WB_API_STEPS,
                store=store,
            )
            .order_by("-created_at", "-id")
        ):
            latest_by_step.setdefault(operation.step_code, operation)
        price_basis = list(_successful_wb_api_operations(store, OperationStepCode.WB_API_PRICES_DOWNLOAD)[:20])
        promotion_basis = list(
            _successful_wb_api_operations(store, OperationStepCode.WB_API_PROMOTIONS_DOWNLOAD)[:20]
        )
        calculations = list(_successful_wb_api_calculations(store)[:20])

    connection = _connection_context(request.user, store)
    selected_calculation = calculations[0] if calculations else None
    operation_visible_id = request.GET.get("operation", "").strip()
    result_operation = None
    if operation_visible_id and store:
        result_operation = (
            Operation.objects.filter(
                visible_id=operation_visible_id,
                store=store,
                marketplace="wb",
                module=OperationModule.WB_API,
                mode=OperationMode.API,
                step_code__in=WB_API_STEPS,
            )
            .first()
        )
        if result_operation:
            _require_operation_view(request.user, result_operation)

    return {
        "stores": stores,
        "selected_store": store,
        "steps": [
            {
                "code": OperationStepCode.WB_API_PRICES_DOWNLOAD,
                "title": "Шаг 1: Скачать цены",
                "readonly_text": "Шаг читает WB API и не меняет WB.",
                "action": "download_prices",
                "button": "Скачать цены",
                "can_run": bool(
                    store
                    and connection["connection_is_active"]
                    and has_permission(request.user, "wb.api.prices.download", store)
                ),
                **_step_context(request.user, latest_by_step.get(OperationStepCode.WB_API_PRICES_DOWNLOAD)),
            },
            {
                "code": OperationStepCode.WB_API_PROMOTIONS_DOWNLOAD,
                "title": "Шаг 2: Скачать текущие акции",
                "readonly_text": "Шаг читает только текущие акции и не меняет WB.",
                "action": "download_promotions",
                "button": "Скачать текущие акции",
                "can_run": bool(
                    store
                    and connection["connection_is_active"]
                    and has_permission(request.user, "wb.api.promotions.download", store)
                ),
                **_step_context(request.user, latest_by_step.get(OperationStepCode.WB_API_PROMOTIONS_DOWNLOAD)),
            },
            {
                "code": OperationStepCode.WB_API_DISCOUNT_CALCULATION,
                "title": "Шаг 3: Рассчитать итоговый Excel",
                "readonly_text": "Расчёт формирует Excel для ручной загрузки в ЛК WB и не меняет WB.",
                "action": "calculate",
                "button": "Рассчитать итоговый Excel",
                "can_run": bool(
                    store
                    and connection["connection_is_active"]
                    and has_permission(request.user, "wb.api.discounts.calculate", store)
                    and price_basis
                    and promotion_basis
                ),
                "price_basis": price_basis,
                "promotion_basis": promotion_basis,
                **_step_context(request.user, latest_by_step.get(OperationStepCode.WB_API_DISCOUNT_CALCULATION)),
            },
            {
                "code": OperationStepCode.WB_API_DISCOUNT_UPLOAD,
                "title": "Шаг 4: Загрузить по API",
                "readonly_text": "Единственный шаг, который отправляет скидки в WB; требуется подтверждение и drift check.",
                "can_run": bool(
                    store
                    and selected_calculation
                    and connection["connection_is_active"]
                    and has_permission(request.user, "wb.api.discounts.upload", store)
                    and has_permission(request.user, "wb.api.discounts.upload.confirm", store)
                    and _upload_ready_count(selected_calculation)
                ),
                "calculations": calculations,
                "selected_calculation": selected_calculation,
                "upload_ready_count": _upload_ready_count(selected_calculation),
                **_step_context(request.user, latest_by_step.get(OperationStepCode.WB_API_DISCOUNT_UPLOAD)),
            },
        ],
        "result_operation": result_operation,
        "api_stage_2_notice": API_STAGE_2_NOTICE,
        **connection,
    }


def _ozon_elastic_redirect(store: StoreAccount, operation: Operation | None = None):
    url = f"{reverse('web:ozon_elastic')}?store={store.pk}"
    if operation is not None:
        url = f"{url}&operation={operation.visible_id}"
    return redirect(url)


def _handle_ozon_elastic_post(request: HttpRequest, store: StoreAccount, action: str | None):
    try:
        if action == "download_actions":
            operation = ozon_api_actions.download_ozon_actions(actor=request.user, store=store)
            return _ozon_elastic_redirect(store, operation)
        if action == "select_action":
            ozon_api_actions.select_elastic_action(
                actor=request.user,
                store=store,
                action_id=request.POST.get("action_id", ""),
            )
            messages.success(request, "Акция Эластичный бустинг выбрана.")
            return _ozon_elastic_redirect(store)
        if action == "download_active":
            operation = ozon_api_products.download_active_products(actor=request.user, store=store)
            return _ozon_elastic_redirect(store, operation)
        if action == "download_candidates":
            operation = ozon_api_products.download_candidate_products(actor=request.user, store=store)
            return _ozon_elastic_redirect(store, operation)
        if action == "download_product_data":
            operation = ozon_api_product_data.download_product_data(actor=request.user, store=store)
            return _ozon_elastic_redirect(store, operation)
        if action == "calculate":
            operation = ozon_api_calculation.calculate_elastic_result(actor=request.user, store=store)
            return _ozon_elastic_redirect(store, operation)

        calculation_id = request.POST.get("calculation_operation_id") or 0
        calculation = get_object_or_404(_ozon_api_calculations(store), pk=calculation_id)
        if action == "accept_result":
            operation = ozon_api_review.accept_elastic_result(actor=request.user, operation=calculation)
            return _ozon_elastic_redirect(store, operation)
        if action == "decline_result":
            operation = ozon_api_review.decline_elastic_result(actor=request.user, operation=calculation)
            return _ozon_elastic_redirect(store, operation)
        if action == "confirm_deactivate":
            operation = ozon_api_upload.confirm_deactivate_group(actor=request.user, operation=calculation)
            return _ozon_elastic_redirect(store, operation)
        if action == "upload":
            operation = ozon_api_upload.upload_elastic_result(
                actor=request.user,
                operation=calculation,
                add_update_confirmed=request.POST.get("add_update_confirmed") == "yes",
            )
            return _ozon_elastic_redirect(store, operation)

        messages.error(request, "Неизвестное действие.")
        return None
    except (PermissionDenied, ValidationError, OzonApiError) as exc:
        messages.error(request, _error_text(exc))
        latest_operation = (
            Operation.objects.filter(
                store=store,
                marketplace="ozon",
                module=OperationModule.OZON_API,
                mode=OperationMode.API,
                step_code__in=OZON_API_STEPS,
            )
            .order_by("-id")
            .first()
        )
        return _ozon_elastic_redirect(store, latest_operation)


def _latest_ozon_operation_by_step(store: StoreAccount | None) -> dict:
    latest_by_step = {}
    if not store:
        return latest_by_step
    for operation in (
        Operation.objects.filter(
            marketplace="ozon",
            module=OperationModule.OZON_API,
            mode=OperationMode.API,
            operation_type=OperationType.NOT_APPLICABLE,
            step_code__in=OZON_API_STEPS,
            store=store,
        )
        .order_by("-created_at", "-id")
    ):
        latest_by_step.setdefault(operation.step_code, operation)
    return latest_by_step


def _latest_accepted_or_reviewable_calculation(store: StoreAccount | None):
    if not store:
        return None
    return _ozon_api_calculations(store).first()


def _calculation_rows(operation: Operation | None) -> list[dict]:
    if not operation or not isinstance(operation.summary, dict):
        return []
    snapshot = operation.summary.get("accepted_calculation_snapshot")
    if isinstance(snapshot, dict) and snapshot.get("calculation_rows"):
        return list(snapshot.get("calculation_rows") or [])
    return list(operation.summary.get("calculation_rows") or [])


def _filter_ozon_rows(request: HttpRequest, rows: list[dict]) -> list[dict]:
    filters = {
        "planned_action": request.GET.get("planned_action", "").strip(),
        "reason_code": request.GET.get("reason_code", "").strip(),
        "source_group": request.GET.get("source_group", "").strip(),
        "upload_ready": request.GET.get("upload_ready", "").strip(),
    }
    filtered = rows
    for key in ("planned_action", "reason_code", "source_group"):
        if filters[key]:
            filtered = [row for row in filtered if str(row.get(key) or "") == filters[key]]
    if filters["upload_ready"]:
        expected = filters["upload_ready"] == "true"
        filtered = [row for row in filtered if bool(row.get("upload_ready")) == expected]
    return filtered


def _file_version_download_context(user, version_id: int | None):
    if not version_id:
        return None
    version = FileVersion.objects.select_related("file", "file__store").filter(pk=version_id).first()
    if not version:
        return None
    return {
        "version": version,
        "can_download": has_permission(user, download_permission_code(version.file), version.file.store),
    }


def _ozon_operation_summary_items(operation: Operation | None, keys: tuple[str, ...]) -> list[tuple[str, object]]:
    summary = operation.summary if operation and isinstance(operation.summary, dict) else {}
    return [(key, summary.get(key, "")) for key in keys if key in summary]


def _ozon_elastic_master_context(request: HttpRequest, stores, store: StoreAccount | None) -> dict:
    connection = _ozon_connection_context(request.user, store)
    latest_by_step = _latest_ozon_operation_by_step(store)
    actions_operation = latest_by_step.get(OperationStepCode.OZON_API_ACTIONS_DOWNLOAD)
    elastic_actions = []
    if actions_operation and isinstance(actions_operation.summary, dict):
        elastic_actions = list(actions_operation.summary.get("elastic_actions") or [])
    selected_action = ozon_api_actions.get_selected_elastic_action_basis(store) if store else None
    selected_action_id = str((selected_action or {}).get("action_id") or "")
    active_operation = latest_by_step.get(OperationStepCode.OZON_API_ELASTIC_ACTIVE_PRODUCTS_DOWNLOAD)
    candidate_operation = latest_by_step.get(OperationStepCode.OZON_API_ELASTIC_CANDIDATE_PRODUCTS_DOWNLOAD)
    product_data_operation = latest_by_step.get(OperationStepCode.OZON_API_ELASTIC_PRODUCT_DATA_DOWNLOAD)
    calculation = _latest_accepted_or_reviewable_calculation(store)
    rows = _calculation_rows(calculation)
    filtered_rows = _filter_ozon_rows(request, rows)
    groups_count = calculation.summary.get("groups_count", {}) if calculation and isinstance(calculation.summary, dict) else {}
    deactivate_count = int(groups_count.get("deactivate_from_action") or 0)
    add_update_count = int(groups_count.get("add_to_action") or 0) + int(groups_count.get("update_action_price") or 0)
    review_state = calculation.summary.get("review_state", "") if calculation and isinstance(calculation.summary, dict) else ""
    deactivate_status = (
        calculation.summary.get("deactivate_confirmation_status", "")
        if calculation and isinstance(calculation.summary, dict)
        else ""
    )
    manual_file = _file_version_download_context(
        request.user,
        calculation.summary.get("manual_upload_file_version_id") if calculation and isinstance(calculation.summary, dict) else None,
    )
    result_file = _file_version_download_context(
        request.user,
        calculation.summary.get("result_report_file_version_id") if calculation and isinstance(calculation.summary, dict) else None,
    )
    deactivate_preview = []
    if calculation and review_state in {"accepted", "review_pending_deactivate_confirmation"}:
        try:
            deactivate_preview = ozon_api_upload.deactivate_confirmation_preview(calculation)
        except ValidationError:
            deactivate_preview = []

    operation_visible_id = request.GET.get("operation", "").strip()
    result_operation = None
    if operation_visible_id and store:
        result_operation = (
            Operation.objects.filter(
                visible_id=operation_visible_id,
                store=store,
                marketplace="ozon",
                module=OperationModule.OZON_API,
                mode=OperationMode.API,
                step_code__in=OZON_API_STEPS,
            )
            .first()
        )
        if result_operation:
            _require_operation_view(request.user, result_operation)

    selected_action_ready = bool(selected_action_id)
    active_ready = bool(
        active_operation
        and active_operation.status in {ProcessStatus.COMPLETED_SUCCESS, ProcessStatus.COMPLETED_WITH_WARNINGS}
        and active_operation.summary.get("action_id") == selected_action_id
    )
    candidate_ready = bool(
        candidate_operation
        and candidate_operation.status in {ProcessStatus.COMPLETED_SUCCESS, ProcessStatus.COMPLETED_WITH_WARNINGS}
        and candidate_operation.summary.get("action_id") == selected_action_id
    )
    product_data_ready = bool(
        product_data_operation
        and product_data_operation.status in {ProcessStatus.COMPLETED_SUCCESS, ProcessStatus.COMPLETED_WITH_WARNINGS}
        and product_data_operation.summary.get("action_id") == selected_action_id
    )
    can_upload = bool(
        calculation
        and review_state == "accepted"
        and connection["connection_is_active"]
        and has_permission(request.user, "ozon.api.elastic.upload", store)
        and has_permission(request.user, "ozon.api.elastic.upload.confirm", store)
        and (not deactivate_count or deactivate_status == "confirmed")
    )
    if deactivate_count:
        can_upload = bool(can_upload and has_permission(request.user, "ozon.api.elastic.deactivate.confirm", store))

    steps = [
        {
            "number": 1,
            "code": OperationStepCode.OZON_API_ACTIONS_DOWNLOAD,
            "title": "Скачать доступные акции",
            "action": "download_actions",
            "button": "Скачать доступные акции",
            "can_run": bool(store and connection["connection_is_active"] and has_permission(request.user, "ozon.api.actions.download", store)),
            "readonly_text": "Read-only: скачивает список Ozon actions.",
            "summary_items": _ozon_operation_summary_items(actions_operation, ("actions_count", "elastic_actions_count", "ambiguous_actions_count")),
            **_step_context(request.user, actions_operation),
        },
        {
            "number": 2,
            "code": "select_action",
            "title": "Выбрать акцию",
            "action": "select_action",
            "button": "Выбрать акцию",
            "can_run": bool(store and elastic_actions and has_permission(request.user, "ozon.api.actions.download", store)),
            "readonly_text": "Доступны только approved Elastic actions из последнего snapshot.",
            "operation": actions_operation,
            "summary_items": [],
            "output_links": [],
        },
        {
            "number": 3,
            "code": OperationStepCode.OZON_API_ELASTIC_ACTIVE_PRODUCTS_DOWNLOAD,
            "title": "Скачать товары участвующие в акции",
            "action": "download_active",
            "button": "Скачать товары участвующие в акции",
            "can_run": bool(store and connection["connection_is_active"] and selected_action_ready and has_permission(request.user, "ozon.api.elastic.active_products.download", store)),
            "readonly_text": "Read-only: скачивает active products выбранной акции.",
            "summary_items": _ozon_operation_summary_items(active_operation, ("products_count", "missing_elastic_fields_count", "source_group")),
            **_step_context(request.user, active_operation),
        },
        {
            "number": 4,
            "code": OperationStepCode.OZON_API_ELASTIC_CANDIDATE_PRODUCTS_DOWNLOAD,
            "title": "Скачать товары кандидаты в акцию",
            "action": "download_candidates",
            "button": "Скачать товары кандидаты в акцию",
            "can_run": bool(store and connection["connection_is_active"] and selected_action_ready and has_permission(request.user, "ozon.api.elastic.candidates.download", store)),
            "readonly_text": "Read-only: скачивает candidate products выбранной акции.",
            "summary_items": _ozon_operation_summary_items(candidate_operation, ("products_count", "missing_elastic_fields_count", "source_group")),
            **_step_context(request.user, candidate_operation),
        },
        {
            "number": 5,
            "code": OperationStepCode.OZON_API_ELASTIC_PRODUCT_DATA_DOWNLOAD,
            "title": "Скачать данные по полученным товарам",
            "action": "download_product_data",
            "button": "Скачать данные по полученным товарам",
            "can_run": bool(store and connection["connection_is_active"] and active_ready and candidate_ready and has_permission(request.user, "ozon.api.elastic.product_data.download", store)),
            "readonly_text": "Read-only: скачивает product info/stocks для union product_id.",
            "summary_items": _ozon_operation_summary_items(product_data_operation, ("source_rows_count", "product_count", "stock_rows_count", "diagnostics_counts")),
            **_step_context(request.user, product_data_operation),
        },
        {
            "number": 6,
            "code": OperationStepCode.OZON_API_ELASTIC_CALCULATION,
            "title": "Обработать",
            "action": "calculate",
            "button": "Обработать",
            "can_run": bool(store and product_data_ready and has_permission(request.user, "ozon.api.elastic.calculate", store)),
            "readonly_text": "Расчёт не меняет Ozon; результат формирует report.",
            "summary_items": _ozon_operation_summary_items(calculation, ("rows_count", "groups_count", "review_state", "deactivate_confirmation_status")),
            **_step_context(request.user, calculation),
        },
        {
            "number": 7,
            "code": "review",
            "title": "Принять результат / Не принять результат",
            "can_run": bool(calculation and has_permission(request.user, "ozon.api.elastic.review", store)),
            "operation": calculation,
            "summary_items": [],
            "output_links": [],
        },
        {
            "number": 8,
            "code": "download_result",
            "title": "Скачать Excel результата",
            "can_run": bool(result_file and result_file["can_download"]),
            "operation": calculation,
            "summary_items": [],
            "output_links": [],
        },
        {
            "number": 9,
            "code": "download_manual",
            "title": "Скачать Excel для ручной загрузки",
            "can_run": bool(manual_file and manual_file["can_download"]),
            "operation": calculation,
            "summary_items": [],
            "output_links": [],
        },
        {
            "number": 10,
            "code": OperationStepCode.OZON_API_ELASTIC_UPLOAD,
            "title": "Загрузить в Ozon",
            "action": "upload",
            "button": "Загрузить в Ozon",
            "can_run": can_upload,
            "readonly_text": "Write: live Ozon actions activate/deactivate после confirmations и drift-check.",
            "summary_items": _ozon_operation_summary_items(latest_by_step.get(OperationStepCode.OZON_API_ELASTIC_UPLOAD), ("result_code", "success_count", "rejected_count", "write_batch_size", "min_interval_ms")),
            **_step_context(request.user, latest_by_step.get(OperationStepCode.OZON_API_ELASTIC_UPLOAD)),
        },
    ]

    return {
        "stores": stores,
        "selected_store": store,
        "steps": steps,
        "elastic_actions": elastic_actions,
        "selected_action": selected_action,
        "selected_action_id": selected_action_id,
        "calculation": calculation,
        "review_state": review_state or "not_reviewed",
        "deactivate_confirmation_status": deactivate_status,
        "groups_count": groups_count,
        "required_counters": {
            "actions downloaded": (actions_operation.summary or {}).get("actions_count", 0) if actions_operation else 0,
            "elastic actions found": len(elastic_actions),
            "selected action_id": selected_action_id,
            "active products count": (active_operation.summary or {}).get("products_count", 0) if active_operation else 0,
            "candidate products count": (candidate_operation.summary or {}).get("products_count", 0) if candidate_operation else 0,
            "product info rows count": (product_data_operation.summary or {}).get("product_count", 0) if product_data_operation else 0,
            "stock rows count": (product_data_operation.summary or {}).get("stock_rows_count", 0) if product_data_operation else 0,
            "add count": groups_count.get("add_to_action", 0),
            "update count": groups_count.get("update_action_price", 0),
            "deactivate count": groups_count.get("deactivate_from_action", 0),
            "skip candidate count": groups_count.get("skip_candidate", 0),
            "blocked/error count": groups_count.get("blocked", 0),
            "upload success count": (latest_by_step.get(OperationStepCode.OZON_API_ELASTIC_UPLOAD).summary or {}).get("success_count", 0) if latest_by_step.get(OperationStepCode.OZON_API_ELASTIC_UPLOAD) else 0,
            "upload rejected count": (latest_by_step.get(OperationStepCode.OZON_API_ELASTIC_UPLOAD).summary or {}).get("rejected_count", 0) if latest_by_step.get(OperationStepCode.OZON_API_ELASTIC_UPLOAD) else 0,
        },
        "rows_page": _paginate(request, filtered_rows, 50),
        "row_filters": {
            "planned_action": request.GET.get("planned_action", "").strip(),
            "reason_code": request.GET.get("reason_code", "").strip(),
            "source_group": request.GET.get("source_group", "").strip(),
            "upload_ready": request.GET.get("upload_ready", "").strip(),
        },
        "deactivate_preview": deactivate_preview,
        "deactivate_count": deactivate_count,
        "add_update_count": add_update_count,
        "result_file": result_file,
        "manual_file": manual_file,
        "result_operation": result_operation,
        "api_stage_2_notice": API_STAGE_2_NOTICE,
        **connection,
    }


def _excel_screen(request: HttpRequest, *, marketplace: str) -> HttpResponse:
    stores = _scenario_stores(request.user, marketplace)
    store = _selected_store(request, marketplace)
    if store is None and stores.exists():
        raise PermissionDenied("No object access for selected store/cabinet.")

    if request.method == "POST":
        action = request.POST.get("action")
        if store is None:
            messages.error(request, "Не выбран доступный магазин/кабинет.")
        elif marketplace == "wb":
            response = _handle_wb_excel_post(request, store, action)
            if response:
                return response
        else:
            response = _handle_ozon_excel_post(request, store, action)
            if response:
                return response

    parameters = wb_services.resolve_wb_parameters(store) if marketplace == "wb" and store else None
    effective_params = (
        effective_parameter_rows(store)
        if marketplace == "wb"
        and store
        and has_permission(request.user, "settings.store_params.view", store)
        else []
    )
    draft = _draft_versions(request, marketplace, store) if store else {"all": []}
    recent_files = FileVersion.objects.select_related("file", "uploaded_by").filter(
        file__store=store,
        file__scenario=(
            FileObject.Scenario.WB_DISCOUNTS_EXCEL
            if marketplace == "wb"
            else FileObject.Scenario.OZON_DISCOUNTS_EXCEL
        ),
    ).order_by("-created_at", "-id")[:20] if store else []
    result_context = _inline_operation_result_context(request, marketplace=marketplace, store=store)

    return _render(
        request,
        f"web/{marketplace}_excel.html",
        {
            "stores": stores,
            "selected_store": store,
            "parameters": parameters,
            "effective_params": effective_params,
            "recent_files": recent_files,
            "draft": draft,
            "can_upload": store and has_permission(request.user, f"{marketplace}_discounts_excel.upload_input", store),
            "can_check": store and has_permission(request.user, f"{marketplace}_discounts_excel.run_check", store),
            "can_process": store and has_permission(request.user, f"{marketplace}_discounts_excel.run_process", store),
            "can_edit_store_params": marketplace == "wb" and store and has_permission(request.user, "settings.store_params.edit", store),
            **result_context,
        },
        section="marketplaces",
    )


def _inline_operation_result_context(
    request: HttpRequest,
    *,
    marketplace: str,
    store: StoreAccount | None,
) -> dict:
    visible_id = request.GET.get("operation", "").strip()
    if not visible_id or store is None:
        return {"result_operation": None}
    operation = (
        Operation.objects.select_related("store", "initiator_user", "check_basis_operation")
        .filter(visible_id=visible_id, marketplace=marketplace, store=store)
        .first()
    )
    if operation is None:
        return {"result_operation": None}
    _require_operation_view(request.user, operation)
    can_download_output = has_permission(
        request.user,
        f"{operation.marketplace}_discounts_excel.download_output",
        operation.store,
    )
    can_download_detail = has_permission(
        request.user,
        f"{operation.marketplace}_discounts_excel.download_detail_report",
        operation.store,
    )
    return {
        "result_operation": operation,
        "result_summary_items": _summary_items(operation.summary),
        "result_output_links": operation.output_files.select_related("file_version", "file_version__file"),
        "result_can_download_output": can_download_output,
        "result_can_download_detail": can_download_detail,
    }


def _excel_redirect(marketplace: str, store: StoreAccount, operation: Operation | None = None):
    route = "web:wb_excel" if marketplace == "wb" else "web:ozon_excel"
    url = f"{reverse(route)}?store={store.pk}"
    if operation is not None:
        url = f"{url}&operation={operation.visible_id}"
    return redirect(url)


def _handle_wb_excel_post(request: HttpRequest, store: StoreAccount, action: str | None):
    if action not in {"upload_price", "upload_promo", "delete_file", "save_wb_params", "check", "process"}:
        messages.error(request, "Неизвестное действие.")
        return None
    try:
        if action == "save_wb_params":
            clear_codes = set(request.POST.getlist("clear"))
            values = {code: request.POST.get(code, "") for code in WB_PARAMETER_CODES}
            changed = save_wb_store_parameters(request.user, store, values, clear_codes)
            messages.success(request, f"Сохранено параметров WB: {len(changed)}.")
            return _excel_redirect("wb", store)

        if action in {"upload_price", "upload_promo", "delete_file"}:
            if not has_permission(request.user, "wb_discounts_excel.upload_input", store):
                raise PermissionDenied("No permission to upload WB input files.")
            if action == "delete_file":
                _delete_draft_version(
                    request,
                    marketplace="wb",
                    store=store,
                    version_id=int(request.POST.get("version_id") or 0),
                )
                messages.success(request, "Файл удалён из чернового контекста.")
                return redirect(f"{reverse('web:wb_excel')}?store={store.pk}")
            if action == "upload_price":
                price_file = request.FILES.get("price_file")
                if price_file is None:
                    messages.error(request, "Выберите файл цен WB.")
                    return None
                _replace_single_draft_file(
                    request,
                    marketplace="wb",
                    store=store,
                    slot="price",
                    uploaded_file=price_file,
                    logical_name="wb_price",
                )
                messages.success(request, "Файл цен загружен в черновой контекст.")
                return redirect(f"{reverse('web:wb_excel')}?store={store.pk}")
            promo_files = request.FILES.getlist("promo_files")
            if not promo_files:
                messages.error(request, "Выберите минимум один файл акций WB.")
                return None
            data = _draft_data(request, "wb", store)
            for uploaded_file in promo_files:
                version = _create_input_version(
                    request,
                    store,
                    uploaded_file,
                    FileObject.Scenario.WB_DISCOUNTS_EXCEL,
                    "wb_promo",
                )
                _audit_input_version_upload(request, store=store, version=version)
                data.setdefault("promo", []).append(version.pk)
            _save_draft_data(request, "wb", store, data)
            messages.success(request, "Файлы акций добавлены в черновой контекст.")
            return redirect(f"{reverse('web:wb_excel')}?store={store.pk}")

        if not has_permission(request.user, f"wb_discounts_excel.run_{action}", store):
            raise PermissionDenied("No permission to run WB action.")
        draft = _draft_versions(request, "wb", store)
        price_version = draft["price"]
        promo_versions = draft["promo"]
        if price_version is None or not promo_versions:
            messages.error(request, "Для WB нужен один файл цен и минимум один файл акций в черновом контексте.")
            return None
        if action == "check":
            operation = wb_services.run_wb_check(
                store=store,
                initiator_user=request.user,
                price_version=price_version,
                promo_versions=promo_versions,
                enforce_permissions=True,
            )
            return _excel_redirect("wb", store, operation)
        result = wb_services.press_wb_process(
            store=store,
            initiator_user=request.user,
            price_version=price_version,
            promo_versions=promo_versions,
            enforce_permissions=True,
        )
        _save_draft_data(request, "wb", store, {"price": None, "promo": [], "input": None})
        return _excel_redirect("wb", store, result.process_operation)
    except (PermissionDenied, ValidationError) as exc:
        messages.error(request, _error_text(exc))
        return None


def _handle_ozon_excel_post(request: HttpRequest, store: StoreAccount, action: str | None):
    if action not in {"upload_input", "delete_file", "check", "process"}:
        messages.error(request, "Неизвестное действие.")
        return None
    try:
        if action in {"upload_input", "delete_file"}:
            if not has_permission(request.user, "ozon_discounts_excel.upload_input", store):
                raise PermissionDenied("No permission to upload Ozon input files.")
            if action == "delete_file":
                _delete_draft_version(
                    request,
                    marketplace="ozon",
                    store=store,
                    version_id=int(request.POST.get("version_id") or 0),
                )
                messages.success(request, "Файл удалён из чернового контекста.")
                return redirect(f"{reverse('web:ozon_excel')}?store={store.pk}")
            input_file = request.FILES.get("input_file")
            if input_file is None:
                messages.error(request, "Для Ozon нужен ровно один .xlsx файл.")
                return None
            _replace_single_draft_file(
                request,
                marketplace="ozon",
                store=store,
                slot="input",
                uploaded_file=input_file,
                logical_name="ozon_input",
            )
            messages.success(request, "Файл Ozon загружен в черновой контекст.")
            return redirect(f"{reverse('web:ozon_excel')}?store={store.pk}")

        if not has_permission(request.user, f"ozon_discounts_excel.run_{action}", store):
            raise PermissionDenied("No permission to run Ozon action.")
        input_version = _draft_versions(request, "ozon", store)["input"]
        if input_version is None:
            messages.error(request, "Для Ozon нужен один файл в черновом контексте.")
            return None
        if action == "check":
            operation = ozon_services.run_ozon_check(
                store=store,
                initiator_user=request.user,
                input_versions=[input_version],
                enforce_permissions=True,
            )
            return _excel_redirect("ozon", store, operation)
        result = ozon_services.press_ozon_process(
            store=store,
            initiator_user=request.user,
            input_versions=[input_version],
            enforce_permissions=True,
        )
        _save_draft_data(request, "ozon", store, {"price": None, "promo": [], "input": None})
        return _excel_redirect("ozon", store, result.process_operation)
    except (PermissionDenied, ValidationError) as exc:
        messages.error(request, _error_text(exc))
        return None


def _create_input_version(
    request,
    store,
    uploaded_file,
    scenario: str,
    logical_name: str,
    *,
    file_object: FileObject | None = None,
) -> FileVersion:
    from apps.files.services import create_file_version

    return create_file_version(
        store=store,
        uploaded_by=request.user,
        uploaded_file=uploaded_file,
        scenario=scenario,
        kind=FileObject.Kind.INPUT,
        logical_name=logical_name,
        file_object=file_object,
        content_type=getattr(uploaded_file, "content_type", "") or "",
    )


def _error_text(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        if hasattr(exc, "messages"):
            return " ".join(str(message) for message in exc.messages)
    return str(exc)


@login_required
def operation_list(request: HttpRequest) -> HttpResponse:
    operations = _visible_operations_queryset(request.user)
    search = request.GET.get("q", "").strip()
    marketplace = request.GET.get("marketplace", "").strip()
    mode = request.GET.get("mode", "").strip()
    operation_type = request.GET.get("type", "").strip()
    step_code = request.GET.get("step_code", "").strip()
    status = request.GET.get("status", "").strip()
    store_id = request.GET.get("store", "").strip()
    if search:
        operations = operations.filter(visible_id__icontains=search)
    if marketplace:
        operations = operations.filter(marketplace=marketplace)
    if mode:
        operations = operations.filter(mode=mode)
    if operation_type:
        operations = operations.filter(mode=OperationMode.EXCEL, operation_type=operation_type)
    if step_code:
        operations = operations.filter(mode=OperationMode.API, step_code=step_code)
    if status:
        operations = operations.filter(status=status)
    if store_id:
        operations = operations.filter(store_id=store_id)
    return _render(
        request,
        "web/operation_list.html",
        {
            "page": _paginate(request, _decorate_operations(operations)),
            "stores": visible_stores_queryset(request.user),
            "filters": {
                "q": search,
                "marketplace": marketplace,
                "mode": mode,
                "type": operation_type,
                "step_code": step_code,
                "status": status,
                "store": store_id,
            },
            "wb_api_step_labels": WB_API_STEP_LABELS,
        },
        section="operations",
    )


@login_required
def operation_card(request: HttpRequest, visible_id: str) -> HttpResponse:
    operation = get_object_or_404(
        Operation.objects.select_related("store", "initiator_user", "check_basis_operation"),
        visible_id=visible_id,
    )
    _require_operation_view(request.user, operation)
    details = operation.detail_rows.all().order_by("row_no", "id")
    reason = request.GET.get("reason", "").strip()
    row_status = request.GET.get("row_status", "").strip()
    q = request.GET.get("q", "").strip()
    if reason:
        details = details.filter(reason_code=reason)
    if row_status:
        details = details.filter(row_status=row_status)
    if q:
        details = details.filter(
            Q(product_ref__icontains=q) | Q(message__icontains=q) | Q(problem_field__icontains=q)
        )
    output_links = operation.output_files.select_related("file_version", "file_version__file")
    is_api_operation = operation.mode == OperationMode.API and operation.marketplace in {"wb", "ozon"}
    if is_api_operation:
        view_permission = "wb.api.operation.view" if operation.marketplace == "wb" else "ozon.api.operation.view"
        default_download_permission = (
            "wb.api.discounts.result.download"
            if operation.marketplace == "wb"
            else "ozon.api.elastic.files.download"
        )
        can_view_details = has_permission(request.user, view_permission, operation.store)
        can_download_output = has_permission(request.user, default_download_permission, operation.store)
        can_download_detail = can_download_output
        for link in output_links:
            link.can_download = _can_download_link(request.user, link)
    else:
        can_view_details = has_permission(
            request.user,
            f"{operation.marketplace}_discounts_excel.view_details",
            operation.store,
        )
        can_download_output = has_permission(
            request.user,
            f"{operation.marketplace}_discounts_excel.download_output",
            operation.store,
        )
        can_download_detail = has_permission(
            request.user,
            f"{operation.marketplace}_discounts_excel.download_detail_report",
            operation.store,
        )
        for link in output_links:
            link.can_download = (
                can_download_detail
                if link.output_kind == OutputKind.DETAIL_REPORT
                else can_download_output
            )
    can_confirm_warnings = (
        operation.operation_type == OperationType.CHECK
        and operation.mode == OperationMode.EXCEL
        and operation.warning_count
        and operation.error_count == 0
        and has_permission(
            request.user,
            f"{operation.marketplace}_discounts_excel.confirm_warnings",
            operation.store,
        )
        and has_permission(
            request.user,
            f"{operation.marketplace}_discounts_excel.run_process",
            operation.store,
        )
    )
    return _render(
        request,
        "web/operation_card.html",
        {
            "operation": operation,
            "classifier_label": _operation_classifier_label(operation),
            "is_api_operation": is_api_operation,
            "summary_items": _summary_items(operation.summary),
            "detail_page": _paginate(request, details, 50) if can_view_details else None,
            "input_files": operation.input_files.select_related("file_version", "file_version__file"),
            "output_links": output_links,
            "parameter_snapshots": operation.parameter_snapshots.all(),
            "warning_confirmations": operation.warning_confirmations_as_process.select_related("user"),
            "audit_records": operation.audit_records.all()[:10],
            "techlog_records": operation.techlog_records.all()[:10],
            "can_view_details": can_view_details,
            "can_download_output": can_download_output,
            "can_download_detail": can_download_detail,
            "can_confirm_warnings": can_confirm_warnings,
            "filters": {"reason": reason, "row_status": row_status, "q": q},
        },
        section="operations",
    )


@login_required
def operation_result(request: HttpRequest, visible_id: str) -> HttpResponse:
    return operation_card(request, visible_id)


@login_required
def warning_confirmation(request: HttpRequest, visible_id: str) -> HttpResponse:
    check_operation = get_object_or_404(Operation, visible_id=visible_id, operation_type=OperationType.CHECK)
    _require_operation_view(request.user, check_operation)
    if not has_permission(
        request.user,
        f"{check_operation.marketplace}_discounts_excel.confirm_warnings",
        check_operation.store,
    ) or not has_permission(
        request.user,
        f"{check_operation.marketplace}_discounts_excel.run_process",
        check_operation.store,
    ):
        raise PermissionDenied("No permission to confirm warnings/process.")

    warnings = check_operation.detail_rows.filter(
        message_level__in=[MessageLevel.WARNING_CONFIRMABLE, MessageLevel.WARNING_INFO]
    )
    if request.method == "POST":
        if request.POST.get("confirm") != "yes":
            messages.error(request, "Для обработки требуется явное подтверждение.")
        else:
            warning_codes = list(warnings.values_list("reason_code", flat=True).distinct())
            try:
                if check_operation.marketplace == "wb":
                    price_version, promo_versions = _wb_versions_from_operation(check_operation)
                    result = wb_services.press_wb_process(
                        store=check_operation.store,
                        initiator_user=request.user,
                        price_version=price_version,
                        promo_versions=promo_versions,
                        confirmed_warning_codes=warning_codes,
                        enforce_permissions=True,
                    )
                else:
                    result = ozon_services.press_ozon_process(
                        store=check_operation.store,
                        initiator_user=request.user,
                        input_versions=_ozon_versions_from_operation(check_operation),
                        confirmed_warning_codes=warning_codes,
                        enforce_permissions=True,
                    )
                return redirect("web:operation_result", visible_id=result.process_operation.visible_id)
            except (PermissionDenied, ValidationError) as exc:
                messages.error(request, _error_text(exc))
    return _render(
        request,
        "web/warning_confirmation.html",
        {"operation": check_operation, "warnings": warnings, "page": _paginate(request, warnings, 50)},
        section="marketplaces",
    )


def _wb_versions_from_operation(operation: Operation):
    links = operation.input_files.select_related("file_version").order_by("role_in_operation", "ordinal_no")
    price = None
    promo = []
    for link in links:
        if link.role_in_operation == wb_services.PRICE_ROLE:
            price = link.file_version
        elif link.role_in_operation == wb_services.PROMO_ROLE:
            promo.append(link.file_version)
    return price, promo


def _ozon_versions_from_operation(operation: Operation):
    return [
        link.file_version
        for link in operation.input_files.select_related("file_version").order_by("ordinal_no")
        if link.role_in_operation == ozon_services.INPUT_ROLE
    ]


@login_required
def download_file(request: HttpRequest, version_id: int) -> HttpResponse:
    version = get_object_or_404(FileVersion.objects.select_related("file", "file__store"), pk=version_id)
    handle = open_file_version_for_download(request.user, version)
    return FileResponse(handle, as_attachment=True, filename=version.original_name)


@login_required
def reference_index(request: HttpRequest) -> HttpResponse:
    can_stores = has_section_access(request.user, "stores.view") and _has_permission_in_scope(
        request.user,
        "stores.list.view",
    )
    can_products = has_section_access(request.user, "products.view")
    if not can_stores and not can_products:
        raise PermissionDenied("No section access to references.")
    return _render(
        request,
        "web/reference_index.html",
        {"can_stores": can_stores, "can_products": can_products},
        section="references",
    )


@login_required
def product_list(request: HttpRequest) -> HttpResponse:
    if not has_section_access(request.user, "products.view"):
        raise PermissionDenied("No section access to products.")
    products = products_visible_to(request.user)
    q = request.GET.get("q", "").strip()
    marketplace = request.GET.get("marketplace", "").strip()
    store_id = request.GET.get("store", "").strip()
    status = request.GET.get("status", "").strip()
    if q:
        products = products.filter(
            Q(sku__icontains=q)
            | Q(barcode__icontains=q)
            | Q(title__icontains=q)
        )
    if marketplace:
        products = products.filter(marketplace=marketplace)
    if store_id:
        products = products.filter(store_id=store_id)
    if status:
        products = products.filter(status=status)
    return _render(
        request,
        "web/product_list.html",
        {
            "page": _paginate(request, products),
            "stores": visible_stores_queryset(request.user),
            "filters": {"q": q, "marketplace": marketplace, "store": store_id, "status": status},
        },
        section="references",
    )


@login_required
def product_card(request: HttpRequest, pk: int) -> HttpResponse:
    product = get_object_or_404(products_visible_to(request.user), pk=pk)
    operations = _visible_operations_queryset(request.user).filter(
        marketplace=product.marketplace,
        store=product.store,
        detail_rows__product_ref=product.sku,
    ).distinct()
    files = FileVersion.objects.select_related("file", "uploaded_by").filter(
        Q(product_history__product=product) | Q(operation_input_links__operation__in=operations),
    ).distinct()[:50]
    return _render(
        request,
        "web/product_card.html",
        {
            "product": product,
            "history": product.history.select_related("operation", "file_version")[:50],
            "operations": operations[:50],
            "files": files,
        },
        section="references",
    )


@login_required
def settings_index(request: HttpRequest) -> HttpResponse:
    stores = visible_stores_queryset(request.user).filter(marketplace=StoreAccount.Marketplace.WB)
    selected_store_id = request.POST.get("store") or request.GET.get("store")
    selected_store = stores.filter(pk=selected_store_id).first() if selected_store_id else stores.first()
    if request.method == "POST" and selected_store:
        clear_codes = set(request.POST.getlist("clear"))
        values = {code: request.POST.get(code, "") for code in WB_PARAMETER_CODES}
        try:
            changed = save_wb_store_parameters(request.user, selected_store, values, clear_codes)
            messages.success(request, f"Сохранено параметров: {len(changed)}.")
            return redirect(f"{reverse('web:settings_index')}?store={selected_store.pk}")
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, _error_text(exc))
    system_params = SystemParameterValue.objects.all().order_by("parameter_code", "-active_from")
    store_params = StoreParameterValue.objects.select_related("store", "changed_by").filter(
        store_id__in=_visible_store_ids(request.user),
        is_active=True,
    )
    if not has_permission(request.user, "settings.system_params.view"):
        system_params = system_params.none()
    visible_store_param_ids = [
        item.pk
        for item in store_params
        if has_permission(request.user, "settings.store_params.view", item.store)
    ]
    return _render(
        request,
        "web/settings_index.html",
        {
            "system_params": system_params[:50],
            "store_params": StoreParameterValue.objects.select_related("store", "changed_by").filter(
                pk__in=visible_store_param_ids,
            )[:50],
            "stores": stores,
            "selected_store": selected_store,
            "effective_params": (
                effective_parameter_rows(selected_store)
                if selected_store and has_permission(request.user, "settings.store_params.view", selected_store)
                else []
            ),
            "can_edit_store_params": selected_store and has_permission(request.user, "settings.store_params.edit", selected_store),
        },
        section="settings",
    )


@login_required
def parameter_history(request: HttpRequest) -> HttpResponse:
    records = StoreParameterChangeHistory.objects.select_related("store", "changed_by", "audit_record").filter(
        store_id__in=_visible_store_ids(request.user),
    )
    visible_ids = [
        item.pk
        for item in records
        if has_permission(request.user, "settings.param_history.view", item.store)
    ]
    records = StoreParameterChangeHistory.objects.select_related("store", "changed_by", "audit_record").filter(pk__in=visible_ids)
    store_id = request.GET.get("store", "").strip()
    parameter = request.GET.get("parameter", "").strip()
    if store_id:
        records = records.filter(store_id=store_id)
    if parameter:
        records = records.filter(parameter_code=parameter)
    return _render(
        request,
        "web/parameter_history.html",
        {
            "page": _paginate(request, records),
            "stores": visible_stores_queryset(request.user).filter(marketplace=StoreAccount.Marketplace.WB),
            "parameter_codes": sorted(WB_PARAMETER_CODES),
            "filters": {"store": store_id, "parameter": parameter},
        },
        section="settings",
    )


@login_required
def admin_index(request: HttpRequest) -> HttpResponse:
    links = {
        "users": has_section_access(request.user, "users.view") and _has_permission_in_scope(request.user, "users.list.view"),
        "roles": has_section_access(request.user, "roles.view") and has_permission(request.user, "roles.list.view"),
        "permissions": has_section_access(request.user, "permissions.view") and (
            _has_permission_in_scope(request.user, "section_access.view") or has_permission(request.user, "roles.list.view")
        ),
        "store_access": has_section_access(request.user, "store_access.view") and (
            _has_permission_in_scope(request.user, "stores.access.assign")
            or _has_permission_in_scope(request.user, "section_access.view")
        ),
    }
    if not any(links.values()):
        raise PermissionDenied("No section access to administration.")
    return _render(request, "web/admin_index.html", {"links": links}, section="admin")


@login_required
def user_list(request: HttpRequest) -> HttpResponse:
    if not _has_permission_in_scope(request.user, "users.list.view"):
        raise PermissionDenied("No permission to view users.")
    if request.method == "POST":
        if not _has_permission_in_scope(request.user, "users.create"):
            raise PermissionDenied("No permission to create users.")
        role = Role.objects.filter(pk=request.POST.get("primary_role")).first()
        if role and not _has_permission_in_scope(request.user, "permissions.assign"):
            raise PermissionDenied("No permission to assign primary role.")
        if role and role.is_owner_role and not is_owner(request.user):
            raise PermissionDenied("Only owner can create owner users.")
        user = get_user_model().objects.create_user(
            login=request.POST.get("login", "").strip(),
            password=request.POST.get("password") or None,
            display_name=request.POST.get("display_name", "").strip(),
            primary_role=role,
        )
        create_audit_record(
            action_code=AuditActionCode.USER_CREATED,
            entity_type="User",
            entity_id=user.visible_id,
            user=request.user,
            safe_message=f"User created: {user.visible_id}",
            source_context=AuditSourceContext.UI,
        )
        messages.success(request, "Пользователь создан.")
        return redirect("web:user_card", visible_id=user.visible_id)
    users = _user_queryset_for_permission(request.user, "users.list.view")
    q = request.GET.get("q", "").strip()
    if q:
        users = users.filter(Q(login__icontains=q) | Q(display_name__icontains=q) | Q(visible_id__icontains=q))
    return _render(
        request,
        "web/user_list.html",
        {
            "page": _paginate(request, users),
            "q": q,
            "roles": Role.objects.exclude(code="owner") if not is_owner(request.user) else Role.objects.all(),
            "can_create": _has_permission_in_scope(request.user, "users.create"),
        },
        section="admin",
    )


@login_required
def user_card(request: HttpRequest, visible_id: str) -> HttpResponse:
    user = get_object_or_404(get_user_model().objects.select_related("primary_role"), visible_id=visible_id)
    if not can_manage_user_action(request.user, user, "users.card.view"):
        raise PermissionDenied("No permission to view user card.")
    if request.method == "POST":
        action = request.POST.get("action", "")
        try:
            if action == "save_user":
                if not can_manage_user_action(request.user, user, "users.edit"):
                    raise PermissionDenied("No permission to edit this user.")
                before = {"display_name": user.display_name, "primary_role": user.primary_role_id}
                role = Role.objects.filter(pk=request.POST.get("primary_role")).first()
                if role and role.is_owner_role and not is_owner(request.user):
                    raise PermissionDenied("Only owner can assign owner role.")
                if before["primary_role"] != (role.pk if role else None) and not can_manage_user_action(
                    request.user,
                    user,
                    "permissions.assign",
                ):
                    raise PermissionDenied("No permission to assign primary role.")
                user.display_name = request.POST.get("display_name", "").strip()
                user.primary_role = role
                user.save(update_fields=["display_name", "primary_role", "updated_at"])
                if before["display_name"] != user.display_name:
                    record_user_change(request.user, user, "display_name", before["display_name"], user.display_name, "ui")
                if before["primary_role"] != user.primary_role_id:
                    record_user_change(request.user, user, "primary_role", str(before["primary_role"]), str(user.primary_role_id), "ui")
                create_audit_record(
                    action_code=AuditActionCode.USER_CHANGED,
                    entity_type="User",
                    entity_id=user.visible_id,
                    user=request.user,
                    safe_message=f"User changed: {user.visible_id}",
                    before_snapshot=before,
                    after_snapshot={"display_name": user.display_name, "primary_role": user.primary_role_id},
                    source_context=AuditSourceContext.UI,
                )
            elif action in {"block", "unblock", "archive"}:
                if action == "archive" and not can_manage_user_action(request.user, user, "users.archive"):
                    raise PermissionDenied("No permission to archive users.")
                if action != "archive" and not can_manage_user_action(request.user, user, "users.status.change"):
                    raise PermissionDenied("No permission to change user status.")
                new_status = {
                    "block": get_user_model().Status.BLOCKED,
                    "unblock": get_user_model().Status.ACTIVE,
                    "archive": get_user_model().Status.ARCHIVED,
                }[action]
                change_user_status(
                    request.user,
                    user,
                    new_status,
                    reason=request.POST.get("reason", ""),
                    source="ui",
                    permission_code="users.archive" if action == "archive" else "users.status.change",
                )
                create_audit_record(
                    action_code=(
                        AuditActionCode.USER_ARCHIVED
                        if action == "archive"
                        else AuditActionCode.USER_BLOCKED_OR_UNBLOCKED
                    ),
                    entity_type="User",
                    entity_id=user.visible_id,
                    user=request.user,
                    safe_message=f"User status changed: {user.visible_id} -> {new_status}",
                    source_context=AuditSourceContext.UI,
                )
            elif action == "permission_override":
                if not can_manage_user_action(request.user, user, "permissions.assign"):
                    raise PermissionDenied("No permission to assign permissions.")
                permission = get_object_or_404(Permission, code=request.POST.get("permission"))
                store = StoreAccount.objects.filter(pk=request.POST.get("store") or None).first()
                if not has_permission(request.user, "permissions.assign", store):
                    raise PermissionDenied("No permission to assign permissions.")
                if store and not has_store_access(request.user, store):
                    raise PermissionDenied("No object access to selected store.")
                effect = request.POST.get("effect")
                override, _ = UserPermissionOverride.objects.update_or_create(
                    user=user,
                    permission=permission,
                    store=store,
                    effect=effect,
                    defaults={"is_active": request.POST.get("is_active", "on") == "on"},
                )
                create_audit_record(
                    action_code=AuditActionCode.PERMISSION_OVERRIDE_CHANGED,
                    entity_type="UserPermissionOverride",
                    entity_id=override.pk,
                    user=request.user,
                    store=store,
                    safe_message=f"Permission override changed for {user.visible_id}",
                    source_context=AuditSourceContext.UI,
                )
            elif action == "store_access":
                store = get_object_or_404(StoreAccount, pk=request.POST.get("store"))
                if not has_permission(request.user, "stores.access.assign", store):
                    raise PermissionDenied("No permission to assign store access.")
                if not has_store_access(request.user, store):
                    raise PermissionDenied("No object access to selected store.")
                access, _ = StoreAccess.objects.update_or_create(
                    user=user,
                    store=store,
                    effect=request.POST.get("effect", AccessEffect.ALLOW),
                    defaults={
                        "access_level": request.POST.get("access_level", StoreAccess.AccessLevel.VIEW),
                        "is_active": request.POST.get("is_active", "on") == "on",
                    },
                )
                create_audit_record(
                    action_code=AuditActionCode.STORE_ACCESS_CHANGED,
                    entity_type="StoreAccess",
                    entity_id=access.pk,
                    user=request.user,
                    store=store,
                    safe_message=f"Store access changed for {user.visible_id}",
                    source_context=AuditSourceContext.UI,
                )
            messages.success(request, "Изменения сохранены.")
            return redirect("web:user_card", visible_id=user.visible_id)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, _error_text(exc))
    return _render(
        request,
        "web/user_card.html",
        {
            "target_user": user,
            "roles": user.roles.all(),
            "store_access": user.store_access.select_related("store"),
            "overrides": user.permission_overrides.select_related("permission", "store"),
            "block_history": user.block_history.select_related("changed_by")[:20],
            "change_history": user.change_history.select_related("changed_by")[:20],
            "all_roles": Role.objects.exclude(code="owner") if not is_owner(request.user) else Role.objects.all(),
            "permissions_all": Permission.objects.all(),
            "stores": visible_stores_queryset(request.user),
            "can_edit_user": can_manage_user_action(request.user, user, "users.edit"),
            "can_change_status": can_manage_user_action(request.user, user, "users.status.change"),
            "can_archive": can_manage_user_action(request.user, user, "users.archive"),
            "can_assign_permissions": can_manage_user_action(request.user, user, "permissions.assign"),
            "can_assign_store_access": _has_permission_in_scope(request.user, "stores.access.assign"),
        },
        section="admin",
    )


@login_required
def role_list(request: HttpRequest) -> HttpResponse:
    if not has_permission(request.user, "roles.list.view"):
        raise PermissionDenied("No permission to view roles.")
    if request.method == "POST":
        if not has_permission(request.user, "roles.edit"):
            raise PermissionDenied("No permission to create roles.")
        role = Role.objects.create(
            code=request.POST.get("code", "").strip(),
            name=request.POST.get("name", "").strip(),
            status=Role.Status.ACTIVE,
            is_system=False,
        )
        create_audit_record(
            action_code=AuditActionCode.ROLE_CREATED,
            entity_type="Role",
            entity_id=role.code,
            user=request.user,
            safe_message=f"Role created: {role.code}",
            source_context=AuditSourceContext.UI,
        )
        messages.success(request, "Роль создана.")
        return redirect("web:role_card", code=role.code)
    roles = Role.objects.all().order_by("code")
    return _render(
        request,
        "web/role_list.html",
        {"page": _paginate(request, roles), "can_edit_roles": has_permission(request.user, "roles.edit")},
        section="admin",
    )


@login_required
def role_card(request: HttpRequest, code: str) -> HttpResponse:
    role = get_object_or_404(Role, code=code)
    if not has_permission(request.user, "roles.card.view"):
        raise PermissionDenied("No permission to view role card.")
    can_edit = has_permission(request.user, "roles.edit") and not role.is_system and not role.is_owner_role
    if request.method == "POST":
        if not can_edit:
            raise PermissionDenied("System/owner roles are protected or edit right is missing.")
        action = request.POST.get("action", "")
        try:
            before = {"name": role.name, "status": role.status}
            if action == "save_role":
                role.name = request.POST.get("name", "").strip()
                role.status = request.POST.get("status", Role.Status.ACTIVE)
                role.save(update_fields=["name", "status"])
            elif action == "set_permissions":
                permission_ids = request.POST.getlist("permissions")
                section_ids = request.POST.getlist("sections")
                RolePermission.objects.filter(role=role).delete()
                RoleSectionAccess.objects.filter(role=role).delete()
                for permission in Permission.objects.filter(code__in=permission_ids):
                    RolePermission.objects.create(role=role, permission=permission)
                for section_access in SectionAccess.objects.filter(code__in=section_ids):
                    RoleSectionAccess.objects.create(role=role, section_access=section_access)
            elif action in {"deactivate", "archive"}:
                role.status = Role.Status.ARCHIVED if action == "archive" else Role.Status.INACTIVE
                role.save(update_fields=["status"])
            create_audit_record(
                action_code=(
                    AuditActionCode.ROLE_ARCHIVED_OR_DEACTIVATED
                    if action in {"deactivate", "archive"}
                    else AuditActionCode.ROLE_CHANGED
                ),
                entity_type="Role",
                entity_id=role.code,
                user=request.user,
                safe_message=f"Role changed: {role.code}",
                before_snapshot=before,
                after_snapshot={"name": role.name, "status": role.status},
                source_context=AuditSourceContext.UI,
            )
            messages.success(request, "Роль сохранена.")
            return redirect("web:role_card", code=role.code)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, _error_text(exc))
    return _render(
        request,
        "web/role_card.html",
        {
            "role": role,
            "permissions": Permission.objects.filter(role_permissions__role=role).order_by("code"),
            "sections": SectionAccess.objects.filter(role_sections__role=role).order_by("section", "code"),
            "users": get_user_model().objects.filter(Q(primary_role=role) | Q(roles=role)).distinct()[:50],
            "all_permissions": Permission.objects.all(),
            "all_sections": SectionAccess.objects.all(),
            "can_edit": can_edit,
        },
        section="admin",
    )


@login_required
def permission_list(request: HttpRequest) -> HttpResponse:
    if not _has_permission_in_scope(request.user, "section_access.view") and not has_permission(request.user, "roles.list.view"):
        raise PermissionDenied("No permission to view access dictionaries.")
    q = request.GET.get("q", "").strip()
    permissions = Permission.objects.all()
    if q:
        permissions = permissions.filter(Q(code__icontains=q) | Q(name__icontains=q))
    return _render(
        request,
        "web/permission_list.html",
        {"page": _paginate(request, permissions), "q": q, "sections": SectionAccess.objects.all()},
        section="admin",
    )


@login_required
def store_access_list(request: HttpRequest) -> HttpResponse:
    if not _has_permission_in_scope(request.user, "stores.access.assign") and not _has_permission_in_scope(request.user, "section_access.view"):
        raise PermissionDenied("No permission to view store access assignments.")
    if request.method == "POST":
        target = get_object_or_404(get_user_model(), pk=request.POST.get("user"))
        store = get_object_or_404(StoreAccount, pk=request.POST.get("store"))
        if not has_permission(request.user, "stores.access.assign", store):
            raise PermissionDenied("No permission to assign store access.")
        if target.is_owner and not is_owner(request.user):
            raise PermissionDenied("Owner store access is protected.")
        if not has_store_access(request.user, store):
            raise PermissionDenied("No object access to selected store.")
        access, _ = StoreAccess.objects.update_or_create(
            user=target,
            store=store,
            effect=request.POST.get("effect", AccessEffect.ALLOW),
            defaults={
                "access_level": request.POST.get("access_level", StoreAccess.AccessLevel.VIEW),
                "is_active": request.POST.get("is_active", "on") == "on",
            },
        )
        create_audit_record(
            action_code=AuditActionCode.STORE_ACCESS_CHANGED,
            entity_type="StoreAccess",
            entity_id=access.pk,
            user=request.user,
            store=store,
            safe_message=f"Store access changed for {target.visible_id}",
            source_context=AuditSourceContext.UI,
        )
        messages.success(request, "Store access сохранён.")
        return redirect("web:store_access_list")
    assignments = StoreAccess.objects.select_related("user", "store").filter(
        store_id__in=_visible_store_ids(request.user),
    ).order_by("store__name", "user__login", "id")
    return _render(
        request,
        "web/store_access_list.html",
        {
            "page": _paginate(request, assignments),
            "permission_overrides": UserPermissionOverride.objects.select_related("user", "permission", "store").filter(
                Q(store__isnull=True) | Q(store_id__in=_visible_store_ids(request.user))
            )[:100],
            "users": get_user_model().objects.all(),
            "stores": visible_stores_queryset(request.user),
            "can_assign": _has_permission_in_scope(request.user, "stores.access.assign"),
        },
        section="admin",
    )


@login_required
def logs_index(request: HttpRequest) -> HttpResponse:
    links = {
        "audit": has_section_access(request.user, "audit.view") and _has_permission_in_scope(request.user, "audit.list.view"),
        "techlog": has_section_access(request.user, "techlog.view") and _has_permission_in_scope(request.user, "techlog.list.view"),
        "notifications": has_section_access(request.user, "techlog.view") or has_section_access(request.user, "audit.view"),
    }
    if not any(links.values()):
        raise PermissionDenied("No section access to logs.")
    return _render(request, "web/logs_index.html", {"links": links}, section="logs")


def _has_full_log_scope(user) -> bool:
    return has_permission(user, "logs.scope.full")


def _visible_audit_queryset(user):
    return audit_records_visible_to(user, permission_code="audit.list.view")


def _visible_techlog_queryset(user):
    queryset = TechLogRecord.objects.select_related("user", "store", "operation")
    if not _has_permission_in_scope(user, "techlog.list.view"):
        return TechLogRecord.objects.none()
    if _has_full_log_scope(user) and has_permission(user, "techlog.list.view"):
        return queryset
    store_ids = list(
        store.pk
        for store in visible_stores_queryset(user)
        if has_permission(user, "techlog.list.view", store)
        and has_permission(user, "logs.scope.limited", store)
    )
    if not store_ids:
        return queryset.none()
    return queryset.filter(
        Q(store_id__in=store_ids)
        | Q(operation__store_id__in=store_ids)
        | Q(store__isnull=True, operation__isnull=True, user=user)
    )


def _visible_notifications_queryset(user):
    store_ids = _visible_store_ids(user)
    return SystemNotification.objects.select_related("related_operation", "related_store").filter(
        Q(related_store_id__in=store_ids)
        | Q(related_operation__store_id__in=store_ids)
        | Q(related_store__isnull=True, related_operation__isnull=True),
        status__in=["open", "acknowledged"],
    )


@login_required
def audit_list(request: HttpRequest) -> HttpResponse:
    records = _visible_audit_queryset(request.user)
    q = request.GET.get("q", "").strip()
    action = request.GET.get("action", "").strip()
    user_id = request.GET.get("user", "").strip()
    store_id = request.GET.get("store", "").strip()
    operation = request.GET.get("operation", "").strip()
    period_from = request.GET.get("period_from", "").strip()
    period_to = request.GET.get("period_to", "").strip()
    if q:
        records = records.filter(Q(entity_id__icontains=q) | Q(entity_type__icontains=q) | Q(safe_message__icontains=q))
    if action:
        records = records.filter(action_code=action)
    if user_id:
        records = records.filter(user_id=user_id)
    if store_id:
        records = records.filter(Q(store_id=store_id) | Q(operation__store_id=store_id))
    if operation:
        records = records.filter(operation__visible_id__icontains=operation)
    parsed_period_from = parse_date(period_from) if period_from else None
    parsed_period_to = parse_date(period_to) if period_to else None
    if parsed_period_from:
        records = records.filter(occurred_at__date__gte=parsed_period_from)
    if parsed_period_to:
        records = records.filter(occurred_at__date__lte=parsed_period_to)
    return _render(
        request,
        "web/audit_list.html",
        {
            "page": _paginate(request, records),
            "filters": {
                "q": q,
                "action": action,
                "user": user_id,
                "store": store_id,
                "operation": operation,
                "period_from": period_from,
                "period_to": period_to,
            },
            "stores": visible_stores_queryset(request.user),
            "users": get_user_model().objects.filter(audit_records__in=_visible_audit_queryset(request.user)).distinct(),
        },
        section="logs",
    )


@login_required
def audit_card(request: HttpRequest, pk: int) -> HttpResponse:
    record = get_object_or_404(_visible_audit_queryset(request.user), pk=pk)
    store = record.store or (record.operation.store if record.operation_id else None)
    if store is None:
        can_view = has_permission(request.user, "audit.card.view") or (
            record.user_id == request.user.pk and _has_permission_in_scope(request.user, "audit.card.view")
        )
    else:
        can_view = has_permission(request.user, "audit.card.view", store)
    if not can_view:
        raise PermissionDenied("No permission to view audit card.")
    return _render(request, "web/audit_card.html", {"record": record}, section="logs")


@login_required
def techlog_list(request: HttpRequest) -> HttpResponse:
    records = _visible_techlog_queryset(request.user)
    q = request.GET.get("q", "").strip()
    severity = request.GET.get("severity", "").strip()
    event = request.GET.get("event", "").strip()
    user_id = request.GET.get("user", "").strip()
    store_id = request.GET.get("store", "").strip()
    operation = request.GET.get("operation", "").strip()
    period_from = request.GET.get("period_from", "").strip()
    period_to = request.GET.get("period_to", "").strip()
    if q:
        records = records.filter(Q(event_type__icontains=q) | Q(safe_message__icontains=q) | Q(entity_id__icontains=q))
    if severity:
        records = records.filter(severity=severity)
    if event:
        records = records.filter(event_type=event)
    if user_id:
        records = records.filter(user_id=user_id)
    if store_id:
        records = records.filter(Q(store_id=store_id) | Q(operation__store_id=store_id))
    if operation:
        records = records.filter(operation__visible_id__icontains=operation)
    parsed_period_from = parse_date(period_from) if period_from else None
    parsed_period_to = parse_date(period_to) if period_to else None
    if parsed_period_from:
        records = records.filter(occurred_at__date__gte=parsed_period_from)
    if parsed_period_to:
        records = records.filter(occurred_at__date__lte=parsed_period_to)
    return _render(
        request,
        "web/techlog_list.html",
        {
            "page": _paginate(request, records),
            "filters": {
                "q": q,
                "severity": severity,
                "event": event,
                "user": user_id,
                "store": store_id,
                "operation": operation,
                "period_from": period_from,
                "period_to": period_to,
            },
            "stores": visible_stores_queryset(request.user),
            "users": get_user_model().objects.filter(techlog_records__in=_visible_techlog_queryset(request.user)).distinct(),
        },
        section="logs",
    )


@login_required
def techlog_card(request: HttpRequest, pk: int) -> HttpResponse:
    record = get_object_or_404(_visible_techlog_queryset(request.user), pk=pk)
    store = record.store or (record.operation.store if record.operation_id else None)
    if store is None:
        can_view = has_permission(request.user, "techlog.card.view") or (
            record.user_id == request.user.pk and _has_permission_in_scope(request.user, "techlog.card.view")
        )
    else:
        can_view = has_permission(request.user, "techlog.card.view", store)
    if not can_view:
        raise PermissionDenied("No permission to view techlog card.")
    return _render(
        request,
        "web/techlog_card.html",
        {"record": record, "can_view_sensitive": has_permission(request.user, "techlog.sensitive.view")},
        section="logs",
    )


@login_required
def notification_list(request: HttpRequest) -> HttpResponse:
    if not (has_section_access(request.user, "audit.view") or has_section_access(request.user, "techlog.view")):
        raise PermissionDenied("No section access to notifications.")
    return _render(
        request,
        "web/notification_list.html",
        {"page": _paginate(request, _visible_notifications_queryset(request.user))},
        section="logs",
    )
