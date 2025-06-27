import os
import json
import faiss
import numpy as np
from typing import List, Dict, Tuple
from configs.ai_config import MODEL_NAME
from sentence_transformers import SentenceTransformer
from configs.project_paths import relevant_text_path, faiss_index_path, faiss_metadata_path


model = SentenceTransformer(MODEL_NAME)


def extract_texts_and_metadata(json_data: dict) -> Tuple[List[str], List[Dict]]:
    texts = []
    metadata = []

    for topic_id, entries in json_data.items():
        for entry in entries:
            if "downloaded_text" in entry:
                msg_data = entry["downloaded_text"]
                if len(msg_data) >= 7:
                    text = msg_data[2]
                    if text:
                        texts.append(text)
                        metadata.append({
                            "id": msg_data[0],
                            "created_at": msg_data[1],
                            "text": text,
                            "author": msg_data[3],
                            "fwd_date": msg_data[4],
                            "fwd_author": msg_data[5],
                            "topic_id": msg_data[6]
                        })
    return texts, metadata


def create_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index


def save_index(index: faiss.IndexFlatL2, path: str):
    faiss.write_index(index, path)


def load_index(path: str) -> faiss.IndexFlatL2:
    return faiss.read_index(path)


def save_metadata(metadata: List[Dict], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def load_metadata(path: str) -> List[Dict]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def build_new_index(json_path=os.path.join(relevant_text_path, "cv.json"), index_path=faiss_index_path, metadata_path=faiss_metadata_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts, metadata = extract_texts_and_metadata(data)
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    index = create_faiss_index(embeddings)
    save_index(index, index_path)
    save_metadata(metadata, metadata_path)

    print(f"[FAISS] индекс создан для {len(texts)} записи(-ей).")


def add_to_index(new_json_path, index_path=faiss_index_path, metadata_path=faiss_metadata_path):
    with open(new_json_path, "r", encoding="utf-8") as f:
        new_data = json.load(f)

    texts, new_metadata = extract_texts_and_metadata(new_data)
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    index = load_index(index_path)
    index.add(embeddings)
    save_index(index, index_path)

    metadata = load_metadata(metadata_path)
    metadata.extend(new_metadata)
    save_metadata(metadata, metadata_path)

    print(f"[FAISS] {len(texts)} записи(-ей) добавлено в индекс.")
