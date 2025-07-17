from typing import List, Dict

import httpx


async def chat_completion_openrouter(messages: List[Dict[str, str]], model, temperature: int = 0) -> str:
    """
    Отправляет запрос к OpenRouter API и получает ответ от модели.

    Args:
        messages (List[Dict[str, str]]): Список сообщений с ролями для диалога (например, system, user).
        model (str): Имя модели OpenRouter для использования (по умолчанию "google/gemini-2.5-flash").
        temperature (int): Креативность модели от 0 до 1.

    Returns:
        str: Текстовый ответ от модели.
    """
    from configs.cfg import openrouter_api_key

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client_http:
            response = await client_http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            return response.json()["choices"][0]["message"]["content"].strip()

    except httpx.HTTPStatusError as e:
        raise
    except Exception as e:
        raise
