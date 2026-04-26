"""Write-flow helpers for store-scoped WB parameters."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.audit.models import AuditActionCode, AuditSourceContext
from apps.audit.services import create_audit_record
from apps.identity_access.services import has_permission

from .models import (
    StoreParameterChangeHistory,
    StoreParameterValue,
    SystemParameterValue,
    WB_PARAMETER_CODES,
)


def _parse_percent(value: str, code: str) -> int:
    text = str(value or "").strip().replace(",", ".")
    try:
        decimal = Decimal(text)
    except InvalidOperation as exc:
        raise ValidationError(f"{code}: value must be numeric.") from exc
    if decimal < 0 or decimal > 100:
        raise ValidationError(f"{code}: value must be within 0..100.")
    return int(decimal)


def latest_store_parameter(store, code: str) -> StoreParameterValue | None:
    return (
        StoreParameterValue.objects.filter(store=store, parameter_code=code, is_active=True)
        .order_by("-active_from", "-id")
        .first()
    )


def latest_system_value(code: str):
    return (
        SystemParameterValue.objects.filter(parameter_code=code)
        .order_by("-active_from", "-id")
        .first()
    )


def effective_parameter_rows(store):
    rows = []
    for code in sorted(WB_PARAMETER_CODES):
        store_value = latest_store_parameter(store, code)
        if store_value is not None:
            rows.append(
                {
                    "code": code,
                    "effective_value": store_value.value,
                    "source": "store",
                    "store_value": store_value.value,
                    "active_from": store_value.active_from,
                }
            )
            continue
        system_value = latest_system_value(code)
        rows.append(
            {
                "code": code,
                "effective_value": system_value.value if system_value else "",
                "source": "system",
                "store_value": "",
                "active_from": system_value.active_from if system_value else None,
            }
        )
    return rows


@transaction.atomic
def save_wb_store_parameters(actor, store, values: dict[str, str], clear_codes: set[str]):
    if not has_permission(actor, "settings.store_params.edit", store):
        raise PermissionDenied("No permission or object access to edit store parameters.")

    changed = []
    for code in sorted(WB_PARAMETER_CODES):
        previous = latest_store_parameter(store, code)
        old_value = previous.value if previous else None
        old_source = "store" if previous else "system"
        if code in clear_codes:
            if previous is None:
                continue
            StoreParameterValue.objects.filter(store=store, parameter_code=code, is_active=True).update(
                is_active=False,
            )
            new_value = None
            new_source = "system"
        else:
            raw = values.get(code, "").strip()
            if raw == "":
                continue
            new_value = _parse_percent(raw, code)
            new_source = "store"
            if previous is not None and previous.value == new_value:
                continue
            StoreParameterValue.objects.filter(store=store, parameter_code=code, is_active=True).update(
                is_active=False,
            )
            StoreParameterValue.objects.create(
                store=store,
                parameter_code=code,
                value=new_value,
                changed_by=actor,
                is_active=True,
            )
        audit = create_audit_record(
            action_code=AuditActionCode.SETTINGS_WB_PARAMETER_CHANGED,
            entity_type="StoreParameterValue",
            entity_id=code,
            user=actor,
            store=store,
            safe_message=f"WB store parameter changed: {code}",
            before_snapshot={"value": old_value, "source": old_source},
            after_snapshot={"value": new_value, "source": new_source},
            source_context=AuditSourceContext.UI,
        )
        StoreParameterChangeHistory.objects.create(
            store=store,
            parameter_code=code,
            changed_by=actor,
            old_value=old_value,
            new_value=new_value,
            old_source=old_source,
            new_source=new_source,
            audit_record=audit,
        )
        changed.append(code)
    return changed
