import os
import json
import shutil
import traceback

from configs.cfg import relevant_text_path, relevant_media_path, tg_dump_media_path


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
    try:
        os.makedirs(destination_folder, exist_ok=True)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        media_filenames = set()

        for entries in data.values():
            for entry in entries:
                media = entry.get("downloaded_media")
                if media and media.get("path"):
                    filename = os.path.basename(media["path"])
                    media_filenames.add(filename)

        copied_count = 0
        skipped_count = 0

        for filename in media_filenames:
            src_path = os.path.join(tg_dump_media_path, filename)
            dst_path = os.path.join(destination_folder, filename)

            if os.path.exists(src_path):
                try:
                    shutil.copy2(src_path, dst_path)
                    copied_count += 1
                    print(f"Скопирован: {src_path} → {dst_path}")
                except Exception as e:
                    print(f"[ERROR] Ошибка при копировании {src_path}: {e}")
            else:
                print(f"[WARNING] Файл не найден в tg_dump: {src_path}")
                skipped_count += 1

        print(f"Копирование завершено. Скопировано: {copied_count}, пропущено: {skipped_count}")
    except:
        print(traceback.format_exc())