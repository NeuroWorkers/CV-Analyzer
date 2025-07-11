import json
import os
from typing import List, Dict, Any

import httpx
from tqdm.asyncio import tqdm_asyncio

from configs.cfg import relevant_text_path

INPUT_PATH = os.path.join(relevant_text_path, "cv.json")
OUTPUT_PATH = os.path.join(relevant_text_path, "non_trash_cv.json")
BATCH_SIZE = 10
MODEL_NAME = "google/gemini-2.5-flash"


def extract_contents_from_dict(data: Dict[str, List[Dict[str, Any]]]) -> List[str]:
    """
    Извлекает список всех content'ов из словаря {chat_id: [messages]}.
    """
    contents = []
    for chat_id, messages in data.items():
        for msg in messages:
            text = msg.get("downloaded_text", [None, None, None])[2]
            contents.append(text or "")
    return contents


def flatten_data(data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Разворачивает словарь {chat_id: [items]} в плоский список записей"""
    flat = []
    for chat_id, items in data.items():
        for item in items:
            flat.append({"chat_id": chat_id, "item": item})
    return flat


def restore_structure(filtered_flat: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Собирает обратно в формат {chat_id: [items]}"""
    grouped = {}
    for entry in filtered_flat:
        chat_id = entry["chat_id"]
        grouped.setdefault(chat_id, []).append(entry["item"])
    return grouped


async def filter_batch(batch: List[str]) -> List[bool]:
    """
    Отправляет батч текстов в LLM и получает список флагов информативности.
    """
    prompt_intro = (
        "Для каждого текста ответь 'Да' — только если он действительно содержит "
        "информативное описание рода занятий, профессии, опыта, проектов, услуг или компетенций.\n"
        "Если это просто междометие, короткая фраза, ироничный или абстрактный текст без конкретики "
        "(например: '.', 'продаю говно', 'живёт в мифе'), или только ссылка — ответ 'Нет'.\n"
        "Формат: одна строка 'Да' или 'Нет' для каждого текста.\n\n"
    )

    numbered = "\n".join([f"{i + 1}. {text}" for i, text in enumerate(batch)])
    full_prompt = prompt_intro + numbered

    try:
        response = await chat_completion_openrouter(
            messages=[{"role": "user", "content": full_prompt}],
            model=MODEL_NAME
        )
        lines = [line.strip().lower() for line in response.splitlines()]
        return [("да" in line) for line in lines if line]
    except Exception as e:
        print(f"Ошибка в батче: {e}")
        return [False] * len(batch)


async def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    flat_data = flatten_data(raw_data)
    contents = [entry["item"].get("downloaded_text", [None, None, None])[2] or "" for entry in flat_data]

    batches = [contents[i:i + BATCH_SIZE] for i in range(0, len(contents), BATCH_SIZE)]

    results = await tqdm_asyncio.gather(*[filter_batch(batch) for batch in batches], desc="Фильтрация")
    informative_mask = [flag for batch_result in results for flag in batch_result]

    filtered_flat = [
        entry for entry, is_good in zip(flat_data, informative_mask) if is_good
    ]

    structured = restore_structure(filtered_flat)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(structured, f, ensure_ascii=False, indent=2)

    print(
        f"\nСохранили {sum(len(v) for v in structured.values())} записей из {sum(len(v) for v in raw_data.values())}")


async def chat_completion_openrouter(messages: List[Dict[str, str]], model) -> str:
    """
    Отправляет запрос к OpenRouter API и получает ответ от модели.

    Args:
        messages (List[Dict[str, str]]): Список сообщений с ролями для диалога (например, system, user).
        model (str): Имя модели OpenRouter для использования (по умолчанию "google/gemini-2.5-flash").

    Returns:
        str: Текстовый ответ от модели.
    """
    from configs.cfg import openrouter_api_key

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client_http:
            response = await client_http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            result = response.json()["choices"][0]["message"]["content"].strip()
            return result

    except httpx.HTTPStatusError as e:
        raise
    except Exception as e:
        raise
