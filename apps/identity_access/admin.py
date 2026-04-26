from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.core.exceptions import PermissionDenied

from .models import (
    Permission,
    Role,
    RolePermission,
    RoleSectionAccess,
    SectionAccess,
    StoreAccess,
    User,
    UserBlockHistory,
    UserChangeHistory,
    UserPermissionOverride,
    UserRole,
    UserSectionAccessOverride,
)
from .services import can_manage_user, is_owner


class SystemDictionaryAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj is not None and getattr(obj, "is_system", False):
            readonly_fields.extend(field.name for field in obj._meta.fields)
        return tuple(dict.fromkeys(readonly_fields))

    def has_delete_permission(self, request, obj=None):
        if obj is not None and getattr(obj, "is_system", False):
            return False
        return super().has_delete_permission(request, obj)


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj is not None and obj.is_system:
            readonly_fields.extend(field.name for field in self.model._meta.fields)
        return tuple(dict.fromkeys(readonly_fields))

    def has_add_permission(self, request, obj=None):
        if obj is not None and obj.is_system:
            return False
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.is_system:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)


class RoleSectionAccessInline(admin.TabularInline):
    model = RoleSectionAccess
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj is not None and obj.is_system:
            readonly_fields.extend(field.name for field in self.model._meta.fields)
        return tuple(dict.fromkeys(readonly_fields))

    def has_add_permission(self, request, obj=None):
        if obj is not None and obj.is_system:
            return False
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.is_system:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Role)
class RoleAdmin(SystemDictionaryAdmin):
    list_display = ("code", "name", "status", "is_system")
    list_filter = ("status", "is_system")
    search_fields = ("code", "name")
    inlines = [RolePermissionInline, RoleSectionAccessInline]

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.is_owner_role and not is_owner(request.user):
            return False
        return super().has_change_permission(request, obj)


@admin.register(Permission)
class PermissionAdmin(SystemDictionaryAdmin):
    list_display = ("code", "name", "scope_type", "is_system")
    list_filter = ("scope_type", "is_system")
    search_fields = ("code", "name")


@admin.register(SectionAccess)
class SectionAccessAdmin(SystemDictionaryAdmin):
    list_display = ("code", "section", "mode", "name", "is_system")
    list_filter = ("section", "mode", "is_system")
    search_fields = ("code", "section", "name")


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 0
    can_delete = False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "role" and not is_owner(request.user):
            kwargs["queryset"] = Role.objects.exclude(code="owner")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class UserPermissionOverrideInline(admin.TabularInline):
    model = UserPermissionOverride
    extra = 0
    can_delete = False


class UserSectionAccessOverrideInline(admin.TabularInline):
    model = UserSectionAccessOverride
    extra = 0
    can_delete = False


class StoreAccessInline(admin.TabularInline):
    model = StoreAccess
    extra = 0
    can_delete = False


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ("visible_id", "login", "display_name", "status", "primary_role", "is_staff")
    list_filter = ("status", "primary_role", "is_staff")
    search_fields = ("visible_id", "login", "display_name")
    ordering = ("visible_id",)
    inlines = [
        UserRoleInline,
        UserPermissionOverrideInline,
        UserSectionAccessOverrideInline,
        StoreAccessInline,
    ]
    fieldsets = (
        (None, {"fields": ("visible_id", "login", "password")}),
        ("Profile", {"fields": ("display_name", "status", "primary_role")}),
        ("Django admin", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "login",
                    "display_name",
                    "primary_role",
                    "status",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
    readonly_fields = ("visible_id", "last_login", "created_at", "updated_at")

    def has_change_permission(self, request, obj=None):
        if obj is not None and not can_manage_user(request.user, obj):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_physically_deleted():
            return False
        return super().has_delete_permission(request, obj)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "primary_role" and not is_owner(request.user):
            kwargs["queryset"] = Role.objects.exclude(code="owner")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def delete_model(self, request, obj):
        if not obj.can_be_physically_deleted():
            raise PermissionDenied("Used users are blocked or archived instead of deleted.")
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)


@admin.register(UserChangeHistory)
class UserChangeHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "changed_at", "changed_by", "field_code", "source")
    list_filter = ("source", "field_code")
    search_fields = ("user__login", "field_code", "old_value", "new_value")
    readonly_fields = [field.name for field in UserChangeHistory._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UserBlockHistory)
class UserBlockHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "changed_at", "changed_by", "old_status", "new_status", "source")
    list_filter = ("source", "old_status", "new_status")
    search_fields = ("user__login", "reason")
    readonly_fields = [field.name for field in UserBlockHistory._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
