import httpx
from typing import List, Dict


async def chat_completion_togetherai(messages: List[Dict[str, str]], model: str, temperature: int = 0) -> str:
    """
    Отправляет запрос к Together AI API и получает ответ от модели.

    Args:
        messages (List[Dict[str, str]]): Список сообщений с ролями для диалога (например, system, user).
        model (str): Имя модели Together AI (например, "mistralai/Mixtral-8x7B-Instruct-v0.1").
        temperature (int): Креативность модели от 0 до 1.

    Returns:
        str: Ответ от модели.
    """
    from configs.cfg import together_api_key

    headers = {
        "Authorization": f"Bearer {together_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client_http:
            response = await client_http.post(
                "https://api.together.xyz/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            return response.json()["choices"][0]["message"]["content"].strip()

    except httpx.HTTPStatusError as e:
        print(f"[HTTP Error] Status: {e.response.status_code}, Response: {e.response.text}")
        raise
    except Exception as e:
        print(f"[Error] {str(e)}")
        raise
