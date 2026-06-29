from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("", views.billing_view, name="index"),
    path("create-payment/", views.create_payment_view, name="create_payment"),
    path("mock-payment/success/<int:payment_id>/", views.mock_payment_success_view, name="mock_payment_success"),
]