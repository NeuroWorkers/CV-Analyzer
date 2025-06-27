import json
import faiss
import openai
import asyncio
from typing import List, Dict, Any
from configs.ai_config import MODEL_NAME
from sentence_transformers import SentenceTransformer
from configs.project_paths import faiss_index_path, faiss_metadata_path


model = SentenceTransformer(MODEL_NAME)
index = faiss.read_index(faiss_index_path)
with open(faiss_metadata_path, "r", encoding="utf-8") as f:
    metadata = json.load(f)


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


async def vector_search(optimized_query: str, k: int = 10) -> list[dict]:
    query_vec = model.encode([optimized_query], convert_to_numpy=True).astype("float32")
    distances, indices = index.search(query_vec, k)

    results = []
    for idx in indices[0]:
        if 0 <= idx < len(metadata):
            results.append(metadata[idx])

    return results


async def filter_results_with_gpt(user_query: str, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    system_prompt = (
        "Ты помощник, фильтрующий резюме по запросу. "
        "Если текст резюме явно соответствует запросу — ответь 'Да', иначе — 'Нет'. "
        "Не додумывай, оцени только на основе явных фактов.\n\n"
        "Формат ответа: Да / Нет. Без объяснений."
    )

    filtered = []
    for r in results:
        text = r.get("text") or r.get("content")
        if not text:
            continue

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


async def full_pipeline(user_query: str) -> list[dict[str, Any]]:
    print(f"[INFO] Запрос: {user_query}")

    optimized_query = await analyze_user_query(user_query)
    print(f"[DEBUG] Оптимизированный запрос: {optimized_query}")

    raw_results = await vector_search(optimized_query)
    print(f"[DEBUG] Найдено {len(raw_results)} кандидатов")

    filtered = await filter_results_with_gpt(user_query, raw_results)
    print(f"[INFO] После фильтрации: {len(filtered)} кандидатов")

    return filtered


def test():
    query = "юристы от 20 до 40 лет"
    results = asyncio.run(full_pipeline(query))

    print("\n--- Результаты ---")
    for r in results:
        print(f"{r.get('timestamp')} — {r.get('author')}: {r.get('text')[:200]}...")
