import hashlib
import json
import time

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.api_keys.models import ApiKey
from apps.billing.models import UserBalance
from apps.usage.models import ApiRequestLog

from .services import (
    build_mock_response,
    estimate_request_tokens,
    estimate_tokens_from_text,
    get_model_multiplier,
)


def get_bearer_token(request):
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return None

    return auth_header.replace("Bearer ", "", 1).strip()


def hash_api_key(raw_key):
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def error_response(message, status=400):
    return JsonResponse({
        "error": message
    }, status=status)


@csrf_exempt
@require_POST
def chat_completions_view(request):
    started_at = time.time()

    raw_api_key = get_bearer_token(request)

    if not raw_api_key:
        return error_response("Missing Authorization Bearer token", status=401)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return error_response("Invalid JSON body", status=400)

    model_name = payload.get("model", "gpt-5.4-mini")
    messages = payload.get("messages", [])

    if not isinstance(messages, list) or not messages:
        return error_response("Messages are required", status=400)

    api_key_hash = hash_api_key(raw_api_key)

    try:
        api_key = (
            ApiKey.objects
            .select_related("user")
            .get(key_hash=api_key_hash)
        )
    except ApiKey.DoesNotExist:
        return error_response("Invalid API key", status=401)

    if not api_key.is_active:
        return error_response("API key is disabled", status=403)

    user_text = ""

    for message in messages:
        if message.get("role") == "user":
            user_text = message.get("content", "")

    if not user_text:
        user_text = "Hello"

    request_tokens = estimate_request_tokens(messages)

    mock_response = build_mock_response(
        model_name=model_name,
        user_text=user_text
    )

    response_text = mock_response["choices"][0]["message"]["content"]
    response_tokens = estimate_tokens_from_text(response_text)

    real_total_tokens = request_tokens + response_tokens
    multiplier = get_model_multiplier(model_name)
    charged_tokens = int(real_total_tokens * multiplier)

    response_time_ms = int((time.time() - started_at) * 1000)

    with transaction.atomic():
        locked_api_key = (
            ApiKey.objects
            .select_for_update()
            .get(id=api_key.id)
        )

        balance, created = (
            UserBalance.objects
            .select_for_update()
            .get_or_create(user=api_key.user)
        )

        if locked_api_key.token_limit:
            new_key_usage = locked_api_key.used_tokens + charged_tokens

            if new_key_usage > locked_api_key.token_limit:
                ApiRequestLog.objects.create(
                    user=api_key.user,
                    api_key_name=locked_api_key.name,
                    model_name=model_name,
                    provider_name="MockProvider",
                    status=ApiRequestLog.STATUS_FAILED,
                    request_tokens=request_tokens,
                    response_tokens=response_tokens,
                    charged_tokens=0,
                    response_time_ms=response_time_ms,
                    error_message="API key limit exceeded",
                )

                return error_response("API key limit exceeded", status=403)

        if balance.token_balance < charged_tokens:
            ApiRequestLog.objects.create(
                user=api_key.user,
                api_key_name=locked_api_key.name,
                model_name=model_name,
                provider_name="MockProvider",
                status=ApiRequestLog.STATUS_FAILED,
                request_tokens=request_tokens,
                response_tokens=response_tokens,
                charged_tokens=0,
                response_time_ms=response_time_ms,
                error_message="Insufficient balance",
            )

            return error_response("Insufficient balance", status=402)

        balance.token_balance -= charged_tokens
        balance.total_used_tokens += charged_tokens
        balance.save(update_fields=[
            "token_balance",
            "total_used_tokens",
            "updated_at",
        ])

        locked_api_key.used_tokens += charged_tokens
        locked_api_key.save(update_fields=[
            "used_tokens",
            "updated_at",
        ])

        ApiRequestLog.objects.create(
            user=api_key.user,
            api_key_name=locked_api_key.name,
            model_name=model_name,
            provider_name="MockProvider",
            status=ApiRequestLog.STATUS_SUCCESS,
            request_tokens=request_tokens,
            response_tokens=response_tokens,
            charged_tokens=charged_tokens,
            response_time_ms=response_time_ms,
        )

    mock_response["usage"] = {
        "prompt_tokens": request_tokens,
        "completion_tokens": response_tokens,
        "total_tokens": real_total_tokens,
        "charged_tokens": charged_tokens,
        "billing_multiplier": multiplier,
    }

    return JsonResponse(mock_response)