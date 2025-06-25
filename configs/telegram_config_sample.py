import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))

API_ID = 0
API_HASH = ''
SESSION_STRING = ''

group_username = 'https://t.me/horizontal_network'

output_filename = os.path.join(BASE_DIR, "tg_fetcher", "downloaded_text", "messages.json")
media_dir_parth = os.path.join(BASE_DIR, "tg_fetcher", "downloaded_media")
output_dir = os.path.join(BASE_DIR, "tg_fetcher", "downloaded_text")
last_dump_file = os.path.join(BASE_DIR, "tg_fetcher", "last_dump", "last_dump_date.txt")
last_dump_dir = os.path.join(BASE_DIR, "tg_fetcher", "last_dump")

specific_topic_id = 1275
