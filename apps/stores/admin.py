from django.contrib import admin

from .models import BusinessGroup, ConnectionBlock, StoreAccount, StoreAccountChangeHistory
from .services import (
    CONNECTION_HISTORY_FIELDS,
    STORE_CHANGE_FIELDS,
    _connection_field_value,
    _validate_connection_marketplace_compatibility,
    _store_field_value,
    record_store_change,
)


@admin.register(BusinessGroup)
class BusinessGroupAdmin(admin.ModelAdmin):
    list_display = ("visible_id", "name", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("visible_id", "name")
    readonly_fields = ("visible_id", "created_at", "updated_at")


@admin.register(StoreAccount)
class StoreAccountAdmin(admin.ModelAdmin):
    list_display = (
        "visible_id",
        "name",
        "marketplace",
        "cabinet_type",
        "status",
        "group",
        "updated_at",
    )
    list_filter = ("marketplace", "cabinet_type", "status")
    search_fields = ("visible_id", "name", "group__name")
    readonly_fields = ("visible_id", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        old_values = {}
        if change:
            previous = StoreAccount.objects.select_related("group").get(pk=obj.pk)
            old_values = {field: _store_field_value(previous, field) for field in STORE_CHANGE_FIELDS}
        super().save_model(request, obj, form, change)
        if not change:
            record_store_change(
                obj,
                "created",
                "",
                obj.visible_id,
                actor=request.user,
                source="admin",
            )
            return
        obj.refresh_from_db()
        for field in STORE_CHANGE_FIELDS:
            record_store_change(
                obj,
                field,
                old_values[field],
                _store_field_value(obj, field),
                actor=request.user,
                source="admin",
            )

    def has_delete_permission(self, request, obj=None):
        if obj and not obj.can_be_physically_deleted():
            return False
        return super().has_delete_permission(request, obj)


@admin.register(ConnectionBlock)
class ConnectionBlockAdmin(admin.ModelAdmin):
    list_display = (
        "store",
        "module",
        "connection_type",
        "status",
        "has_secret_ref",
        "is_stage1_used",
        "updated_at",
    )
    list_filter = ("status", "module", "connection_type")
    search_fields = ("store__visible_id", "store__name", "module", "connection_type")
    readonly_fields = ("is_stage1_used", "created_at", "updated_at")

    @admin.display(boolean=True, description="Secret reference")
    def has_secret_ref(self, obj):
        return bool(obj.protected_secret_ref)

    def save_model(self, request, obj, form, change):
        _validate_connection_marketplace_compatibility(
            store=obj.store,
            module=obj.module,
            connection_type=obj.connection_type,
        )
        old_values = {}
        if change:
            previous = ConnectionBlock.objects.get(pk=obj.pk)
            old_values = {
                field: _connection_field_value(previous, field) for field in CONNECTION_HISTORY_FIELDS
            }
        else:
            old_values = {field: "" for field in CONNECTION_HISTORY_FIELDS}
        obj.is_stage1_used = False
        super().save_model(request, obj, form, change)
        obj.refresh_from_db()
        for field in CONNECTION_HISTORY_FIELDS:
            record_store_change(
                obj.store,
                f"connection.{field}",
                old_values[field],
                _connection_field_value(obj, field),
                actor=request.user,
                source="admin",
            )

    def has_delete_permission(self, request, obj=None):
        if obj and obj.has_physical_delete_usage():
            return False
        return super().has_delete_permission(request, obj)


@admin.register(StoreAccountChangeHistory)
class StoreAccountChangeHistoryAdmin(admin.ModelAdmin):
    list_display = ("store", "changed_at", "changed_by", "field_code", "source")
    list_filter = ("field_code", "source", "changed_at")
    search_fields = ("store__visible_id", "store__name", "field_code", "old_value", "new_value")
    readonly_fields = (
        "store",
        "changed_at",
        "changed_by",
        "field_code",
        "old_value",
        "new_value",
        "source",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
