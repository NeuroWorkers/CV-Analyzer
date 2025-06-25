import os
import json
import shutil
from configs.project_paths import relevant_text_path, relevant_media_path


def copy_media_from_json(json_path: str = os.path.join(relevant_text_path, "cv.json"), destination_folder: str = relevant_media_path):
    os.makedirs(destination_folder, exist_ok=True)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    copied_count = 0
    skipped_count = 0

    for topic_id, entries in data.items():
        for entry in entries:
            media = entry.get("Загруженное медиа")
            if not media:
                continue

            media_path = media.get("path")
            if not media_path:
                print(f"Пропущено: путь к медиа отсутствует (media = {media})")
                skipped_count += 1
                continue

            src_path = os.path.join('tg_dumper', media_path)
            if os.path.isfile(src_path):
                dst_path = os.path.join(destination_folder, os.path.basename(src_path))
                try:
                    shutil.copy2(src_path, dst_path)
                    copied_count += 1
                    print(f"Скопирован: {src_path} → {dst_path}")
                except Exception as e:
                    print(f"[ERROR] Ошибка при копировании {src_path}: {e}")
            else:
                print(f"Файл не найден: {src_path}")
                skipped_count += 1

    print(f"\nИтого скопировано: {copied_count}, пропущено: {skipped_count}")
