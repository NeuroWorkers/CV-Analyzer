import json
import os
import asyncio
import re
from pprint import pformat

import edgedb
from typing import List, Any

import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from configs.cfg import faiss_index_path, faiss_metadata_path, faiss_deep
from configs.cfg import faiss_model, db_conn_name

from utils.logger import setup_logger

logger = setup_logger("faiss")

model = None
index = None
metadata = None

print("db_conn_name=" + db_conn_name)
client = edgedb.create_async_client(db_conn_name)

THRESHOLD_SCORE = 0.4


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
    global model, index, metadata

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    if device == "cpu":
        num_threads = os.cpu_count()
        faiss.omp_set_num_threads(num_threads)

    logger.info(f"[INIT RESOURCES] device: {device}")

    model = SentenceTransformer(faiss_model, device=device)

    index = faiss.read_index(faiss_index_path)
    index.nprobe = 20
    with open(faiss_metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)


def extract_highlights(query: str, text: str) -> List[str]:
    query_words = set(re.findall(r"\w+", query.lower()))
    text_words = re.findall(r"\w+", text.lower())
    return [word for word in query_words if word in text_words]


async def vector_search(optimized_query: str, k: int = faiss_deep) -> tuple[list[dict[str, list[str] | Any]], list[str]]:
    logger.debug(f"Starting vector search for query: '{optimized_query}' with k={k}")

    query_vec = model.encode([optimized_query.lower()], normalize_embeddings=False)
    scores, indices = index.search(np.array(query_vec), k)

    logger.debug(f"FAISS search completed. Top scores: {scores[0][:5]}")

    results = []
    highlights_set = set()

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1 or score < THRESHOLD_SCORE:
            continue

        item = metadata[idx]

        combined_text = f"Автор CV(резюме), автор текста: {item['author']}. Резюме: {item['content']}"
        hl = extract_highlights(optimized_query, combined_text)

        results.append({
            "telegram_id": item["telegram_id"],
            "date": item["date"],
            "content": item["content"],
            "author": item["author"],
            "highlights": hl,
            "media_path": item["media_path"]
        })

        highlights_set.update(hl)

    logger.info(f"Vector search returned {len(results)} results above threshold {THRESHOLD_SCORE}")
    logger.debug(f"Search results preview: {pformat(results[:3])}")

    return results, list(highlights_set)


async def full_pipeline(user_query: str) -> tuple[list[dict[str, list[str] | Any]], list[str]]:
    try:
        logger.info(f"Starting full pipeline for query: '{user_query}'")
        raw_results, highlights = await vector_search(user_query)
        return raw_results, highlights
    except Exception as e:
        logger.error(f"Error in full pipeline: {str(e)}")
        raise


def test() -> None:
    query = "искусственный интеллект"
    results, highlights = asyncio.run(full_pipeline(query))

    for r, hl in zip(results, highlights):
        print(f"{r['created_at']} — {r['author']}: {r['content']}")
        print(f"[Подсветка]: {hl}\n")


if __name__ == "__main__":
    test()
