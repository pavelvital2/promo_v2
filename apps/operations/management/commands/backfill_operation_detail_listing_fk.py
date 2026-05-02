from __future__ import annotations

import json

from django.core.management.base import BaseCommand

from apps.operations.listing_enrichment import backfill_operation_detail_listing_fk


class Command(BaseCommand):
    help = "Backfill OperationDetailRow.marketplace_listing_id by deterministic same-store listing keys."

    def add_arguments(self, parser):
        parser.add_argument(
            "--write",
            action="store_true",
            help="Persist FK updates. Without this flag the command runs as a dry-run.",
        )
        parser.add_argument("--limit", type=int, default=1000, help="Maximum rows to scan in this run.")
        parser.add_argument("--start-id", type=int, default=None, help="First OperationDetailRow id to scan.")
        parser.add_argument("--end-id", type=int, default=None, help="Last OperationDetailRow id to scan.")

    def handle(self, *args, **options):
        report = backfill_operation_detail_listing_fk(
            dry_run=not options["write"],
            limit=options["limit"],
            start_id=options["start_id"],
            end_id=options["end_id"],
        )
        self.stdout.write(json.dumps(report.as_dict(), sort_keys=True, indent=2))
