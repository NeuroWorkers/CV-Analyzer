import os
import json
import re
import faiss
import torch
import numpy as np
from typing import List, Dict
from sentence_transformers import SentenceTransformer

from configs.cfg import (
    N_LIST, faiss_model, relevant_text_path,
    faiss_index_path, faiss_metadata_path, faiss_chunk_vectors_path
)

model = None


def init_resources():
    """
    Инициализирует модель SentenceTransformer и настраивает FAISS для многопоточности.
    Использует 'mps' на Mac, если доступно, иначе 'cpu'.
    """
    global model
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    if device == "cpu":
        faiss.omp_set_num_threads(os.cpu_count())
    model = SentenceTransformer(faiss_model, device=device)


def flatten_json(json_data: Dict) -> List[Dict]:
    """
    Преобразует вложенный JSON с резюме в плоский список словарей с данными.

    Args:
        json_data (Dict): Вложенный словарь с исходными данными.

    Returns:
        List[Dict]: Список словарей с полями telegram_id, date, content, author и media_path.
    """
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


def split_chunks(text: str) -> List[str]:
    """
    Разбивает текст на предложения, а также извлекает униграммы, биграммы и триграммы.

    Args:
        text (str): Исходный текст.

    Returns:
        List[str]: Список чанков — предложений и n-грамм (n=1,2,3).
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    tokens = text.split()
    return (
        sentences +
        [' '.join(tokens[i:i + 1]) for i in range(len(tokens))] +
        [' '.join(tokens[i:i + 2]) for i in range(len(tokens) - 1)] +
        [' '.join(tokens[i:i + 3]) for i in range(len(tokens) - 2)]
    )


def prepare_index(path: str, dim: int) -> faiss.IndexIVFFlat:
    """
    Создаёт новый FAISS индекс с заданной размерностью.

    Args:
        path (str): Путь к файлу индекса.
        dim (int): Размерность эмбеддингов.

    Returns:
        faiss.IndexIVFFlat: Новый индекс FAISS.
    """
    quantizer = faiss.IndexFlatIP(dim)
    index = faiss.IndexIVFFlat(quantizer, dim, N_LIST, faiss.METRIC_INNER_PRODUCT)
    return index


def save_chunk_vectors(path: str, new_data: List[np.ndarray]):
    """
    Сохраняет эмбеддинги чанков в .npy-файл, добавляя их к существующим (если есть).

    Args:
        path (str): Путь к файлу с эмбеддингами.
        new_data (List[np.ndarray]): Список массивов эмбеддингов для каждого документа.
    """
    if os.path.exists(path):
        existing = np.load(path, allow_pickle=True)
        updated = np.concatenate([existing, np.array(new_data, dtype=object)])
    else:
        updated = np.array(new_data, dtype=object)
    np.save(path, updated)


def process_index(index_path: str, meta_path: str, vectors_path: str, records: List[Dict]):
    """
    Создаёт или обновляет индекс и метаданные для заданного поля ('author' или 'content').

    Args:
        index_path (str): Путь к файлу FAISS индекса.
        meta_path (str): Путь к JSON-файлу с метаданными.
        vectors_path (str): Путь к файлу с эмбеддингами чанков.
        records (List[Dict]): Список всех записей.
    """
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
        chunks = split_chunks(f"{rec['author']}. {rec['content']}")
        for ch in chunks:
            all_chunks.append(ch)
            chunk_meta.append({**rec, "chunk": ch})

    print(f"[FAISS] Эмбеддинг {len(all_chunks)} чанков.")
    embs = model.encode(all_chunks, batch_size=32, show_progress_bar=True, normalize_embeddings=True)

    if index is None:
        dim = model.get_sentence_embedding_dimension()
        index = prepare_index(index_path, dim)
        print(f"[FAISS: Тренировка индекса.")
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
    """
    Загружает JSON с данными, извлекает записи и вызывает процессинг индексов
    для полей 'author' и 'content', создавая или обновляя FAISS индексы и метаданные.
    """
    with open(os.path.join(relevant_text_path, "cv.json"), encoding="utf-8") as f:
        data = json.load(f)

    print("\n[FAISS] Извлечение записей...")
    records = flatten_json(data)
    print(f"[FAISS] Найдено {len(records)} записей.")

    process_index(faiss_index_path, faiss_metadata_path, faiss_chunk_vectors_path, records)
