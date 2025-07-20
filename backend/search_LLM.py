import os

from configs.cfg import relevant_text_path

import json
import asyncio
from typing import List, Dict, Any

from utils.togetherai_request import chat_completion_togetherai
from utils.logger import setup_logger

logger = setup_logger("LLM")

async_count_1 = 0
async_count_2 = 0


async def semantic_search_with_llm(
    query: str,
    json_path: str,
    *,
    model: str,
    temperature: float = 0.0,
    max_concurrent: int = 10,
    snippet_len: int = 2048,
) -> List[Dict[str, Any]]:
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

    async def inspect_message(telegram_id: int, content: str, author: str) -> None:
        global async_count_1, async_count_2
        trimmed = content[:snippet_len]

        prompt = (
            f"Тебе дан пользовательский запрос и описание человека (автор и его сообщение). "
            f"Нужно решить, релевантен ли этот человек запросу. "
            f"Если да — кратко укажи, почему. Если нет — просто ответь NO.\n\n"
            f"Запрос пользователя:\n\"{query}\"\n\n"
            f"Автор:\n\"{author}\"\n\n"
            f"Сообщение:\n\"{trimmed}\"\n\n"
            f"Ответь в одном из двух форматов:\n"
            f"1. YES: <одна релевантная фраза из сообщения>\n"
            f"2. NO"
        )

        messages = [
            {"role": "system", "content": "Ты бинарный фильтр. Ты не даёшь советы, не обсуждаешь. Только определяешь, релевантно ли сообщение запросу."},
            {"role": "user", "content": prompt},
        ]

        async with semaphore:
            try:
                logger.info(f"Отправка запроса в together для {async_count_1}")
                async_count_1 += 1
                reply = await chat_completion_togetherai(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                )
            except Exception as e:
                logger.warning(f"[LLM Error] telegram_id={telegram_id}: {e}")
                return

        logger.info(f"Получение запроса для {async_count_2}")
        async_count_2 += 1

        reply = reply.strip()
        if reply.upper().startswith("YES"):
            parts = reply.split(":", 1)
            highlight = parts[1].strip() if len(parts) > 1 else trimmed[:120]
            relevant_results.append({"telegram_id": telegram_id, "highlight": highlight})
            logger.info(f"[LLM] Релевантно: {telegram_id}")
        elif reply.upper().startswith("NO"):
            pass
        else:
            logger.warning(f"[LLM ⚠️ Нестандартный ответ] telegram_id={telegram_id}, reply={reply}")

    tasks: List[asyncio.Task] = []

    for records in data.values():
        for rec in records:
            text_block = rec.get("downloaded_text", [])
            if len(text_block) >= 4:
                try:
                    telegram_id = int(text_block[0])
                    content = text_block[2]
                    author = text_block[3]
                    tasks.append(asyncio.create_task(inspect_message(telegram_id, content, author)))
                except Exception as e:
                    logger.warning(f"[Parse Error] {e}")
                    continue

    await asyncio.gather(*tasks, return_exceptions=True)
    return relevant_results


def get_records_by_telegram_ids_from_json(json_path: str, telegram_ids: List[int]) -> List[Dict[str, Any]]:
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
