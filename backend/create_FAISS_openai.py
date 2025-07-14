import os
import json
import re
import faiss
import numpy as np
from typing import List, Dict

from utils.ij_remover import remove_interjections
import openai
from configs.cfg import (
    N_LIST, relevant_text_path, faiss_openai_model,
    faiss_index_path, faiss_metadata_path, faiss_chunk_vectors_path, EMBEDDING_DIM_OPENAI
)

from configs.cfg import openai_api_key
import time


openai.api_key = openai_api_key


def get_openai_embeddings(texts: list[str], model: str = faiss_openai_model, batch_size: int = 1000) -> np.ndarray:
    embeddings = []
    total = len(texts)
    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        print(f"[OpenAI] Обработка батча {i}–{i + len(batch)} из {total}")
        try:
            response = openai.Embedding.create(input=batch, model=model)
            batch_embeddings = [item["embedding"] for item in sorted(response["data"], key=lambda x: x["index"])]
            embeddings.extend(batch_embeddings)
        except Exception as e:
            print(f"[OpenAI] Ошибка на батче {i}–{i + len(batch)}: {e}")
            embeddings.extend([[0.0] * EMBEDDING_DIM_OPENAI] * len(batch))
            time.sleep(1)
    return np.array(embeddings, dtype="float32")


def flatten_json(json_data: Dict) -> List[Dict]:
    return [
        {
            "telegram_id": item["downloaded_text"][0],
            "date": item["downloaded_text"][1],
            "content": item["downloaded_text"][2],
            "author": item["downloaded_text"][3],
            "media_path": item["downloaded_media"]["path"]
        }
        for items in json_data.values() for item in items
        if item["downloaded_text"][2]
    ]


def split_author_chunks(text: str) -> List[str]:
    tokens = text.split()
    return remove_interjections([' '.join(tokens[i:i + 1]) for i in range(len(tokens))]) + \
           [' '.join(tokens[i:i + 2]) for i in range(len(tokens) - 1)]


def split_content_chunks(text: str) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    tokens = text.split()
    return (
        sentences +
        remove_interjections([' '.join(tokens[i:i + 1]) for i in range(len(tokens))]) +
        [' '.join(tokens[i:i + 2]) for i in range(len(tokens) - 1)] +
        [' '.join(tokens[i:i + 3]) for i in range(len(tokens) - 2)]
    )


def prepare_index(dim: int) -> faiss.IndexIVFFlat:
    quantizer = faiss.IndexFlatIP(dim)
    return faiss.IndexIVFFlat(quantizer, dim, N_LIST, faiss.METRIC_INNER_PRODUCT)


def save_chunk_vectors(path: str, new_data: List[np.ndarray]):
    if os.path.exists(path):
        existing = np.load(path, allow_pickle=True)
        updated = np.concatenate([existing, np.array(new_data, dtype=object)])
    else:
        updated = np.array(new_data, dtype=object)
    np.save(path, updated)


def process_index(index_path: str, meta_path: str, vectors_path: str, records: List[Dict]):
    if os.path.exists(index_path) and os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            existing_meta = json.load(f)
        known_ids = {entry["telegram_id"] for entry in existing_meta}
        records = [r for r in records if r["telegram_id"] not in known_ids]
        if not records:
            print(f"[FAISS] Новых записей нет.")
            return
        index = faiss.read_index(index_path)
    else:
        index = None
        existing_meta = []

    all_chunks, chunk_meta = [], []
    for rec in records:
        a_chunks = split_author_chunks(f"{rec['author']}")
        c_chunks = split_content_chunks(f"{rec['content']}")
        chunks = a_chunks + c_chunks
        for ch in chunks:
            all_chunks.append(ch)
            chunk_meta.append({**rec, "chunk": ch})

    print(f"[FAISS] Эмбеддинг {len(all_chunks)} чанков.")
    embs = get_openai_embeddings(all_chunks)

    if index is None:
        index = prepare_index(EMBEDDING_DIM_OPENAI)
        print(f"[FAISS] Тренировка индекса.")
        index.train(embs)

    index.add(embs)
    faiss.write_index(index, index_path)

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(existing_meta + chunk_meta, f, ensure_ascii=False, indent=2)

    grouped, temp_vecs, current_id = [], [], None
    for meta, vec in zip(chunk_meta, embs):
        tid = meta["telegram_id"]
        if tid != current_id:
            if temp_vecs:
                grouped.append(np.array(temp_vecs))
            temp_vecs = []
            current_id = tid
        temp_vecs.append(vec)
    if temp_vecs:
        grouped.append(np.array(temp_vecs))

    save_chunk_vectors(vectors_path, grouped)
    print(f"[FAISS] Обработано {len(records)} записей, {len(all_chunks)} чанков.")


def build_or_update_index():
    with open(os.path.join(relevant_text_path, "cv.json"), encoding="utf-8") as f:
        data = json.load(f)

    print("\n[FAISS] Извлечение записей...")
    records = flatten_json(data)
    print(f"[FAISS] Найдено {len(records)} записей.")
    process_index(faiss_index_path, faiss_metadata_path, faiss_chunk_vectors_path, records)