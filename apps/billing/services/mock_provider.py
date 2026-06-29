from django.urls import reverse

from .base import BasePaymentProvider, PaymentInitResult


class MockPaymentProvider(BasePaymentProvider):
    provider_name = "mock"

    def create_payment(self, payment):
        success_url = reverse("billing:mock_payment_success", args=[payment.id])

        return PaymentInitResult(
            external_payment_id=f"mock-payment-{payment.id}",
            payment_url=success_url,
            is_available=True,
            message="Mock payment created",
        )