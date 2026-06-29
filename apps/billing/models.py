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
        return f"{self.user} balance: {self.token_balance}"