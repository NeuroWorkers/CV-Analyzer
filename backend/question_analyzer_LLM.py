import asyncio
import json
import re
from typing import Any, List, Tuple

import httpx
import edgedb

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


async def semantic_search(user_query: str, messages: List[Any]) -> Tuple[List[dict[str, Any]], List[List[str]]]:
    """
    Отправляет один пакетный запрос в ИИ-модель с пользовательским запросом и списком резюме.
    Получает список результатов с индексами, флагом релевантности и списком подсвеченных ключевых слов.
    Возвращает только релевантные резюме с подсветками.

    Args:
        user_query (str): Запрос пользователя.
        messages (List[Any]): Список объектов резюме с атрибутом content и метаданными.

    Returns:
        Tuple[
            List[dict[str, Any]],    # Релевантные резюме с полями ('telegram_id', 'content', 'author', 'created_at', 'media_path')
            List[List[str]]          # Списки подсвеченных ключевых слов для каждого релевантного резюме
        ]
    """
    system_prompt = (
        "Ты ИИ-помощник, который помогает искать релевантные резюме. "
        "На входе у тебя есть пользовательский запрос и список резюме с их индексами. "
        "Если резюме подходит, верни JSON-массив объектов вида:\n"
        "[{'index': 0, 'match': true, 'highlights': ['ключ1', 'ключ2']}, ...]\n"
        "Если не подходит — {'match': false, 'highlights': []}.\n"
        "Выделяй только осмысленные совпадения — по смыслу и форме (синонимы, склонения и т.д.)."
    )

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
    }

    user_content = f"Запрос: {user_query}\nРезюме:\n" + "".join(
        f"{i}: {msg.content}\n" for i, msg in enumerate(messages)
    )

    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 1
    }

    async with httpx.AsyncClient(timeout=20.0) as client_http:
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


async def full_pipeline(user_query: str) -> Tuple[List[dict[str, Any]], List[List[str]]]:
    """
    Запускает процесс поиска релевантных резюме по запросу.

    Args:
        user_query (str): Пользовательский поисковый запрос.

    Returns:
        Tuple[
            List[dict[str, Any]],  # Релевантные резюме
            List[List[str]]       # Подсветки ключевых слов для каждого резюме
        ]
    """
    print(f"[INFO] Запрос: {user_query}")
    all_messages = await fetch_all_messages()
    print(f"[INFO] Загружено {len(all_messages)} сообщений")

    results, highlights = await semantic_search(user_query, all_messages)
    print(f"[INFO] Найдено релевантных: {len(results)}")

    return results, highlights


def test() -> None:
    query = "искусственный интеллект"
    results, highlights = asyncio.run(full_pipeline(query))

    for r, hl in zip(results, highlights):
        print(f"{r['created_at']} — {r['author']}: {r['content']}")
        print(f"[Подсветка]: {hl}\n")


if __name__ == "__main__":
    test()
