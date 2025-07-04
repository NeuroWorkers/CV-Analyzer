import asyncio
import json
import logging
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
        "Ты ИИ-помощник, который помогает искать релевантные резюме.\n"
        "На входе — пользовательский запрос и список резюме, каждый из которых содержит:\n"
        "- telegram_id (уникальный идентификатор)\n"
        "- author (имя и ник автора)\n"
        "- content (текст резюме)\n\n"
        "Если резюме релевантно запросу (например, совпадает имя или совпадает по смыслу), "
        "верни JSON-массив объектов:\n"
        "[{'telegram_id': 123456789, 'match': true, 'highlights': ['ключ1', 'ключ2']}, ...]\n"
        "Если не подходит — не включай.\n"
        "Учитывай имя и ник автора так же, как и текст.\n"
        "Подсвечивай только осмысленные совпадения: имена, роли, ключевые слова."
    )

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
    }

    user_content = f"Запрос: {user_query}\nРезюме:\n" + "".join(
        f"{msg.telegram_id}: Автор: {msg.author}\nТекст: {msg.content}\n\n" for msg in messages
    )

    payload = {
        "model": openai_model,
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

    msg_by_tid = {msg.telegram_id: msg for msg in messages}

    relevant = []
    highlights = []

    for res in parsed_list:
        tid = res.get("telegram_id")
        if tid is None or tid not in msg_by_tid:
            continue

        current_highlights = [w for w in res.get("highlights", []) if len(w) >= 3]
        msg = msg_by_tid[tid]
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
