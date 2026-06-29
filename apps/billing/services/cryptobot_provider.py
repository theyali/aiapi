from .base import BasePaymentProvider, PaymentInitResult


class CryptoBotPaymentProvider(BasePaymentProvider):
    provider_name = "cryptobot"

    def create_payment(self, payment):
        return PaymentInitResult(
            external_payment_id="",
            payment_url="",
            is_available=False,
            message="CryptoBot payment is not connected yet",
        )