import json
import os
import asyncio
from pprint import pformat

import edgedb
from typing import List, Any, Tuple, Dict

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
    db_conn_name
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
    global model, index, metadata, chunk_vectors

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    if device == "cpu":
        faiss.omp_set_num_threads(os.cpu_count())

    logger.info(f"[INIT RESOURCES] device: {device}")
    model = SentenceTransformer(faiss_model, device=device)

    index = faiss.read_index(faiss_index_path)
    index.nprobe = 10

    with open(faiss_metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    chunk_vectors = np.load(faiss_chunk_vectors_path, allow_pickle=True)


def get_relevant_chunks(query_vector: np.ndarray, chunks: List[str], chunk_embeds: np.ndarray, threshold: float = 0.8) -> List[str]:
    """
    Находит релевантные чанки на основе косинусной близости.
    """
    similarities = np.dot(chunk_embeds, query_vector.T).flatten()
    relevant_chunks = [chunk for chunk, score in zip(chunks, similarities) if score >= threshold]
    return relevant_chunks


async def vector_search(optimized_query: str, k: int = faiss_deep) -> tuple[List[Dict[str, Any]], List[List[str]]]:
    logger.debug(f"Starting vector search for query: '{optimized_query}' with k={k}")

    query_vec = model.encode([optimized_query], normalize_embeddings=True)
    scores, indices = index.search(np.array(query_vec), k)

    results = []
    highlights_list = []

    for idx in indices[0]:
        if idx == -1:
            continue

        item = metadata[idx]
        chunk_embeds = chunk_vectors[idx]
        chunks = item.get("chunks", [])

        if not chunks or len(chunk_embeds) == 0:
            continue

        highlights = get_relevant_chunks(query_vec[0], chunks, chunk_embeds)
        if not highlights:
            continue

        results.append({
            "id": item["id"],
            "text": item["text"],
            "meta": item["meta"],
            "highlights": highlights,
            "media_path": item["media_path"]
        })
        highlights_list.append(highlights)

    logger.info(f"Vector search returned {len(results)} records with highlights")
    logger.debug(f"Top results: {pformat(results)}")

    return results, highlights_list


async def full_pipeline(user_query: str) -> Tuple[List[Dict[str, Any]], List[List[str]]]:
    logger.info(f"Starting full pipeline for query: '{user_query}'")
    try:
        raw_results, highlights = await vector_search(user_query)
        return raw_results, highlights
    except Exception as e:
        logger.error(f"Error in full pipeline: {str(e)}")
        raise


def test() -> None:
    init_resources()
    query = "искусственный интеллект"
    results, highlights = asyncio.run(full_pipeline(query))

    for r, hl in zip(results, highlights):
        print(f"{r['meta']['author']}: {r['text'][:120]}...")
        print(f"[Подсветка]: {hl}\n")


if __name__ == "__main__":
    test()