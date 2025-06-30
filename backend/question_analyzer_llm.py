import asyncio
import httpx
from typing import Any, List, Tuple
import edgedb
from configs.ai_config import *

client = edgedb.create_async_client("database")


async def fetch_all_messages() -> List[dict[str, Any]]:
    return await client.query("""
        SELECT ResumeMessage {
            id,
            content,
            author,
            created_at,
            media_path
        }
    """)


async def semantic_search_with_gpt(user_query: str, messages: List[dict[str, Any]]) -> tuple[list[dict[str, Any]], list]:
    """
    Фильтрует релевантные резюме с помощью GPT через OpenRouter, включая выделение ключевых фраз.
    Возвращает список слов для подсветки в каждом сообщении.
    """
    system_prompt = (
        "Ты ИИ-помощник, который помогает искать релевантные резюме. "
        "На входе у тебя есть пользовательский запрос и текст резюме. "
        "Если резюме подходит, верни JSON вида:\n"
        "{'match': True, 'highlights': ['ключ1', 'ключ2']}\n"
        "Если не подходит — {'match': False, 'highlights': []}.\n"
        "Выделяй только осмысленные совпадения — по смыслу и форме (синонимы, склонения и т.д.)."
    )

    relevant = []
    highlights = []

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client_http:
        for msg in messages:
            payload = {
                "model": "openai/gpt-4",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Запрос: {user_query}\nРезюме: {msg.content}"}
                ],
                "temperature": 0
            }

            response = await client_http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            parsed = eval(content) if content.startswith("{") else {}

            if parsed.get("match"):
                current_highlights = [w for w in parsed.get("highlights", []) if len(w) >= 3]
                highlights.extend(current_highlights)
                relevant.append(msg)

    return relevant, highlights


async def full_pipeline(user_query: str) -> tuple[Any, Any]:
    print(f"[INFO] Запрос: {user_query}")

    all_messages = await fetch_all_messages()
    print(f"[DEBUG] Загружено {len(all_messages)} сообщений")

    results, highlights = await semantic_search_with_gpt(user_query, all_messages)
    print(f"[INFO] Найдено релевантных: {len(results)}")

    return results, highlights


def test():
    query = "искусственный интеллект"
    results, highlights = asyncio.run(full_pipeline(query))

    for r in results:
        print(f"{r.created_at} — {r.author}: {r.content}")
        print(f"[Подсветка]: {highlights}\n")


if __name__ == "__main__":
    test()