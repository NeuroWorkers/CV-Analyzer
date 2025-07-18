import json
import os
import re
from typing import Any

import faiss
import numpy as np
import openai
import torch
from sentence_transformers import SentenceTransformer

from utils.logger import setup_logger
from configs.cfg import index_path, metadata_path, chunk_path, embedding_model, embedding_dim, threshold, \
    N_PROBE, EMBEDDING_MODE, POST_PROCESSING_FLAG, PRE_PROCESSING_LLM_FLAG, PRE_PROCESSING_SIMPLE_FLAG

import backend.subprocessing_LLM
import backend.subprocessing_nltk
from backend.q_preprocess import query_preprocess_faiss

logger = setup_logger("faiss")

model = None
index = None
metadata = None
chunk_vectors = None


def init_resources():
    """
    Инициализирует модель SentenceTransformer, загружает FAISS индекс,
    метаданные и эмбеддинги чанков.
    """
    global model, index, metadata, chunk_vectors

    if EMBEDDING_MODE == "sentence_transformers":
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        if device == "cpu":
            faiss.omp_set_num_threads(os.cpu_count())

        logger.info(f"[INIT RESOURCES] device: {device}")

        model = SentenceTransformer(embedding_model, device=device)

    index = faiss.read_index(index_path)
    index.nprobe = N_PROBE

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    chunk_vectors = np.load(chunk_path, allow_pickle=True)


def get_openai_embedding(text: str, embed_model: str = embedding_model) -> np.ndarray:
    try:
        response = openai.Embedding.create(input=text, model=embed_model)
        return np.array(response.data[0].embedding, dtype="float32").reshape(1, -1)
    except Exception as e:
        print(f"[OpenAI] Ошибка эмбеддинга: {e}")
        return np.zeros((1, embedding_dim), dtype="float32")


async def vector_search(optimized_query: str, k: int = 30):
    query_vec = None

    if EMBEDDING_MODE == "sentence_transformers":
        query_vec = model.encode([optimized_query], normalize_embeddings=True)
    else:
        if EMBEDDING_MODE == "openai":
            query_vec = get_openai_embedding(optimized_query)
        else:
            raise ValueError("ОШИБКА ФОРМИРОВАНИЯ ЕМБЕДДИНГОВ")

    scores, indices = index.search(query_vec, k)

    results = {}
    highlights = []

    for idx, score in zip(indices[0], scores[0]):
        if idx == -1:
            continue

        item = metadata[idx]

        if float(score) < threshold:
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

    logger.info(f"[FAISS/VECTOR_SEARCH] было отдано {len(results)} записей на FASTAPI")

    return list(results.values()), highlights


def split_query_by_lang(query: str) -> tuple[str, str]:
    """
    Разделяет запрос на русскую и английскую части,
    сохраняя знаки препинания и пробелы.

    Возвращает две подстроки: русскую и английскую.
    """
    ru_parts = []
    en_parts = []

    tokens = re.findall(r'[а-яА-ЯёЁa-zA-Z]+|\s+|[^\s\w]', query)

    for token in tokens:
        if re.search(r'[а-яА-ЯёЁ]', token):
            ru_parts.append(token)
        elif re.search(r'[a-zA-Z]', token):
            en_parts.append(token)
        else:
            ru_parts.append(token)
            en_parts.append(token)

    return "".join(ru_parts).strip(), "".join(en_parts).strip()


async def full_pipeline(user_query: str) -> tuple[list[dict[str, float | Any]], list[Any]]:
    try:
        query = None

        if PRE_PROCESSING_SIMPLE_FLAG:
            query = query_preprocess_faiss(user_query)
            logger.info(f"\n[FAISS/FULL_PIPELINE] Предобработанный запрос пользователя: {query}\n")

        if PRE_PROCESSING_LLM_FLAG:
            logger.info(f"\n backend.subprocessing_LLM.pre_proccessing() Start\n")
            query = await backend.subprocessing_LLM.pre_proccessing(user_query)
            logger.info(f"\n[FAISS/FULL_PIPELINE] Обогащенный запрос пользователя: {query}\n")

        if query is None:
            query = user_query

        ru_query, en_query = split_query_by_lang(query)
        logger.info(f"[FAISS/FULL_PIPELINE] RU-query: {ru_query}")
        logger.info(f"[FAISS/FULL_PIPELINE] EN-query: {en_query}")

        results_ru, highlights_ru = await vector_search(ru_query) if ru_query else ([], [])
        results_en, highlights_en = await vector_search(en_query) if en_query else ([], [])

        seen_ids = set()
        merged_results = []
        merged_highlights = []

        for result, highlight in zip(results_ru + results_en, highlights_ru + highlights_en):
            tid = result["telegram_id"]
            if tid not in seen_ids:
                merged_results.append(result)
                merged_highlights.append(highlight)
                seen_ids.add(tid)

        logger.info(f"\n[FAISS/FULL_PIPELINE] Релевантные хайлайты: {merged_highlights}\n")

        if POST_PROCESSING_FLAG:
            merged_results, merged_highlights = await backend.subprocessing_nltk.post_proccessing(
                query, merged_results, merged_highlights
            )
            logger.info(f"\n[FAISS/FULL_PIPELINE] Постобработанные хайлайты: {merged_highlights}\n")

        return merged_results, merged_highlights

    except Exception as e:
        logger.error(f"[FAISS/FULL_PIPELINE] Ошибка: {e}")
        return [], []