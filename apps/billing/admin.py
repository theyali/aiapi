from django.contrib import admin

from .models import (
    UserBalance,
    BillingSettings,
    TokenPackage,
    Payment,
    BalanceTransaction,
)


@admin.register(UserBalance)
class UserBalanceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "token_balance",
        "total_purchased_tokens",
        "total_used_tokens",
        "updated_at",
    )
    search_fields = ("user__username", "user__email")


@admin.register(BillingSettings)
class BillingSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "rub_per_1m_tokens",
        "usd_to_rub_rate",
        "min_custom_million_tokens",
        "max_custom_million_tokens",
        "is_custom_topup_enabled",
        "updated_at",
    )

    def has_add_permission(self, request):
        if BillingSettings.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(TokenPackage)
class TokenPackageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "tokens_amount",
        "price_rub",
        "is_popular",
        "is_active",
        "sort_order",
    )
    list_filter = ("is_active", "is_popular")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "source",
        "package",
        "amount_rub",
        "amount_usd",
        "tokens_amount",
        "status",
        "provider",
        "created_at",
        "paid_at",
    )
    list_filter = ("status", "provider", "source", "created_at")
    search_fields = (
        "user__username",
        "user__email",
        "external_payment_id",
    )
    readonly_fields = ("created_at", "paid_at")


@admin.register(BalanceTransaction)
class BalanceTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "transaction_type",
        "amount_tokens",
        "balance_before",
        "balance_after",
        "created_at",
    )
    list_filter = ("transaction_type", "created_at")
    search_fields = ("user__username", "user__email", "description")
    readonly_fields = ("created_at",)