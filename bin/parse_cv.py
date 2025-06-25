#!/usr/bin/env python3
#import asyncio
from backend.sort_cv import sort_cv
from configs.telegram_config import (
    API_ID, API_HASH, SESSION_STRING,
    group_username, output_filename, specific_topic_id, media_dir_parth, last_dump_file
)
from utils.preprocessing_db import copy_media_from_json

# SORT CV
sort_cv()
copy_media_from_json()
