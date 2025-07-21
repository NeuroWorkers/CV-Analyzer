import json
import os
import re
from typing import Any, Tuple, List

import faiss
import numpy as np
import openai
import torch
from sentence_transformers import SentenceTransformer

from utils.logger import setup_logger
from configs.cfg import (
    index_path,
    metadata_path,
    chunk_path,
    embedding_model,
    embedding_dim,
    threshold,
    N_PROBE,
    EMBEDDING_MODE,
    POST_PROCESSING_FLAG,
    PRE_PROCESSING_LLM_FLAG,
    PRE_PROCESSING_SIMPLE_FLAG,
)

import backend.subprocessing_LLM
import backend.subprocessing_nltk
from backend.q_preprocess import query_preprocess_faiss

logger = setup_logger("faiss")

model = index = metadata = chunk_vectors = None


def init_resources() -> None:
    """Однократно загружает модель и FAISS‑индекс."""
    global model, index, metadata, chunk_vectors

    if EMBEDDING_MODE == "sentence_transformers":
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        if device == "cpu":
            faiss.omp_set_num_threads(os.cpu_count())
        logger.info(f"[INIT] device: {device}")
        model = SentenceTransformer(embedding_model, device=device)

    index = faiss.read_index(index_path)
    index.nprobe = N_PROBE

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    chunk_vectors = np.load(chunk_path, allow_pickle=True)


def get_openai_embeddings(texts: List[str], embed_model: str = embedding_model) -> np.ndarray:
    if not texts:
        return np.zeros((0, embedding_dim), dtype="float32")
    try:
        response = openai.Embedding.create(input=texts, model=embed_model)
        data = sorted(response.data, key=lambda x: x.index)
        return np.array([d.embedding for d in data], dtype="float32")
    except Exception as e:
        logger.error(f"[OpenAI] Ошибка эмбеддинга батча: {e}")
        return np.zeros((len(texts), embedding_dim), dtype="float32")


def split_query_by_lang(query: str) -> Tuple[str, str]:
    ru, en = [], []
    for tok in re.findall(r'\b[\w-]+\b', query):
        (ru if re.search(r'[а-яА-ЯёЁ]', tok) else en).append(tok)
    return " ".join(ru), " ".join(en)


def vector_search_batch(queries: List[str], k: int = 30) -> List[Tuple[dict, str, str]]:
    """
    Возвращает список кортежей (результат, highlight, источник-запрос), чтобы позже приоритизировать user_query.
    """
    if not queries:
        return []

    if EMBEDDING_MODE == "sentence_transformers":
        vecs = model.encode(queries, normalize_embeddings=True)
    elif EMBEDDING_MODE == "openai":
        vecs = get_openai_embeddings(queries)
    else:
        raise ValueError("Неизвестный EMBEDDING_MODE")

    scores, indices = index.search(vecs, k)

    triples = []  # (result_dict, highlight, query_text)
    for q_idx, query in enumerate(queries):
        for idx, score in zip(indices[q_idx], scores[q_idx]):
            if idx == -1 or score < threshold:
                continue
            item = metadata[idx]
            triples.append((
                {
                    "telegram_id": item["telegram_id"],
                    "date": item["date"],
                    "content": item["content"],
                    "author": item["author"],
                    "media_path": item["media_path"],
                    "score": float(score),
                },
                item.get("chunk", ""),
                query
            ))

    logger.info(f"[FAISS/BATCH] queries={len(queries)}, hits={len(triples)}")
    return triples


async def full_pipeline(user_query: str) -> Tuple[List[dict[str, Any]], List[str]]:
    query = user_query
    if PRE_PROCESSING_SIMPLE_FLAG:
        query = query_preprocess_faiss(query)
        logger.info(f"\n[FAISS/FULL_PIPELINE] Предобработанный запрос пользователя: {query}\n")
    if PRE_PROCESSING_LLM_FLAG:
        query = await backend.subprocessing_LLM.pre_proccessing(query)
        logger.info(f"\n[FAISS/FULL_PIPELINE] Обогащенный запрос пользователя: {query}\n")

    ru_part, en_part = split_query_by_lang(query)

    ru_tokens = [tok for tok in ru_part.split() if len(tok) > 2]
    en_tokens = [tok for tok in en_part.split() if len(tok) > 2]

    search_queries = [user_query, query] + en_tokens + ru_tokens
    uniq_queries = list(dict.fromkeys(search_queries))

    triples = vector_search_batch(uniq_queries)

    top_results = []
    seen = set()

    for rec, hl, src in triples:
        if src == user_query:
            tid = rec["telegram_id"]
            if tid not in seen:
                top_results.append((rec, hl))
                seen.add(tid)

    other_results = []
    for rec, hl, _ in sorted(triples, key=lambda x: x[0]["score"], reverse=True):
        tid = rec["telegram_id"]
        if tid not in seen:
            other_results.append((rec, hl))
            seen.add(tid)

    final_results = [r for r, _ in top_results + other_results]
    final_highlights = [h for _, h in top_results + other_results]

    logger.info(f"[PIPELINE] уникальных записей: {len(final_results)}")
    logger.info(f"\n[FAISS/FULL_PIPELINE] Релевантные хайлайты: {final_highlights}\n")

    if POST_PROCESSING_FLAG:
        final_results, final_highlights = await backend.subprocessing_nltk.post_proccessing(
            query + " " + user_query, final_results, final_highlights
        )
        logger.info(f"\n[FAISS/FULL_PIPELINE] Постобработанные хайлайты: {final_highlights}\n")

    return final_results, final_highlights
