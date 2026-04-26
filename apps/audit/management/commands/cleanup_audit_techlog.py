"""Regulated non-UI retention cleanup for audit and techlog."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.audit.services import cleanup_expired_audit_records
from apps.techlog.services import cleanup_expired_techlog_records


class Command(BaseCommand):
    help = "Delete audit and techlog records whose 90-day retention_until has expired."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show records eligible for cleanup without deleting them.",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        if options["dry_run"]:
            from apps.audit.models import AuditRecord
            from apps.techlog.models import TechLogRecord

            audit_count = AuditRecord.objects.filter(retention_until__lte=now).count()
            techlog_count = TechLogRecord.objects.filter(retention_until__lte=now).count()
            self.stdout.write(
                f"DRY RUN audit_expired={audit_count} techlog_expired={techlog_count}",
            )
            return

        audit_result = cleanup_expired_audit_records(now=now)
        techlog_result = cleanup_expired_techlog_records(now=now)
        self.stdout.write(
            "cleanup_audit_techlog completed "
            f"audit_deleted={audit_result.deleted_count} "
            f"techlog_deleted={techlog_result.deleted_count}",
        )
