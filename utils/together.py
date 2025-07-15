import openai
from typing import List, Dict
from configs.cfg import openrouter_api_key
import os

client = openai.OpenAI(
    api_key=openrouter_api_key,
    base_url="https://api.together.xyz/v1"
)


async def chat_completion_openrouter(
    messages: List[Dict[str, str]],
    model: str = "gpt-4",
    temperature: float = 0.0
) -> str:
    """
    Отправляет запрос к Together AI через официальный OpenAI-клиент.

    Args:
        messages (List[Dict[str, str]]): Список сообщений с ролями (system, user и т.д.)
        model (str): Название модели.
        temperature (float): Креативность.

    Returns:
        str: Ответ модели.
    """

    import asyncio
    loop = asyncio.get_running_loop()

    def sync_call():
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return completion.choices[0].message.content.strip()

    result = await loop.run_in_executor(None, sync_call)
    return result