import json
import os
import re
import time
from typing import Dict, List

import faiss
import numpy as np
import openai
import torch
from sentence_transformers import SentenceTransformer

from configs.cfg import N_LIST, EMBEDDING_MODE, embedding_model, embedding_dim, index_path, metadata_path, chunk_path, \
    relevant_text_path
from utils.ij_remover import remove_interjections

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

    model = SentenceTransformer(embedding_model, device=device)


def get_openai_embeddings(texts: list[str], emb_model: str = embedding_model, batch_size: int = 1000) -> np.ndarray:
    embeddings = []
    total = len(texts)
    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        print(f"[OpenAI] Обработка батча {i}–{i + len(batch)} из {total}")
        try:
            response = openai.Embedding.create(input=batch, model=emb_model)
            batch_embeddings = [item["embedding"] for item in sorted(response["data"], key=lambda x: x["index"])]
            embeddings.extend(batch_embeddings)
        except Exception as e:
            print(f"[OpenAI] Ошибка на батче {i}–{i + len(batch)}: {e}")
            embeddings.extend([[0.0] * embedding_dim] * len(batch))
            time.sleep(1)
    return np.array(embeddings, dtype="float32")


def flatten_json(json_data: Dict) -> List[Dict]:
    return [
        {
            "telegram_id": item["downloaded_text"][0],
            "date": item["downloaded_text"][1],
            "content": item["downloaded_text"][2],
            "author": item["downloaded_text"][3],
            "media_path": item["downloaded_media"]["path"],
            "c_translated": item["c_translated"]
        }
        for items in json_data.values() for item in items
        if item["downloaded_text"][2]
    ]


def split_author_chunks(text: str) -> List[str]:
    tokens = text.split()
    return remove_interjections([' '.join(tokens[i:i + 1]) for i in range(len(tokens))]) + \
        [' '.join(tokens[i:i + 2]) for i in range(len(tokens) - 1)]


def clean_formatting(text: str) -> str:
    """
    Удаляет markdown-форматирование из текста.
    Убирает парные и одиночные теги: **, *, __, _, ~~, ``, и т.д.
    """
    if not text:
        return text

    # Удаляем парные теги (жирный, курсив, зачеркнутый, код)
    patterns = [
        r'\*\*(.*?)\*\*',  # **bold**
        r'__(.*?)__',  # __bold__
        r'\*(.*?)\*',  # *italic*
        r'_(.*?)_',  # _italic_
        r'~~(.*?)~~',  # ~~strikethrough~~
        r'`(.*?)`',  # `code`
        r'```(.*?)```',  # ```code block```
    ]

    for pattern in patterns:
        text = re.sub(pattern, r'\1', text, flags=re.DOTALL)

    # Удаляем одиночные форматирующие символы в начале и конце
    single_patterns = [
        r'^(\*\*|\*|__|_|~~|`)(.*)$',  # начинающиеся с форматирования
        r'^(.*?)(\*\*|\*|__|_|~~|`)$',  # заканчивающиеся форматированием
    ]

    for pattern in single_patterns:
        match = re.match(pattern, text.strip())
        if match:
            if pattern.startswith('^(\\*\\*'):  # начинающиеся
                text = match.group(2).strip()
            else:  # заканчивающиеся
                text = match.group(1).strip()

    # Удаляем множественные пробелы
    text = re.sub(r'\s+', ' ', text).strip()

    return text


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
        # no split_engcontent_chunks(), same function
        d_chunks = []
        if 'c_translated' in rec and rec['c_translated']:
            d_chunks = split_content_chunks(f"{rec['c_translated']}")
        else:
            print("No translation")
        chunks = a_chunks + c_chunks + d_chunks
        for ch in chunks:
            cleaned_chunk = clean_formatting(ch)
            if cleaned_chunk:  # добавляем только непустые чанки
                all_chunks.append(cleaned_chunk)
                chunk_meta.append({**rec, "chunk": cleaned_chunk})

    print(f"[FAISS] Эмбеддинг {len(all_chunks)} чанков.")

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(existing_meta + chunk_meta, f, ensure_ascii=False, indent=2)

    embs = None
    if EMBEDDING_MODE == "sentence_transformers":
        init_resources()
        embs = model.encode(all_chunks, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    else:
        if EMBEDDING_MODE == "openai":
            embs = get_openai_embeddings(all_chunks)
        else:
            raise ValueError("ОШИБКА ПОЛУЧЕНИЯ ЕБМЕДДИНГОВ")

    if index is None:
        index = prepare_index(embedding_dim)
        print(f"[FAISS] Тренировка индекса.")
        index.train(embs)

    index.add(embs)
    faiss.write_index(index, index_path)

    # with open(meta_path, "w", encoding="utf-8") as f:
    #    json.dump(existing_meta + chunk_meta, f, ensure_ascii=False, indent=2)

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

    process_index(index_path, metadata_path, chunk_path, records)
