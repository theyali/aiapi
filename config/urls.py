from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect


urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("apps.core.urls")),
    path("api/", include("apps.gateway.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("api-keys/", include("apps.api_keys.urls")),
]