from django.core.management.base import BaseCommand

from apps.identity_access.seeds import seed_identity_access


class Command(BaseCommand):
    help = "Seed TASK-002 system roles, permissions and section access."

    def handle(self, *args, **options):
        stats = seed_identity_access()
        self.stdout.write(
            self.style.SUCCESS(
                "Seeded identity/access: "
                + ", ".join(f"{key}={value}" for key, value in stats.items()),
            ),
        )
