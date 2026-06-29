from dataclasses import dataclass


@dataclass
class PaymentInitResult:
    external_payment_id: str
    payment_url: str
    is_available: bool = True
    message: str = ""


class BasePaymentProvider:
    provider_name = "base"

    def create_payment(self, payment):
        raise NotImplementedError