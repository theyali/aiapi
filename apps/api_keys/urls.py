from django.urls import path

from .ajax import (
    ajax_create_api_key,
    ajax_delete_api_key,
    ajax_regenerate_api_key,
    ajax_toggle_api_key,
)

app_name = "api_keys"

urlpatterns = [
    path("ajax/create/", ajax_create_api_key, name="ajax_create"),
    path("ajax/delete/", ajax_delete_api_key, name="ajax_delete"),
    path("ajax/regenerate/", ajax_regenerate_api_key, name="ajax_regenerate"),
    path("ajax/toggle/", ajax_toggle_api_key, name="ajax_toggle"),
]