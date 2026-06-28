from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from apps.api_keys.models import ApiKey


@login_required
def dashboard_view(request):
    return render(request, "dashboard/index.html")


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