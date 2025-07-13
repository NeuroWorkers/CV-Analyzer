import json
import asyncio
from typing import Dict, Any, List

import os
from utils.openrouter_request import chat_completion_openrouter
from configs.cfg import relevant_text_path

SYSTEM_PROMPT = (
    "Ты — текстовый фильтр. На вход ты получаешь текст на русском языке. "
    "Твоя задача — найти в нём все русские аббревиатуры, написанные ЗАГЛАВНЫМИ кириллическими буквами (например: ИИ, ФНС, СПБ), "
    "и заменить их на соответствующие английские аббревиатуры в верхнем регистре (например: AI, FNS, SPB). "
    "⚠️ Ты не должен расшифровывать аббревиатуры, не должен переводить обычные слова, не должен менять структуру текста. "
    "⚠️ Ты не должен добавлять пояснения, списки, примеры или метаданные. "
    "Верни только текст с заменами — **ничего лишнего, никаких объяснений**. "
    "Если аббревиатура тебе неизвестна, просто транслитерируй её в латиницу в UPPERCASE. "
)

MODEL = "google/gemini-2.5-flash"


async def process_abbreviations_with_llm(input_path: str = os.path.join(relevant_text_path, "cv.json"), output_path: str = os.path.join(relevant_text_path, "fixed_abbr_cv.json")):
    with open(input_path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    tasks = []
    index_map = []

    for outer_key, records in data.items():
        for i, item in enumerate(records):
            original_text = item["downloaded_text"][2]
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": original_text}
            ]
            tasks.append(chat_completion_openrouter(messages, model=MODEL, temperature=0))
            index_map.append((outer_key, i))

    responses = await asyncio.gather(*tasks)

    for (outer_key, i), new_text in zip(index_map, responses):
        data[outer_key][i]["downloaded_text"][2] = new_text

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Обработка завершена. Файл сохранён в {output_path}")