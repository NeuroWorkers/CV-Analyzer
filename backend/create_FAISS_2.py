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
    faiss_chunk_vectors_path,
    faiss_author_index_path,
    faiss_author_metadata_path,
    faiss_author_vectors_path,
    N_LIST,
    EMBEDDING_DIM
)

model = None
author_model = None


def init_resources():
    global model, author_model
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    if device == "cpu":
        faiss.omp_set_num_threads(os.cpu_count())

    model = SentenceTransformer(faiss_model, device=device)
    author_model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased-v1", device=device)


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
    return text.split('.')  # Разделение по предложениям


def build_or_update_index():
    with open(os.path.join(relevant_text_path, "cv.json"), "r", encoding="utf-8") as f:
        json_data = json.load(f)

    print("\nИзвлечение данных")
    records = flatten_json_data(json_data)
    print(f"Найдено {len(records)} записей.")

    texts = [r["content"] for r in records]
    print(f"Создаем эмбеддинги для {len(texts)} записей.")
    embeddings = model.encode([t.lower() for t in texts], show_progress_bar=True, batch_size=32,
                              normalize_embeddings=True)

    print("\nСоздание индекса по контенту")
    quantizer = faiss.IndexFlatIP(EMBEDDING_DIM)
    index = faiss.IndexIVFFlat(quantizer, EMBEDDING_DIM, N_LIST, faiss.METRIC_INNER_PRODUCT)
    index.train(embeddings)
    index.add(embeddings)
    faiss.write_index(index, faiss_index_path)

    print("\nОбработка чанков для подсветки")
    all_chunks = []
    chunk_vectors = []
    content_metadata = []

    for record in records:
        chunks = split_into_chunks(record["content"])
        chunk_embeds = model.encode(chunks, batch_size=16, normalize_embeddings=True)

        content_metadata.append({
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
        json.dump(content_metadata, f, ensure_ascii=False, indent=2)
    np.save(faiss_chunk_vectors_path, np.array(chunk_vectors, dtype=object))

    print(
        f"\nНовый индекс по контенту создан. Всего записей: {len(records)}, чанков сохранено: {sum(len(c) for c in all_chunks)}")

    # === Авторский индекс ===
    authors = list({r["author"] for r in records if r["author"]})
    print(f"\nСоздание эмбеддингов для {len(authors)} авторов")
    author_vectors = author_model.encode(authors, show_progress_bar=True, batch_size=16, normalize_embeddings=True)

    print("Создание авторского индекса")
    author_quantizer = faiss.IndexFlatIP(EMBEDDING_DIM)
    author_index = faiss.IndexIVFFlat(author_quantizer, EMBEDDING_DIM, N_LIST, faiss.METRIC_INNER_PRODUCT)
    author_index.train(author_vectors)
    author_index.add(author_vectors)
    faiss.write_index(author_index, faiss_author_index_path)

    with open(faiss_author_metadata_path, "w", encoding="utf-8") as f:
        json.dump(authors, f, ensure_ascii=False, indent=2)
    np.save(faiss_author_vectors_path, author_vectors)

    print(f"Авторский индекс создан: {len(authors)} авторов закодировано")


if __name__ == "__main__":
    init_resources()
    build_or_update_index()
