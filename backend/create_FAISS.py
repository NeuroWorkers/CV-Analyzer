import os
import json
import faiss
import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer

from configs.ai_config import MODEL_NAME
from configs.project_paths import relevant_text_path, faiss_index_path, faiss_metadata_path


model = SentenceTransformer(MODEL_NAME)


def extract_texts_and_metadata(json_data: dict) -> Tuple[List[str], List[Dict]]:
    texts = []
    metadata = []

    for entries in json_data.values():
        for entry in entries:
            msg = entry.get("downloaded_text")
            if not msg or len(msg) < 7:
                continue

            text = msg[2]
            if not text:
                continue

            texts.append(text)
            metadata.append({
                "telegram_id": msg[0],
                "created_at": msg[1],
                "content": text,
                "author": msg[3],
                "fwd_date": msg[4],
                "fwd_author": msg[5],
                "topic_id": msg[6]
            })

    return texts, metadata


def build_or_update_index(json_path=os.path.join(relevant_text_path, "cv.json"), index_path=faiss_index_path, metadata_path=faiss_metadata_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts, metadata = extract_texts_and_metadata(data)

    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        print("[FAISS] Индекс не найден — создаём новый.")
        embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)
        faiss.write_index(index, index_path)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"[FAISS] Новый индекс создан. Всего записей: {len(texts)}")
    else:
        print("[FAISS] Индекс найден — обновляем только новыми.")
        with open(metadata_path, "r", encoding="utf-8") as f:
            existing_metadata = json.load(f)
        existing_ids = {entry["telegram_id"] for entry in existing_metadata}

        new_texts = []
        new_metadata = []

        for text, meta in zip(texts, metadata):
            if meta["telegram_id"] not in existing_ids:
                new_texts.append(text)
                new_metadata.append(meta)

        if not new_texts:
            print("[FAISS] Нет новых записей для добавления.")
            return

        embeddings = model.encode(new_texts, show_progress_bar=True, convert_to_numpy=True)
        index = faiss.read_index(index_path)
        index.add(embeddings)
        faiss.write_index(index, index_path)

        existing_metadata.extend(new_metadata)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(existing_metadata, f, ensure_ascii=False, indent=2)

        print(f"[FAISS] Добавлено {len(new_texts)} новых записи(-ей) в индекс.")