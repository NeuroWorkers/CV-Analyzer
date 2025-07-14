import json
import asyncio
import os
from typing import List, Dict, Any

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


def batchify_by_token_estimate(data: List[Dict], max_chars: int = 6000) -> List[List[Dict]]:
    """
    Разбивает список записей на батчи, ограниченные по символам (примерно как токены).
    Это позволяет сделать батчи примерно равномерными по нагрузке.
    """
    batches = []
    current_batch = []
    current_len = 0

    for entry in data:
        entry_len = len(entry["content"]) + len(entry["author"]) + 50
        if current_len + entry_len > max_chars and current_batch:
            batches.append(current_batch)
            current_batch = [entry]
            current_len = entry_len
        else:
            current_batch.append(entry)
            current_len += entry_len

    if current_batch:
        batches.append(current_batch)

    return batches


def clean_json_response(text: str) -> str:
    if text.startswith("```json"):
        text = text.strip()[7:]
    if text.endswith("```"):
        text = text.strip()[:-3]
    return text.strip()


async def process_batch_highlight(batch: List[Dict[str, str]], user_query: str, model: str) -> List[Dict[str, str]]:
    content_block = "\n".join(
        [f"{i+1}. telegram_id: {entry['telegram_id']}\nАвтор: {entry['author']}\nКонтент: {entry['content']}" for i, entry in enumerate(batch)]
    )

    messages = [
        {
            "role": "system",
            "content": (
                "Ты эксперт, который помогает находить только строго релевантные записи по смыслу. "
                "Пользователь прислал список (telegram_id, author, content) и свой запрос. "
                "Твоя задача — выбрать ТОЛЬКО те записи, которые:\n"
                "1. Содержат явное совпадение по ключевым словам ИЛИ\n"
                "2. Тесно связаны по смыслу и тематике с вопросом.\n\n"
                "Не добавляй записи, которые слабо связаны или просто поверхностно упоминают тему.\n"
                "Выводи только точные совпадения. Ответ — JSON-массив с telegram_id и highlight."
            )
        },
        {
            "role": "user",
            "content": (
                f"Вопрос пользователя: {user_query}\n\n"
                f"Список записей:\n{content_block}\n\n"
                f"Ответь JSON-массивом релевантных записей: telegram_id и highlight."
            )
        }
    ]

    try:
        response = await chat_completion_openrouter(messages, model=model)
        clean = clean_json_response(response)
        relevant = json.loads(clean)
        return relevant if isinstance(relevant, list) else []
    except Exception as e:
        print(f"[Ошибка в батче] {e}")
        return []


async def find_relevant_telegram_ids_with_highlights(
    json_path: str,
    user_query: str,
    model: str = "openai/gpt-4",
    max_chars_per_batch: int = 6000,
    max_batches: int = 70
) -> List[Dict[str, str]]:
    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    all_entries = []
    for group in raw.values():
        for item in group:
            try:
                fields = item["downloaded_text"]
                telegram_id = fields[0]
                timestamp = fields[1]
                content = fields[2]
                author = fields[3]

                all_entries.append({
                    "telegram_id": telegram_id,
                    "author": author,
                    "content": content,
                    "date": timestamp
                })
            except Exception as e:
                print(f"[Парсинг] Ошибка: {e}")

    print(f"Всего записей: {len(all_entries)}")

    batches = batchify_by_token_estimate(all_entries, max_chars=max_chars_per_batch)
    if max_batches:
        batches = batches[:max_batches]

    tasks = [process_batch_highlight(batch, user_query, model) for batch in batches]
    results = await asyncio.gather(*tasks)

    relevant = []
    for r in results:
        relevant.extend(r)

    return relevant


def get_records_by_telegram_ids_from_json(
    json_path: str,
    telegram_ids: List[int]
) -> List[Dict[str, Any]]:
    """
    Извлекает полные записи из cv.json по списку telegram_id.

    Args:
        json_path (str): Путь к файлу cv.json.
        telegram_ids (List[int]): Список целевых telegram_id.

    Returns:
        List[Dict[str, Any]]: Список словарей с полными данными.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    result = []
    telegram_ids_set = set(telegram_ids)

    for group in raw.values():
        for item in group:
            try:
                fields = item["downloaded_text"]
                tg_id = fields[0]
                timestamp = fields[1]
                content = fields[2]
                author = fields[3]
                media_path = item.get("downloaded_media", {}).get("path", None)

                if tg_id in telegram_ids_set:
                    result.append({
                        "telegram_id": tg_id,
                        "author": author,
                        "content": content,
                        "date": timestamp,
                        "media_path": media_path
                    })
            except Exception as e:
                print(f"[Ошибка при извлечении записи] {e}")

    return result


async def full_pipeline(user_query: str):
    json_path = os.path.join(relevant_text_path, "cv.json")
    relevant = await find_relevant_telegram_ids_with_highlights(json_path=json_path, user_query=user_query)

    ids = [r["telegram_id"] for r in relevant]

    full_records = get_records_by_telegram_ids_from_json(json_path, ids)

    highlight_map = {r["telegram_id"]: r["highlight"] for r in relevant}

    for rec in full_records:
        rec["highlight"] = highlight_map.get(rec["telegram_id"])

    return full_records, highlight_map
