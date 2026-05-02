from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.operations.models import (
    CheckStatus,
    Marketplace,
    MessageLevel,
    Operation,
    OperationDetailRow,
    OperationType,
    Run,
)
from apps.product_core.models import InternalProduct, MarketplaceListing, ProductVariant
from apps.stores.models import StoreAccount

from .models import MarketplaceProduct, MarketplaceProductHistory
from .services import (
    backfill_marketplace_listings_from_legacy_products,
    record_product_from_operation_detail,
    sync_listing_from_legacy_product,
    validate_legacy_product_listing_backfill,
)


class MarketplaceProductListingCompatibilityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            login="product-migration",
            password="password",
            display_name="Product Migration",
        )
        self.store = StoreAccount.objects.create(
            name="WB Store",
            marketplace=StoreAccount.Marketplace.WB,
            cabinet_type=StoreAccount.CabinetType.STORE,
        )

    def test_sync_listing_from_legacy_product_copies_legacy_fields_without_variant(self):
        product = MarketplaceProduct.objects.create(
            marketplace="wb",
            store=self.store,
            sku="1001",
            external_ids={"nmID": "1001", "vendorCode": "ART-1001"},
            title="Marketplace title",
            barcode="460000000001",
            last_values={"price": "100.00"},
        )

        listing = sync_listing_from_legacy_product(product)

        self.assertEqual(listing.marketplace, product.marketplace)
        self.assertEqual(listing.store, product.store)
        self.assertEqual(listing.external_primary_id, "1001")
        self.assertEqual(listing.external_ids, product.external_ids)
        self.assertEqual(listing.seller_article, "ART-1001")
        self.assertEqual(listing.barcode, product.barcode)
        self.assertEqual(listing.title, product.title)
        self.assertEqual(listing.last_values, product.last_values)
        self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.UNMATCHED)
        self.assertIsNone(listing.internal_variant_id)
        self.assertEqual(listing.last_source, "migration")
        self.assertEqual(InternalProduct.objects.count(), 0)
        self.assertEqual(ProductVariant.objects.count(), 0)
        self.assertTrue(listing.history.filter(change_type="appeared", source="migration").exists())

    def test_backfill_is_rerunnable_and_validation_reports_no_missing_listings(self):
        MarketplaceProduct.objects.create(
            marketplace="wb",
            store=self.store,
            sku="1001",
            external_ids={"nmID": "1001"},
        )
        MarketplaceProduct.objects.create(
            marketplace="wb",
            store=self.store,
            sku="1002",
            external_ids={"nmID": "1002"},
        )

        first_result = backfill_marketplace_listings_from_legacy_products()
        second_result = backfill_marketplace_listings_from_legacy_products()
        validation = validate_legacy_product_listing_backfill()

        self.assertEqual(first_result["legacy_products"], 2)
        self.assertEqual(first_result["created_listings"], 2)
        self.assertEqual(second_result["created_listings"], 0)
        self.assertEqual(MarketplaceListing.objects.count(), 2)
        self.assertEqual(validation["missing_listing_product_ids"], [])
        self.assertEqual(validation["mismatched_mapping_product_ids"], [])

    def test_record_product_from_operation_detail_preserves_product_ref_and_syncs_listing(self):
        run = Run.objects.create(
            marketplace=Marketplace.WB,
            store=self.store,
            initiated_by=self.user,
        )
        operation = Operation.objects.create(
            marketplace=Marketplace.WB,
            operation_type=OperationType.CHECK,
            status=CheckStatus.CREATED,
            run=run,
            store=self.store,
            initiator_user=self.user,
            logic_version="test",
        )
        detail = OperationDetailRow.objects.create(
            operation=operation,
            row_no=1,
            product_ref="1001",
            row_status="valid",
            reason_code="wb_valid_calculated",
            message_level=MessageLevel.INFO,
            message="ok",
        )

        product = record_product_from_operation_detail(operation, detail)
        detail.refresh_from_db()

        self.assertEqual(detail.product_ref, "1001")
        self.assertEqual(product.sku, "1001")
        self.assertTrue(MarketplaceProductHistory.objects.filter(product=product).exists())
        listing = MarketplaceListing.objects.get(
            marketplace="wb",
            store=self.store,
            external_primary_id="1001",
        )
        self.assertEqual(listing.mapping_status, MarketplaceListing.MappingStatus.UNMATCHED)
        self.assertIsNone(listing.internal_variant_id)
