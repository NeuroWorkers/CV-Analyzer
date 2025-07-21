import os
import json
import asyncio
import re
from typing import List, Dict, Any

from configs.cfg import relevant_text_path
from utils.togetherai_request import chat_completion_togetherai
from utils.logger import setup_logger

logger = setup_logger("LLM")

async_count_1 = 0
async_count_2 = 0


async def semantic_search_with_llm(query: str, json_path: str, *, model: str, temperature: float = 0.0,
                                   max_concurrent: int = 10, snippet_len: int = 2048) -> List[Dict[str, Any]]:
    """
    Семантический + полнотекстовый поиск по content/author.

    Возвращает список словарей:
    [{"telegram_id": int, "highlight": str}, ...]
    Только релевантные.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data: Dict[str, List[Dict[str, Any]]] = json.load(f)

    semaphore = asyncio.Semaphore(max_concurrent)
    relevant_results: List[Dict[str, Any]] = []

    async def inspect_batch(batch: List[Dict[str, Any]]) -> None:
        nonlocal relevant_results
        global async_count_1, async_count_2

        formatted_messages = []
        for i, rec in enumerate(batch):
            author = rec["author"]
            content = rec["content"]
            trimmed = content[:snippet_len]
            formatted_messages.append(
                f"{i + 1}.\nАвтор:\n\"{author}\"\nСообщение:\n\"{trimmed}\"\n"
            )

        batch_prompt = (
                f"Тебе дан запрос пользователя и список сообщений. "
                f"Твоя задача — найти точное вхождение запроса в каждом сообщении. "
                f"Если запрос явно содержится в авторе или тексте — ответь YES: и скопируй точный фрагмент из текста. "
                f"Если совпадений нет — просто ответь NO.\n\n"
                f"Запрос:\n\"{query}\"\n\n"
                f"Сообщения:\n" + "\n\n".join(formatted_messages) + "\n\n"
                                                                    f"Формат ответа:\n"
                                                                    f"1. YES: <цитата из текста или автора>\n"
                                                                    f"2. NO\n"
                                                                    f"3. и т.д."
        )

        messages = [
            {"role": "system",
             "content": "Ты бинарный фильтр. Не даёшь советы, не обсуждаешь. Отвечаешь строго по формату."},
            {"role": "user", "content": batch_prompt},
        ]

        async with semaphore:
            try:
                logger.info(f"Отправка батча #{async_count_1}")
                async_count_1 += 1
                reply = await chat_completion_togetherai(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                )
            except Exception as e:
                logger.warning(f"[LLM Error] batch failed: {e}")
                return

        logger.info(f"Получен ответ на батч #{async_count_2}")
        async_count_2 += 1

        lines = reply.strip().splitlines()
        for line, rec in zip(lines, batch):
            line = line.strip()
            match = re.match(r"^\d+\.\s*(YES|NO)(?::\s*(.*))?$", line, re.IGNORECASE)
            if not match:
                logger.warning(f"[LLM ⚠️ Нестандартный ответ] telegram_id={rec['telegram_id']}, reply={line}")
                continue

            decision = match.group(1).upper()
            detail = match.group(2) or rec["content"][:120]

            if decision == "YES":
                relevant_results.append({
                    "telegram_id": rec["telegram_id"],
                    "highlight": detail.strip()
                })

    tasks: List[asyncio.Task] = []

    current_batch = []
    current_len = 0
    max_batch_chars = snippet_len

    def flush_batch():
        nonlocal current_batch, current_len
        if current_batch:
            tasks.append(asyncio.create_task(inspect_batch(current_batch)))
            current_batch = []
            current_len = 0

    for records in data.values():
        for rec in records:
            text_block = rec.get("downloaded_text", [])
            if len(text_block) >= 4:
                try:
                    telegram_id = int(text_block[0])
                    content = text_block[2]
                    author = text_block[3]

                    est_len = len(content) + len(author)
                    if current_len + est_len > max_batch_chars:
                        flush_batch()

                    current_batch.append({
                        "telegram_id": telegram_id,
                        "content": content,
                        "author": author
                    })
                    current_len += est_len
                except Exception as e:
                    logger.warning(f"[Parse Error] {e}")
                    continue

    flush_batch()
    await asyncio.gather(*tasks, return_exceptions=True)
    return relevant_results


def get_records_by_telegram_ids_from_json(json_path: str, telegram_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Извлекает полные записи из cv.json по списку telegram_id.
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


async def full_pipeline(user_query: str) -> tuple[list[dict[str, Any]], list[Any | None]]:
    json_path = os.path.join(relevant_text_path, "cv.json")

    results = await semantic_search_with_llm(
        query=user_query,
        json_path=json_path,
        model="meta-llama/Llama-3-70b-chat-hf",
        temperature=0.0,
        max_concurrent=40
    )

    telegram_ids = [r["telegram_id"] for r in results]
    logger.info(f"{telegram_ids}")
    highlight_map = {r["telegram_id"]: r["highlight"] for r in results}
    logger.info(f"{highlight_map}")
    full_records = get_records_by_telegram_ids_from_json(json_path, telegram_ids)
    logger.info(f"{full_records}")

    filtered_records = []
    matched_highlights = []

    for rec in full_records:
        highlight = highlight_map.get(rec["telegram_id"])
        if highlight:
            rec["highlight"] = highlight
            filtered_records.append(rec)
            matched_highlights.append(highlight)

    return filtered_records, matched_highlights
