from django.urls import path

from . import views


app_name = "stores"

urlpatterns = [
    path("stores/", views.store_list, name="store_list"),
    path("stores/create/", views.store_create, name="store_create"),
    path("stores/<str:visible_id>/", views.store_card, name="store_card"),
    path("stores/<str:visible_id>/edit/", views.store_edit, name="store_edit"),
    path("stores/<str:visible_id>/history/", views.store_history, name="store_history"),
    path(
        "stores/<str:visible_id>/connections/new/",
        views.connection_edit,
        name="connection_create",
    ),
    path(
        "stores/<str:visible_id>/connections/<int:pk>/edit/",
        views.connection_edit,
        name="connection_edit",
    ),
]
