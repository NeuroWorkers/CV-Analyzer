import os
import json
import re
import pickle
from typing import List, Dict, Tuple
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
import openai
from configs.cfg import relevant_text_path, openai_api_key

openai.api_key = openai_api_key

EMB_MODEL = "text-embedding-3-small"
EMB_DIM = 1536
HNSW_M = 32
HNSW_EF_SEARCH = 64
ALPHA = 0.95
SEMANTIC_THRESHOLD = 0.78
TOP_K = 100
CACHE_DIR = os.path.join(relevant_text_path, "_hybrid_cache")

os.makedirs(CACHE_DIR, exist_ok=True)
FAISS_PATH = os.path.join(CACHE_DIR, "faiss.index")
EMB_PATH = os.path.join(CACHE_DIR, "embeddings.npy")
BM25_PATH = os.path.join(CACHE_DIR, "bm25.pkl")
REC_PATH = os.path.join(CACHE_DIR, "records.pkl")

CHUNK_SIZE = 300
CHUNK_OVERLAP = 50


def chunk_text(text: str, author: str, uid: str) -> List[Dict]:
    words = text.split()
    return [
        {"telegram_id": uid, "text": f"{author}\n{' '.join(words[i:i + CHUNK_SIZE])}", "author": author}
        for i in range(0, len(words), CHUNK_SIZE - CHUNK_OVERLAP)
    ]


def load_records() -> List[Dict]:
    if os.path.exists(REC_PATH):
        with open(REC_PATH, "rb") as f:
            return pickle.load(f)

    with open(os.path.join(relevant_text_path, "cv.json"), encoding="utf-8") as f:
        raw_data = json.load(f)

    records = []
    for _, entries in raw_data.items():
        for entry in entries:
            t = entry["downloaded_text"]
            uid, content, author = t[0], t[2], t[3]
            records.extend(chunk_text(content, author, uid))

    with open(REC_PATH, "wb") as f:
        pickle.dump(records, f)
    return records


def build_embeddings(texts: List[str]) -> np.ndarray:
    BATCH = 512
    out = []
    for i in range(0, len(texts), BATCH):
        batch = texts[i:i + BATCH]
        resp = openai.Embedding.create(model=EMB_MODEL, input=batch)
        vecs = [d["embedding"] for d in sorted(resp["data"], key=lambda x: x["index"])]
        out.extend(vecs)
    vecs_np = np.array(out, dtype=np.float32)
    np.save(EMB_PATH, vecs_np)
    return vecs_np


def get_embeddings(texts: List[str]) -> np.ndarray:
    if os.path.exists(EMB_PATH):
        return np.load(EMB_PATH)
    return build_embeddings(texts)


def build_faiss(vecs: np.ndarray) -> faiss.Index:
    faiss.normalize_L2(vecs)
    index = faiss.IndexHNSWFlat(EMB_DIM, HNSW_M, faiss.METRIC_INNER_PRODUCT)
    index.hnsw.efSearch = HNSW_EF_SEARCH
    index.add(vecs)
    faiss.write_index(index, FAISS_PATH)
    return index


def get_faiss(vecs: np.ndarray) -> faiss.Index:
    if os.path.exists(FAISS_PATH):
        idx = faiss.read_index(FAISS_PATH)
        idx.hnsw.efSearch = HNSW_EF_SEARCH
        return idx
    return build_faiss(vecs)


def build_bm25(texts: List[str]) -> BM25Okapi:
    tokenized = [re.findall(r"\w+", t.lower()) for t in texts]
    bm25 = BM25Okapi(tokenized)
    with open(BM25_PATH, "wb") as f:
        pickle.dump(bm25, f)
    return bm25


def get_bm25(texts: List[str]) -> BM25Okapi:
    if os.path.exists(BM25_PATH):
        with open(BM25_PATH, "rb") as f:
            return pickle.load(f)
    return build_bm25(texts)


async def embed_query(query: str) -> np.ndarray:
    resp = openai.Embedding.create(model=EMB_MODEL, input=[query])
    vec = np.array(resp["data"][0]["embedding"], dtype="float32").reshape(1, -1)
    faiss.normalize_L2(vec)
    return vec


def bm25_rank(query: str, k: int) -> Tuple[np.ndarray, np.ndarray]:
    tokens = re.findall(r"\w+", query.lower())
    scores = bm25.get_scores(tokens)
    idx = np.argsort(scores)[::-1][:k]
    return idx, scores[idx]


def is_acronym_or_short_query(query: str) -> bool:
    query = query.strip()
    if len(query.split()) == 1:
        if re.fullmatch(r"[A-ZА-Я]{2,}", query):
            return True
        if len(query) < 5:
            return True
    return False


async def hybrid_search(query: str, top_k: int = TOP_K, alpha: float = ALPHA) -> List[Dict]:
    use_bm25_boost = is_acronym_or_short_query(query)

    q_vec = await embed_query(query)
    sim, idx_f = index.search(q_vec, top_k)
    sim = sim.flatten()
    idx_f = idx_f.flatten()

    idx_b, bm25_scores = bm25_rank(query, top_k)

    hybrid_scores = {}
    for i, s in zip(idx_f, sim):
        weight = alpha * (s if s >= SEMANTIC_THRESHOLD else s * 0.25)
        hybrid_scores[int(i)] = hybrid_scores.get(int(i), 0) + weight

    for i, s in zip(idx_b, bm25_scores):
        if use_bm25_boost or hybrid_scores.get(int(i), 0) >= SEMANTIC_THRESHOLD * alpha:
            boost = (1 - alpha) * s if not use_bm25_boost else s  # полный вес для коротких/аббревиатур
            hybrid_scores[int(i)] = hybrid_scores.get(int(i), 0) + boost

    ranked = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [records[i] for i, _ in ranked]


print("[Init] Загружаем данные")
records = load_records()
texts = [r["text"] for r in records]
embeddings = get_embeddings(texts)
index = get_faiss(embeddings)
bm25 = get_bm25(texts)
print("[Init] Готово")
