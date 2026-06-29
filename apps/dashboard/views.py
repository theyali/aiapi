from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from apps.api_keys.models import ApiKey
from datetime import timedelta
from django.db.models import Count, Sum
from django.db.models.functions import TruncHour
from django.utils import timezone

from apps.billing.models import UserBalance
from apps.usage.models import ApiRequestLog


def format_tokens(tokens):
    if tokens >= 1_000_000_000:
        return f"{tokens / 1_000_000_000:.1f}B"

    if tokens >= 1_000_000:
        value = tokens / 1_000_000

        if value.is_integer():
            return f"{int(value)}M"

        return f"{value:.1f}M"

    if tokens >= 1_000:
        return f"{tokens / 1_000:.1f}K"

    return str(tokens)


@login_required
def dashboard_view(request):
    balance, created = UserBalance.objects.get_or_create(
        user=request.user
    )

    now = timezone.now()
    seven_days_ago = now - timedelta(days=7)
    two_days_ago = now - timedelta(days=2)

    requests_in_7_days = ApiRequestLog.objects.filter(
        user=request.user,
        created_at__gte=seven_days_ago
    ).count()

    charged_tokens_7_days = ApiRequestLog.objects.filter(
        user=request.user,
        created_at__gte=seven_days_ago
    ).aggregate(
        total=Sum("charged_tokens")
    )["total"] or 0

    # Base price пример: $2.5 за 1M charged tokens
    estimated_cost = (charged_tokens_7_days / 1_000_000) * 2.5

    chart_rows = (
        ApiRequestLog.objects
        .filter(
            user=request.user,
            created_at__gte=two_days_ago
        )
        .annotate(hour=TruncHour("created_at"))
        .values("hour")
        .annotate(total=Sum("charged_tokens"))
        .order_by("hour")
    )

    chart_map = {}

    for row in chart_rows:
        chart_map[row["hour"].replace(minute=0, second=0, microsecond=0)] = row["total"] or 0

    chart_data = []

    # Делаем точки каждые 6 часов за последние 48 часов
    for index in range(8, -1, -1):
        point_time = now - timedelta(hours=index * 6)
        point_time = point_time.replace(minute=0, second=0, microsecond=0)

        value = 0

        for hour, total in chart_map.items():
            if point_time <= hour < point_time + timedelta(hours=6):
                value += total

        chart_data.append({
            "label": point_time.strftime("%d.%m, %H:%M"),
            "value": value,
        })

    max_chart_value = max([point["value"] for point in chart_data] or [0])

    if max_chart_value <= 0:
        max_chart_value = 1

    middle_chart_value = max_chart_value / 2
    
    request_logs = ApiRequestLog.objects.filter(
        user=request.user
    ).order_by("-created_at")[:10]

    invite_link = request.build_absolute_uri(
        f"/accounts/register/?ref={request.user.username}"
    )

    return render(request, "dashboard/index.html", {
        "balance": balance,
        "formatted_balance": format_tokens(balance.token_balance),
        "requests_in_7_days": requests_in_7_days,
        "estimated_cost": estimated_cost,
        "chart_data": chart_data,
        "max_chart_value": max_chart_value,
        "middle_chart_value": middle_chart_value,
        "request_logs": request_logs,
        "invite_link": invite_link,
        "total_invited": 0,
    })


@login_required
def settings_view(request):
    api_keys = ApiKey.objects.filter(user=request.user).order_by("-created_at")

    return render(request, "dashboard/settings.html", {
        "api_keys": api_keys,
    })


@login_required
def guides_view(request):
    return render(request, "dashboard/guides.html")


@login_required
def ai_image_view(request):
    return render(request, "dashboard/ai_image.html")