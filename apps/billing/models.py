from decimal import Decimal

from django.conf import settings
from django.db import models


class UserBalance(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="balance"
    )
    token_balance = models.PositiveBigIntegerField(default=5_000_000)
    total_purchased_tokens = models.PositiveBigIntegerField(default=0)
    total_used_tokens = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} balance: {self.token_balance} tokens"


class BillingSettings(models.Model):
    """
    Настройки конвертации токенов в деньги.
    Пока используем как singleton: в админке должна быть одна запись.
    """

    rub_per_1m_tokens = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("2.45"),
        help_text="Цена за 1 миллион токенов в рублях."
    )
    usd_to_rub_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("90.00"),
        help_text="Курс USD/RUB для крипто-платежей."
    )

    min_custom_million_tokens = models.PositiveIntegerField(
        default=10,
        help_text="Минимальное custom-пополнение в миллионах токенов."
    )
    max_custom_million_tokens = models.PositiveIntegerField(
        default=5000,
        help_text="Максимальное custom-пополнение в миллионах токенов."
    )

    is_custom_topup_enabled = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Billing settings"
        verbose_name_plural = "Billing settings"

    def __str__(self):
        return f"{self.rub_per_1m_tokens} ₽ / 1M tokens"

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj

    def calculate_rub_for_tokens(self, tokens_amount: int) -> Decimal:
        million_amount = Decimal(tokens_amount) / Decimal(1_000_000)
        return (million_amount * self.rub_per_1m_tokens).quantize(Decimal("0.01"))

    def calculate_usd_from_rub(self, amount_rub: Decimal) -> Decimal:
        if not self.usd_to_rub_rate:
            return Decimal("0.00")

        return (amount_rub / self.usd_to_rub_rate).quantize(Decimal("0.01"))


class TokenPackage(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    tokens_amount = models.PositiveBigIntegerField()
    price_rub = models.PositiveIntegerField()
    description = models.CharField(max_length=255, blank=True)
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "price_rub"]

    def __str__(self):
        return f"{self.name} — {self.tokens_amount} tokens"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        CANCELED = "canceled", "Canceled"

    class Provider(models.TextChoices):
        MOCK = "mock", "Mock"
        SBP = "sbp", "SBP"
        CARDS = "cards", "Cards"
        CRYPTOBOT = "cryptobot", "CryptoBot"
        YOOKASSA = "yookassa", "YooKassa"

    class Source(models.TextChoices):
        PACKAGE = "package", "Package"
        CUSTOM = "custom", "Custom amount"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    package = models.ForeignKey(
        TokenPackage,
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True
    )

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.PACKAGE
    )

    amount_rub = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    amount_usd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    tokens_amount = models.PositiveBigIntegerField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    provider = models.CharField(
        max_length=50,
        choices=Provider.choices,
        default=Provider.MOCK
    )

    external_payment_id = models.CharField(max_length=120, blank=True)
    payment_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment #{self.id} — {self.user} — {self.status}"


class BalanceTransaction(models.Model):
    class Type(models.TextChoices):
        PURCHASE = "purchase", "Purchase"
        API_USAGE = "api_usage", "API Usage"
        REFUND = "refund", "Refund"
        ADMIN_ADJUSTMENT = "admin_adjustment", "Admin Adjustment"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="balance_transactions"
    )

    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="balance_transactions"
    )

    transaction_type = models.CharField(
        max_length=30,
        choices=Type.choices
    )

    amount_tokens = models.BigIntegerField()
    balance_before = models.PositiveBigIntegerField()
    balance_after = models.PositiveBigIntegerField()
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.transaction_type} — {self.amount_tokens}"