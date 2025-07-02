import json
import re
import asyncio
import edgedb
from typing import List, Any, Tuple, Dict

import httpx

from configs.project_paths import faiss_index_path, faiss_metadata_path
from configs.ai_config import MODEL_NAME

model = None
index = None
metadata = None


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


async def init_resources():
    """
    Инициализирует глобальные ресурсы: модель SentenceTransformer,
    индекс FAISS и метаданные.

    Загружает модель на устройство "mps" (Apple Silicon) если доступно,
    иначе на CPU. Загружает индекс FAISS и метаданные из файлов.

    Возвращаемое значение:
        None
    """
    global model, index, metadata
    if model is None or index is None or metadata is None:
        import torch
        from sentence_transformers import SentenceTransformer
        import faiss

        device = "mps" if torch.backends.mps.is_available() else "cpu"
        model = SentenceTransformer(MODEL_NAME, device=device)

        index = faiss.read_index(faiss_index_path)
        with open(faiss_metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)


async def analyze_user_query(user_query: str) -> str:
    """
    Оптимизирует пользовательский запрос, расширяя его синонимами,
    связанными терминами и аббревиатурами через вызов OpenRouter.

    Args:
        user_query (str): Исходный текст запроса пользователя.

    Returns:
        str: Оптимизированный запрос — строка с ключевыми словами и синонимами.
    """
    system_prompt = (
        "Ты ИИ-ассистент по поиску резюме. Преобразуй запрос пользователя в короткий список ключевых слов, "
        "синонимов и связанных терминов. Добавляй формы слов, синонимы, аббревиатуры, связанные роли. "
        "Игнорируй нерелевантные слова. Верни одну строку."
    )
    return await chat_completion_openrouter([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ], model="google/gemini-2.5-flash")


async def vector_search(optimized_query: str, k: int = 20) -> List[Dict[str, Any]]:
    """
    Выполняет поиск по FAISS индексу на основе векторного представления запроса.

    Args:
        optimized_query (str): Оптимизированный поисковый запрос.
        k (int): Максимальное число возвращаемых результатов (по умолчанию 20).

    Returns:
        List[Dict[str, Any]]: Список метаданных наиболее релевантных резюме.
    """
    await init_resources()

    query_vec = model.encode([optimized_query], convert_to_numpy=True).astype("float32")
    distances, indices = index.search(query_vec, k)
    return [metadata[idx] for idx in indices[0] if 0 <= idx < len(metadata)]


async def filter_and_highlight(user_query: str, results: List[Dict[str, Any]]) -> Tuple[
    List[Dict[str, Any]], List[List[str]]]:
    """
    Фильтрует результаты поиска, используя OpenRouter для подтверждения релевантности,
    а также выделяет ключевые слова, подтверждающие релевантность.

    Args:
        user_query (str): Исходный запрос пользователя.
        results (List[Dict[str, Any]]): Список резюме с метаданными.

    Returns:
        Tuple[List[Dict[str, Any]], List[List[str]]]:
            - Список отфильтрованных релевантных резюме.
            - Список списков ключевых слов/фраз для каждого релевантного резюме.
    """
    system_prompt = (
        "Ты ИИ-ассистент по отбору резюме.\n"
        "На входе — запрос пользователя и список резюме с их индексами.\n"
        "Для каждого резюме верни JSON объект с ключами:\n"
        "'index' — индекс резюме,\n"
        "'релевантно' — 'Да' или 'Нет',\n"
        "'подсветка' — список ключевых слов или фраз длиной 3+ символа, подтверждающих релевантность.\n"
        "Верни JSON-массив таких объектов.\n"
        "Пример:\n"
        "[{'index': 0, 'релевантно': 'Да', 'подсветка': ['машинное обучение', 'python']}, ...]"
    )

    user_content = f"Запрос: {user_query}\nРезюме:\n" + "".join(
        f"{i}: {r['content']}\n" for i, r in enumerate(results)
    )

    payload_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    response_text = await chat_completion_openrouter(payload_messages, model="google/gemini-2.5-flash")

    clean_response = re.sub(r"```json\s*|```", "", response_text).strip()
    try:
        parsed_list = json.loads(clean_response)
    except json.JSONDecodeError:
        try:
            parsed_list = eval(clean_response)
        except Exception as e:
            print(f"Error parsing response: {e}")
            parsed_list = []

    filtered = []
    highlights = []

    for item in sorted(parsed_list, key=lambda x: x.get("index", -1)):
        idx = item.get("index")
        if idx is None or idx >= len(results):
            continue
        if item.get("релевантно", "").lower().startswith("да"):
            phrases = [w for w in item.get("подсветка", []) if len(w) >= 3]
            filtered.append(results[idx])
            highlights.append(phrases)

    return filtered, highlights


async def chat_completion_openrouter(messages: List[Dict[str, str]], model: str = "google/gemini-2.5-flash") -> str:
    """
    Отправляет запрос к OpenRouter API и получает ответ от модели.

    Args:
        messages (List[Dict[str, str]]): Список сообщений с ролями для диалога (например, system, user).
        model (str): Имя модели OpenRouter для использования (по умолчанию "google/gemini-2.5-flash").

    Returns:
        str: Текстовый ответ от модели.
    """
    from configs.ai_config import openrouter_api_key

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
    Полный пайплайн поиска резюме:
    - Оптимизация запроса
    - Поиск по FAISS индексу
    - Фильтрация результатов и подсветка ключевых слов

    Args:
        user_query (str): Исходный запрос пользователя.

    Returns:
        Tuple[List[Dict[str, Any]], List[List[str]]]:
            - Список релевантных резюме.
            - Список списков ключевых слов для каждого резюме.
    """
    print(f"[INFO] Запрос: {user_query}")
    optimized_query = await analyze_user_query(user_query)
    print(f"[INFO] Оптимизированный запрос: {optimized_query}")

    raw_results = await vector_search(optimized_query)
    print(f"[INFO] Найдено кандидатов: {len(raw_results)}")

    filtered, highlighted = await filter_and_highlight(user_query, raw_results)
    print(f"[INFO] Отфильтровано: {len(filtered)}")
    print(f"[INFO] Подсветка завершена")

    return filtered, highlighted


def test() -> None:
    query = "искусственный интеллект"
    results, highlights = asyncio.run(full_pipeline(query))

    for r, hl in zip(results, highlights):
        print(f"{r['created_at']} — {r['author']}: {r['content']}")
        print(f"[Подсветка]: {hl}\n")


if __name__ == "__main__":
    test()
