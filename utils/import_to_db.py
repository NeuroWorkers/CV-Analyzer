import os
import pytz
import json
import edgedb
from datetime import datetime
from configs.project_paths import relevant_text_path


def make_aware(dt_str):
    if dt_str is None:
        return None
    dt_naive = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    utc = pytz.UTC
    return utc.localize(dt_naive)


async def update_messages_to_db(json_path: str = os.path.join(relevant_text_path, "cv.json")):
    client = edgedb.create_async_client("database")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for topic_id, messages in data.items():
        for message in messages:
            text_data = message.get("downloaded_text")
            media_data = message.get("downloaded_media")

            if not text_data:
                continue

            telegram_id = text_data[0]
            created_at = make_aware(text_data[1])
            content = text_data[2]
            author = text_data[3]
            fwd_date = make_aware(text_data[4])
            fwd_author = text_data[5]
            topic_id = text_data[6]

            media_type = media_data["type"] if media_data else None
            media_path = media_data["path"] if media_data else None

            try:
                await client.query("""
                    INSERT ResumeMessage {
                        telegram_id := <int64>$telegram_id,
                        created_at := <datetime>$created_at,
                        content := <str>$content,
                        author := <str>$author,
                        fwd_date := <optional datetime>$fwd_date,
                        fwd_author := <optional str>$fwd_author,
                        topic_id := <int64>$topic_id,
                        media_type := <optional str>$media_type,
                        media_path := <optional str>$media_path
                    }
                    UNLESS CONFLICT ON .telegram_id
                    ELSE (
                        UPDATE ResumeMessage
                        SET {
                            content := <str>$content,
                            created_at := <datetime>$created_at,
                            author := <str>$author,
                            fwd_date := <optional datetime>$fwd_date,
                            fwd_author := <optional str>$fwd_author,
                            topic_id := <int64>$topic_id,
                            media_type := <optional str>$media_type,
                            media_path := <optional str>$media_path
                        }
                    );
                """,
                                   telegram_id=telegram_id,
                                   created_at=created_at,
                                   content=content,
                                   author=author,
                                   fwd_date=fwd_date,
                                   fwd_author=fwd_author,
                                   topic_id=topic_id,
                                   media_type=media_type,
                                   media_path=media_path
                                   )

                print(f"Загружено или обновлено сообщение {telegram_id}")
            except Exception as e:
                print(f"Ошибка при вставке/обновлении сообщения {telegram_id}: {e}")

    await client.aclose()
