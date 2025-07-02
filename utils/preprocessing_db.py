import os
import json
import shutil
from configs.project_paths import relevant_text_path, relevant_media_path, tg_dump_media_path


def copy_media_from_json(
    json_path: str = os.path.join(relevant_text_path, "cv.json"),
    destination_folder: str = relevant_media_path
) -> None:
    """
    Копирует файлы медиа из папки tg_dump_media_path в папку назначения,
    основываясь на данных из JSON файла с резюме.

    Проходит по JSON-файлу, извлекает пути к медиафайлам, затем копирует
    все файлы из tg_dump_media_path в папку назначения.

    Args:
        json_path (str): Путь к JSON файлу с данными резюме и медиа (по умолчанию "<relevant_text_path>/cv.json").
        destination_folder (str): Папка, в которую будут скопированы медиафайлы (по умолчанию <relevant_media_path>).

    Returns:
        None

    Side Effects:
        Создает папку назначения, если её нет.
        Копирует файлы, выводит в консоль информацию о процессе копирования и ошибках.
    """
    os.makedirs(destination_folder, exist_ok=True)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    copied_count = 0
    skipped_count = 0

    # Итерация по всем темам и сообщениям, чтобы проверить наличие медиа
    for topic_id, entries in data.items():
        for entry in entries:
            media = entry.get("downloaded_media")
            if not media:
                continue

            media_path = media.get("path")
            if not media_path:
                print(f"Пропущено: путь к медиа отсутствует (media = {media})")
                skipped_count += 1
                continue

    # Копирование всех файлов из tg_dump_media_path в папку назначения
    for filename in os.listdir(tg_dump_media_path):
        tg_dump_media_file_path = os.path.join(tg_dump_media_path, filename)

        if os.path.isfile(tg_dump_media_file_path):
            dst_path = os.path.join(destination_folder, filename)
            try:
                shutil.copy2(tg_dump_media_file_path, dst_path)
                copied_count += 1
                print(f"Скопирован: {tg_dump_media_file_path} → {dst_path}")
            except Exception as e:
                print(f"[ERROR] Ошибка при копировании {tg_dump_media_file_path}: {e}")
        else:
            print(f"Пропущено (не файл): {tg_dump_media_file_path}")
            skipped_count += 1

    print(f"Копирование завершено. Скопировано: {copied_count}, пропущено: {skipped_count}")