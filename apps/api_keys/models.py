import hashlib
import secrets

from django.conf import settings
from django.db import models


class ApiKey(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_keys"
    )

    name = models.CharField(max_length=120)

    key_hash = models.CharField(max_length=128, unique=True)
    key_prefix = models.CharField(max_length=24)

    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    token_limit = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text="Limit in tokens. Empty means unlimited."
    )

    used_tokens = models.PositiveBigIntegerField(default=0)

    last_used_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.user}"

    @staticmethod
    def generate_raw_key():
        return "sk-clb-" + secrets.token_urlsafe(32)

    @staticmethod
    def hash_key(raw_key):
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @property
    def masked_key(self):
        return f"{self.key_prefix}••••••••••••••••"

    @property
    def usage_percent(self):
        if not self.token_limit:
            return 0

        if self.token_limit <= 0:
            return 0

        percent = int((self.used_tokens / self.token_limit) * 100)

        return min(percent, 100)

    @property
    def remaining_tokens(self):
        if not self.token_limit:
            return None

        remaining = self.token_limit - self.used_tokens

        return max(remaining, 0)

    @classmethod
    def create_for_user(cls, user, name, token_limit=None, is_primary=False):
        raw_key = cls.generate_raw_key()

        api_key = cls.objects.create(
            user=user,
            name=name,
            key_hash=cls.hash_key(raw_key),
            key_prefix=raw_key[:14],
            token_limit=token_limit,
            is_primary=is_primary,
        )

        return api_key, raw_key

    def regenerate(self):
        raw_key = self.generate_raw_key()

        self.key_hash = self.hash_key(raw_key)
        self.key_prefix = raw_key[:14]
        self.save(update_fields=["key_hash", "key_prefix", "updated_at"])

        return raw_key