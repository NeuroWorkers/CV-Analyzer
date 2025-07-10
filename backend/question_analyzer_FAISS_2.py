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
    chunk_threshold,
    top_k,
    db_conn_name,
    faiss_author_index_path,
    faiss_author_metadata_path,
    faiss_author_vectors_path
)

from utils.logger import setup_logger

logger = setup_logger("faiss")

model = None
author_model = None
index = None
metadata = None
chunk_vectors = None
author_index = None
author_metadata = None
author_vectors = None

print("db_conn_name=" + db_conn_name)
client = edgedb.create_async_client(db_conn_name)

def init_resources():
    global model, index, metadata, chunk_vectors
    global author_model, author_index, author_metadata, author_vectors

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    if device == "cpu":
        faiss.omp_set_num_threads(os.cpu_count())

    logger.info(f"[INIT RESOURCES] device: {device}")
    model = SentenceTransformer(faiss_model, device=device)
    author_model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased-v1", device=device)

    index = faiss.read_index(faiss_index_path)
    index.nprobe = 100

    with open(faiss_metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    chunk_vectors = np.load(faiss_chunk_vectors_path, allow_pickle=True)

    author_index = faiss.read_index(faiss_author_index_path)
    author_index.nprobe = 100

    with open(faiss_author_metadata_path, "r", encoding="utf-8") as f:
        author_metadata = json.load(f)
    author_vectors = np.load(faiss_author_vectors_path, allow_pickle=True)

def is_name_like(query: str) -> bool:
    tokens = query.strip().split()
    return 1 <= len(tokens) <= 3 and all(t[0].isupper() for t in tokens if t.isalpha())

def author_search(query: str, k: int = 5) -> List[str]:
    if not is_name_like(query):
        return []

    query_vec = author_model.encode([query], normalize_embeddings=True)
    scores, indices = author_index.search(np.array(query_vec), k)
    return [author_metadata[i] for i in indices[0] if i != -1]

def get_relevant_chunks(query_vector: np.ndarray, chunks: List[str], chunk_embeds: np.ndarray, threshold: float = 0.85, top_k: int = 10) -> List[str]:
    query_norm = query_vector / np.linalg.norm(query_vector)
    chunk_norms = chunk_embeds / np.linalg.norm(chunk_embeds, axis=1, keepdims=True)

    similarities = np.dot(chunk_norms, query_norm.T)

    relevant_indices = np.where(similarities >= threshold)[0]
    sorted_indices = relevant_indices[np.argsort(similarities[relevant_indices])[::-1]]
    top_indices = sorted_indices[:top_k]

    return [chunks[i] for i in top_indices]

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

        highlights = get_relevant_chunks(query_vec[0], chunks, chunk_embeds, chunk_threshold, top_k)
        if not highlights:
            continue

        results.append({
            "telegram_id": item["telegram_id"],
            "date": item["date"],
            "content": item["content"],
            "author": item["author"],
            "media_path": item['media_path'],
            "highlights": highlights
        })
        highlights_list.append(highlights)

    logger.info(f"Vector search returned {len(results)} records with highlights")
    logger.debug(f"Top results: {pformat(results)}")

    return results, highlights_list

async def full_pipeline(user_query: str) -> Tuple[List[Dict[str, Any]], List[List[str]]]:
    logger.info(f"Starting full pipeline for query: '{user_query}'")
    try:
        raw_results, highlights = await vector_search(user_query)

        author_results = []
        if is_name_like(user_query):
            matched_authors = author_search(user_query)
            logger.debug(f"[AUTHOR SEARCH] Найдены авторы: {matched_authors}")
            if matched_authors:
                all_messages = await fetch_all_messages()
                author_results = [msg for msg in all_messages if msg["author"] in matched_authors]

        combined_results = raw_results
        if author_results:
            seen_ids = {r["telegram_id"] for r in combined_results}
            combined_results.extend([r for r in author_results if r["telegram_id"] not in seen_ids])

        return combined_results, highlights
    except Exception as e:
        logger.error(f"Error in full pipeline: {str(e)}")
        raise

def test() -> None:
    init_resources()
    query = "искусственный интеллект"
    results, highlights = asyncio.run(full_pipeline(query))

    for r, hl in zip(results, highlights):
        print(f"{r['author']}: {r['content'][:120]}...")
        print(f"[Подсветка]: {hl}\n")

if __name__ == "__main__":
    test()
