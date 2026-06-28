from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import ApiKey


def api_key_to_dict(api_key):
    return {
        "id": api_key.id,
        "name": api_key.name,
        "masked_key": api_key.masked_key,
        "key_prefix": api_key.key_prefix,
        "is_primary": api_key.is_primary,
        "is_active": api_key.is_active,
        "token_limit": api_key.token_limit,
        "used_tokens": api_key.used_tokens,
        "remaining_tokens": api_key.remaining_tokens,
        "usage_percent": api_key.usage_percent,
    }


@login_required
@require_POST
def ajax_create_api_key(request):
    name = request.POST.get("name", "").strip()
    token_limit_raw = request.POST.get("token_limit", "").strip()

    if not name:
        return JsonResponse({
            "success": False,
            "message": "Введите название ключа."
        }, status=400)

    token_limit = None

    if token_limit_raw:
        try:
            token_limit_millions = int(token_limit_raw)
            token_limit = token_limit_millions * 1_000_000
        except ValueError:
            return JsonResponse({
                "success": False,
                "message": "Лимит должен быть числом."
            }, status=400)

    keys_count = ApiKey.objects.filter(user=request.user).count()

    if keys_count >= 20:
        return JsonResponse({
            "success": False,
            "message": "Максимум 20 API-ключей."
        }, status=400)

    api_key, raw_key = ApiKey.create_for_user(
        user=request.user,
        name=name,
        token_limit=token_limit,
        is_primary=False,
    )

    return JsonResponse({
        "success": True,
        "message": "API-ключ создан.",
        "api_key": api_key_to_dict(api_key),
        "raw_key": raw_key,
    })


@login_required
@require_POST
def ajax_delete_api_key(request):
    key_id = request.POST.get("id")

    try:
        api_key = ApiKey.objects.get(id=key_id, user=request.user)
    except ApiKey.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "API-ключ не найден."
        }, status=404)

    if api_key.is_primary:
        return JsonResponse({
            "success": False,
            "message": "Основной ключ нельзя удалить."
        }, status=400)

    api_key.delete()

    return JsonResponse({
        "success": True,
        "message": "API-ключ удалён."
    })


@login_required
@require_POST
def ajax_regenerate_api_key(request):
    key_id = request.POST.get("id")

    try:
        api_key = ApiKey.objects.get(id=key_id, user=request.user)
    except ApiKey.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "API-ключ не найден."
        }, status=404)

    raw_key = api_key.regenerate()

    return JsonResponse({
        "success": True,
        "message": "API-ключ обновлён.",
        "api_key": api_key_to_dict(api_key),
        "raw_key": raw_key,
    })


@login_required
@require_POST
def ajax_toggle_api_key(request):
    key_id = request.POST.get("id")

    try:
        api_key = ApiKey.objects.get(id=key_id, user=request.user)
    except ApiKey.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "API-ключ не найден."
        }, status=404)

    api_key.is_active = not api_key.is_active
    api_key.save(update_fields=["is_active", "updated_at"])

    return JsonResponse({
        "success": True,
        "message": "Статус ключа обновлён.",
        "api_key": api_key_to_dict(api_key),
    })