import asyncio
import re

import edgedb
import openai
from typing import Any, Tuple, List, Dict
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
        "Ты помощник, который преобразует пользовательский запрос в оптимизированную строку "
        "для полнотекстового поиска в базе данных резюме. "
        "Выделяй ключевые слова, связанные термины, и если упомянут числовой диапазон — укажи все числа в нём. "
        "Например, 'от 20 до 25' превращай в '20 21 22 23 24 25'. "
        "Также добавляй синонимы: 'молодой' → 'начинающий, без опыта, джун'. "
        "Не добавляй лишних слов. Верни одну строку — готовую поисковую фразу."
    )

    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()


async def filter_results_with_gpt(user_query: str, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    system_prompt = (
        "Ты помощник, фильтрующий резюме по запросу. "
        "Если текст резюме явно соответствует запросу — ответь 'Да', иначе — 'Нет'. "
        "Не додумывай, оцени только на основе явных фактов.\n\n"
        "Формат ответа: Да / Нет. Без объяснений."
    )

    filtered = []
    for r in results:
        text = r.content
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Запрос: {user_query}\nРезюме: {text}"}
            ],
            temperature=0
        )
        decision = response.choices[0].message.content.strip().lower()
        if decision.startswith("да"):
            filtered.append(r)
    return filtered


async def vector_search(optimized_query: str, k: int = 10):
    return await client.query(
        """
        WITH results := ext::ai::search(ResumeMessage, <str>$q)
        SELECT results.object {
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


async def highlight_matches_with_gpt(optimized_query: str, filtered: list[dict[str, Any]]) -> list[dict[str, Any]]:
    system_prompt = (
        "Ты помогаешь выделить в тексте слова и фразы, которые соответствуют запросу. "
        "Используй только точные совпадения по смыслу (синонимы, разные формы слова, склонения, времена и т.п.). "
        "Игнорируй совпадения, которые не связаны с запросом.\n\n"
        "Формат: Верни список слов или фраз из текста, которые соответствуют запросу.\n"
        "Пример ответа: ['начинающий', 'без опыта', 'джуниор']"
    )

    results_with_highlights = []

    for r in filtered:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Запрос: {optimized_query}\nТекст: {r.content}"}
            ],
            temperature=0
        )

        highlights_raw = response.choices[0].message.content.strip()
        try:
            highlights = eval(highlights_raw) if highlights_raw.startswith("[") else []
        except Exception:
            highlights = []

        results_with_highlights.append(highlights)

    return results_with_highlights


async def full_pipeline(user_query: str) -> tuple[list[dict[str, Any]], list[list[Any]]]:
    print(f"[INFO] Запрос: {user_query}")

    # Этап 1: Преобразовать запрос
    optimized_query = await analyze_user_query(user_query)
    print(f"[DEBUG] Оптимизированный запрос: {optimized_query}")

    # Этап 2: Найти по эмбеддингам
    raw_results = await vector_search(optimized_query)
    print(f"[DEBUG] Получено {len(raw_results)} кандидатов из поиска")

    # Этап 3: Фильтрация через GPT
    filtered = await filter_results_with_gpt(user_query, raw_results)
    print(f"[INFO] Осталось {len(filtered)} после фильтрации")

    # Этап 4: Подсветка совпадений
    highlighted = await highlight_matches_with_gpt(optimized_query, filtered)
    print(f"[DEBUG] Подсветка выполнена")

    re_highlighted = [
        [word for word in re.findall(r'\w+', row[0]) if len(word) >= 3]
        for row in highlighted
    ]



    return filtered, re_highlighted


def test():
    query = "Юрист основатель"
    results, highlights = asyncio.run(full_pipeline(query))

    print("\n--- Результаты ---")
    for r in results:
        print(f"{r.created_at} — {r.author}: {r.content}")
        print(f"[Подсветка]: {highlights}\n")
