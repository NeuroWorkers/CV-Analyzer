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


def is_cv_openai(text):
    try:
        prompt = PROMPT_TEMPLATE.format(text=text)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        result = response['choices'][0]['message']['content'].strip().lower()
        return "yes" in result
    except Exception as e:
        print(f"[ERROR]: {e}")
        return False


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
            if not text_block or len(text_block) < 3:
                continue

            text = text_block[2]

            if len(text.strip()) < 50:
                continue

            print(f"Проверка сообщения: {text_block[0]}")

            if is_cv_openai(text):
                filtered.setdefault(topic_id, []).append(msg)

            count += 1
            time.sleep(1.2)

    os.makedirs(relevant_text_path, exist_ok=True)

    with open(os.path.join(relevant_text_path, "cv.json"), "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=4)

