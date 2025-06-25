#!/usr/bin/env python3
import asyncio
from database.db.import_to_db import update_messages_to_db
from configs.telegram_config import (
    API_ID, API_HASH, SESSION_STRING,
    group_username, output_filename, specific_topic_id, media_dir_parth, last_dump_file
)


asyncio.run(update_messages_to_db())
