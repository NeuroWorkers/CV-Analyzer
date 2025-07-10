import os
import json
import faiss
import numpy as np
from typing import List, Dict

import torch
from sentence_transformers import SentenceTransformer

from configs.cfg import (
    faiss_model,
    relevant_text_path,
    faiss_index_path,
    faiss_metadata_path,
    faiss_chunk_vectors_path
)

model = None
index = None
metadata = None

N_LIST = 100
EMBEDDING_DIM = 384


def init_resources():
    global model
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    if device == "cpu":
        faiss.omp_set_num_threads(os.cpu_count())
    model = SentenceTransformer(faiss_model, device=device)


def flatten_json_data(json_data: Dict) -> List[Dict]:
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
    words = text.split()
    return words


def build_or_update_index():
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

        texts = [r["content"] for r in new_records]

        print(f"Создаем эмбеддинги для {len(texts)} новых записей.")
        embeddings = model.encode([t.lower() for t in texts], show_progress_bar=True, batch_size=32, normalize_embeddings=True)

        index = faiss.read_index(faiss_index_path)
        index.add(embeddings)
        faiss.write_index(index, faiss_index_path)

        print("\nОбработка чанков для новых записей")
        with open(faiss_chunk_vectors_path, "rb") as f:
            existing_chunk_vectors = np.load(f, allow_pickle=True)

        new_metadata = []
        new_chunk_vectors = []

        for record in new_records:
            chunks = split_into_chunks(record["text"])
            chunk_embeds = model.encode(chunks, batch_size=16, normalize_embeddings=True)

            new_metadata.append({
                "telegram_id": record["telegram_id"],
                "date": record["date"],
                "content": record["content"],
                "author": record["author"],
                "media_path": record['media_path'],
                "chunks": chunks
            })
            new_chunk_vectors.append(chunk_embeds)

        updated_metadata = existing_metadata + new_metadata
        updated_chunk_vectors = np.concatenate([existing_chunk_vectors, np.array(new_chunk_vectors, dtype=object)])

        with open(faiss_metadata_path, "w", encoding="utf-8") as f:
            json.dump(updated_metadata, f, ensure_ascii=False, indent=2)
        np.save(faiss_chunk_vectors_path, updated_chunk_vectors)

        print(f"[FAISS] Добавлено {len(new_records)} новых записей и {sum(len(c) for c in new_chunk_vectors)} чанков.")
    else:
        print("[FAISS] Индекс не найден — создаём новый.")
        texts = [r["content"] for r in records]
        print(f"Создаем эмбеддинги для {len(texts)} записей.")
        embeddings = model.encode([t.lower() for t in texts], show_progress_bar=True, batch_size=32, normalize_embeddings=True)

        print("\nСоздание индекса")
        quantizer = faiss.IndexFlatIP(EMBEDDING_DIM)
        index = faiss.IndexIVFFlat(quantizer, EMBEDDING_DIM, N_LIST, faiss.METRIC_INNER_PRODUCT)

        print("Тренинг")
        index.train(embeddings)

        print("Добавляем векторы...")
        index.add(embeddings)
        faiss.write_index(index, faiss_index_path)

        print("\nОбработка чанков для подсветки")
        all_chunks = []
        chunk_vectors = []
        metadata = []

        for record in records:
            chunks = split_into_chunks(record["content"])
            chunk_embeds = model.encode(chunks, batch_size=16, normalize_embeddings=True)

            metadata.append({
                "telegram_id": record["telegram_id"],
                "date": record["date"],
                "content": record["content"],
                "author": record["author"],
                "media_path": record['media_path'],
                "chunks": chunks
            })

            all_chunks.append(chunks)
            chunk_vectors.append(chunk_embeds)

        with open(faiss_metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        np.save(faiss_chunk_vectors_path, np.array(chunk_vectors, dtype=object))

        print(f"\nНовый индекс создан. Всего записей: {len(records)}, чанков сохранено: {sum(len(c) for c in all_chunks)}")