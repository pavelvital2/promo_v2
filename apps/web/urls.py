from django.urls import path

from . import views


app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("marketplaces/", views.marketplaces, name="marketplaces"),
    path("marketplaces/wb/discounts/excel/", views.wb_excel, name="wb_excel"),
    path("marketplaces/ozon/discounts/excel/", views.ozon_excel, name="ozon_excel"),
    path("operations/", views.operation_list, name="operation_list"),
    path("operations/<str:visible_id>/", views.operation_card, name="operation_card"),
    path("operations/<str:visible_id>/result/", views.operation_result, name="operation_result"),
    path("operations/<str:visible_id>/confirm-warnings/", views.warning_confirmation, name="warning_confirmation"),
    path("files/versions/<int:version_id>/download/", views.download_file, name="download_file"),
    path("references/", views.reference_index, name="reference_index"),
    path("references/products/", views.product_list, name="product_list"),
    path("references/products/<int:pk>/", views.product_card, name="product_card"),
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
