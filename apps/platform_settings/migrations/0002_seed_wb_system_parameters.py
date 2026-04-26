# Generated for TASK-007 WB approved system parameter defaults.

from django.db import migrations
from django.utils import timezone


WB_SYSTEM_PARAMETERS = {
    "wb_threshold_percent": 70,
    "wb_fallback_over_threshold_percent": 55,
    "wb_fallback_no_promo_percent": 55,
}


def seed_wb_system_parameters(apps, schema_editor):
    ParameterDefinition = apps.get_model("platform_settings", "ParameterDefinition")
    SystemParameterValue = apps.get_model("platform_settings", "SystemParameterValue")

    for code, value in WB_SYSTEM_PARAMETERS.items():
        ParameterDefinition.objects.update_or_create(
            code=code,
            defaults={
                "module": "discounts_excel",
                "value_type": "integer",
                "is_user_managed": True,
            },
        )
        if not SystemParameterValue.objects.filter(parameter_code=code).exists():
            SystemParameterValue.objects.create(
                parameter_code=code,
                value=value,
                active_from=timezone.now(),
            )


def unseed_wb_system_parameters(apps, schema_editor):
    ParameterDefinition = apps.get_model("platform_settings", "ParameterDefinition")
    SystemParameterValue = apps.get_model("platform_settings", "SystemParameterValue")

    SystemParameterValue.objects.filter(
        parameter_code__in=WB_SYSTEM_PARAMETERS,
        value__in=list(WB_SYSTEM_PARAMETERS.values()),
    ).delete()
    ParameterDefinition.objects.filter(code__in=WB_SYSTEM_PARAMETERS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("platform_settings", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_wb_system_parameters, unseed_wb_system_parameters),
    ]
