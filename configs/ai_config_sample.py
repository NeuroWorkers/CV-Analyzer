import os
import openai

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))

openai.api_key = ""

messages_json = os.path.join(BASE_DIR, "tg_fetcher", "downloaded_text", "messages.json")
relevant_messages_json = os.path.join(BASE_DIR, "database", "messages", "cv.json")
relevant_messages_dir = os.path.join(BASE_DIR, "database", "messages")
relevant_media = os.path.join(BASE_DIR, "database", "media")

max_processing_message_count = 100
