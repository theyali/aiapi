from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import RegisterForm


def get_form_errors(form):
    errors = {}

    for field, field_errors in form.errors.items():
        if field == "__all__":
            errors["non_field"] = field_errors[0]
        else:
            errors[field] = field_errors[0]

    return errors


@require_POST
def ajax_login_view(request):
    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    next_url = request.POST.get("next") or request.GET.get("next") or "/dashboard/"

    if not username:
        return JsonResponse({
            "success": False,
            "message": "Введите логин.",
            "errors": {
                "username": "Введите логин."
            }
        }, status=400)

    if not password:
        return JsonResponse({
            "success": False,
            "message": "Введите пароль.",
            "errors": {
                "password": "Введите пароль."
            }
        }, status=400)

    user = authenticate(
        request,
        username=username,
        password=password
    )

    if user is None:
        return JsonResponse({
            "success": False,
            "message": "Неверный логин или пароль.",
            "errors": {
                "non_field": "Неверный логин или пароль."
            }
        }, status=400)

    if not user.is_active:
        return JsonResponse({
            "success": False,
            "message": "Этот аккаунт отключён.",
            "errors": {
                "non_field": "Этот аккаунт отключён."
            }
        }, status=400)

    login(request, user)

    return JsonResponse({
        "success": True,
        "message": "Вход выполнен успешно.",
        "redirect_url": next_url
    })


@require_POST
def ajax_register_view(request):
    form = RegisterForm(request.POST)
    next_url = request.POST.get("next") or request.GET.get("next") or "/dashboard/"

    if not form.is_valid():
        return JsonResponse({
            "success": False,
            "message": "Исправьте ошибки ниже.",
            "errors": get_form_errors(form)
        }, status=400)

    user = form.save()
    login(request, user)

    return JsonResponse({
        "success": True,
        "message": "Аккаунт успешно создан.",
        "redirect_url": next_url
    })