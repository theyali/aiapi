from apps.billing.models import Payment

from .mock_provider import MockPaymentProvider
from .cryptobot_provider import CryptoBotPaymentProvider
from .yookassa_provider import YooKassaPaymentProvider


def get_payment_provider(provider_name):
    if provider_name == Payment.Provider.MOCK:
        return MockPaymentProvider()

    if provider_name == Payment.Provider.CRYPTOBOT:
        return CryptoBotPaymentProvider()

    if provider_name == Payment.Provider.YOOKASSA:
        return YooKassaPaymentProvider()

    return None