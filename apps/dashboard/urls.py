from django.urls import path

from apps.dashboard.ajax import ajax_change_password

from .views import (
    dashboard_view,
    settings_view,
    guides_view,
    ai_image_view,
)

app_name = "dashboard"

urlpatterns = [
    path("", dashboard_view, name="index"),
    path("settings/", settings_view, name="settings"),
    path("guides/", guides_view, name="guides"),
    path("ai-image/", ai_image_view, name="ai_image"),
    path("ajax/change-password/", ajax_change_password, name="ajax_change_password"),
]