import edgedb
import asyncio

from typing import Any
from langchain.docstore.document import Document
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer


model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
client = edgedb.create_async_client("database")


async def fetch_all_messages():
    return await client.query("""
        SELECT ResumeMessage {
            id,
            content,
            author,
            created_at,
            media_path
        }
    """)


class SentenceTransformerEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return model.encode(texts, convert_to_numpy=True).tolist()

    def embed_query(self, text):
        return model.encode([text], convert_to_numpy=True)[0].tolist()


async def main_search(user_query):
    messages = await fetch_all_messages()

    docs = [
        Document(page_content=m.content, metadata={
            "author": m.author,
            "created_at": m.created_at.isoformat()
        })
        for m in messages
    ]

    embeddings = SentenceTransformerEmbeddings()

    faiss_index = FAISS.from_documents(docs, embeddings)

    relevant = faiss_index.similarity_search(user_query, k=5)

    output = []
    for doc in relevant:
        output.append({
            "content": doc.page_content,
            "author": doc.metadata.get("author"),
            "created_at": doc.metadata.get("created_at"),
            "media_path": doc.metadata.get("media_path")
        })

    return output


async def question_analyzer(query: str) -> list[dict[str, str | None | Any]]:
    results = await main_search(query)
    for r in results:
        print(f"{r['created_at']} - {r['author']}: {r['content']}")

    return results

