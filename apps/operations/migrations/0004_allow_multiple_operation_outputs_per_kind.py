# Generated for TASK-013 on 2026-04-26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0003_remove_operation_operation_status_matches_type_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="operationoutputfile",
            name="uniq_operation_output_kind",
        ),
        migrations.AlterField(
            model_name="operationoutputfile",
            name="output_kind",
            field=models.CharField(
                choices=[
                    ("output_workbook", "Output workbook"),
                    ("detail_report", "Detail report"),
                    ("promotion_export", "Promotion export"),
                ],
                default="output_workbook",
                max_length=32,
            ),
        ),
    ]
