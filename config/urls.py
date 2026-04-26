"""URL configuration for the stage 1 bootstrap."""
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("apps.stores.urls")),
    path("", include("apps.web.urls")),
]
