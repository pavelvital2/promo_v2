from django.db import migrations


def seed_identity_access(apps, schema_editor):
    from apps.identity_access.seeds import seed_identity_access as run_seed

    run_seed()


class Migration(migrations.Migration):

    dependencies = [
        ("identity_access", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_identity_access, reverse_code=migrations.RunPython.noop),
    ]
