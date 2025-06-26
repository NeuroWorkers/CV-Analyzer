import os
import time
import json
import openai

from configs.ai_config import max_processing_message_count
from configs.project_paths import tg_dump_text_path, relevant_text_path

PROMPT_TEMPLATE = """
Ты — помощник, который помогает отбирать сообщения, содержащие CV (резюме) или краткое описание профессионального опыта человека.

Ответь только "YES" если текст — это CV, или "NO" если это обычное сообщение.

Пример сообщения:
\"\"\"{text}\"\"\"
"""

REAL_AUTHOR_PROMPT = """
Ты — помощник, который анализирует пересланные сообщения в Telegram.

Вот текст сообщения:
\"\"\"{text}\"\"\"

Имя отправителя, записанное системой: "{system_author}"
Имя автора, у которого сообщение было переслано (если есть): "{fwd_author}"

Если в тексте сообщения явно указано настоящее имя автора (например: "Меня зовут Иван", "Я - Ольга Смирнова", "Екатерина Крылова, личное CV"), вытащи его и верни как ответ. 
Если нет, но указано `fwd_author`, то верни `fwd_author`. 
Если и это не помогает — верни `system_author`. Ответь одним именем, без объяснений.
"""


def is_cv_openai(text: str) -> bool:
    try:
        prompt = PROMPT_TEMPLATE.format(text=text)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        result = response['choices'][0]['message']['content'].strip().lower()
        return "yes" in result
    except Exception as e:
        print(f"[ERROR is_cv]: {e}")
        return False


def determine_real_author(text: str, system_author: str, fwd_author: str) -> str:
    try:
        prompt = REAL_AUTHOR_PROMPT.format(
            text=text,
            system_author=system_author or "",
            fwd_author=fwd_author or ""
        )
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"[ERROR author_detect]: {e}")
        return system_author


def sort_cv():
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
            if not text_block or len(text_block) < 7:
                continue

            telegram_id = text_block[0]
            created_at = text_block[1]
            content = text_block[2]
            system_author = text_block[3]
            fwd_date = text_block[4]
            fwd_author = text_block[5]
            topic = text_block[6]

            if len(content.strip()) < 50:
                continue

            print(f"Проверка сообщения: {telegram_id}")

            if is_cv_openai(content):
                true_author = determine_real_author(content, system_author, fwd_author)
                text_block[3] = true_author
                filtered.setdefault(topic_id, []).append(msg)

            count += 1
            time.sleep(1.2)

    os.makedirs(relevant_text_path, exist_ok=True)
    with open(os.path.join(relevant_text_path, "cv.json"), "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=4)