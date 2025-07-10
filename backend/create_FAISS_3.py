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
    N_LIST,
    EMBEDDING_DIM,
    faiss_chunk_vectors_path
)

model = None
index = None
metadata = None


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

def split_into_faiss_chunks(text: str) -> List[str]:
    texts = text.split(".")
    texts = texts + text.split()
    return texts


def build_or_update_index():
    with open(os.path.join(relevant_text_path, "cv.json"), "r", encoding="utf-8") as f:
        json_data = json.load(f)

    print("\nИзвлечение данных")
    records = flatten_json_data(json_data)
    print(f"Найдено {len(records)} записей.")

    if os.path.exists(faiss_index_path) and os.path.exists(faiss_metadata_path):
        #print("[FAISS] Индекс найден — обновляем только новыми.EXIT")
        print("[FAISS] Индекс найден — EXIT")
        exit()
    else:
        print("[FAISS] Индекс не найден — создаём новый.")
        texts = [r["content"] for r in records]
        
        # доп для каждого content
        text2=[]
        index_n_faiss={}
        ind_main=0
        for ind, t in enumerate(texts):
            print (f"I - {ind} ind_main={ind_main}")
            a=split_into_faiss_chunks(t)
            for ind2, t2 in enumerate(a):
                index_n_faiss[ind_main]=ind
                ind_main=ind_main+1
            print(f"    append {len(a)} faiss chunks")
            text2=text2+a
            pass
        #faiss_metadata_path
        with open("data/FAISS/index_n_faiss.json", "w", encoding="utf-8") as f:
            json.dump(index_n_faiss, f, ensure_ascii=False, indent=2)
        texts=text2
        #import pickle
        #with open("data/FAISS/texts.pkl", "wb") as f:
        #    pickle.dump(texts,f)
        #print (texts)
        with open("data/FAISS/texts.json", "w", encoding="utf-8") as f:
            json.dump(texts, f, ensure_ascii=False, indent=2)
        #exit()

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