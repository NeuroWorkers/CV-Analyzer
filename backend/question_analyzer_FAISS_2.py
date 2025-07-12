import json
import os
import re
import asyncio

import edgedb
from typing import List, Any, Dict

import faiss
import httpx
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from utils.misc_func import capitalize_sentence

from configs.cfg import (
    POST_PROCESSING_FLAG,
    highlight_model,
    faiss_content_index_path,
    faiss_content_metadata_path,
    faiss_content_chunk_vectors_path,
    faiss_deep,
    faiss_model,
    chunk_threshold,
    db_conn_name,
    N_PROBE
)

from utils.logger import setup_logger

logger = setup_logger("faiss")

model = None
index = None
metadata = None
chunk_vectors = None

print("db_conn_name=" + db_conn_name)
client = edgedb.create_async_client(db_conn_name)


async def fetch_all_messages() -> List[dict[str, Any]]:
    """
    Загружает все сообщения с резюме из базы данных EdgeDB.

    Returns:
        List[dict[str, Any]]: Список словарей с полями резюме:
            'telegram_id' (int),
            'content' (str),
            'author' (str),
            'created_at' (datetime),
            'media_path' (str|None).
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
    Инициализирует модель SentenceTransformer, загружает FAISS индекс,
    метаданные и эмбеддинги чанков.
    """
    global model, index, metadata, chunk_vectors

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    if device == "cpu":
        faiss.omp_set_num_threads(os.cpu_count())

    logger.info(f"[INIT RESOURCES] device: {device}")
    model = SentenceTransformer(faiss_model, device=device)

    index = faiss.read_index(faiss_content_index_path)
    index.nprobe = N_PROBE

    with open(faiss_content_metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    chunk_vectors = np.load(faiss_content_chunk_vectors_path, allow_pickle=True)


def vector_search(optimized_query: str, k: int = faiss_deep) -> tuple[list[dict[str, float | Any]], list[Any]]:
    """
    Выполняет поиск по векторному FAISS индексу.

    Args:
        optimized_query (str): Поисковый запрос.
        k (int): Количество возвращаемых результатов.

    Returns:
        tuple[list[dict], list]: Список результатов с метаданными и список подсветок чанков.
    """
    logger.debug(f"Starting vector search for query: '{optimized_query}' with k={k}")

    query_vec = model.encode([optimized_query], normalize_embeddings=True)
    scores, indices = index.search(np.array(query_vec), k)

    results = {}
    highlights = []

    for idx, score in zip(indices[0], scores[0]):
        if idx == -1:
            continue

        item = metadata[idx]

        if float(score) < chunk_threshold:
            continue

        telegram_id = item["telegram_id"]

        if telegram_id not in results or results[telegram_id]["score"] < float(score):
            results[telegram_id] = {
                "telegram_id": telegram_id,
                "date": item["date"],
                "content": item['content'],
                "author": item["author"],
                "media_path": item["media_path"],
                "score": float(score)
            }
            highlights.append(item.get("chunk", ""))

    logger.info(f"Vector search returned {len(results)} unique telegram_ids")

    return list(results.values()), highlights


def chunk_list(lst, size):
    """Разбивает список на чанки размера size."""
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


"""
БЕЗ МНОГОПОТОЧКИ
async def filter_with_llm(user_query: str, results: List[dict]) -> List[dict]:
    if not results:
        return []

    system_prompt = (
        "Ты — ИИ, фильтрующий резюме по запросу пользователя.\n"
        "На входе — запрос и список результатов. Каждый результат содержит telegram_id, автора и текст.\n"
        "Верни JSON-массив объектов вида: {'telegram_id': <id>, 'релевантно': 'Да'} — только для релевантных результатов.\n"
        "Если результат нерелевантен — просто не включай его в ответ."
    )

    resume_blocks = []
    for r in results:
        resume_blocks.append(f"[{r['telegram_id']}] Автор: {r['author']}\nТекст: {r['content']}")

    user_prompt = f"Запрос: {user_query}\nРезультаты:\n" + "\n\n".join(resume_blocks)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    response = await chat_completion_openrouter(messages, model=highlight_model)

    try:
        clean = re.sub(r"```json\s*|```", "", response).strip()
        parsed = json.loads(clean)
    except Exception as e:
        logger.error(f"Ошибка парсинга ответа LLM: {e}")
        return []

    # Сопоставляем по telegram_id
    telegram_id_to_result = {r["telegram_id"]: r for r in results}
    filtered = []

    for item in parsed:
        tid = item.get("telegram_id")
        if item.get("релевантно", "").lower().startswith("да") and tid in telegram_id_to_result:
            filtered.append(telegram_id_to_result[tid])

    logger.info(f"LLM-фильтрация завершена: {len(filtered)} релевантных результатов из {len(results)}")

    return filtered
"""


async def filter_with_llm(user_query: str, results: List[dict], highlights: List[str], chunk_size: int = 5) -> List[dict]:
    """
    Фильтрует результаты поиска, отправляя LLM только highlights вместо полного текста.

    Args:
        user_query (str): Поисковый запрос пользователя.
        results (List[dict]): Результаты поиска.
        highlights (List[str]): Список подсвеченных фрагментов для результатов.
        chunk_size (int): Размер одного батча.

    Returns:
        List[dict]: Только релевантные результаты.
    """
    if not results or not highlights:
        return []

    async def process_chunk(chunk: List[tuple[dict, str]]) -> List[dict]:
        system_prompt = (
            "Ты — ИИ, фильтрующий короткие фрагменты резюме по запросу пользователя.\n"
            "На входе — запрос и список фрагментов. Каждый фрагмент содержит telegram_id и текст.\n"
            "Верни JSON-массив объектов вида: {'telegram_id': <id>, 'релевантно': 'Да'} — только для релевантных.\n"
            "Если фрагмент нерелевантен — просто не включай его в ответ."
        )

        blocks = [f"[{r['telegram_id']}] {highlight}" for r, highlight in chunk]

        user_prompt = f"Запрос: {user_query}\nФрагменты:\n" + "\n\n".join(blocks)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = await chat_completion_openrouter(messages, model=highlight_model)
            clean = re.sub(r"```json\s*|```", "", response).strip()
            parsed = json.loads(clean)
        except Exception as e:
            logger.error(f"[LLM Chunk] Ошибка обработки чанка: {e}")
            return []

        telegram_id_to_result = {r["telegram_id"]: r for r, _ in chunk}
        filtered = []

        for item in parsed:
            tid = item.get("telegram_id")
            if item.get("релевантно", "").lower().startswith("да") and tid in telegram_id_to_result:
                filtered.append(telegram_id_to_result[tid])

        return filtered

    paired = list(zip(results, highlights))
    tasks = [process_chunk(chunk) for chunk in chunk_list(paired, chunk_size)]
    all_filtered = await asyncio.gather(*tasks)

    flat_results = [item for sublist in all_filtered for item in sublist]
    logger.info(f"Фильтрация по highlights завершена: {len(flat_results)} из {len(results)}")
    return flat_results


async def chat_completion_openrouter(messages: List[Dict[str, str]], model) -> str:
    """
    Отправляет запрос к OpenRouter API и получает ответ от модели.

    Args:
        messages (List[Dict[str, str]]): Список сообщений с ролями для диалога (например, system, user).
        model (str): Имя модели OpenRouter для использования (по умолчанию "google/gemini-2.5-flash").

    Returns:
        str: Текстовый ответ от модели.
    """
    from configs.cfg import openrouter_api_key

    logger.debug(f"Sending request to OpenRouter API with model: {model}")

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client_http:
            logger.debug("Making HTTP request to OpenRouter API")
            response = await client_http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            result = response.json()["choices"][0]["message"]["content"].strip()
            logger.debug(f"OpenRouter API response received, length: {len(result)} characters")
            return result

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from OpenRouter API: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in OpenRouter API call: {str(e)}")
        raise


async def full_pipeline(user_query: str) -> tuple[list[dict[str, float | Any]], list[Any]]:
    """
    Запускает полный пайплайн поиска по запросу: поиск в FAISS и возврат результатов.

    Args:
        user_query (str): Поисковый запрос пользователя.

    Returns:
        tuple[list[dict], list]: Результаты поиска и подсветки.
    """
    logger.info(f"Starting full pipeline for query: '{user_query}'")
    user_query=capitalize_sentence(user_query)
    try:
        if POST_PROCESSING_FLAG:
            results, highlights = vector_search(user_query)
            filtered_results = await filter_with_llm(user_query, results, highlights)
        else:
            filtered_results, highlights = vector_search(user_query)

        return filtered_results, highlights
    except Exception as e:
        logger.error(f"Error in full pipeline: {str(e)}")
        raise
