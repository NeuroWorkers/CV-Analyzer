import os
import time
import json
import asyncio
import httpx

from configs.ai_config import max_processing_message_count, openrouter_api_key
from configs.project_paths import tg_dump_text_path, relevant_text_path, relevant_media_path

PROMPT_TEMPLATE = """
Ты — помощник, который отбирает сообщения, содержащие резюме (CV) или любые описания профессионального опыта, навыков, достижений, карьерного пути человека.

Твоя задача — ответить только "YES" или "NO".

Ответь "YES", если сообщение:
- Похоже на CV, даже если оно неформальное
- Содержит перечень навыков, технологий, сфер деятельности
- Описывает, где человек работал, какие у него компетенции, что он умеет
- Может использоваться для оценки кандидата или как отклик на вакансию

Ответь "NO", если в сообщении нет информации о профессиональных качествах или опыте.

Сообщение:
\"\"\"{text}\"\"\"
"""

REAL_AUTHOR_PROMPT = """
Ты — помощник, который анализирует пересланные сообщения в Telegram.

Вот текст сообщения:
\"\"\"{text}\"\"\"

Имя отправителя, записанное системой: "{system_author}"
Имя автора, у которого сообщение было переслано (если есть): "{fwd_author}"

Если в тексте сообщения явно указано настоящее имя автора (например: "Меня зовут Иван", "Я - Ольга Смирнова", "Екатерина Крылова, личное CV"), 
вытащи его и верни как ответ. Также добавь в ответ ник человека в телеграм (например: @ник). Полноценный ответ должен выглядеть так - "@krisi432 Кристина Соколова".
Если нет, но указано `fwd_author`, то верни `fwd_author`. 
Если и это не помогает — верни `system_author`. Ответь одним именем, без объяснений.
"""


HEADERS = {
    "Authorization": f"Bearer {openrouter_api_key}",
    "Content-Type": "application/json"
}


async def chat_completion(messages: list[dict], model: str = "openai/gpt-4") -> str:
    """
    Отправляет запрос в OpenRouter API для генерации ответа модели чат-ИИ.

    Args:
        messages (list[dict]): Список сообщений (словарей с ролями и контентом) для диалога.
        model (str): Название модели ИИ (по умолчанию "openai/gpt-4").

    Returns:
        str: Текст ответа модели.
    """
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()


def is_cv(text: str) -> bool:
    """
    Определяет, является ли текст резюме (CV) с помощью модели ИИ.

    Args:
        text (str): Текст сообщения для проверки.

    Returns:
        bool: True, если текст похож на резюме (ответ модели содержит "yes"), иначе False.
    """
    try:
        prompt = PROMPT_TEMPLATE.format(text=text)
        result = asyncio.run(chat_completion([
            {"role": "user", "content": prompt}
        ]))
        return "yes" in result.lower()
    except Exception as e:
        print(f"[ERROR is_cv]: {e}")
        return False


def detect_real_author(text: str, system_author: str, fwd_author: str) -> str:
    """
    Определяет реальное имя автора пересланного сообщения на основе текста и метаданных.

    Args:
        text (str): Текст сообщения.
        system_author (str): Имя автора, записанное системой.
        fwd_author (str): Имя автора, у которого сообщение было переслано.

    Returns:
        str: Имя реального автора в формате "@ник Имя Фамилия" или одно из переданных имён.
    """
    try:
        prompt = REAL_AUTHOR_PROMPT.format(
            text=text,
            system_author=system_author or "",
            fwd_author=fwd_author or ""
        )
        result = asyncio.run(chat_completion([
            {"role": "user", "content": prompt}
        ]))
        return result if result else system_author
    except Exception as e:
        print(f"[ERROR author_detect]: {e}")
        return system_author


def sort_cv() -> None:
    """
    Загружает сообщения из файла non_filtered_cv.json, фильтрует резюме с помощью ИИ,
    определяет реального автора и сохраняет отфильтрованные данные в cv.json.

    Ограничивает обработку максимальным количеством сообщений, заданным в конфиге.
    Для каждого сообщения с резюме сохраняет обновлённые данные.

    Side Effects:
        Создает папку relevant_text_path, если её нет.
        Записывает файл cv.json с отфильтрованными резюме.
        Выводит в консоль прогресс обработки и ошибки.
    """
    with open(os.path.join(tg_dump_text_path, "non_filtered_cv.json"), "r", encoding="utf-8") as f:
        data = json.load(f)

    messages_by_topic = data.get("text", {})
    filtered = {}
    count = 0

    for topic_id, messages in messages_by_topic.items():
        for msg in messages:
            if count >= max_processing_message_count:
                break

            text_block = msg.get("downloaded_text")
            media_block = msg.get("downloaded_media")
            if not text_block or len(text_block) < 7:
                continue

            telegram_id = text_block[0]
            created_at = text_block[1]
            content = text_block[2]
            system_author = text_block[3]
            fwd_date = text_block[4]
            fwd_author = text_block[5]

            if media_block and media_block.get("path"):
                media_block["path"] = os.path.join("relevant", "media", os.path.basename(media_block["path"]))

            if len(content.strip()) < 50:
                continue

            print(f"\nОбрабатывается сообщение: {telegram_id}\n")

            if is_cv(content):
                true_author = detect_real_author(content, system_author, fwd_author)
                text_block[3] = true_author
                filtered.setdefault(topic_id, []).append(msg)

            count += 1
            time.sleep(1.2)

    os.makedirs(relevant_text_path, exist_ok=True)
    with open(os.path.join(relevant_text_path, "cv.json"), "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=4)