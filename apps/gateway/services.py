import json


MODEL_MULTIPLIERS = {
    "gpt-5.4-mini": 0.9,
    "gpt-5.4": 1,
    "gpt-5.5": 4.5,

    "claude-haiku-4-5": 0.75,
    "claude-sonnet-4-6": 2.5,
    "claude-opus-4-6": 4,
    "claude-opus-4-7": 5,
    "claude-opus-4-8": 6,
}


def get_model_multiplier(model_name):
    return MODEL_MULTIPLIERS.get(model_name, 1)


def estimate_tokens_from_text(text):
    """
    Очень простая MVP-оценка токенов.
    Потом заменим на реальный tokenizer.
    Примерно: 1 token ~= 4 chars.
    """
    if not text:
        return 1

    return max(1, len(text) // 4)


def estimate_request_tokens(messages):
    text = ""

    for message in messages:
        content = message.get("content", "")

        if isinstance(content, str):
            text += content + " "
        else:
            text += json.dumps(content, ensure_ascii=False)

    return estimate_tokens_from_text(text)


def build_mock_response(model_name, user_text):
    return {
        "id": "chatcmpl-mock",
        "object": "chat.completion",
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"Mock response from AIAPI. You said: {user_text}"
                },
                "finish_reason": "stop"
            }
        ]
    }