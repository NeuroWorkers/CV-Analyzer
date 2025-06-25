import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))

messages_json = os.path.join(BASE_DIR, "tg_fetcher", "downloaded_text", "messages.json")
relevant_media = os.path.join(BASE_DIR, "database", "media")
relevant_messages_json = os.path.join(BASE_DIR, "database", "messages", "cv.json")
relevant_messages_dir = os.path.join(BASE_DIR, "database", "messages")

output_filename = os.path.join(BASE_DIR, "tg_fetcher", "downloaded_text", "messages.json")
media_dir_parth = os.path.join(BASE_DIR, "tg_fetcher", "downloaded_media")
output_dir = os.path.join(BASE_DIR, "tg_fetcher", "downloaded_text")
last_dump_file = os.path.join(BASE_DIR, "tg_fetcher", "last_dump", "last_dump_date.txt")
last_dump_dir = os.path.join(BASE_DIR, "tg_fetcher", "last_dump")