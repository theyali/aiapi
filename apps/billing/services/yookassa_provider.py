from .base import BasePaymentProvider, PaymentInitResult


class YooKassaPaymentProvider(BasePaymentProvider):
    provider_name = "yookassa"

    def create_payment(self, payment):
        return PaymentInitResult(
            external_payment_id="",
            payment_url="",
            is_available=False,
            message="YooKassa payment is not connected yet",
        )