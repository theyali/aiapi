from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@login_required
@require_POST
def ajax_change_password(request):
    current_password = request.POST.get("current_password", "")
    new_password = request.POST.get("new_password", "")
    confirm_password = request.POST.get("confirm_password", "")

    if not current_password:
        return JsonResponse({
            "success": False,
            "message": "Введите текущий пароль.",
            "errors": {
                "current_password": "Введите текущий пароль."
            }
        }, status=400)

    if not request.user.check_password(current_password):
        return JsonResponse({
            "success": False,
            "message": "Текущий пароль указан неверно.",
            "errors": {
                "current_password": "Текущий пароль указан неверно."
            }
        }, status=400)

    if not new_password:
        return JsonResponse({
            "success": False,
            "message": "Введите новый пароль.",
            "errors": {
                "new_password": "Введите новый пароль."
            }
        }, status=400)

    if len(new_password) < 8:
        return JsonResponse({
            "success": False,
            "message": "Пароль должен содержать минимум 8 символов.",
            "errors": {
                "new_password": "Пароль должен содержать минимум 8 символов."
            }
        }, status=400)

    if new_password != confirm_password:
        return JsonResponse({
            "success": False,
            "message": "Пароли не совпадают.",
            "errors": {
                "confirm_password": "Пароли не совпадают."
            }
        }, status=400)

    request.user.set_password(new_password)
    request.user.save(update_fields=["password"])

    update_session_auth_hash(request, request.user)

    return JsonResponse({
        "success": True,
        "message": "Пароль успешно обновлён."
    })