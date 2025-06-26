import asyncio
import edgedb
import openai
from typing import Any
from configs.ai_config import *

client = edgedb.create_async_client("database")


async def analyze_user_query(user_query: str) -> str:
    system_prompt = (
        "Ты помощник, который преобразует пользовательский запрос в строку для векторного или полнотекстового поиска "
        "по резюме. Сделай следующее:\n"
        "- Извлеки ключевые профессии, навыки, отрасли, должности и компании.\n"
        "- Преобразуй диапазоны чисел в список (например, 25–30 → 25 26 27 28 29 30).\n"
        "- Добавь синонимы или родственные слова (например, 'юрист' → 'адвокат', 'юрисконсульт').\n"
        "- Верни одну строку — итоговую фразу для поиска, без лишнего контекста."
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


async def full_pipeline(user_query: str) -> list[dict[str, Any]]:
    print(f"[INFO] Запрос: {user_query}")

    # Этап 1: Преобразовать запрос
    optimized_query = await analyze_user_query(user_query)
    print(f"[DEBUG] Оптимизированный запрос: {optimized_query}")

    # Этап 2: Найти по эмбеддингам в EdgeDB
    raw_results = await vector_search(optimized_query)
    print(f"[DEBUG] Получено {len(raw_results)} кандидатов из поиска")

    # Этап 3: Фильтрация через GPT
    filtered = await filter_results_with_gpt(user_query, raw_results)
    print(f"[INFO] Осталось {len(filtered)} после фильтрации")

    return filtered


if __name__ == "__main__":
    query = "Павел"
    results = asyncio.run(full_pipeline(query))

    print("\n--- Результаты ---")
    for r in results:
        print(f"{r.created_at} — {r.author}: {r.content}")