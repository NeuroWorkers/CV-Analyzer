import json
import os

import edgedb
from typing import List, Any

import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from configs.cfg import (
    faiss_index_path,
    faiss_metadata_path,
    faiss_chunk_vectors_path,
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

    index = faiss.read_index(faiss_index_path)
    index.nprobe = N_PROBE

    with open(faiss_metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    chunk_vectors = np.load(faiss_chunk_vectors_path, allow_pickle=True)


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

    results = []
    highlights = []

    for idx, score in zip(indices[0], scores[0]):
        if idx == -1:
            continue

        item = metadata[idx]

        if float(score) < chunk_threshold:
            continue

        results.append({
            "telegram_id": item["telegram_id"],
            "date": item["date"],
            "content": item['content'],
            "author": item["author"],
            "media_path": item["media_path"],
            "score": float(score)
        })
        highlights.append(item.get("chunk", ""))

    logger.info(f"Vector search returned {len(results)} chunks")
    return results, highlights


async def full_pipeline(user_query: str) -> tuple[list[dict[str, float | Any]], list[Any]]:
    """
    Запускает полный пайплайн поиска по запросу: поиск в FAISS и возврат результатов.

    Args:
        user_query (str): Поисковый запрос пользователя.

    Returns:
        tuple[list[dict], list]: Результаты поиска и подсветки.
    """
    logger.info(f"Starting full pipeline for query: '{user_query}'")
    try:
        results, highlights = vector_search(user_query)
        return results, highlights
    except Exception as e:
        logger.error(f"Error in full pipeline: {str(e)}")
        raise
