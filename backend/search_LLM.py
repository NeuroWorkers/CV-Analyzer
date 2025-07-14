import json
import asyncio
import os
from typing import List, Dict, Any

from datetime import datetime

import edgedb

from utils.openrouter_request import chat_completion_openrouter

from configs.cfg import relevant_text_path, db_conn_name

client = edgedb.create_async_client(db_conn_name)


async def fetch_all_messages() -> List[dict[str, Any]]:
    """
    Загружает все сообщения с резюме из базы данных EdgeDB.

    Returns:
        List[dict[str, Any]]: Список словарей с полями резюме:
            'telegram_id' (int),
            'content' (str),
            'author' (str),
            'created_at' (datetime),
            'media_path' (str|None).
    """
    return await client.query("""
        SELECT ResumeMessage {
            telegram_id,
            content,
            author,
            created_at,
            media_path
        }
    """)


def batchify(data: List[Dict], batch_size: int) -> List[List[Dict]]:
    return [data[i:i + batch_size] for i in range(0, len(data), batch_size)]


def clean_json_response(text: str) -> str:
    """
    Убирает Markdown-обёртку ```json ... ``` из ответа модели.
    """
    if text.startswith("```json"):
        text = text.strip()[7:]
    if text.endswith("```"):
        text = text.strip()[:-3]
    return text.strip()


async def process_batch(batch: List[Dict[str, str]], user_query: str, model: str) -> List[Dict[str, str]]:
    content_block = "\n".join(
        [f"{i + 1}. Автор: {entry['author']}\n   Контент: {entry['content']}" for i, entry in enumerate(batch)]
    )

    messages = [
        {
            "role": "system",
            "content": (
                "Ты помощник, который помогает находить релевантные записи по запросу пользователя. "
                "Пользователь предоставил вопрос и список записей. Выбери и выведи только те записи, которые наиболее соответствуют вопросу. "
                "Ответ должен быть в JSON-массиве, где каждая запись имеет поля 'author' и 'content'."
            )
        },
        {
            "role": "user",
            "content": (
                f"Вопрос пользователя: {user_query}\n\n"
                f"Список записей:\n{content_block}\n\n"
                f"Ответи JSON-массивом релевантных записей."
            )
        }
    ]

    try:
        response = await chat_completion_openrouter(messages, model=model)
        clean = clean_json_response(response)
        relevant = json.loads(clean)
        return relevant if isinstance(relevant, list) else []
    except Exception as e:
        print(e)


async def find_relevant_records_parallel_for_ui(user_query: str, model: str = "google/gemini-2.5-flash", batch_size: int = 10, max_batches: int = 20) -> List[Dict[str, str]]:
    json_path = os.path.join(relevant_text_path, "cv.json")
    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    all_entries = []
    for group in raw.values():
        for item in group:
            try:
                text_fields = item["downloaded_text"]
                content = text_fields[2]
                author = text_fields[3]
                timestamp = text_fields[1]
                media_path = item.get("downloaded_media", {}).get("path", None)

                all_entries.append({
                    "author": author,
                    "content": content,
                    "date": timestamp,
                    "media_path": media_path
                })
            except Exception as e:
                print(f"Ошибка при парсинге: {e}")

    print(f"Всего подходящих записей: {len(all_entries)}")

    entries_for_llm = [{"author": e["author"], "content": e["content"]} for e in all_entries]
    batches = batchify(entries_for_llm, batch_size)
    if max_batches:
        batches = batches[:max_batches]

    tasks = [process_batch(batch, user_query, model) for batch in batches]
    results = await asyncio.gather(*tasks)

    relevant = []
    for r in results:
        relevant.extend(r)

    entry_lookup = {
        (entry["author"], entry["content"]): entry
        for entry in all_entries
    }

    final_results = []
    for match in relevant:
        entry = entry_lookup.get((match["author"], match["content"]))
        if not entry:
            continue

        photo_url = (
            f"/media/{os.path.basename(entry['media_path'])}"
            if entry["media_path"] and os.path.exists(
                os.path.join("relevant", "media", os.path.basename(entry["media_path"])))
            else None
        )

        final_results.append({
            "author": entry["author"],
            "date": datetime.fromisoformat(entry["date"]).isoformat() if entry["date"] else None,
            "content": entry["content"],
            "media_path": photo_url
        })

    return final_results


async def main():
    query = "Найди записи, где авторы пишут про работу с большими языковыми моделями"

    results = await find_relevant_records_parallel_for_ui(query, batch_size=30, max_batches=30)
    for r in results:
        print(r)
