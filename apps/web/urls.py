from django.urls import path

from . import views


app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("marketplaces/", views.marketplaces, name="marketplaces"),
    path("marketplaces/wb/discounts/excel/", views.wb_excel, name="wb_excel"),
    path("marketplaces/wb/discounts/api/", views.wb_api, name="wb_api"),
    path(
        "marketplaces/wb/discounts/api/upload/confirm/",
        views.wb_api_upload_confirm,
        name="wb_api_upload_confirm",
    ),
    path("marketplaces/ozon/discounts/excel/", views.ozon_excel, name="ozon_excel"),
    path(
        "marketplaces/ozon/actions/api/elastic-boosting/",
        views.ozon_elastic,
        name="ozon_elastic",
    ),
    path("operations/", views.operation_list, name="operation_list"),
    path("operations/<str:visible_id>/", views.operation_card, name="operation_card"),
    path("operations/<str:visible_id>/result/", views.operation_result, name="operation_result"),
    path("operations/<str:visible_id>/confirm-warnings/", views.warning_confirmation, name="warning_confirmation"),
    path("files/versions/<int:version_id>/download/", views.download_file, name="download_file"),
    path("references/", views.reference_index, name="reference_index"),
    path("references/products/", views.product_list, name="product_list"),
    path("references/products/<int:pk>/", views.product_card, name="product_card"),
    path("references/product-core/products/", views.internal_product_list, name="internal_product_list"),
    path(
        "references/product-core/products/export.csv",
        views.internal_product_export,
        name="internal_product_export",
    ),
    path(
        "references/product-core/variants/imported-drafts/",
        views.imported_draft_variant_list,
        name="imported_draft_variant_list",
    ),
    path(
        "references/product-core/variants/<int:variant_pk>/review/",
        views.imported_draft_variant_action,
        name="imported_draft_variant_action",
    ),
    path("references/product-core/products/create/", views.internal_product_create, name="internal_product_create"),
    path("references/product-core/products/<int:pk>/", views.internal_product_card, name="internal_product_card"),
    path(
        "references/product-core/products/<int:pk>/edit/",
        views.internal_product_update,
        name="internal_product_update",
    ),
    path(
        "references/product-core/products/<int:pk>/archive/",
        views.internal_product_archive,
        name="internal_product_archive",
    ),
    path("references/marketplace-listings/", views.marketplace_listing_list, name="marketplace_listing_list"),
    path(
        "references/marketplace-listings/export.csv",
        views.marketplace_listing_export,
        name="marketplace_listing_export",
    ),
    path(
        "references/marketplace-listings/latest-values.csv",
        views.listing_latest_values_export,
        name="listing_latest_values_export",
    ),
    path(
        "references/marketplace-listings/mapping-report.csv",
        views.listing_mapping_report_export,
        name="listing_mapping_report_export",
    ),
    path(
        "references/marketplace-listings/operation-links.csv",
        views.operation_link_report_export,
        name="operation_link_report_export",
    ),
    path(
        "references/marketplace-listings/unmatched/",
        views.unmatched_listing_list,
        name="unmatched_listing_list",
    ),
    path(
        "references/marketplace-listings/unmatched/export.csv",
        views.unmatched_listing_export,
        name="unmatched_listing_export",
    ),
    path(
        "references/marketplace-listings/<int:pk>/",
        views.marketplace_listing_card,
        name="marketplace_listing_card",
    ),
    path(
        "references/marketplace-listings/<int:pk>/mapping/",
        views.marketplace_listing_mapping,
        name="marketplace_listing_mapping",
    ),
    path(
        "references/product-core/products/<int:product_pk>/variants/create/",
        views.internal_variant_create,
        name="internal_variant_create",
    ),
    path(
        "references/product-core/products/<int:product_pk>/variants/<int:variant_pk>/edit/",
        views.internal_variant_update,
        name="internal_variant_update",
    ),
    path(
        "references/product-core/products/<int:product_pk>/variants/<int:variant_pk>/archive/",
        views.internal_variant_archive,
        name="internal_variant_archive",
    ),
    path("settings/", views.settings_index, name="settings_index"),
    path("settings/parameter-history/", views.parameter_history, name="parameter_history"),
    path("administration/", views.admin_index, name="admin_index"),
    path("administration/users/", views.user_list, name="user_list"),
    path("administration/users/<str:visible_id>/", views.user_card, name="user_card"),
    path("administration/roles/", views.role_list, name="role_list"),
    path("administration/roles/<str:code>/", views.role_card, name="role_card"),
    path("administration/permissions/", views.permission_list, name="permission_list"),
    path("administration/store-access/", views.store_access_list, name="store_access_list"),
    path("logs/", views.logs_index, name="logs_index"),
    path("logs/audit/", views.audit_list, name="audit_list"),
    path("logs/audit/<int:pk>/", views.audit_card, name="audit_card"),
    path("logs/techlog/", views.techlog_list, name="techlog_list"),
    path("logs/techlog/<int:pk>/", views.techlog_card, name="techlog_card"),
    path("logs/notifications/", views.notification_list, name="notification_list"),
]
