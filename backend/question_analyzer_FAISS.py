import json
import re
import asyncio
from pprint import pformat

import edgedb
from typing import List, Any, Tuple, Dict

import faiss
import httpx
import torch
from sentence_transformers import SentenceTransformer

from configs.project_paths import faiss_index_path, faiss_metadata_path
from configs.ai_config import faiss_model, openai_model, db_conn_name

from utils.logger import MyLogger

model = None
index = None
metadata = None


logger = MyLogger(__name__)


print("db_conn_name=" + db_conn_name)  # default "database"
client = edgedb.create_async_client(db_conn_name)


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


def init_resources():
    """
    Инициализирует глобальные ресурсы: модель SentenceTransformer,
    индекс FAISS и метаданные.

    Загружает модель на устройство "mps" (Apple Silicon) если доступно,
    иначе на CPU. Загружает индекс FAISS и метаданные из файлов.

    Returns:
        None
    """
    global model, index, metadata

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    logger.info(f"[INIT RESOURCES] device: {device}")

    model = SentenceTransformer(faiss_model, device=device)

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
    ], model=openai_model)


async def vector_search(optimized_query: str, k: int = 20) -> List[Dict[str, Any]]:
    """
    Выполняет поиск по FAISS индексу на основе векторного представления запроса.

    Args:
        optimized_query (str): Оптимизированный поисковый запрос.
        k (int): Максимальное число возвращаемых результатов (по умолчанию 20).

    Returns:
        List[Dict[str, Any]]: Список метаданных наиболее релевантных резюме.
    """
    query_vec = model.encode([optimized_query], convert_to_numpy=True).astype("float32")
    distances, indices = index.search(query_vec, k)

    search_results = [metadata[idx] for idx in indices[0] if 0 <= idx < len(metadata)]
    logger.info(f"[VECTOR SEARCH] search results: {pformat(search_results)}")
    return search_results


async def filter_and_highlight(user_query: str, results: List[Dict[str, Any]]) -> Tuple[
    List[Dict[str, Any]], List[List[str]]]:
    """
    Фильтрует результаты поиска, используя OpenRouter для подтверждения релевантности,
    а также выделяет ключевые слова, подтверждающие релевантность.

    Returns:
         Отфильтрованный массив и хайлайты.
    """
    system_prompt = (
        "Ты ИИ-ассистент по отбору резюме.\n"
        "На входе — запрос пользователя и список резюме, каждый из которых имеет telegram_id, автора и текст.\n\n"
        "Для каждого резюме реши, релевантно ли оно запросу. Если да, верни объект:\n"
        "{'telegram_id': 123456789, 'релевантно': 'Да', 'подсветка': ['ключ1', 'ключ2']}.\n"
        "Если резюме не подходит — не включай его в ответ.\n"
        "Верни JSON-массив таких объектов."
    )

    resume_blocks = []
    for r in results:
        author = r.get("author", "").strip()
        content = r.get("content", "").strip()
        telegram_id = r.get("telegram_id")
        full_text = f"[{telegram_id}] Автор: {author}\nТекст: {content}\n"
        resume_blocks.append(full_text)

    user_content = f"Запрос: {user_query}\nРезюме:\n" + "\n".join(resume_blocks)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    response_text = await chat_completion_openrouter(messages, model=openai_model)

    clean_response = re.sub(r"```json\s*|```", "", response_text).strip()

    try:
        parsed_list = json.loads(clean_response)
    except json.JSONDecodeError:
        try:
            parsed_list = eval(clean_response)
        except Exception as e:
            print(f"[ERROR parse JSON]: {e}")
            parsed_list = []

    result_by_tid = {r["telegram_id"]: r for r in results}

    filtered = []
    highlights = []

    for item in parsed_list:
        tid = item.get("telegram_id")
        if tid is None or tid not in result_by_tid:
            continue
        if item.get("релевантно", "").lower().startswith("да"):
            phrases = [w for w in item.get("подсветка", []) if len(w) >= 3]
            filtered.append(result_by_tid[tid])
            highlights.append(phrases)

    logger.info(f"[FILTER AND HIGHLIGHT] filtered: {pformat(filtered)}\nhighlights: {pformat(highlights)}")
    return filtered, highlights


async def chat_completion_openrouter(messages: List[Dict[str, str]], model: str = openai_model) -> str:
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
