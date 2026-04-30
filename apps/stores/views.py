from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.identity_access.services import has_permission

from .forms import ConnectionBlockForm, StoreAccountForm
from .models import ConnectionBlock, StoreAccount
from .services import (
    API_STAGE_2_NOTICE,
    OZON_API_CONNECTION_TYPE,
    OZON_API_MODULE,
    WB_API_CONNECTION_TYPE,
    WB_API_MODULE,
    check_ozon_api_connection,
    check_wb_api_connection,
    connection_metadata_display,
    create_store_account,
    require_ozon_store_for_ozon_api,
    require_wb_store_for_wb_api,
    require_store_permission,
    save_connection_block,
    store_history_value_display,
    update_store_account,
    visible_stores_queryset,
)


@login_required
def store_list(request):
    stores = visible_stores_queryset(request.user)
    search = request.GET.get("q", "").strip()
    marketplace = request.GET.get("marketplace", "").strip()
    status = request.GET.get("status", "").strip()
    group = request.GET.get("group", "").strip()
    api_block = request.GET.get("api_block", "").strip()

    if search:
        stores = stores.filter(Q(name__icontains=search) | Q(visible_id__icontains=search))
    if marketplace:
        stores = stores.filter(marketplace=marketplace)
    if status:
        stores = stores.filter(status=status)
    if group:
        stores = stores.filter(group_id=group)
    if api_block == "present":
        stores = stores.filter(connection_blocks__isnull=False)
    elif api_block == "absent":
        stores = stores.filter(connection_blocks__isnull=True)

    stores = stores.distinct().order_by("name", "id")
    page = Paginator(stores, 25).get_page(request.GET.get("page"))
    can_create = has_permission(request.user, "stores.create")
    return render(
        request,
        "stores/store_list.html",
        {
            "page": page,
            "search": search,
            "marketplace": marketplace,
            "status": status,
            "group": group,
            "api_block": api_block,
            "marketplace_choices": StoreAccount.Marketplace.choices,
            "status_choices": StoreAccount.Status.choices,
            "can_create": can_create,
            "api_stage_2_notice": API_STAGE_2_NOTICE,
        },
    )


@login_required
def store_create(request):
    if not has_permission(request.user, "stores.create"):
        raise PermissionDenied("No permission to create stores/cabinets.")
    form = StoreAccountForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        store = create_store_account(request.user, **form.cleaned_data)
        messages.success(request, "Store/cabinet created.")
        return redirect("stores:store_card", visible_id=store.visible_id)
    return render(request, "stores/store_form.html", {"form": form, "mode": "create"})


@login_required
def store_card(request, visible_id: str):
    store = get_object_or_404(StoreAccount.objects.select_related("group"), visible_id=visible_id)
    require_store_permission(request.user, "stores.card.view", store)
    connections = list(store.connection_blocks.all())
    for connection in connections:
        connection.metadata_display = connection_metadata_display(connection.metadata)
    can_edit = has_permission(request.user, "stores.edit", store)
    is_wb_store = store.marketplace == StoreAccount.Marketplace.WB
    is_ozon_store = store.marketplace == StoreAccount.Marketplace.OZON
    can_view_connection = (
        (is_wb_store and has_permission(request.user, "wb.api.connection.view", store))
        or (is_ozon_store and has_permission(request.user, "ozon.api.connection.view", store))
    )
    can_edit_connection = (
        (is_wb_store and has_permission(request.user, "wb.api.connection.manage", store))
        or (is_ozon_store and has_permission(request.user, "ozon.api.connection.manage", store))
    )
    can_open_wb_api = is_wb_store and any(
        has_permission(request.user, code, store)
        for code in (
            "wb.api.operation.view",
            "wb.api.prices.download",
            "wb.api.promotions.download",
            "wb.api.discounts.calculate",
            "wb.api.discounts.upload",
            "wb.api.discounts.upload.confirm",
        )
    )
    can_open_ozon_elastic = is_ozon_store and any(
        has_permission(request.user, code, store)
        for code in (
            "ozon.api.operation.view",
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
    )
    can_view_history = has_permission(request.user, "stores.history.view", store)
    return render(
        request,
        "stores/store_card.html",
        {
            "store": store,
            "connections": connections,
            "can_edit": can_edit,
            "can_view_connection": can_view_connection,
            "can_edit_connection": can_edit_connection,
            "can_open_wb_api": can_open_wb_api,
            "can_open_ozon_elastic": can_open_ozon_elastic,
            "can_view_history": can_view_history,
            "is_wb_store": is_wb_store,
            "is_ozon_store": is_ozon_store,
            "api_stage_2_notice": API_STAGE_2_NOTICE,
        },
    )


@login_required
def store_edit(request, visible_id: str):
    store = get_object_or_404(StoreAccount.objects.select_related("group"), visible_id=visible_id)
    require_store_permission(request.user, "stores.edit", store)
    form = StoreAccountForm(request.POST or None, instance=store)
    if request.method == "POST" and form.is_valid():
        update_store_account(request.user, store, **form.cleaned_data)
        messages.success(request, "Store/cabinet updated.")
        return redirect("stores:store_card", visible_id=store.visible_id)
    return render(
        request,
        "stores/store_form.html",
        {"form": form, "store": store, "mode": "edit"},
    )


@login_required
def store_history(request, visible_id: str):
    store = get_object_or_404(StoreAccount.objects.select_related("group"), visible_id=visible_id)
    require_store_permission(request.user, "stores.history.view", store)
    page = Paginator(store.history.select_related("changed_by"), 50).get_page(request.GET.get("page"))
    for item in page.object_list:
        item.old_value_display = store_history_value_display(item.field_code, item.old_value)
        item.new_value_display = store_history_value_display(item.field_code, item.new_value)
    return render(request, "stores/store_history.html", {"store": store, "page": page})


@login_required
def connection_edit(request, visible_id: str, pk: int | None = None):
    store = get_object_or_404(StoreAccount, visible_id=visible_id)
    if store.marketplace == StoreAccount.Marketplace.WB:
        require_wb_store_for_wb_api(store)
        module = WB_API_MODULE
        connection_type = WB_API_CONNECTION_TYPE
        manage_permission = "wb.api.connection.manage"
    else:
        require_ozon_store_for_ozon_api(store)
        module = OZON_API_MODULE
        connection_type = OZON_API_CONNECTION_TYPE
        manage_permission = "ozon.api.connection.manage"
    require_store_permission(request.user, manage_permission, store)
    if pk is None:
        connection = ConnectionBlock(
            store=store,
            module=module,
            connection_type=connection_type,
        )
    else:
        connection = get_object_or_404(ConnectionBlock, pk=pk, store=store)
        if connection.module != module or connection.connection_type != connection_type:
            raise PermissionDenied("Connection type does not match this marketplace flow.")

    existing_protected_secret_ref = connection.protected_secret_ref
    form = ConnectionBlockForm(request.POST or None, instance=connection)
    can_edit_secret_ref = has_permission(request.user, manage_permission, store)
    if not can_edit_secret_ref:
        form.fields.pop("protected_secret_ref", None)

    if request.method == "POST" and form.is_valid():
        fields = {field: form.cleaned_data[field] for field in form.fields}
        fields["module"] = module
        fields["connection_type"] = connection_type
        if connection.pk and not fields.get("protected_secret_ref"):
            connection.protected_secret_ref = existing_protected_secret_ref
            fields.pop("protected_secret_ref", None)
        save_connection_block(request.user, connection, **fields)
        messages.success(request, "Connection block updated.")
        return redirect("stores:store_card", visible_id=store.visible_id)

    return render(
        request,
        "stores/connection_form.html",
        {
            "form": form,
            "store": store,
            "connection": connection,
            "can_edit_secret_ref": can_edit_secret_ref,
            "api_stage_2_notice": API_STAGE_2_NOTICE,
        },
    )


@login_required
def connection_check(request, visible_id: str, pk: int):
    if request.method != "POST":
        raise PermissionDenied("Connection check must be started by POST.")
    store = get_object_or_404(StoreAccount, visible_id=visible_id)
    connection = get_object_or_404(ConnectionBlock, pk=pk, store=store)
    if connection.module == WB_API_MODULE:
        require_wb_store_for_wb_api(store)
        check_wb_api_connection(request.user, connection)
    elif connection.module == OZON_API_MODULE:
        require_ozon_store_for_ozon_api(store)
        check_ozon_api_connection(request.user, connection)
    else:
        raise PermissionDenied("Only documented marketplace API connections can be checked.")
    messages.info(request, connection.last_check_message)
    return redirect("stores:store_card", visible_id=store.visible_id)
