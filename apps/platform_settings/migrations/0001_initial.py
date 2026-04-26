# Generated for TASK-007 WB parameter snapshots.

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("stores", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ParameterDefinition",
            fields=[
                ("code", models.CharField(max_length=128, primary_key=True, serialize=False)),
                ("module", models.CharField(max_length=64)),
                (
                    "value_type",
                    models.CharField(
                        choices=[
                            ("integer", "Integer"),
                            ("decimal", "Decimal"),
                            ("string", "String"),
                        ],
                        max_length=32,
                    ),
                ),
                ("is_user_managed", models.BooleanField(default=True)),
            ],
            options={"ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="SystemParameterValue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("parameter_code", models.CharField(max_length=128)),
                ("value", models.JSONField()),
                ("active_from", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"ordering": ["parameter_code", "-active_from", "-id"]},
        ),
        migrations.CreateModel(
            name="StoreParameterValue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("parameter_code", models.CharField(max_length=128)),
                ("value", models.JSONField()),
                ("active_from", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "changed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="changed_store_parameters",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "store",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="parameter_values",
                        to="stores.storeaccount",
                    ),
                ),
            ],
            options={"ordering": ["store_id", "parameter_code", "-active_from", "-id"]},
        ),
        migrations.AddIndex(
            model_name="systemparametervalue",
            index=models.Index(fields=["parameter_code", "active_from"], name="platform_se_paramet_aaa0f6_idx"),
        ),
        migrations.AddIndex(
            model_name="storeparametervalue",
            index=models.Index(fields=["store", "parameter_code", "active_from"], name="platform_se_store_i_5d3107_idx"),
        ),
    ]
