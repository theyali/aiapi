from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    UserBalance,
    BillingSettings,
    TokenPackage,
    Payment,
    BalanceTransaction,
)
from .services.factory import get_payment_provider


@login_required
def billing_view(request):
    balance, created = UserBalance.objects.get_or_create(user=request.user)

    billing_settings = BillingSettings.get_solo()

    packages = TokenPackage.objects.filter(is_active=True)

    payments = Payment.objects.filter(user=request.user).select_related("package")[:10]

    transactions = BalanceTransaction.objects.filter(user=request.user)[:10]

    payment_methods = [
        {
            "code": Payment.Provider.MOCK,
            "title": "Mock Pay",
            "subtitle": "Test payment",
            "is_active": True,
        },
        {
            "code": Payment.Provider.SBP,
            "title": "SBP",
            "subtitle": "QR payment",
            "is_active": False,
        },
        {
            "code": Payment.Provider.CARDS,
            "title": "Cards",
            "subtitle": "Visa / Mastercard",
            "is_active": False,
        },
        {
            "code": Payment.Provider.YOOKASSA,
            "title": "YooKassa",
            "subtitle": "Cards / SBP",
            "is_active": False,
        },
        {
            "code": Payment.Provider.CRYPTOBOT,
            "title": "CryptoBot",
            "subtitle": "Telegram Crypto",
            "is_active": False,
        },
    ]

    context = {
        "balance": balance,
        "billing_settings": billing_settings,
        "packages": packages,
        "payments": payments,
        "transactions": transactions,
        "payment_methods": payment_methods,
    }

    return render(request, "billing/index.html", context)


@login_required
def create_payment_view(request):
    if request.method != "POST":
        return redirect("billing:index")

    provider_name = request.POST.get("provider")
    source = request.POST.get("source")

    if provider_name not in Payment.Provider.values:
        messages.error(request, "Неверный способ оплаты.")
        return redirect("billing:index")

    if source not in Payment.Source.values:
        messages.error(request, "Неверный тип пополнения.")
        return redirect("billing:index")

    billing_settings = BillingSettings.get_solo()

    package = None
    amount_rub = Decimal("0.00")
    amount_usd = None
    tokens_amount = 0

    if source == Payment.Source.PACKAGE:
        package_id = request.POST.get("package_id")

        package = get_object_or_404(
            TokenPackage,
            id=package_id,
            is_active=True,
        )

        tokens_amount = package.tokens_amount
        amount_rub = Decimal(package.price_rub).quantize(Decimal("0.01"))

    elif source == Payment.Source.CUSTOM:
        if not billing_settings.is_custom_topup_enabled:
            messages.error(request, "Custom top-up сейчас отключён.")
            return redirect("billing:index")

        try:
            million_tokens = int(request.POST.get("million_tokens", "0"))
        except ValueError:
            messages.error(request, "Введите корректное количество миллионов токенов.")
            return redirect("billing:index")

        if million_tokens < billing_settings.min_custom_million_tokens:
            messages.error(
                request,
                f"Минимальное пополнение: {billing_settings.min_custom_million_tokens}M tokens."
            )
            return redirect("billing:index")

        if million_tokens > billing_settings.max_custom_million_tokens:
            messages.error(
                request,
                f"Максимальное пополнение: {billing_settings.max_custom_million_tokens}M tokens."
            )
            return redirect("billing:index")

        tokens_amount = million_tokens * 1_000_000
        amount_rub = billing_settings.calculate_rub_for_tokens(tokens_amount)

    if provider_name == Payment.Provider.CRYPTOBOT:
        amount_usd = billing_settings.calculate_usd_from_rub(amount_rub)

    payment_provider = get_payment_provider(provider_name)

    if payment_provider is None:
        messages.error(request, "Этот способ оплаты пока не подключён.")
        return redirect("billing:index")

    payment = Payment.objects.create(
        user=request.user,
        package=package,
        source=source,
        amount_rub=amount_rub,
        amount_usd=amount_usd,
        tokens_amount=tokens_amount,
        status=Payment.Status.PENDING,
        provider=provider_name,
    )

    result = payment_provider.create_payment(payment)

    if not result.is_available:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status"])

        messages.error(request, result.message)
        return redirect("billing:index")

    payment.external_payment_id = result.external_payment_id
    payment.payment_url = result.payment_url
    payment.save(update_fields=["external_payment_id", "payment_url"])

    return redirect(result.payment_url)


@login_required
def mock_payment_success_view(request, payment_id):
    payment = get_object_or_404(
        Payment,
        id=payment_id,
        user=request.user,
        provider=Payment.Provider.MOCK,
    )

    if payment.status == Payment.Status.PAID:
        messages.info(request, "Этот платёж уже был обработан.")
        return redirect("billing:index")

    if payment.status != Payment.Status.PENDING:
        messages.error(request, "Этот платёж нельзя обработать.")
        return redirect("billing:index")

    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(id=payment.id)

        if payment.status == Payment.Status.PAID:
            messages.info(request, "Этот платёж уже был обработан.")
            return redirect("billing:index")

        balance, created = UserBalance.objects.select_for_update().get_or_create(
            user=request.user
        )

        balance_before = balance.token_balance
        balance_after = balance_before + payment.tokens_amount

        balance.token_balance = balance_after
        balance.total_purchased_tokens += payment.tokens_amount
        balance.save(update_fields=[
            "token_balance",
            "total_purchased_tokens",
            "updated_at",
        ])

        payment.status = Payment.Status.PAID
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "paid_at"])

        BalanceTransaction.objects.create(
            user=request.user,
            payment=payment,
            transaction_type=BalanceTransaction.Type.PURCHASE,
            amount_tokens=payment.tokens_amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=f"Top-up via {payment.provider}",
        )

    messages.success(
        request,
        f"Баланс пополнен на {payment.tokens_amount:,} tokens."
    )

    return redirect("billing:index")