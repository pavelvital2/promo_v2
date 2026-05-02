"""Deterministic OperationDetailRow to MarketplaceListing enrichment."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from django.core.exceptions import ValidationError
from django.db import models, transaction

from apps.audit.models import AuditActionCode, AuditSourceContext
from apps.audit.services import create_audit_record
from apps.product_core.models import MarketplaceListing
from apps.techlog.models import TechLogEventType
from apps.techlog.services import create_techlog_record

from .models import (
    Marketplace,
    OperationDetailRow,
    OperationMode,
    OperationModule,
    OperationStepCode,
    allow_operation_detail_listing_fk_enrichment_update,
)


CONFLICT_NO_LISTING_MATCH = "no_listing_match"
CONFLICT_MULTIPLE_LISTING_MATCHES = "multiple_listing_matches"
CONFLICT_STORE_MARKETPLACE_MISMATCH = "store_marketplace_mismatch"
CONFLICT_ROW_NOT_PRODUCT_IDENTIFIER = "row_not_product_identifier"
CONFLICT_SOURCE_SCOPE_NOT_APPROVED = "source_scope_not_approved"
CONFLICT_API_DATA_INTEGRITY_DUPLICATE = "api_data_integrity_duplicate"

WB_EXTERNAL_ID_KEYS = ("nmID", "vendorCode")
OZON_EXTERNAL_ID_KEYS = ("product_id", "offer_id")

WB_PROMOTION_PRODUCT_REASON_CODES = {
    "wb_api_promotion_product_valid",
    "wb_api_promotion_product_invalid",
}
WB_PROMOTION_SUMMARY_REASON_CODES = {
    "wb_api_promotion_current",
    "wb_api_promotion_not_current_filtered",
    "wb_api_promotion_regular",
    "wb_api_promotion_auto_no_nomenclatures",
}


@dataclass(frozen=True)
class ResolveResult:
    listing: MarketplaceListing | None = None
    conflict_class: str = ""
    matched_key: str = ""
    candidate_count: int = 0
    existing_same_fk: bool = False

    @property
    def matched(self) -> bool:
        return self.listing is not None and not self.conflict_class


@dataclass
class BackfillReport:
    dry_run: bool
    row_count_before: int
    checksum_before: str
    row_count_after: int = 0
    checksum_after: str = ""
    scanned_count: int = 0
    enriched_count: int = 0
    idempotent_count: int = 0
    skipped_count: int = 0
    same_scope_violation_count: int = 0
    changed_product_ref_count: int = 0
    conflict_counts: Counter = field(default_factory=Counter)
    family_counts: Counter = field(default_factory=Counter)
    enriched_by_family: Counter = field(default_factory=Counter)
    skipped_by_family: Counter = field(default_factory=Counter)

    def as_dict(self) -> dict:
        return {
            "dry_run": self.dry_run,
            "row_count_before": self.row_count_before,
            "checksum_before": self.checksum_before,
            "row_count_after": self.row_count_after,
            "checksum_after": self.checksum_after,
            "scanned_count": self.scanned_count,
            "enriched_count": self.enriched_count,
            "idempotent_count": self.idempotent_count,
            "skipped_count": self.skipped_count,
            "same_scope_violation_count": self.same_scope_violation_count,
            "changed_product_ref_count": self.changed_product_ref_count,
            "conflict_counts": dict(sorted(self.conflict_counts.items())),
            "family_counts": dict(sorted(self.family_counts.items())),
            "enriched_by_family": dict(sorted(self.enriched_by_family.items())),
            "skipped_by_family": dict(sorted(self.skipped_by_family.items())),
        }


def operation_family(row: OperationDetailRow) -> str:
    operation = row.operation
    if operation.mode == OperationMode.EXCEL and operation.module == OperationModule.DISCOUNTS_EXCEL:
        return f"stage1_{operation.marketplace}_excel"
    return operation.step_code or "unclassified"


def is_product_detail_row(row: OperationDetailRow) -> bool:
    operation = row.operation
    product_ref = (row.product_ref or "").strip()
    if not product_ref:
        return False
    if operation.mode == OperationMode.EXCEL and operation.module == OperationModule.DISCOUNTS_EXCEL:
        return True
    if operation.step_code == OperationStepCode.OZON_API_ACTIONS_DOWNLOAD:
        return False
    if operation.step_code == OperationStepCode.WB_API_PROMOTIONS_DOWNLOAD:
        if row.reason_code in WB_PROMOTION_PRODUCT_REASON_CODES:
            return True
        if row.reason_code in WB_PROMOTION_SUMMARY_REASON_CODES:
            return False
        return False
    return operation.step_code in {
        OperationStepCode.WB_API_PRICES_DOWNLOAD,
        OperationStepCode.WB_API_DISCOUNT_CALCULATION,
        OperationStepCode.WB_API_DISCOUNT_UPLOAD,
        OperationStepCode.OZON_API_ELASTIC_ACTIVE_PRODUCTS_DOWNLOAD,
        OperationStepCode.OZON_API_ELASTIC_CANDIDATE_PRODUCTS_DOWNLOAD,
        OperationStepCode.OZON_API_ELASTIC_PRODUCT_DATA_DOWNLOAD,
        OperationStepCode.OZON_API_ELASTIC_CALCULATION,
        OperationStepCode.OZON_API_ELASTIC_UPLOAD,
    }


def _external_id_keys(marketplace: str) -> tuple[str, ...]:
    if marketplace == Marketplace.WB:
        return WB_EXTERNAL_ID_KEYS
    if marketplace == Marketplace.OZON:
        return OZON_EXTERNAL_ID_KEYS
    return ()


def _trimmed_scalar(value) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, (dict, list, tuple, set)):
        return ""
    return str(value).strip()


def _candidate_match_keys(listing: MarketplaceListing, lookup_value: str) -> list[str]:
    matched_keys = []
    if _trimmed_scalar(listing.external_primary_id) == lookup_value:
        matched_keys.append("external_primary_id")
    if _trimmed_scalar(listing.seller_article) == lookup_value:
        matched_keys.append("seller_article")
    external_ids = listing.external_ids if isinstance(listing.external_ids, dict) else {}
    for key in _external_id_keys(listing.marketplace):
        if _trimmed_scalar(external_ids.get(key)) == lookup_value:
            matched_keys.append(f"external_ids.{key}")
    return matched_keys


def resolve_listing_for_detail_row(row: OperationDetailRow) -> ResolveResult:
    operation = row.operation
    if not operation.store_id or not operation.marketplace:
        return ResolveResult(conflict_class=CONFLICT_STORE_MARKETPLACE_MISMATCH)

    lookup_value = (row.product_ref or "").strip()
    if not lookup_value or not is_product_detail_row(row):
        return ResolveResult(conflict_class=CONFLICT_ROW_NOT_PRODUCT_IDENTIFIER)

    if operation.marketplace not in {Marketplace.WB, Marketplace.OZON}:
        return ResolveResult(conflict_class=CONFLICT_SOURCE_SCOPE_NOT_APPROVED)

    candidates: dict[int, tuple[MarketplaceListing, set[str]]] = {}
    duplicate_key_counts: defaultdict[str, int] = defaultdict(int)
    for listing in MarketplaceListing.objects.filter(
        marketplace=operation.marketplace,
        store_id=operation.store_id,
    ):
        matched_keys = _candidate_match_keys(listing, lookup_value)
        if not matched_keys:
            continue
        candidates[listing.pk] = (listing, set(matched_keys))
        for key in matched_keys:
            duplicate_key_counts[key] += 1

    if row.marketplace_listing_id:
        if row.marketplace_listing_id in candidates and len(candidates) == 1:
            listing, matched_keys = next(iter(candidates.values()))
            return ResolveResult(
                listing=listing,
                matched_key=sorted(matched_keys)[0],
                candidate_count=1,
                existing_same_fk=True,
            )
        return ResolveResult(
            conflict_class=CONFLICT_MULTIPLE_LISTING_MATCHES,
            candidate_count=len(candidates),
        )

    if not candidates:
        return ResolveResult(conflict_class=CONFLICT_NO_LISTING_MATCH)
    if len(candidates) > 1:
        duplicate = any(count > 1 for count in duplicate_key_counts.values())
        return ResolveResult(
            conflict_class=(
                CONFLICT_API_DATA_INTEGRITY_DUPLICATE
                if duplicate
                else CONFLICT_MULTIPLE_LISTING_MATCHES
            ),
            candidate_count=len(candidates),
        )

    listing, matched_keys = next(iter(candidates.values()))
    return ResolveResult(
        listing=listing,
        matched_key=sorted(matched_keys)[0],
        candidate_count=1,
    )


def _safe_row_key_hash(row: OperationDetailRow) -> str:
    basis = f"{row.operation_id}:{row.id}:{(row.product_ref or '').strip()}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def _record_enrichment_error(
    *,
    row: OperationDetailRow,
    result: ResolveResult,
    family: str,
    severity: str = "warning",
) -> None:
    create_techlog_record(
        severity=severity,
        event_type=TechLogEventType.OPERATION_DETAIL_ROW_ENRICHMENT_ERROR,
        source_component="apps.operations.listing_enrichment",
        operation=row.operation,
        store=row.operation.store,
        entity_type="OperationDetailRow",
        entity_id=str(row.pk),
        safe_message="Operation detail row listing FK enrichment skipped or failed.",
        sensitive_details_ref="redacted:operation-detail-row-enrichment",
    )


def enrich_detail_row_marketplace_listing(
    row: OperationDetailRow,
    *,
    dry_run: bool = False,
    emit_techlog: bool = True,
) -> ResolveResult:
    result = resolve_listing_for_detail_row(row)
    if not result.matched:
        if emit_techlog and result.conflict_class:
            _record_enrichment_error(
                row=row,
                result=result,
                family=operation_family(row),
                severity=(
                    "error"
                    if result.conflict_class == CONFLICT_STORE_MARKETPLACE_MISMATCH
                    else "warning"
                ),
            )
        return result
    if result.existing_same_fk or row.marketplace_listing_id == result.listing.pk:
        return result
    if result.listing.store_id != row.operation.store_id or result.listing.marketplace != row.operation.marketplace:
        return ResolveResult(conflict_class=CONFLICT_STORE_MARKETPLACE_MISMATCH)
    if dry_run:
        return result

    with transaction.atomic():
        locked = OperationDetailRow.objects.select_for_update().select_related("operation").get(pk=row.pk)
        if locked.marketplace_listing_id:
            return resolve_listing_for_detail_row(locked)
        with allow_operation_detail_listing_fk_enrichment_update():
            updated = OperationDetailRow.objects.filter(pk=locked.pk).update(
                marketplace_listing_id=result.listing.pk,
            )
        if updated != 1:
            raise ValidationError("Operation detail listing FK enrichment did not update exactly one row.")
        create_audit_record(
            action_code=AuditActionCode.OPERATION_DETAIL_ROW_LISTING_FK_ENRICHED,
            entity_type="OperationDetailRow",
            entity_id=str(locked.pk),
            user=getattr(locked.operation, "initiator_user", None),
            store=locked.operation.store,
            operation=locked.operation,
            safe_message="Operation detail row listing FK enriched.",
            after_snapshot={
                "row_id": locked.pk,
                "operation_id": locked.operation_id,
                "operation_visible_id": locked.operation.visible_id,
                "listing_id": result.listing.pk,
                "matched_key_class": result.matched_key,
                "operation_family": operation_family(locked),
                "write_source": "listing_fk_enrichment",
                "product_ref_key_hash": _safe_row_key_hash(locked),
            },
            source_context=AuditSourceContext.SERVICE,
        )
    return result


def operation_detail_product_ref_checksum(*, max_id: int | None = None) -> tuple[int, str]:
    queryset = OperationDetailRow.objects.order_by("id").values_list("id", "product_ref")
    if max_id is not None:
        queryset = queryset.filter(id__lte=max_id)
    digest = hashlib.md5()
    count = 0
    for row_id, product_ref in queryset.iterator():
        if count:
            digest.update(b"|")
        digest.update(f"{row_id}:{product_ref if product_ref is not None else '<NULL>'}".encode("utf-8"))
        count += 1
    return count, digest.hexdigest()


def count_same_scope_fk_violations() -> int:
    return OperationDetailRow.objects.filter(marketplace_listing__isnull=False).exclude(
        operation__store_id=models.F("marketplace_listing__store_id"),
    ).count() + OperationDetailRow.objects.filter(marketplace_listing__isnull=False).exclude(
        operation__marketplace=models.F("marketplace_listing__marketplace"),
    ).count()


def backfill_operation_detail_listing_fk(
    *,
    dry_run: bool = True,
    limit: int = 1000,
    start_id: int | None = None,
    end_id: int | None = None,
) -> BackfillReport:
    high_water_id = OperationDetailRow.objects.order_by("-id").values_list("id", flat=True).first()
    row_count_before, checksum_before = operation_detail_product_ref_checksum(max_id=high_water_id)
    before_product_refs = dict(
        OperationDetailRow.objects.filter(id__lte=high_water_id).values_list("id", "product_ref")
    )
    report = BackfillReport(
        dry_run=dry_run,
        row_count_before=row_count_before,
        checksum_before=checksum_before,
    )

    queryset = OperationDetailRow.objects.select_related("operation").order_by("id")
    queryset = queryset.filter(id__lte=high_water_id)
    if start_id is not None:
        queryset = queryset.filter(id__gte=start_id)
    if end_id is not None:
        queryset = queryset.filter(id__lte=end_id)
    if limit:
        queryset = queryset[:limit]

    for row in queryset:
        family = operation_family(row)
        report.scanned_count += 1
        report.family_counts[family] += 1
        result = enrich_detail_row_marketplace_listing(row, dry_run=dry_run, emit_techlog=False)
        if result.matched:
            if result.existing_same_fk or row.marketplace_listing_id == result.listing.pk:
                report.idempotent_count += 1
            else:
                report.enriched_count += 1
                report.enriched_by_family[family] += 1
        else:
            report.skipped_count += 1
            report.skipped_by_family[family] += 1
            report.conflict_counts[result.conflict_class] += 1

    report.row_count_after, report.checksum_after = operation_detail_product_ref_checksum(max_id=high_water_id)
    after_product_refs = dict(
        OperationDetailRow.objects.filter(id__lte=high_water_id).values_list("id", "product_ref")
    )
    report.changed_product_ref_count = sum(
        1
        for row_id, product_ref in before_product_refs.items()
        if after_product_refs.get(row_id) != product_ref
    )
    report.same_scope_violation_count = count_same_scope_fk_violations()
    if not dry_run and report.conflict_counts:
        create_techlog_record(
            severity="error" if report.same_scope_violation_count else "warning",
            event_type=TechLogEventType.OPERATION_DETAIL_ROW_ENRICHMENT_ERROR,
            source_component="apps.operations.listing_enrichment",
            safe_message="Operation detail row listing FK enrichment completed with skipped rows.",
            sensitive_details_ref="redacted:operation-detail-row-enrichment-backfill",
        )
    return report
