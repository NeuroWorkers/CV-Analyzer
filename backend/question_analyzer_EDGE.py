import json
import re
import edgedb
import httpx
import asyncio
from typing import List, Any, Tuple, Dict

from configs.ai_config import *

client = edgedb.create_async_client("database")


async def fetch_all_messages() -> List[dict[str, Any]]:
    """
    Загружает все сообщения с резюме из базы данных EdgeDB.

    Returns:
        List[dict[str, Any]]: Список словарей с полями резюме:
            'telegram_id' (int) — ID пользователя в Telegram,
            'content' (str) — текст резюме,
            'author' (str) — автор сообщения,
            'created_at' (datetime) — дата создания,
            'media_path' (str|None) — путь к медиафайлу, если есть.
    """
    return await client.query("""
        SELECT ResumeMessage {
            telegram_id,
            content,
            author,
            created_at,
            media_path
        }
    """)


async def analyze_user_query(user_query: str) -> str:
    """
    Оптимизирует запрос пользователя, расширяя синонимами и связанными терминами.

    Args:
        user_query (str): Исходный запрос пользователя.

    Returns:
        str: Оптимизированная строка запроса с ключевыми словами, синонимами и связанными терминами.
    """
    system_prompt = (
        "Ты ИИ-ассистент по поиску резюме. Преобразуй запрос пользователя в короткий список ключевых слов, "
        "синонимов и связанных терминов. Добавляй формы слов, синонимы, аббревиатуры, связанные роли. "
        "Игнорируй нерелевантные слова. Верни одну строку."
    )

    return await chat_completion_openrouter([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ], model=openai_model)


async def semantic_search(user_query: str, messages: List[Any]) -> Tuple[List[dict[str, Any]], List[List[str]]]:
    """
    Выполняет семантический поиск релевантных резюме с подсветкой ключевых слов.

    Args:
        user_query (str): Исходный запрос пользователя.
        messages (List[Any]): Список объектов сообщений с полями (content, telegram_id, author и т.д.).

    Returns:
        Tuple[List[dict[str, Any]], List[List[str]]]:
            - Список релевантных резюме (каждое — словарь с полями telegram_id, content, author, created_at, media_path).
            - Список списков ключевых слов или фраз для каждого релевантного резюме.
    """
    system_prompt = (
        "Ты ИИ-помощник, который помогает искать релевантные резюме. "
        "На входе у тебя есть пользовательский запрос и список резюме с их индексами. "
        "Если резюме подходит, верни JSON-массив объектов вида:\n"
        "[{'index': 0, 'match': true, 'highlights': ['ключ1', 'ключ2']}, ...]"
    )

    user_content = f"Запрос: {user_query}\nРезюме:\n" + "".join(
        f"{i}: {msg.content}\n" for i, msg in enumerate(messages)
    )

    payload = {
        "model": openai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.5
    }

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client_http:
        response = await client_http.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()

    clean_content = re.sub(r"```json\s*|```", "", content).strip()

    try:
        parsed_list = json.loads(clean_content)
    except json.JSONDecodeError:
        try:
            parsed_list = eval(clean_content)
        except Exception as e:
            parsed_list = []
            print(e)

    relevant = []
    highlights = []

    for res in sorted(parsed_list, key=lambda x: x.get("index", -1)):
        idx = res.get("index")
        if idx is None or idx >= len(messages):
            continue
        if res.get("match"):
            current_highlights = [w for w in res.get("highlights", []) if len(w) >= 3]
            msg = messages[idx]
            relevant.append({
                "telegram_id": msg.telegram_id,
                "content": msg.content,
                "author": msg.author,
                "created_at": msg.created_at,
                "media_path": msg.media_path
            })
            highlights.append(current_highlights)

    return relevant, highlights


async def chat_completion_openrouter(messages: List[Dict[str, str]], model: str = openai_model) -> str:
    """
    Отправляет запрос к OpenRouter API и возвращает ответ модели.

    Args:
        messages (List[Dict[str, str]]): Список сообщений для диалога с ролями ('system', 'user').
        model (str): Имя модели OpenRouter (по умолчанию "google/gemini-2.5-flash").

    Returns:
        str: Текстовый ответ модели.
    """
    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0
    }
    async with httpx.AsyncClient(timeout=60.0) as client_http:
        response = await client_http.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()


async def full_pipeline(user_query: str) -> Tuple[List[Dict[str, Any]], List[List[str]]]:
    """
    Полный пайплайн поиска релевантных резюме с подсветкой ключевых слов.

    Args:
        user_query (str): Исходный запрос пользователя.

    Returns:
        Tuple[List[Dict[str, Any]], List[List[str]]]:
            - Список отфильтрованных релевантных резюме.
            - Список списков ключевых слов для каждого из релевантных резюме.
    """
    print(f"[INFO] Запрос: {user_query}")
    optimized_query = await analyze_user_query(user_query)
    print(f"[INFO] Оптимизированный запрос: {optimized_query}")

    raw_results = await fetch_all_messages()
    print(f"[INFO] Всего сообщений: {len(raw_results)}")

    filtered, highlighted = await semantic_search(user_query, raw_results)
    print(f"[INFO] Отфильтровано: {len(filtered)}")
    print(f"[INFO] Подсветка завершена")

    return filtered, highlighted


def test():
    query = "искусственный интеллект"
    results, highlights = asyncio.run(full_pipeline(query))

    for r, hl in zip(results, highlights):
        print(f"{r['created_at']} — {r['author']}: {r['content']}")
        print(f"[Подсветка]: {hl}\n")


if __name__ == "__main__":
    test()
