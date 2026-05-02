from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.audit.models import AuditActionCode, AuditRecord
from apps.identity_access.models import AccessEffect, Role, StoreAccess, UserPermissionOverride
from apps.identity_access.seeds import (
    ROLE_LOCAL_ADMIN,
    ROLE_MARKETPLACE_MANAGER,
    ROLE_OBSERVER,
    seed_identity_access,
)
from apps.stores.models import StoreAccount
from apps.techlog.models import TechLogEventType, TechLogRecord, TechLogSeverity
from apps.techlog.services import create_techlog_record
from apps.operations.models import OperationStepCode
from apps.operations.services import create_api_operation

from .models import (
    InternalProduct,
    ListingSource,
    Marketplace,
    MarketplaceListing,
    MarketplaceSyncRun,
    PriceSnapshot,
    PromotionSnapshot,
    ProductIdentifier,
    ProductIdentifierSource,
    ProductMappingHistory,
    ProductStatus,
    ProductVariant,
    SalesPeriodSnapshot,
    StockSnapshot,
    validate_core2_internal_sku,
)
from .services import (
    can_view_marketplace_listing,
    can_view_marketplace_snapshot,
    can_view_marketplace_snapshot_technical_details,
    complete_marketplace_sync_run,
    create_price_snapshot,
    create_promotion_snapshot,
    create_stock_snapshot,
    DuplicateActiveSyncRun,
    exact_mapping_candidates_for_listing,
    fail_marketplace_sync_run,
    map_listing_to_variant,
    MarketplaceSyncAdapterError,
    mark_listing_conflict,
    mark_listing_needs_review,
    marketplace_listings_visible_to,
    refresh_mapping_candidate_status,
    start_marketplace_sync_run,
    sync_ozon_elastic_action_rows_to_product_core,
    sync_ozon_elastic_stock_rows_to_product_core,
    sync_wb_price_rows_to_product_core,
    sync_wb_regular_promotion_rows_to_product_core,
    unmap_listing,
)


class ProductCoreModelTests(TestCase):
    def setUp(self):
        self.wb_store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
        )
        self.ozon_store = StoreAccount.objects.create(
            name="Ozon Store",
            marketplace=StoreAccount.Marketplace.OZON,
        )
        self.product = InternalProduct.objects.create(
            internal_code="IP-001",
            name="Internal product",
            product_type=InternalProduct.ProductType.FINISHED_GOOD,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            internal_sku="SKU-001",
            name="Default variant",
        )

    def test_internal_product_variant_and_identifier_constraints(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            InternalProduct.objects.create(internal_code="IP-001", name="Duplicate")

        with self.assertRaises(IntegrityError), transaction.atomic():
            ProductVariant.objects.create(
                product=self.product,
                internal_sku="SKU-001",
                name="Duplicate SKU",
            )

        ProductIdentifier.objects.create(
            variant=self.variant,
            identifier_type=ProductIdentifier.IdentifierType.WB_VENDOR_CODE,
            value="WB-ART-1",
            source=ProductIdentifierSource.MANUAL,
            is_primary=True,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            ProductIdentifier.objects.create(
                variant=self.variant,
                identifier_type=ProductIdentifier.IdentifierType.WB_VENDOR_CODE,
                value="WB-ART-2",
                source=ProductIdentifierSource.MANUAL,
                is_primary=True,
            )

    def test_core2_internal_sku_validator_accepts_fixed_structured_examples(self):
        valid_skus = [
            "nash_kit2_rg_pict0001",
            "chev_pz_kit2_text0001",
            "nash_mvd_pict0001",
            "chev_back_mvd_text0001",
        ]

        for internal_sku in valid_skus:
            with self.subTest(internal_sku=internal_sku):
                validate_core2_internal_sku(internal_sku)
                variant = ProductVariant(
                    product=self.product,
                    internal_sku=internal_sku,
                    name="Structured variant",
                )
                variant.full_clean()

    def test_core2_internal_sku_validator_rejects_non_unified_examples(self):
        invalid_skus = [
            "SKU-001",
            "NASH_MVD_PICT0001",
            "nash-pict0001",
            "nash_mvd_photo0001",
            "nash_rg_pict001",
            "chev_kit0_text0001",
            "wb123456",
        ]

        for internal_sku in invalid_skus:
            with self.subTest(internal_sku=internal_sku):
                with self.assertRaises(ValidationError):
                    validate_core2_internal_sku(internal_sku)

    def test_manual_confirmed_variant_allows_legacy_internal_sku(self):
        variant = ProductVariant(
            product=self.product,
            internal_sku="MANUAL-LEGACY-001",
            name="Manual legacy variant",
            review_state=ProductVariant.ReviewState.MANUAL_CONFIRMED,
        )

        variant.full_clean()

    def test_manual_confirmed_variant_allows_blank_internal_sku(self):
        variant = ProductVariant(
            product=self.product,
            internal_sku="   ",
            name="Manual blank SKU variant",
            review_state=ProductVariant.ReviewState.MANUAL_CONFIRMED,
        )

        variant.full_clean()
        self.assertEqual(variant.internal_sku, "")

    def test_imported_draft_variant_requires_structured_internal_sku(self):
        variant = ProductVariant(
            product=self.product,
            internal_sku="SKU-001",
            name="Imported draft variant",
            review_state=ProductVariant.ReviewState.IMPORTED_DRAFT,
            import_source_context={
                "basis": "api_valid_internal_sku",
                "source": "wb_api_prices",
                "seller_article": "SKU-001",
            },
        )

        with self.assertRaises(ValidationError):
            variant.full_clean()

    def test_imported_draft_variant_rejects_blank_internal_sku(self):
        for internal_sku in ["", "   "]:
            with self.subTest(internal_sku=repr(internal_sku)):
                variant = ProductVariant(
                    product=self.product,
                    internal_sku=internal_sku,
                    name="Imported draft blank SKU variant",
                    review_state=ProductVariant.ReviewState.IMPORTED_DRAFT,
                    import_source_context={
                        "basis": "api_valid_internal_sku",
                        "source": "wb_api_prices",
                        "seller_article": internal_sku,
                    },
                )

                with self.assertRaises(ValidationError) as context:
                    variant.full_clean()

                self.assertIn("internal_sku", context.exception.error_dict)

    def test_imported_draft_lifecycle_is_explicit_and_separate_from_status(self):
        imported_product = InternalProduct.objects.create(
            internal_code="nash_kit2_rg_pict0001",
            name="Imported product shell",
        )
        variant = ProductVariant.objects.create(
            product=imported_product,
            internal_sku="nash_kit2_rg_pict0001",
            name="Imported draft variant",
            status=ProductStatus.ACTIVE,
            review_state=ProductVariant.ReviewState.IMPORTED_DRAFT,
            import_source_context={
                "basis": "api_valid_internal_sku",
                "source": "wb_api_prices",
                "seller_article": "nash_kit2_rg_pict0001",
            },
        )

        variant.full_clean()
        self.assertEqual(variant.status, ProductStatus.ACTIVE)
        self.assertEqual(variant.review_state, ProductVariant.ReviewState.IMPORTED_DRAFT)
        self.assertEqual(variant.import_source_context["basis"], "api_valid_internal_sku")

    def test_listing_requires_store_marketplace_and_variant_for_matched_status(self):
        listing = MarketplaceListing(
            marketplace=Marketplace.WB,
            store=self.ozon_store,
            external_primary_id="100",
            mapping_status=MarketplaceListing.MappingStatus.UNMATCHED,
            last_source="manual_import",
        )
        with self.assertRaises(ValidationError):
            listing.full_clean()

        matched_without_variant = MarketplaceListing(
            marketplace=Marketplace.WB,
            store=self.wb_store,
            external_primary_id="101",
            mapping_status=MarketplaceListing.MappingStatus.MATCHED,
            last_source="manual_import",
        )
        with self.assertRaises(ValidationError):
            matched_without_variant.full_clean()

        matched = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=self.wb_store,
            internal_variant=self.variant,
            external_primary_id="102",
            mapping_status=MarketplaceListing.MappingStatus.MATCHED,
            last_source="manual_import",
        )
        self.assertEqual(matched.internal_variant, self.variant)

    def test_listing_external_identity_is_unique_per_marketplace_and_store(self):
        MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=self.wb_store,
            external_primary_id="nm-1",
            last_source="migration",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            MarketplaceListing.objects.create(
                marketplace=Marketplace.WB,
                store=self.wb_store,
                external_primary_id="nm-1",
                last_source="migration",
            )

    def test_sync_run_and_price_snapshot_context_validation(self):
        started_at = timezone.now()
        sync_run = MarketplaceSyncRun.objects.create(
            marketplace=Marketplace.WB,
            store=self.wb_store,
            sync_type=MarketplaceSyncRun.SyncType.PRICES,
            source="wb_api_prices",
            started_at=started_at,
        )
        listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=self.wb_store,
            external_primary_id="nm-2",
            last_source="wb_api_prices",
            last_sync_run=sync_run,
        )
        PriceSnapshot.objects.create(
            listing=listing,
            sync_run=sync_run,
            snapshot_at=started_at,
            price=Decimal("100.00"),
            currency="RUB",
        )

        other_sync_run = MarketplaceSyncRun.objects.create(
            marketplace=Marketplace.OZON,
            store=self.ozon_store,
            sync_type=MarketplaceSyncRun.SyncType.PRICES,
            source="ozon_api_actions",
            started_at=started_at,
        )
        inconsistent_snapshot = PriceSnapshot(
            listing=listing,
            sync_run=other_sync_run,
            snapshot_at=started_at,
            price=Decimal("100.00"),
            currency="RUB",
        )
        with self.assertRaises(ValidationError):
            inconsistent_snapshot.full_clean()

    def test_sales_period_snapshot_rejects_inverted_period(self):
        started_at = timezone.now()
        sync_run = MarketplaceSyncRun.objects.create(
            marketplace=Marketplace.WB,
            store=self.wb_store,
            sync_type=MarketplaceSyncRun.SyncType.SALES,
            source="wb_api_prices",
            started_at=started_at,
        )
        listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=self.wb_store,
            external_primary_id="nm-3",
            last_source="wb_api_prices",
        )

        snapshot = SalesPeriodSnapshot(
            listing=listing,
            sync_run=sync_run,
            period_start=started_at,
            period_end=started_at - timedelta(days=1),
        )

        with self.assertRaises(ValidationError):
            snapshot.full_clean()

    def test_product_mapping_history_records_result_status_context_and_reason(self):
        listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=self.wb_store,
            external_primary_id="nm-map-history",
            seller_article="ART-001",
            barcode="460000000001",
            last_source="manual_import",
        )
        other_product = InternalProduct.objects.create(
            internal_code="IP-002",
            name="Other internal product",
        )
        other_variant = ProductVariant.objects.create(
            product=other_product,
            internal_sku="SKU-002",
            name="Other variant",
        )
        changed_at = timezone.now()

        cases = [
            {
                "action": ProductMappingHistory.MappingAction.MAP,
                "previous_variant": None,
                "new_variant": self.variant,
                "mapping_status_after": MarketplaceListing.MappingStatus.MATCHED,
                "source_context": {
                    "basis": "exact_seller_article",
                    "listing_seller_article": "ART-001",
                    "variant_identifier": "ART-001",
                },
                "reason_comment": "Confirmed exact seller article candidate.",
            },
            {
                "action": ProductMappingHistory.MappingAction.UNMAP,
                "previous_variant": self.variant,
                "new_variant": None,
                "mapping_status_after": MarketplaceListing.MappingStatus.UNMATCHED,
                "source_context": {"basis": "manual_unmap"},
                "reason_comment": "Removed incorrect mapping.",
            },
            {
                "action": ProductMappingHistory.MappingAction.NEEDS_REVIEW_MARKER,
                "previous_variant": None,
                "new_variant": None,
                "mapping_status_after": MarketplaceListing.MappingStatus.NEEDS_REVIEW,
                "source_context": {
                    "basis": "multiple_exact_candidates",
                    "candidate_variant_ids": [self.variant.id, other_variant.id],
                },
                "reason_comment": "Multiple exact candidates require review.",
            },
            {
                "action": ProductMappingHistory.MappingAction.CONFLICT_MARKER,
                "previous_variant": self.variant,
                "new_variant": other_variant,
                "mapping_status_after": MarketplaceListing.MappingStatus.CONFLICT,
                "source_context": {
                    "basis": "conflicting_exact_matches",
                    "listing_barcode": "460000000001",
                    "candidate_variant_ids": [self.variant.id, other_variant.id],
                },
                "reason_comment": "Conflicting exact matches require resolution.",
            },
        ]

        for index, case in enumerate(cases):
            history = ProductMappingHistory.objects.create(
                listing=listing,
                changed_at=changed_at + timedelta(seconds=index),
                source="manual_import",
                **case,
            )

            history.refresh_from_db()
            self.assertEqual(history.mapping_status_after, case["mapping_status_after"])
            self.assertEqual(history.source_context, case["source_context"])
            self.assertEqual(history.reason_comment, case["reason_comment"])


class ProductCorePermissionsAuditTechlogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_identity_access()
        user_model = get_user_model()
        cls.local_admin = user_model.objects.create_user(
            login="pc-local-admin",
            password="test",
            display_name="PC Local Admin",
            primary_role=Role.objects.get(code=ROLE_LOCAL_ADMIN),
        )
        cls.manager = user_model.objects.create_user(
            login="pc-manager",
            password="test",
            display_name="PC Manager",
            primary_role=Role.objects.get(code=ROLE_MARKETPLACE_MANAGER),
        )
        cls.observer = user_model.objects.create_user(
            login="pc-observer",
            password="test",
            display_name="PC Observer",
            primary_role=Role.objects.get(code=ROLE_OBSERVER),
        )
        cls.wb_store = StoreAccount.objects.create(
            name="WB Product Core Store",
            marketplace=StoreAccount.Marketplace.WB,
        )
        cls.other_store = StoreAccount.objects.create(
            name="Other Product Core Store",
            marketplace=StoreAccount.Marketplace.WB,
        )
        StoreAccess.objects.create(
            user=cls.local_admin,
            store=cls.wb_store,
            access_level=StoreAccess.AccessLevel.ADMIN,
            effect=AccessEffect.ALLOW,
        )
        StoreAccess.objects.create(
            user=cls.manager,
            store=cls.wb_store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        StoreAccess.objects.create(
            user=cls.observer,
            store=cls.wb_store,
            access_level=StoreAccess.AccessLevel.VIEW,
            effect=AccessEffect.ALLOW,
        )
        cls.product = InternalProduct.objects.create(
            internal_code="PC-001",
            name="Product Core product",
        )
        cls.variant = ProductVariant.objects.create(
            product=cls.product,
            internal_sku="PC-SKU-001",
            name="Variant",
        )
        cls.listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=cls.wb_store,
            external_primary_id="pc-listing-1",
            seller_article="PC-ART-1",
            last_source=ListingSource.MANUAL_IMPORT,
        )
        cls.other_listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=cls.other_store,
            external_primary_id="pc-listing-2",
            last_source=ListingSource.MANUAL_IMPORT,
        )
        cls.sync_run = MarketplaceSyncRun.objects.create(
            marketplace=Marketplace.WB,
            store=cls.wb_store,
            sync_type=MarketplaceSyncRun.SyncType.PRICES,
            source=ListingSource.MANUAL_IMPORT,
            started_at=timezone.now(),
        )
        cls.snapshot = PriceSnapshot.objects.create(
            listing=cls.listing,
            sync_run=cls.sync_run,
            snapshot_at=timezone.now(),
            price=Decimal("100.00"),
            currency="RUB",
        )

    def test_listing_and_snapshot_object_access_is_store_scoped(self):
        self.assertTrue(can_view_marketplace_listing(self.manager, self.listing))
        self.assertFalse(can_view_marketplace_listing(self.manager, self.other_listing))
        self.assertEqual(
            list(marketplace_listings_visible_to(self.manager)),
            [self.listing],
        )
        self.assertTrue(can_view_marketplace_snapshot(self.manager, self.snapshot))
        self.assertFalse(
            can_view_marketplace_snapshot_technical_details(self.manager, self.snapshot),
        )
        self.assertFalse(can_view_marketplace_listing(self.observer, self.other_listing))

    def test_mapping_helper_requires_mapping_permission_and_records_audit_history(self):
        with self.assertRaises(PermissionDenied):
            map_listing_to_variant(
                actor=self.manager,
                listing=self.listing,
                variant=self.variant,
                source_context={"basis": "manual"},
            )

        history = map_listing_to_variant(
            actor=self.local_admin,
            listing=self.listing,
            variant=self.variant,
            source_context={"basis": "exact_seller_article"},
            reason_comment="Confirmed exact candidate.",
        )
        self.listing.refresh_from_db()

        self.assertEqual(history.action, ProductMappingHistory.MappingAction.MAP)
        self.assertEqual(self.listing.internal_variant, self.variant)
        self.assertEqual(self.listing.mapping_status, MarketplaceListing.MappingStatus.MATCHED)
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.MARKETPLACE_LISTING_MAPPED,
                entity_id=str(history.pk),
                store=self.wb_store,
                user=self.local_admin,
            ).exists(),
        )

        unmap_history = unmap_listing(
            actor=self.local_admin,
            listing=self.listing,
            source_context={"basis": "manual_unmap"},
        )
        self.listing.refresh_from_db()
        self.assertEqual(unmap_history.previous_variant, self.variant)
        self.assertIsNone(self.listing.internal_variant)
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.MARKETPLACE_LISTING_UNMAPPED,
                entity_id=str(unmap_history.pk),
            ).exists(),
        )

    def test_unmap_can_set_review_status_and_preserves_previous_variant(self):
        map_listing_to_variant(
            actor=self.local_admin,
            listing=self.listing,
            variant=self.variant,
            source_context={"basis": "manual"},
        )

        history = unmap_listing(
            actor=self.local_admin,
            listing=self.listing,
            source_context={"basis": "manual_unmap"},
            mapping_status_after=MarketplaceListing.MappingStatus.NEEDS_REVIEW,
            reason_comment="Check another candidate.",
        )
        self.listing.refresh_from_db()

        self.assertEqual(history.previous_variant, self.variant)
        self.assertIsNone(self.listing.internal_variant)
        self.assertEqual(self.listing.mapping_status, MarketplaceListing.MappingStatus.NEEDS_REVIEW)

    def test_exact_candidate_suggestions_are_non_authoritative_and_exact_only(self):
        exact_article_variant = ProductVariant.objects.create(
            product=self.product,
            internal_sku="PC-ART-1",
            name="Exact article",
        )
        exact_barcode_variant = ProductVariant.objects.create(
            product=self.product,
            internal_sku="PC-BAR",
            barcode_internal="4600000000099",
            name="Exact barcode",
        )
        ProductIdentifier.objects.create(
            variant=self.variant,
            identifier_type=ProductIdentifier.IdentifierType.WB_VENDOR_CODE,
            value="WB-EXT-1",
        )
        partial_variant = ProductVariant.objects.create(
            product=self.product,
            internal_sku="PC-ART-1-PARTIAL",
            name="Partial should not match title",
        )
        listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=self.wb_store,
            external_primary_id="WB-EXT-1",
            external_ids={"nmID": "WB-EXT-1"},
            seller_article="PC-ART-1",
            barcode="4600000000099",
            title=partial_variant.name,
            last_source=ListingSource.MANUAL_IMPORT,
        )

        candidates = exact_mapping_candidates_for_listing(listing)
        candidate_variant_ids = {candidate.variant.pk for candidate in candidates}

        self.assertIn(exact_article_variant.pk, candidate_variant_ids)
        self.assertIn(exact_barcode_variant.pk, candidate_variant_ids)
        self.assertIn(self.variant.pk, candidate_variant_ids)
        self.assertNotIn(partial_variant.pk, candidate_variant_ids)
        listing.refresh_from_db()
        self.assertIsNone(listing.internal_variant)
        self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.UNMATCHED)

    def test_candidate_status_refresh_sets_needs_review_or_conflict_without_mapping(self):
        ProductVariant.objects.create(
            product=self.product,
            internal_sku="PC-ART-1",
            name="Single exact",
        )
        single_listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=self.wb_store,
            external_primary_id="single-candidate",
            seller_article="PC-ART-1",
            last_source=ListingSource.MANUAL_IMPORT,
        )

        history = refresh_mapping_candidate_status(actor=self.local_admin, listing=single_listing)
        single_listing.refresh_from_db()

        self.assertEqual(history.action, ProductMappingHistory.MappingAction.NEEDS_REVIEW_MARKER)
        self.assertIsNone(single_listing.internal_variant)
        self.assertEqual(single_listing.mapping_status, MarketplaceListing.MappingStatus.NEEDS_REVIEW)

        ProductVariant.objects.create(
            product=self.product,
            internal_sku="DUP-ART",
            name="Duplicate 1",
        )
        duplicate_identifier_variant = ProductVariant.objects.create(
            product=self.product,
            internal_sku="DUP-ART-2",
            name="Duplicate 2",
        )
        ProductIdentifier.objects.create(
            variant=duplicate_identifier_variant,
            identifier_type=ProductIdentifier.IdentifierType.LEGACY_ARTICLE,
            value="DUP-ART",
        )
        conflict_listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=self.wb_store,
            external_primary_id="multiple-candidates",
            seller_article="DUP-ART",
            last_source=ListingSource.MANUAL_IMPORT,
        )

        conflict_history = refresh_mapping_candidate_status(
            actor=self.local_admin,
            listing=conflict_listing,
        )
        conflict_listing.refresh_from_db()

        self.assertEqual(conflict_history.action, ProductMappingHistory.MappingAction.CONFLICT_MARKER)
        self.assertIsNone(conflict_listing.internal_variant)
        self.assertEqual(conflict_listing.mapping_status, MarketplaceListing.MappingStatus.CONFLICT)

    def test_manual_review_and_conflict_markers_write_history_and_audit(self):
        review_history = mark_listing_needs_review(
            actor=self.local_admin,
            listing=self.listing,
            source_context={"basis": "manual_marker"},
            reason_comment="Needs data owner review.",
        )
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.mapping_status, MarketplaceListing.MappingStatus.NEEDS_REVIEW)
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.MARKETPLACE_LISTING_MAPPING_REVIEW_MARKED,
                entity_id=str(review_history.pk),
            ).exists(),
        )

        conflict_history = mark_listing_conflict(
            actor=self.local_admin,
            listing=self.listing,
            source_context={"basis": "manual_marker"},
            reason_comment="Conflicting identifiers.",
        )
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.mapping_status, MarketplaceListing.MappingStatus.CONFLICT)
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.MARKETPLACE_LISTING_MAPPING_CONFLICT_MARKED,
                entity_id=str(conflict_history.pk),
            ).exists(),
        )

    def test_product_core_safe_contours_reject_secrets(self):
        with self.assertRaises(ValueError):
            map_listing_to_variant(
                actor=self.local_admin,
                listing=self.listing,
                variant=self.variant,
                source_context={"api_key": "abcdef123456"},
            )
        with self.assertRaises(ValueError):
            create_techlog_record(
                severity=TechLogSeverity.ERROR,
                event_type=TechLogEventType.MARKETPLACE_SYNC_SECRET_REDACTION_VIOLATION,
                source_component="apps.product_core",
                store=self.wb_store,
                safe_message="Authorization: Bearer abcdefghijklmnopqrstuvwxyz1234567890",
            )

    def test_direct_store_deny_blocks_product_core_listing_access(self):
        UserPermissionOverride.objects.create(
            user=self.manager,
            permission_id="marketplace_listing.view",
            effect=AccessEffect.DENY,
            store=self.wb_store,
        )

        self.assertFalse(can_view_marketplace_listing(self.manager, self.listing))

    def test_product_core_techlog_catalog_records_sync_and_migration_events(self):
        sync_record = create_techlog_record(
            severity=TechLogSeverity.INFO,
            event_type=TechLogEventType.MARKETPLACE_SYNC_STARTED,
            source_component="apps.product_core.sync",
            store=self.wb_store,
            safe_message="Marketplace listing sync started.",
        )
        migration_record = create_techlog_record(
            severity=TechLogSeverity.ERROR,
            event_type=TechLogEventType.PRODUCT_CORE_MIGRATION_FAILED,
            source_component="apps.product_core.migration",
            safe_message="Product Core migration failed.",
        )

        self.assertEqual(sync_record.severity, TechLogSeverity.INFO)
        self.assertEqual(migration_record.severity, TechLogSeverity.CRITICAL)
        self.assertTrue(TechLogRecord.objects.filter(pk=sync_record.pk).exists())


class ProductCoreSyncFoundationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_identity_access()
        user_model = get_user_model()
        cls.manager = user_model.objects.create_user(
            login="pc-sync-manager",
            password="test",
            display_name="PC Sync Manager",
            primary_role=Role.objects.get(code=ROLE_MARKETPLACE_MANAGER),
        )
        cls.store = StoreAccount.objects.create(
            name="WB Sync Store",
            marketplace=StoreAccount.Marketplace.WB,
        )
        cls.ozon_store = StoreAccount.objects.create(
            name="Ozon Sync Store",
            marketplace=StoreAccount.Marketplace.OZON,
        )
        StoreAccess.objects.create(
            user=cls.manager,
            store=cls.store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )
        StoreAccess.objects.create(
            user=cls.manager,
            store=cls.ozon_store,
            access_level=StoreAccess.AccessLevel.WORK,
            effect=AccessEffect.ALLOW,
        )

    def _listing(self, external_primary_id="sync-nm-1", last_values=None):
        return MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=self.store,
            external_primary_id=external_primary_id,
            last_values=last_values or {},
            last_source=ListingSource.MIGRATION,
        )

    def _structured_variant(
        self,
        internal_sku,
        *,
        product_code=None,
        title="Structured variant",
        status=None,
        product_status=None,
    ):
        product = InternalProduct.objects.create(
            internal_code=product_code or f"prod-{internal_sku}",
            name=title,
            product_type=InternalProduct.ProductType.FINISHED_GOOD,
            status=product_status or ProductStatus.ACTIVE,
        )
        return ProductVariant.objects.create(
            product=product,
            internal_sku=internal_sku,
            name=title,
            status=status or ProductStatus.ACTIVE,
        )

    def test_sync_run_start_complete_and_duplicate_active_guard(self):
        sync_run = start_marketplace_sync_run(
            marketplace=Marketplace.WB,
            store=self.store,
            sync_type=MarketplaceSyncRun.SyncType.PRICES,
            source=ListingSource.WB_API_PRICES,
            requested_by=self.manager,
            summary={"source": "wb_prices"},
        )
        self.assertEqual(sync_run.status, MarketplaceSyncRun.SyncStatus.RUNNING)
        self.assertIsNotNone(sync_run.started_at)

        with self.assertRaises(DuplicateActiveSyncRun):
            start_marketplace_sync_run(
                marketplace=Marketplace.WB,
                store=self.store,
                sync_type=MarketplaceSyncRun.SyncType.PRICES,
                source=ListingSource.WB_API_PRICES,
            )

        completed = complete_marketplace_sync_run(sync_run, summary={"rows": 0})
        self.assertEqual(completed.status, MarketplaceSyncRun.SyncStatus.COMPLETED_SUCCESS)
        self.assertIsNotNone(completed.finished_at)

        next_run = start_marketplace_sync_run(
            marketplace=Marketplace.WB,
            store=self.store,
            sync_type=MarketplaceSyncRun.SyncType.PRICES,
            source=ListingSource.WB_API_PRICES,
        )
        self.assertEqual(next_run.status, MarketplaceSyncRun.SyncStatus.RUNNING)

    def test_successful_sync_links_snapshots_to_operation_and_updates_listing_cache(self):
        operation = create_api_operation(
            marketplace=Marketplace.WB,
            store=self.store,
            initiator_user=self.manager,
            step_code=OperationStepCode.WB_API_PRICES_DOWNLOAD,
            logic_version="pc-sync-test",
        )
        listing = self._listing(last_values={"price": "90.00"})
        sync_run = start_marketplace_sync_run(
            marketplace=Marketplace.WB,
            store=self.store,
            sync_type=MarketplaceSyncRun.SyncType.PRICES,
            source=ListingSource.WB_API_PRICES,
            operation=operation,
            requested_by=self.manager,
        )
        price_snapshot = create_price_snapshot(
            sync_run=sync_run,
            listing=listing,
            price=Decimal("123.45"),
            price_with_discount=Decimal("100.00"),
            discount_percent=Decimal("19.00"),
            currency="RUB",
            raw_safe={"nmID": "sync-nm-1", "price": "123.45"},
            source_endpoint="wb_prices_list_goods_filter",
        )
        stock_snapshot = create_stock_snapshot(
            sync_run=sync_run,
            listing=listing,
            total_stock=7,
            stock_by_warehouse={"main": 7},
            raw_safe={"nmID": "sync-nm-1", "stock": 7},
            source_endpoint="wb_stock_future",
        )
        promotion_snapshot = create_promotion_snapshot(
            sync_run=sync_run,
            listing=listing,
            marketplace_promotion_id="promo-1",
            action_name="Current promo",
            participation_status="active",
            action_price=Decimal("99.00"),
            raw_safe={"promotion_id": "promo-1"},
            source_endpoint="wb_promotions",
        )

        complete_marketplace_sync_run(sync_run, summary={"rows": 1}, warning_count=1)
        listing.refresh_from_db()

        self.assertEqual(price_snapshot.operation, operation)
        self.assertEqual(stock_snapshot.operation, operation)
        self.assertEqual(promotion_snapshot.operation, operation)
        self.assertEqual(listing.last_sync_run, sync_run)
        self.assertEqual(listing.last_source, ListingSource.WB_API_PRICES)
        self.assertEqual(listing.last_values["price"], "123.45")
        self.assertEqual(listing.last_values["price_with_discount"], "100.00")
        self.assertEqual(listing.last_values["total_stock"], 7)
        self.assertEqual(listing.last_values["promotions"][0]["marketplace_promotion_id"], "promo-1")
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.MARKETPLACE_LISTING_SYNCED,
                entity_id=str(listing.pk),
                operation=operation,
            ).exists(),
        )

    def test_failed_sync_keeps_last_successful_listing_values_visible(self):
        listing = self._listing(last_values={"price": "75.00", "total_stock": 3})
        successful_run = start_marketplace_sync_run(
            marketplace=Marketplace.WB,
            store=self.store,
            sync_type=MarketplaceSyncRun.SyncType.PRICES,
            source=ListingSource.WB_API_PRICES,
        )
        create_price_snapshot(
            sync_run=successful_run,
            listing=listing,
            price=Decimal("80.00"),
            currency="RUB",
            raw_safe={"nmID": "sync-nm-1"},
        )
        complete_marketplace_sync_run(successful_run, summary={"rows": 1})
        listing.refresh_from_db()
        self.assertEqual(listing.last_values["price"], "80.00")
        last_successful_at = listing.last_successful_sync_at

        failed_run = start_marketplace_sync_run(
            marketplace=Marketplace.WB,
            store=self.store,
            sync_type=MarketplaceSyncRun.SyncType.PRICES,
            source=ListingSource.WB_API_PRICES,
        )
        create_price_snapshot(
            sync_run=failed_run,
            listing=listing,
            price=Decimal("10.00"),
            currency="RUB",
            raw_safe={"nmID": "sync-nm-1", "temporary": "bad_source_value"},
        )
        fail_marketplace_sync_run(failed_run, error_summary={"error": "temporary"})
        listing.refresh_from_db()

        self.assertEqual(listing.last_values["price"], "80.00")
        self.assertEqual(listing.last_sync_run, successful_run)
        self.assertEqual(listing.last_successful_sync_at, last_successful_at)

    def test_raw_safe_secret_values_are_rejected_by_service_and_model_save(self):
        listing = self._listing()
        sync_run = start_marketplace_sync_run(
            marketplace=Marketplace.WB,
            store=self.store,
            sync_type=MarketplaceSyncRun.SyncType.PRICES,
            source=ListingSource.WB_API_PRICES,
        )
        with self.assertRaises(ValueError):
            create_price_snapshot(
                sync_run=sync_run,
                listing=listing,
                price=Decimal("100.00"),
                currency="RUB",
                raw_safe={"Authorization": "Bearer abcdefghijklmnopqrstuvwxyz1234567890"},
            )
        with self.assertRaises(ValueError):
            PriceSnapshot.objects.create(
                listing=listing,
                sync_run=sync_run,
                snapshot_at=timezone.now(),
                price=Decimal("100.00"),
                currency="RUB",
                raw_safe={"api_key": "abcdef1234567890"},
            )
        self.assertFalse(StockSnapshot.objects.exists())
        self.assertFalse(PromotionSnapshot.objects.exists())

    def test_wb_price_adapter_upserts_listing_snapshot_and_cache(self):
        sync_run = sync_wb_price_rows_to_product_core(
            store=self.store,
            rows=[
                {
                    "nmID": 101,
                    "vendorCode": "ART-101",
                    "derived_price": "123.45",
                    "discounted_price": "100.00",
                    "discount": 19,
                    "currency": "RUB",
                    "external_ids": {"sizeIDs": [1], "techSizeNames": ["0"]},
                }
            ],
            requested_by=self.manager,
        )

        listing = MarketplaceListing.objects.get(store=self.store, external_primary_id="101")
        self.assertEqual(sync_run.status, MarketplaceSyncRun.SyncStatus.COMPLETED_SUCCESS)
        self.assertEqual(listing.seller_article, "ART-101")
        self.assertEqual(listing.last_values["price"], "123.45")
        self.assertEqual(listing.last_values["price_with_discount"], "100.00")
        self.assertEqual(PriceSnapshot.objects.filter(sync_run=sync_run, listing=listing).count(), 1)

    def test_api_exact_valid_article_links_existing_variant_with_history_and_audit(self):
        internal_sku = "nash_kit2_rg_pict0001"
        variant = self._structured_variant(internal_sku)

        sync_run = sync_wb_price_rows_to_product_core(
            store=self.store,
            rows=[
                {
                    "nmID": "api-link-1",
                    "vendorCode": internal_sku,
                    "derived_price": "123.45",
                    "currency": "RUB",
                }
            ],
            requested_by=self.manager,
        )

        listing = MarketplaceListing.objects.get(store=self.store, external_primary_id="api-link-1")
        history = ProductMappingHistory.objects.get(listing=listing)
        self.assertEqual(listing.internal_variant, variant)
        self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.MATCHED)
        self.assertEqual(history.action, ProductMappingHistory.MappingAction.MAP)
        self.assertEqual(history.source_context["basis"], "api_exact_valid_internal_sku")
        self.assertEqual(history.source_context["outcome"], "existing_variant_linked")
        self.assertEqual(history.sync_run, sync_run)
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.MARKETPLACE_LISTING_MAPPED,
                entity_id=str(history.pk),
                store=self.store,
                source_context="api",
            ).exists()
        )

    def test_api_article_matching_is_trim_only_not_case_hyphen_or_partial(self):
        internal_sku = "chev_pz_kit2_text0001"
        variant = self._structured_variant(internal_sku)

        sync_wb_price_rows_to_product_core(
            store=self.store,
            rows=[
                {
                    "nmID": "trim-match",
                    "vendorCode": f"  {internal_sku}  ",
                    "derived_price": "10.00",
                    "currency": "RUB",
                },
                {
                    "nmID": "case-no-match",
                    "vendorCode": internal_sku.upper(),
                    "derived_price": "10.00",
                    "currency": "RUB",
                },
                {
                    "nmID": "hyphen-no-match",
                    "vendorCode": internal_sku.replace("_", "-"),
                    "derived_price": "10.00",
                    "currency": "RUB",
                },
                {
                    "nmID": "partial-no-match",
                    "vendorCode": internal_sku[:-1],
                    "derived_price": "10.00",
                    "currency": "RUB",
                },
            ],
        )

        trim_listing = MarketplaceListing.objects.get(external_primary_id="trim-match")
        self.assertEqual(trim_listing.internal_variant, variant)
        self.assertEqual(trim_listing.mapping_status, MarketplaceListing.MappingStatus.MATCHED)
        for external_primary_id in ["case-no-match", "hyphen-no-match", "partial-no-match"]:
            with self.subTest(external_primary_id=external_primary_id):
                listing = MarketplaceListing.objects.get(external_primary_id=external_primary_id)
                self.assertIsNone(listing.internal_variant)
                self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.UNMATCHED)

    def test_api_valid_article_auto_creates_imported_draft_with_field_policy(self):
        internal_sku = "nash_mvd_pict0001"
        sync_run = sync_ozon_elastic_action_rows_to_product_core(
            store=self.ozon_store,
            action_id="auto-create",
            source_group="active",
            rows=[
                {
                    "product_id": "auto-create-1",
                    "offer_id": internal_sku,
                    "name": "First marketplace title",
                    "action_price": "120.00",
                }
            ],
            requested_by=self.manager,
        )

        listing = MarketplaceListing.objects.get(store=self.ozon_store, external_primary_id="auto-create-1")
        product = InternalProduct.objects.get(internal_code=internal_sku)
        variant = ProductVariant.objects.get(internal_sku=internal_sku)
        self.assertEqual(product.name, "First marketplace title")
        self.assertEqual(product.product_type, InternalProduct.ProductType.FINISHED_GOOD)
        self.assertEqual(product.status, ProductStatus.ACTIVE)
        self.assertIsNone(product.category)
        self.assertEqual(product.comments, "")
        self.assertEqual(product.attributes["structure"], "mvd")
        self.assertEqual(product.attributes["content_type"], "pict")
        self.assertEqual(variant.product, product)
        self.assertEqual(variant.name, "First marketplace title")
        self.assertEqual(variant.status, ProductStatus.ACTIVE)
        self.assertEqual(variant.review_state, ProductVariant.ReviewState.IMPORTED_DRAFT)
        self.assertEqual(variant.import_source_context["basis"], "api_exact_valid_internal_sku")
        self.assertEqual(listing.internal_variant, variant)
        self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.MATCHED)
        self.assertEqual(sync_run.summary["api_article_mapping_count"], 1)
        self.assertTrue(
            AuditRecord.objects.filter(
                action_code=AuditActionCode.PRODUCT_VARIANT_CREATED,
                entity_id=str(variant.pk),
                source_context="api",
            ).exists()
        )

    def test_api_reuses_existing_parent_when_no_variant_exists(self):
        internal_sku = "chev_back_mvd_text0001"
        parent = InternalProduct.objects.create(
            internal_code=internal_sku,
            name="Existing shell",
            product_type=InternalProduct.ProductType.FINISHED_GOOD,
            status=ProductStatus.ACTIVE,
        )

        sync_wb_price_rows_to_product_core(
            store=self.store,
            rows=[{"nmID": "reuse-parent", "vendorCode": internal_sku, "derived_price": "1.00", "currency": "RUB"}],
        )

        variant = ProductVariant.objects.get(internal_sku=internal_sku)
        self.assertEqual(variant.product, parent)
        self.assertEqual(InternalProduct.objects.filter(internal_code=internal_sku).count(), 1)

    def test_api_repeated_same_sku_reuses_variant_and_title_mismatch_marks_review(self):
        internal_sku = "nash_kit2_rg_pict0002"
        sync_ozon_elastic_action_rows_to_product_core(
            store=self.ozon_store,
            action_id="same-sku-1",
            source_group="active",
            rows=[
                {
                    "product_id": "same-sku-ozon-1",
                    "offer_id": internal_sku,
                    "name": "Original marketplace title",
                    "action_price": "120.00",
                }
            ],
        )
        variant = ProductVariant.objects.get(internal_sku=internal_sku)
        product = variant.product

        sync_wb_price_rows_to_product_core(
            store=self.store,
            rows=[
                {
                    "nmID": "same-sku-wb-1",
                    "vendorCode": internal_sku,
                    "derived_price": "10.00",
                    "currency": "RUB",
                }
            ],
        )
        sync_ozon_elastic_action_rows_to_product_core(
            store=self.ozon_store,
            action_id="same-sku-2",
            source_group="active",
            rows=[
                {
                    "product_id": "same-sku-ozon-2",
                    "offer_id": internal_sku,
                    "name": "Later different title",
                    "action_price": "121.00",
                }
            ],
        )

        variant.refresh_from_db()
        product.refresh_from_db()
        wb_listing = MarketplaceListing.objects.get(external_primary_id="same-sku-wb-1")
        ozon_listing = MarketplaceListing.objects.get(external_primary_id="same-sku-ozon-2")
        self.assertEqual(ProductVariant.objects.filter(internal_sku=internal_sku).count(), 1)
        self.assertEqual(InternalProduct.objects.filter(internal_code=internal_sku).count(), 1)
        self.assertEqual(wb_listing.internal_variant, variant)
        self.assertEqual(ozon_listing.internal_variant, variant)
        self.assertEqual(ozon_listing.title, "Later different title")
        self.assertEqual(product.name, "Original marketplace title")
        self.assertEqual(variant.name, "Original marketplace title")
        self.assertEqual(variant.review_state, ProductVariant.ReviewState.NEEDS_REVIEW)

    def test_api_blank_invalid_and_title_only_rows_remain_listing_only(self):
        internal_sku = "nash_kit2_rg_pict0003"
        self._structured_variant(internal_sku, title="Title Only Should Not Match")

        sync_ozon_elastic_action_rows_to_product_core(
            store=self.ozon_store,
            action_id="listing-only",
            source_group="active",
            rows=[
                {
                    "product_id": "blank-article",
                    "offer_id": "",
                    "name": "Title Only Should Not Match",
                    "action_price": "10.00",
                },
                {
                    "product_id": "legacy-article",
                    "offer_id": "LEGACY-001",
                    "name": "Title Only Should Not Match",
                    "action_price": "10.00",
                },
                {
                    "product_id": "internal-space",
                    "offer_id": "nash_kit2_rg_ pict0003",
                    "name": "Title Only Should Not Match",
                    "action_price": "10.00",
                },
            ],
        )

        for external_primary_id in ["blank-article", "legacy-article", "internal-space"]:
            with self.subTest(external_primary_id=external_primary_id):
                listing = MarketplaceListing.objects.get(external_primary_id=external_primary_id)
                self.assertIsNone(listing.internal_variant)
                self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.UNMATCHED)
        self.assertFalse(InternalProduct.objects.filter(internal_code="LEGACY-001").exists())

    def test_api_archived_variant_conflict_does_not_auto_create_or_overwrite(self):
        internal_sku = "chev_pz_kit2_text0002"
        archived_variant = self._structured_variant(
            internal_sku,
            product_code=f"archived-{internal_sku}",
            status=ProductStatus.ARCHIVED,
        )

        sync_wb_price_rows_to_product_core(
            store=self.store,
            rows=[
                {
                    "nmID": "archived-conflict",
                    "vendorCode": internal_sku,
                    "derived_price": "10.00",
                    "currency": "RUB",
                }
            ],
        )

        listing = MarketplaceListing.objects.get(external_primary_id="archived-conflict")
        self.assertIsNone(listing.internal_variant)
        self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.CONFLICT)
        self.assertEqual(ProductVariant.objects.filter(internal_sku=internal_sku).count(), 1)
        self.assertEqual(ProductVariant.objects.get(internal_sku=internal_sku), archived_variant)

    def test_api_inactive_variant_conflict_does_not_auto_link_or_auto_create(self):
        internal_sku = "chev_pz_kit2_text0003"
        inactive_variant = self._structured_variant(
            internal_sku,
            product_code=f"inactive-variant-{internal_sku}",
            status=ProductStatus.INACTIVE,
        )

        sync_wb_price_rows_to_product_core(
            store=self.store,
            rows=[
                {
                    "nmID": "inactive-variant-conflict",
                    "vendorCode": internal_sku,
                    "derived_price": "10.00",
                    "currency": "RUB",
                }
            ],
        )

        listing = MarketplaceListing.objects.get(external_primary_id="inactive-variant-conflict")
        self.assertIsNone(listing.internal_variant)
        self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.CONFLICT)
        self.assertEqual(ProductVariant.objects.filter(internal_sku=internal_sku).count(), 1)
        self.assertEqual(ProductVariant.objects.get(internal_sku=internal_sku), inactive_variant)

    def test_api_inactive_product_with_active_variant_conflict_does_not_auto_link(self):
        internal_sku = "nash_mvd_pict0004"
        variant = self._structured_variant(
            internal_sku,
            product_code=f"inactive-product-{internal_sku}",
            product_status=ProductStatus.INACTIVE,
        )

        sync_wb_price_rows_to_product_core(
            store=self.store,
            rows=[
                {
                    "nmID": "inactive-product-variant-conflict",
                    "vendorCode": internal_sku,
                    "derived_price": "10.00",
                    "currency": "RUB",
                }
            ],
        )

        listing = MarketplaceListing.objects.get(external_primary_id="inactive-product-variant-conflict")
        self.assertIsNone(listing.internal_variant)
        self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.CONFLICT)
        self.assertEqual(ProductVariant.objects.filter(internal_sku=internal_sku).count(), 1)
        self.assertEqual(ProductVariant.objects.get(internal_sku=internal_sku), variant)

    def test_api_inactive_parent_without_variant_conflict_does_not_auto_create(self):
        internal_sku = "chev_back_mvd_text0003"
        parent = InternalProduct.objects.create(
            internal_code=internal_sku,
            name="Inactive parent",
            product_type=InternalProduct.ProductType.FINISHED_GOOD,
            status=ProductStatus.INACTIVE,
        )

        sync_wb_price_rows_to_product_core(
            store=self.store,
            rows=[
                {
                    "nmID": "inactive-parent-conflict",
                    "vendorCode": internal_sku,
                    "derived_price": "10.00",
                    "currency": "RUB",
                }
            ],
        )

        listing = MarketplaceListing.objects.get(external_primary_id="inactive-parent-conflict")
        self.assertIsNone(listing.internal_variant)
        self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.CONFLICT)
        self.assertEqual(InternalProduct.objects.filter(internal_code=internal_sku).count(), 1)
        self.assertEqual(InternalProduct.objects.get(internal_code=internal_sku), parent)
        self.assertFalse(ProductVariant.objects.filter(internal_sku=internal_sku).exists())

    def test_api_existing_different_listing_mapping_is_conflict_not_overwritten(self):
        first_sku = "nash_mvd_pict0002"
        second_sku = "chev_back_mvd_text0002"
        first_variant = self._structured_variant(first_sku)
        second_variant = self._structured_variant(second_sku)
        listing = MarketplaceListing.objects.create(
            marketplace=Marketplace.WB,
            store=self.store,
            external_primary_id="prelinked-conflict",
            seller_article=first_sku,
            internal_variant=second_variant,
            mapping_status=MarketplaceListing.MappingStatus.MATCHED,
            last_source=ListingSource.MIGRATION,
        )

        sync_wb_price_rows_to_product_core(
            store=self.store,
            rows=[
                {
                    "nmID": "prelinked-conflict",
                    "vendorCode": first_sku,
                    "derived_price": "10.00",
                    "currency": "RUB",
                }
            ],
        )

        listing.refresh_from_db()
        self.assertEqual(listing.internal_variant, second_variant)
        self.assertNotEqual(listing.internal_variant, first_variant)
        self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.CONFLICT)

    def test_duplicate_valid_article_rows_are_excluded_from_auto_create_and_link(self):
        internal_sku = "nash_mvd_pict0003"
        sync_run = sync_wb_price_rows_to_product_core(
            store=self.store,
            rows=[
                {"nmID": "dup-valid-1", "vendorCode": internal_sku, "derived_price": "1.00", "currency": "RUB"},
                {"nmID": "dup-valid-2", "vendorCode": internal_sku, "derived_price": "2.00", "currency": "RUB"},
            ],
        )

        self.assertEqual(sync_run.summary["duplicate_external_article_count"], 1)
        self.assertEqual(sync_run.summary["api_article_mapping_count"], 0)
        self.assertFalse(MarketplaceListing.objects.filter(external_primary_id__startswith="dup-valid").exists())
        self.assertFalse(InternalProduct.objects.filter(internal_code=internal_sku).exists())
        self.assertFalse(ProductVariant.objects.filter(internal_sku=internal_sku).exists())

    def test_wb_price_adapter_uses_duplicate_active_sync_guard(self):
        start_marketplace_sync_run(
            marketplace=Marketplace.WB,
            store=self.store,
            sync_type=MarketplaceSyncRun.SyncType.PRICES,
            source=ListingSource.WB_API_PRICES,
        )

        with self.assertRaises(DuplicateActiveSyncRun):
            sync_wb_price_rows_to_product_core(
                store=self.store,
                rows=[{"nmID": 110, "derived_price": "10.00", "currency": "RUB"}],
            )

    def test_wb_price_adapter_failure_preserves_previous_cache(self):
        listing = self._listing(external_primary_id="102", last_values={"price": "77.00"})
        sync_wb_price_rows_to_product_core(
            store=self.store,
            rows=[{"nmID": 102, "derived_price": "88.00", "currency": "RUB"}],
        )
        listing.refresh_from_db()
        self.assertEqual(listing.last_values["price"], "88.00")
        last_sync_run = listing.last_sync_run

        with self.assertRaises(ValueError):
            sync_wb_price_rows_to_product_core(
                store=self.store,
                rows=[
                    {
                        "nmID": 102,
                        "derived_price": "10.00",
                        "currency": "RUB",
                        "external_ids": {"authorization": "Bearer abcdefghijklmnopqrstuvwxyz1234567890"},
                    }
                ],
            )

        listing.refresh_from_db()
        failed_run = MarketplaceSyncRun.objects.exclude(pk=last_sync_run.pk).latest("id")
        self.assertEqual(failed_run.status, MarketplaceSyncRun.SyncStatus.INTERRUPTED_FAILED)
        self.assertEqual(listing.last_values["price"], "88.00")
        self.assertEqual(listing.last_sync_run, last_sync_run)

    def test_wb_regular_promotion_adapter_skips_missing_listing_without_fabrication(self):
        sync_run = sync_wb_regular_promotion_rows_to_product_core(
            store=self.store,
            promotion_id=555,
            action_name="Regular promo",
            rows=[
                {
                    "nmID": 201,
                    "inAction": True,
                    "planPrice": "99.00",
                    "planDiscount": 10,
                    "currencyCode": "RUB",
                }
            ],
        )

        self.assertEqual(sync_run.status, MarketplaceSyncRun.SyncStatus.COMPLETED_WITH_WARNINGS)
        self.assertEqual(sync_run.summary["listings_upserted_count"], 0)
        self.assertEqual(sync_run.summary["listings_matched_count"], 0)
        self.assertEqual(sync_run.summary["missing_listing_match_count"], 1)
        self.assertFalse(MarketplaceListing.objects.filter(store=self.store, external_primary_id="201").exists())
        self.assertFalse(PromotionSnapshot.objects.filter(sync_run=sync_run).exists())

    def test_wb_regular_promotion_adapter_writes_snapshot_for_existing_deterministic_listing(self):
        listing = self._listing(external_primary_id="201")

        sync_run = sync_wb_regular_promotion_rows_to_product_core(
            store=self.store,
            promotion_id=555,
            action_name="Regular promo",
            rows=[
                {
                    "nmID": 201,
                    "inAction": True,
                    "planPrice": "99.00",
                    "planDiscount": 10,
                    "currencyCode": "RUB",
                }
            ],
        )

        listing.refresh_from_db()
        self.assertEqual(sync_run.status, MarketplaceSyncRun.SyncStatus.COMPLETED_SUCCESS)
        self.assertEqual(sync_run.summary["listings_upserted_count"], 0)
        self.assertEqual(sync_run.summary["listings_matched_count"], 1)
        self.assertEqual(sync_run.summary["promotion_snapshots_count"], 1)
        self.assertEqual(listing.last_values["promotions"][0]["marketplace_promotion_id"], "555")

    def test_wb_regular_auto_promotion_no_fabricated_rows(self):
        auto_run = sync_wb_regular_promotion_rows_to_product_core(
            store=self.store,
            promotion_id=556,
            rows=[{"nmID": 202}],
            is_auto_promotion=True,
        )

        self.assertEqual(auto_run.status, MarketplaceSyncRun.SyncStatus.COMPLETED_WITH_WARNINGS)
        self.assertFalse(MarketplaceListing.objects.filter(store=self.store, external_primary_id="202").exists())

    def test_ozon_elastic_adapter_scoped_success_and_invalid_group_failure(self):
        sync_run = sync_ozon_elastic_action_rows_to_product_core(
            store=self.ozon_store,
            action_id="act-1",
            source_group="active",
            rows=[
                {
                    "product_id": "9001",
                    "offer_id": "OFFER-1",
                    "name": "Ozon Product",
                    "action_price": "120.00",
                    "price_min_elastic": "100.00",
                    "price_max_elastic": "140.00",
                }
            ],
        )
        listing = MarketplaceListing.objects.get(store=self.ozon_store, external_primary_id="9001")
        self.assertEqual(sync_run.status, MarketplaceSyncRun.SyncStatus.COMPLETED_SUCCESS)
        self.assertEqual(listing.seller_article, "OFFER-1")
        self.assertEqual(sync_run.summary["not_full_catalog"], True)
        self.assertEqual(listing.last_values["promotions"][0]["marketplace_promotion_id"], "act-1")

        with self.assertRaises(MarketplaceSyncAdapterError):
            sync_ozon_elastic_action_rows_to_product_core(
                store=self.ozon_store,
                action_id="act-1",
                source_group="full_catalog",
                rows=[],
            )

    def test_duplicate_external_article_guard_skips_affected_rows(self):
        sync_run = sync_wb_price_rows_to_product_core(
            store=self.store,
            rows=[
                {"nmID": "301", "vendorCode": "DUP", "derived_price": "1.00", "currency": "RUB"},
                {"nmID": "302", "vendorCode": "DUP", "derived_price": "2.00", "currency": "RUB"},
                {"nmID": "303", "vendorCode": "OK", "derived_price": "3.00", "currency": "RUB"},
            ],
        )

        self.assertEqual(sync_run.status, MarketplaceSyncRun.SyncStatus.COMPLETED_WITH_WARNINGS)
        self.assertEqual(sync_run.summary["duplicate_external_article_count"], 1)
        self.assertFalse(MarketplaceListing.objects.filter(store=self.store, external_primary_id="301").exists())
        self.assertFalse(MarketplaceListing.objects.filter(store=self.store, external_primary_id="302").exists())
        self.assertTrue(MarketplaceListing.objects.filter(store=self.store, external_primary_id="303").exists())
        self.assertTrue(
            TechLogRecord.objects.filter(
                event_type=TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR,
                severity=TechLogSeverity.ERROR,
                store=self.store,
            ).exists()
        )
        techlog_record = TechLogRecord.objects.get(
            event_type=TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR,
            store=self.store,
        )
        self.assertEqual(techlog_record.severity, TechLogSeverity.ERROR)
        self.assertEqual(
            techlog_record.event_type,
            TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR,
        )

    def test_wb_price_duplicate_same_article_same_primary_id_is_skipped(self):
        sync_run = sync_wb_price_rows_to_product_core(
            store=self.store,
            rows=[
                {"nmID": "311", "vendorCode": "DUP-SAME", "derived_price": "1.00", "currency": "RUB"},
                {"nmID": "311", "vendorCode": "DUP-SAME", "derived_price": "2.00", "currency": "RUB"},
            ],
        )

        self.assertEqual(sync_run.status, MarketplaceSyncRun.SyncStatus.COMPLETED_WITH_WARNINGS)
        self.assertEqual(sync_run.summary["duplicate_external_article_count"], 1)
        self.assertEqual(sync_run.summary["source_data_integrity_warning"]["affected_rows_count"], 2)
        self.assertEqual(sync_run.summary["skipped_rows_count"], 2)
        self.assertFalse(MarketplaceListing.objects.filter(store=self.store, external_primary_id="311").exists())
        self.assertFalse(PriceSnapshot.objects.filter(sync_run=sync_run).exists())

    def test_wb_regular_promotion_duplicate_article_rows_skip_snapshots(self):
        self._listing(external_primary_id="401")

        sync_run = sync_wb_regular_promotion_rows_to_product_core(
            store=self.store,
            promotion_id=555,
            action_name="Regular promo",
            rows=[
                {
                    "nmID": "401",
                    "vendorCode": "PROMO-DUP",
                    "inAction": True,
                    "planPrice": "99.00",
                    "planDiscount": 10,
                    "currencyCode": "RUB",
                },
                {
                    "nmID": "401",
                    "vendorCode": "PROMO-DUP",
                    "inAction": True,
                    "planPrice": "98.00",
                    "planDiscount": 11,
                    "currencyCode": "RUB",
                },
            ],
        )

        self.assertEqual(sync_run.status, MarketplaceSyncRun.SyncStatus.COMPLETED_WITH_WARNINGS)
        self.assertEqual(sync_run.summary["duplicate_external_article_count"], 1)
        self.assertEqual(sync_run.summary["source_data_integrity_warning"]["affected_rows_count"], 2)
        self.assertEqual(sync_run.summary["listings_upserted_count"], 0)
        self.assertEqual(sync_run.summary["listings_matched_count"], 0)
        self.assertEqual(sync_run.summary["promotion_snapshots_count"], 0)
        self.assertEqual(sync_run.summary["skipped_rows_count"], 2)
        self.assertFalse(PromotionSnapshot.objects.filter(sync_run=sync_run).exists())
        self.assertTrue(
            TechLogRecord.objects.filter(
                event_type=TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR,
                severity=TechLogSeverity.ERROR,
                store=self.store,
            ).exists()
        )

    def test_ozon_elastic_duplicate_same_article_same_primary_id_is_skipped(self):
        sync_run = sync_ozon_elastic_action_rows_to_product_core(
            store=self.ozon_store,
            action_id="act-dup",
            source_group="active",
            rows=[
                {"product_id": "9011", "offer_id": "OZON-DUP", "action_price": "120.00"},
                {"product_id": "9011", "offer_id": "OZON-DUP", "action_price": "119.00"},
            ],
        )

        self.assertEqual(sync_run.status, MarketplaceSyncRun.SyncStatus.COMPLETED_WITH_WARNINGS)
        self.assertEqual(sync_run.summary["duplicate_external_article_count"], 1)
        self.assertEqual(sync_run.summary["source_data_integrity_warning"]["affected_rows_count"], 2)
        self.assertEqual(sync_run.summary["skipped_rows_count"], 2)
        self.assertFalse(MarketplaceListing.objects.filter(store=self.ozon_store, external_primary_id="9011").exists())
        self.assertFalse(PromotionSnapshot.objects.filter(sync_run=sync_run).exists())
        self.assertTrue(
            TechLogRecord.objects.filter(
                event_type=TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR,
                severity=TechLogSeverity.ERROR,
                store=self.ozon_store,
            ).exists()
        )

    def test_ozon_stock_adapter_sums_present_preserves_zero_and_keeps_in_way_null(self):
        sync_run = sync_ozon_elastic_stock_rows_to_product_core(
            store=self.ozon_store,
            action_id="stock-act",
            rows=[
                {
                    "product_id": "stock-1",
                    "offer_id": "O-STOCK-1",
                    "name": "Stock product",
                    "source_group": "active",
                    "stock_info": {
                        "stocks": [
                            {"type": "fbo", "present": "2", "reserved": "99"},
                            {"type": "fbs", "present": "3", "reserved": "1"},
                        ]
                    },
                },
                {
                    "product_id": "stock-0",
                    "offer_id": "O-STOCK-0",
                    "source_group": "candidate",
                    "stock_info": {"stocks": [{"type": "fbo", "present": "0", "reserved": "10"}]},
                },
            ],
        )

        listing = MarketplaceListing.objects.get(store=self.ozon_store, external_primary_id="stock-1")
        zero_listing = MarketplaceListing.objects.get(store=self.ozon_store, external_primary_id="stock-0")
        snapshot = StockSnapshot.objects.get(sync_run=sync_run, listing=listing)
        zero_snapshot = StockSnapshot.objects.get(sync_run=sync_run, listing=zero_listing)
        self.assertEqual(sync_run.status, MarketplaceSyncRun.SyncStatus.COMPLETED_SUCCESS)
        self.assertEqual(snapshot.total_stock, 5)
        self.assertEqual(zero_snapshot.total_stock, 0)
        self.assertIsNone(snapshot.in_way_to_client)
        self.assertIsNone(snapshot.in_way_from_client)
        self.assertEqual(snapshot.source_endpoint, "ozon_product_info_stocks")
        self.assertEqual(listing.last_values["total_stock"], 5)
        self.assertEqual(zero_listing.last_values["total_stock"], 0)
        self.assertEqual(snapshot.stock_by_warehouse["rows"][0]["reserved"], "99")

    def test_ozon_stock_adapter_skips_no_parseable_present_and_duplicate_articles(self):
        sync_run = sync_ozon_elastic_stock_rows_to_product_core(
            store=self.ozon_store,
            action_id="stock-warn",
            rows=[
                {
                    "product_id": "stock-missing",
                    "offer_id": "O-MISSING",
                    "stock_info": {"stocks": [{"type": "fbo", "reserved": "1"}]},
                },
                {
                    "product_id": "stock-dup-1",
                    "offer_id": "O-DUP",
                    "stock_info": {"stocks": [{"present": "4"}]},
                },
                {
                    "product_id": "stock-dup-2",
                    "offer_id": "O-DUP",
                    "stock_info": {"stocks": [{"present": "5"}]},
                },
            ],
        )

        self.assertEqual(sync_run.status, MarketplaceSyncRun.SyncStatus.COMPLETED_WITH_WARNINGS)
        self.assertEqual(sync_run.summary["stock_snapshots_count"], 0)
        self.assertEqual(sync_run.summary["no_parseable_present_count"], 1)
        self.assertEqual(sync_run.summary["duplicate_external_article_count"], 1)
        self.assertFalse(StockSnapshot.objects.filter(sync_run=sync_run).exists())
        self.assertFalse(MarketplaceListing.objects.filter(store=self.ozon_store, external_primary_id="stock-missing").exists())
        self.assertTrue(
            TechLogRecord.objects.filter(
                event_type=TechLogEventType.MARKETPLACE_SYNC_DATA_INTEGRITY_ERROR,
                severity=TechLogSeverity.ERROR,
                store=self.ozon_store,
            ).exists()
        )

    def test_adapter_redaction_rejects_secret_like_summaries(self):
        with self.assertRaises(ValueError):
            sync_ozon_elastic_action_rows_to_product_core(
                store=self.ozon_store,
                action_id="act-2",
                source_group="candidate",
                rows=[
                    {
                        "product_id": "9010",
                        "offer_id": "Bearer abcdefghijklmnopqrstuvwxyz1234567890",
                    }
                ],
            )
