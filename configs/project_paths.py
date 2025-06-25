import os
from configs.main_paths import DATA_PATH, DATABASE_PATH

if DATA_PATH == "":
    DATA_PATH = "../data"

if DATABASE_PATH == "":
    DATABASE_PATH = "../database"

relevant_path = os.path.join(DATA_PATH, "relevant")
relevant_media_path = os.path.join(relevant_path, "media")
relevant_text_path = os.path.join(relevant_path, "text")

tg_dump_path = os.path.join(DATA_PATH, "tg_dump")
tg_dump_media_path = os.path.join(tg_dump_path, "media")
tg_dump_text_path = os.path.join(tg_dump_path, "text")
tg_dump_last_dump_path = os.path.join(tg_dump_path, "last_dump")


db_path = os.path.join(DATABASE_PATH, "db")
db_schema_path = os.path.join(db_path, "dbschema")



