"""Permission resolution and owner protection helpers."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.db.models import Q

from .models import (
    AccessEffect,
    Permission,
    RoleSectionAccess,
    StoreAccess,
    UserBlockHistory,
    UserChangeHistory,
    is_owner_user,
    user_role_codes as model_user_role_codes,
)
from .seeds import ROLE_GLOBAL_ADMIN, ROLE_OWNER


FULL_OBJECT_SCOPE_ROLE_CODES = {ROLE_OWNER, ROLE_GLOBAL_ADMIN}


def user_role_codes(user) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    return model_user_role_codes(user)


def is_owner(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False) and is_owner_user(user))


def has_full_object_scope(user) -> bool:
    return bool(user_role_codes(user) & FULL_OBJECT_SCOPE_ROLE_CODES)


def has_store_access(user, store, allow_global: bool = True) -> bool:
    if not user or not getattr(user, "is_authenticated", False) or not user.is_active:
        return False
    if is_owner(user):
        return True
    if store is not None:
        active_access = StoreAccess.objects.filter(user=user, store=store, is_active=True)
        if active_access.filter(effect=AccessEffect.DENY).exists():
            return False
        if active_access.filter(effect=AccessEffect.ALLOW).exists():
            return True
    if allow_global and has_full_object_scope(user):
        return True
    return False


def _active_allowed_store_ids(user) -> set[int]:
    if not user or not getattr(user, "is_authenticated", False) or not user.is_active:
        return set()
    rows = user.store_access.filter(is_active=True).values_list("store_id", "effect")
    allowed = {store_id for store_id, effect in rows if effect == AccessEffect.ALLOW}
    denied = {store_id for store_id, effect in rows if effect == AccessEffect.DENY}
    return allowed - denied


def _has_role_permission(user, permission: Permission) -> bool:
    role_ids = list(user.roles.values_list("id", flat=True))
    if user.primary_role_id:
        role_ids.append(user.primary_role_id)
    return permission.role_permissions.filter(
        role_id__in=role_ids,
        role__status="active",
    ).exists()


def _has_direct_permission(user, permission: Permission, store) -> bool:
    filters = Q(store__isnull=True)
    if store is not None:
        filters |= Q(store=store)
    return user.permission_overrides.filter(
        filters,
        permission=permission,
        effect=AccessEffect.ALLOW,
        is_active=True,
    ).exists()


def _has_direct_deny(user, permission: Permission, store) -> bool:
    filters = Q(store__isnull=True)
    if store is not None:
        filters |= Q(store=store)
    return user.permission_overrides.filter(
        filters,
        permission=permission,
        effect=AccessEffect.DENY,
        is_active=True,
    ).exists()


def has_permission(user, permission_code: str, store=None) -> bool:
    if not user or not getattr(user, "is_authenticated", False) or not user.is_active:
        return False

    permission = Permission.objects.filter(code=permission_code).first()
    if permission is None:
        return False

    if is_owner(user):
        return True

    if permission.scope_type == Permission.ScopeType.OWNER_ONLY:
        return False

    if _has_direct_deny(user, permission, store):
        return False

    if permission.scope_type == Permission.ScopeType.GLOBAL:
        return _has_direct_permission(user, permission, store) or _has_role_permission(
            user,
            permission,
        )

    if permission.scope_type in {
        Permission.ScopeType.STORE,
        Permission.ScopeType.GLOBAL_STORE,
    }:
        has_action = _has_direct_permission(user, permission, store) or _has_role_permission(
            user,
            permission,
        )
        if not has_action:
            return False
        return has_store_access(user, store, allow_global=True)

    return False


def has_section_access(user, section_code: str, store=None) -> bool:
    if not user or not getattr(user, "is_authenticated", False) or not user.is_active:
        return False
    if is_owner(user):
        return True

    filters = Q(store__isnull=True)
    if store is not None:
        filters |= Q(store=store)
    if user.section_overrides.filter(
        filters,
        section_access_id=section_code,
        effect=AccessEffect.DENY,
        is_active=True,
    ).exists():
        return False
    if user.section_overrides.filter(
        filters,
        section_access_id=section_code,
        effect=AccessEffect.ALLOW,
        is_active=True,
    ).exists():
        return True

    role_ids = list(user.roles.values_list("id", flat=True))
    if user.primary_role_id:
        role_ids.append(user.primary_role_id)
    return RoleSectionAccess.objects.filter(
        role_id__in=role_ids,
        role__status="active",
        section_access_id=section_code,
    ).exists()


def can_manage_user_action(actor, target, permission_code: str, store=None) -> bool:
    if not actor or not target or not getattr(actor, "is_authenticated", False):
        return False
    if is_owner(actor):
        return True
    if is_owner(target):
        return False

    if has_full_object_scope(actor):
        return has_permission(actor, permission_code, store)

    if has_full_object_scope(target):
        return False

    if store is not None:
        return (
            has_permission(actor, permission_code, store)
            and has_store_access(actor, store, allow_global=False)
            and has_store_access(target, store, allow_global=False)
        )

    actor_store_ids = _active_allowed_store_ids(actor)
    target_store_ids = _active_allowed_store_ids(target)
    shared_store_ids = actor_store_ids & target_store_ids
    if not shared_store_ids:
        return False

    from apps.stores.models import StoreAccount

    stores = StoreAccount.objects.filter(pk__in=shared_store_ids)
    return any(has_permission(actor, permission_code, scoped_store) for scoped_store in stores)


def can_manage_user(actor, target, store=None) -> bool:
    return can_manage_user_action(actor, target, "users.edit", store) or can_manage_user_action(
        actor,
        target,
        "users.status.change",
        store,
    )


def change_user_status(
    actor,
    target,
    new_status: str,
    reason: str = "",
    source: str = "admin",
    permission_code: str = "users.status.change",
):
    if not can_manage_user_action(actor, target, permission_code):
        raise PermissionDenied("Actor cannot change this user status.")
    old_status = target.status
    if old_status == new_status:
        return target

    target.status = new_status
    target.save(update_fields=["status", "updated_at"])
    UserBlockHistory.objects.create(
        user=target,
        changed_by=actor,
        old_status=old_status,
        new_status=new_status,
        reason=reason,
        source=source,
    )
    return target


def record_user_change(actor, target, field_code: str, old_value: str, new_value: str, source: str):
    return UserChangeHistory.objects.create(
        user=target,
        changed_by=actor,
        field_code=field_code,
        old_value=old_value,
        new_value=new_value,
        source=source,
    )
