"""History hooks for store-related rows owned by other apps."""

from __future__ import annotations

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.identity_access.models import StoreAccess

from .services import record_store_access_change


def _access_value(access: StoreAccess) -> str:
    return (
        f"user={access.user.visible_id or access.user_id}; "
        f"level={access.access_level}; effect={access.effect}; active={access.is_active}"
    )


@receiver(pre_save, sender=StoreAccess)
def remember_store_access_previous_value(sender, instance: StoreAccess, **kwargs):
    if not instance.pk:
        instance._store_history_old_value = ""
        return
    previous = sender.objects.select_related("user").get(pk=instance.pk)
    instance._store_history_old_value = _access_value(previous)


@receiver(post_save, sender=StoreAccess)
def record_store_access_history(sender, instance: StoreAccess, created: bool, **kwargs):
    old_value = getattr(instance, "_store_history_old_value", "")
    if created:
        old_value = ""
    record_store_access_change(instance, old_value=old_value, source="model")
