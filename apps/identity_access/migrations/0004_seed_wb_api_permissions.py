from django.db import migrations


def seed_wb_api_permissions(apps, schema_editor):
    from apps.identity_access.seeds import seed_identity_access as run_seed

    run_seed()


class Migration(migrations.Migration):

    dependencies = [
        ("identity_access", "0003_alter_storeaccess_store_alter_storeaccess_user_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_wb_api_permissions, reverse_code=migrations.RunPython.noop),
    ]
