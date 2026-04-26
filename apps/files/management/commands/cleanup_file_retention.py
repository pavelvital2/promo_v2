"""Delete expired physical files while preserving metadata."""

from django.core.management.base import BaseCommand

from apps.files.services import cleanup_expired_physical_files


class Command(BaseCommand):
    help = "Delete physical files older than the 3-day retention window; metadata is preserved."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report without deleting files.")
        parser.add_argument("--limit", type=int, default=None, help="Maximum rows to process.")

    def handle(self, *args, **options):
        result = cleanup_expired_physical_files(
            dry_run=options["dry_run"],
            limit=options["limit"],
        )
        mode = "dry-run" if result.dry_run else "applied"
        self.stdout.write(
            self.style.SUCCESS(
                f"file retention cleanup {mode}: scanned={result.scanned}, "
                f"deleted={result.deleted}, missing={result.missing}"
            )
        )
