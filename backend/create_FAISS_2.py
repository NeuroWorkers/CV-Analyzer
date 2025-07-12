import os
import json
import faiss
import numpy as np
from typing import List, Dict
import re

import torch
from sentence_transformers import SentenceTransformer

from configs.cfg import (
    faiss_model,
    relevant_text_path,
    faiss_index_path,
    faiss_metadata_path,
    N_LIST,
    faiss_chunk_vectors_path
)

model = None
index = None
metadata = None


def init_resources():
    """
    Инициализация модели SentenceTransformer и настройка Faiss для многопоточности на CPU.

    Выбирает устройство ('mps' или 'cpu') и загружает модель с указанным faiss_model.
    Для CPU устанавливает количество потоков Faiss равным числу ядер процессора.
    """
    global model
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    if device == "cpu":
        faiss.omp_set_num_threads(os.cpu_count())
    model = SentenceTransformer(faiss_model, device=device)


def flatten_json_data(json_data: Dict) -> List[Dict]:
    """
    Преобразует вложенный JSON с резюме в плоский список записей.

    Args:
        json_data (Dict): Словарь с исходными данными.

    Returns:
        List[Dict]: Список записей с ключами telegram_id, date, content, author, media_path.
    """
    records = []
    for _, items in json_data.items():
        for item in items:
            if item["downloaded_text"][2]:
                records.append({
                    "telegram_id": item["downloaded_text"][0],
                    "date": item["downloaded_text"][1],
                    "content": item["downloaded_text"][2],
                    "author": item["downloaded_text"][3],
                    "media_path": item['downloaded_media']['path']
                })
    return records


def split_into_chunks(text: str) -> List[str]:
    """
    Разбивает текст на чанки: предложения, биграммы и триграммы.

    Args:
        text (str): Исходный текст.

    Returns:
        List[str]: Список чанков (предложений и n-грамм).
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    #tokens = text.strip().lower().split()
    tokens = text.strip().split()
    onegrams = [' '.join(tokens[i:i+1]) for i in range(len(tokens))]
    bigrams = [' '.join(tokens[i:i+2]) for i in range(len(tokens) - 1)]
    trigrams = [' '.join(tokens[i:i+3]) for i in range(len(tokens) - 2)]
    return sentences + onegrams + bigrams + trigrams


def build_or_update_index():
    """
    Создаёт или обновляет FAISS индекс и сопутствующие метаданные.

    Если индекс и метаданные существуют, добавляет только новые записи.
    Для каждой записи создаются эмбеддинги чанков (предложений и n-грамм),
    обновляется FAISS индекс, метаданные и файл с эмбеддингами чанков.

    Если индекс отсутствует, создаёт новый с нуля.

    Выводит прогресс и количество добавленных записей/чанков.
    """
    with open(os.path.join(relevant_text_path, "cv.json"), "r", encoding="utf-8") as f:
        json_data = json.load(f)

    print("\nИзвлечение данных")
    records = flatten_json_data(json_data)
    print(f"Найдено {len(records)} записей.")

    if os.path.exists(faiss_index_path) and os.path.exists(faiss_metadata_path):
        print("[FAISS] Индекс найден — обновляем только новыми.")
        with open(faiss_metadata_path, "r", encoding="utf-8") as f:
            existing_metadata = json.load(f)
        existing_ids = {entry["telegram_id"] for entry in existing_metadata}

        new_records = [r for r in records if r["telegram_id"] not in existing_ids]
        if not new_records:
            print("[FAISS] Нет новых записей для добавления.")
            return

        all_chunks = []
        chunk_metadata = []

        for record in new_records:
            chunks = split_into_chunks(f"Автор: {record['author']}. Текст: {record['content']}")
            for chunk in chunks:
                all_chunks.append(chunk)
                chunk_metadata.append({
                    "telegram_id": record["telegram_id"],
                    "date": record["date"],
                    "content": record['content'],
                    "author": record["author"],
                    "media_path": record["media_path"],
                    "chunk": chunk
                })

        print(f"Создаем эмбеддинги для {len(all_chunks)} новых чанков.")
        embeddings = model.encode(all_chunks, show_progress_bar=True, batch_size=32, normalize_embeddings=True)

        index = faiss.read_index(faiss_index_path)
        index.add(embeddings)
        faiss.write_index(index, faiss_index_path)

        updated_metadata = existing_metadata + chunk_metadata
        with open(faiss_metadata_path, "w", encoding="utf-8") as f:
            json.dump(updated_metadata, f, ensure_ascii=False, indent=2)

        if os.path.exists(faiss_chunk_vectors_path):
            existing_chunk_vectors = np.load(faiss_chunk_vectors_path, allow_pickle=True)
        else:
            existing_chunk_vectors = np.empty((0,), dtype=object)

        new_grouped_vectors = []
        current_id = None
        temp_vecs = []

        for meta, vec in zip(chunk_metadata, embeddings):
            telegram_id = meta["telegram_id"]
            if telegram_id != current_id:
                if temp_vecs:
                    new_grouped_vectors.append(np.array(temp_vecs))
                temp_vecs = []
                current_id = telegram_id
            temp_vecs.append(vec)
        if temp_vecs:
            new_grouped_vectors.append(np.array(temp_vecs))

        updated_chunk_vectors = np.concatenate([existing_chunk_vectors, np.array(new_grouped_vectors, dtype=object)])
        np.save(faiss_chunk_vectors_path, updated_chunk_vectors)

        print(f"[FAISS] Добавлено {len(new_records)} новых записей и {len(all_chunks)} чанков.")

    else:
        print("[FAISS] Индекс не найден — создаём новый.")
        all_chunks = []
        chunk_metadata = []

        for record in records:
            chunks = split_into_chunks(f"Автор: {record['author']}. Текст: {record['content']}")
            for chunk in chunks:
                all_chunks.append(chunk)
                chunk_metadata.append({
                    "telegram_id": record["telegram_id"],
                    "date": record["date"],
                    "content": record['content'],
                    "author": record["author"],
                    "media_path": record["media_path"],
                    "chunk": chunk
                })

        print(f"Создаем эмбеддинги для {len(all_chunks)} чанков.")
        embeddings = model.encode(all_chunks, show_progress_bar=True, batch_size=32, normalize_embeddings=True)

        print("\nСоздание индекса")
        EMBEDDING_DIM = model.get_sentence_embedding_dimension()
        quantizer = faiss.IndexFlatIP(EMBEDDING_DIM)
        index = faiss.IndexIVFFlat(quantizer, EMBEDDING_DIM, N_LIST, faiss.METRIC_INNER_PRODUCT)

        print("Тренинг")
        index.train(embeddings)
        index.add(embeddings)
        faiss.write_index(index, faiss_index_path)

        with open(faiss_metadata_path, "w", encoding="utf-8") as f:
            json.dump(chunk_metadata, f, ensure_ascii=False, indent=2)

        grouped_vectors = []
        current_id = None
        temp_vecs = []

        for meta, vec in zip(chunk_metadata, embeddings):
            telegram_id = meta["telegram_id"]
            if telegram_id != current_id:
                if temp_vecs:
                    grouped_vectors.append(np.array(temp_vecs))
                temp_vecs = []
                current_id = telegram_id
            temp_vecs.append(vec)
        if temp_vecs:
            grouped_vectors.append(np.array(temp_vecs))

        np.save(faiss_chunk_vectors_path, np.array(grouped_vectors, dtype=object))

        print(f"\nНовый индекс создан. Всего чанков: {len(all_chunks)}")
