import os
import time
import json
import asyncio

from configs.cfg import max_processing_message_count
from configs.cfg import tg_dump_text_path, relevant_text_path
from utils.openrouter_request import chat_completion_openrouter

PROMPT_TEMPLATE = """
Ты — помощник, который помогает отбирать сообщения, содержащие CV (резюме) или подробное описание профессионального опыта, навыков и достижений человека.

Ответь только "YES", если сообщение:
- Является самопрезентацией профессионального опыта (даже если написано в свободной форме)
- Содержит факты о карьере, проектах, местах работы, обязанностях, достижениях или навыках
- Может быть полезно рекрутеру или работодателю для понимания, чем человек занимался, в чём его сильные стороны

Ответь "NO", если:
- Это просто обсуждение, воспоминания, рефлексия или обрывочные мысли без ясной цели презентовать себя
- В сообщении нет системной или хотя бы информативной картины профессионального профиля

Важно:
- Допускаются как структурированные, так и свободные описания
- Не имеет значения, насколько текст длинный или рекламный, если он рассказывает о конкретных компетенциях, опыте и целях

Пример сообщения:
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
        result = asyncio.run(chat_completion_openrouter([
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
        result = asyncio.run(chat_completion_openrouter([
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
    with open(os.path.join(relevant_text_path, "sort_cv.json"), "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=4)