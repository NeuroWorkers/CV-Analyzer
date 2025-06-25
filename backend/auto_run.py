import os
import shutil
import asyncio
from backend.sort_cv import sort_cv
from tg_dumper.tgrabber import main
from utils.preprocessing_db import copy_media_from_json
from utils.import_to_db import update_messages_to_db
from configs.project_paths import tg_dump_text_path, tg_dump_media_path, relevant_text_path, relevant_media_path


def auto_complete_dump() -> bool:
    try:
        print("ВЫПОЛНЯЕТСЯ ДАМП В БАЗУ")
        # DUMP
        asyncio.run(main())

        # SORT CV
        # sort_cv()

        # MOVE
        # copy_media_from_json()

        # IMPORT
        # asyncio.run(update_messages_to_db())
        print("ДАМП В БАЗУ ЗАВЕРШЕН")

        # clear_directory(relevant_text_path)
        # clear_directory(relevant_media_path)
        # clear_directory(tg_dump_media_path)
        # clear_directory(tg_dump_text_path)
        print("ДИРЕКТОРИИ ОБНОВЛЕНЫ")
    except Exception as e:
        print(f"[ERROR] {e}")
        return False
    return True


def clear_directory(directory_path):
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Директория '{directory_path}' не существует.")

    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)


auto_complete_dump()
