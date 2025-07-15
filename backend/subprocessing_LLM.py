import asyncio
import json
import re
from typing import List, Tuple

from configs.cfg import preprocessing_model, postprocessing_model
from utils.openrouter_request import chat_completion_openrouter

from utils.logger import setup_logger

logger = setup_logger("SUBLLM")


async def pre_proccessing(user_query: str) -> str:
    """
    Оптимизирует пользовательский запрос, расширяя его синонимами,
    связанными терминами и аббревиатурами через вызов OpenRouter.

    Args:
        user_query (str): Исходный текст запроса пользователя.

    Returns:
        str: Оптимизированный запрос — строка с ключевыми словами и синонимами.
    """
    system_prompt = (
        "Ты ИИ-ассистент по поиску резюме. Преобразуй запрос пользователя в короткий список ключевых слов, "
        "синонимов и связанных терминов. Добавляй формы слов, синонимы, аббревиатуры, связанные роли. "
        "Игнорируй нерелевантные слова. Верни одну строку."
    )
    response = await chat_completion_openrouter([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ],
        model=preprocessing_model)

    return response


def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


async def post_proccessing(user_query: str, results: List[dict], highlights: List[str], chunk_size: int = 5) -> Tuple[List[dict], List[str]]:
    """
    Фильтрует результаты поиска, отправляя LLM только highlights вместо полного текста.

    Args:
        user_query (str): Поисковый запрос пользователя.
        results (List[dict]): Результаты поиска.
        highlights (List[str]): Список подсвеченных фрагментов для результатов.
        chunk_size (int): Размер одного батча.

    Returns:
        Tuple[List[dict], List[str]]: Списки релевантных results и соответствующих highlights.
    """
    if not results or not highlights:
        return [], []

    async def process_chunk(chunk: List[Tuple[dict, str]]) -> Tuple[List[dict], List[str]]:
        system_prompt = (
            "Ты — ИИ, фильтрующий короткие фрагменты резюме по запросу пользователя.\n"
            "На входе — запрос и список фрагментов. Каждый фрагмент содержит telegram_id и текст.\n"
            "Верни JSON-массив объектов вида: {'telegram_id': <id>, 'релевантно': 'Да'} — только для релевантных.\n"
            "Если фрагмент нерелевантен — просто не включай его в ответ."
        )

        blocks = [f"[{r['telegram_id']}] {highlight}" for r, highlight in chunk]

        user_prompt = f"Запрос: {user_query}\nФрагменты:\n" + "\n\n".join(blocks)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = await chat_completion_openrouter(messages, model=postprocessing_model)
            clean = re.sub(r"```json\s*|```", "", response).strip()
            parsed = json.loads(clean)
        except Exception as e:
            logger.error(f"[LLM Chunk] Ошибка обработки чанка: {e}")
            return [], []

        telegram_id_to_pair = {r["telegram_id"]: (r, h) for r, h in chunk}
        filtered_results = []
        filtered_highlights = []

        for item in parsed:
            tid = item.get("telegram_id")
            if item.get("релевантно", "").lower().startswith("да") and tid in telegram_id_to_pair:
                result, highlight = telegram_id_to_pair[tid]
                filtered_results.append(result)
                filtered_highlights.append(highlight)

        return filtered_results, filtered_highlights

    paired = list(zip(results, highlights))
    tasks = [process_chunk(chunk) for chunk in chunk_list(paired, chunk_size)]
    all_filtered = await asyncio.gather(*tasks)

    flat_results = [item for chunk in all_filtered for item in chunk[0]]
    flat_highlights = [item for chunk in all_filtered for item in chunk[1]]

    logger.info(f"Фильтрация по highlights завершена: {len(flat_results)} из {len(results)}")
    return flat_results, flat_highlights
