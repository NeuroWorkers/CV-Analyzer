import asyncio
import re
import httpx
import edgedb
from typing import Any

from configs.ai_config import *

client = edgedb.create_async_client("database")


async def fetch_all_messages():
    return await client.query("""
        SELECT ResumeMessage {
            id,
            content,
            author,
            created_at,
            media_path
        }
    """)


async def analyze_user_query(user_query: str) -> str:
    system_prompt = (
        "Ты ИИ-ассистент по поиску резюме. Преобразуй запрос пользователя в короткий список ключевых слов, "
        "синонимов и связанных терминов. Добавляй формы слов, синонимы, аббревиатуры, связанные роли. "
        "Игнорируй нерелевантные слова. Верни одну строку."
    )

    response = await chat_completion_openrouter([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ])
    return response.strip()


async def filter_results_with_gpt(user_query: str, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    system_prompt = (
        "Ты ассистент по оценке релевантности резюме. На входе пользовательский запрос и текст резюме.\n"
        "Отвечай 'Да' только если соответствие явно выражено. Не фантазируй.\n"
        "Примеры релевантности: упоминаются нужные технологии, профессия, опыт."
    )

    filtered = []
    for r in results:
        prompt = f"Запрос: {user_query}\nРезюме: {r.content}"
        response = await chat_completion_openrouter([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ])
        if response.lower().startswith("да"):
            filtered.append(r)
    return filtered


async def edge_search(optimized_query: str, k: int = 20):
    return await client.query(
        """
        WITH results := ext::ai::search(ResumeMessage, <str>$q)
        SELECT results.object {
            id,
            content,
            author,
            created_at,
            media_path
        }
        LIMIT <int64>$k;
        """,
        q=optimized_query,
        k=k
    )


async def highlight_matches_with_gpt(user_query: str, filtered: list[dict[str, Any]]) -> list[list[str]]:
    system_prompt = (
        "Ты подсвечиваешь ключевые фразы в тексте, которые связаны с запросом.\n"
        "Выделяй только точные и смысловые совпадения. Возвращай список слов или фраз."
    )

    highlights = []
    for r in filtered:
        prompt = f"Запрос: {user_query}\nРезюме: {r.content}"
        response = await chat_completion_openrouter([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ])

        try:
            words = eval(response) if response.startswith("[") else []
            highlights.append([w for w in words if len(w) >= 3])
        except Exception:
            highlights.append([])

    return highlights


async def chat_completion_openrouter(messages: list[dict], model="openai/gpt-4") -> str:
    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()


async def full_pipeline(user_query: str) -> tuple[list[dict[str, Any]], list[list[str]]]:
    print(f"[INFO] Запрос: {user_query}")
    optimized_query = await analyze_user_query(user_query)
    print(f"[DEBUG] Оптимизированный запрос: {optimized_query}")

    raw_results = await edge_search(optimized_query)
    print(f"[DEBUG] Найдено кандидатов: {len(raw_results)}")

    filtered = await filter_results_with_gpt(user_query, raw_results)
    print(f"[INFO] Отфильтровано: {len(filtered)}")

    highlighted = await highlight_matches_with_gpt(user_query, filtered)
    print(f"[INFO] Подсветка завершена")

    return filtered, highlighted


def test():
    query = "искусственный интеллект"
    results, highlights = asyncio.run(full_pipeline(query))

    for r, hl in zip(results, highlights):
        print(f"{r.created_at} — {r.author}: {r.content}")
        print(f"[Подсветка]: {hl}\n")


if __name__ == "__main__":
    test()
