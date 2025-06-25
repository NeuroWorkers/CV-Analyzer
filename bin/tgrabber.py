#!/usr/bin/env python3
import asyncio
#from tg_dumper.tgrabber import main
#import tg_dumper
from tg_fetcher.tgrabber import main
from configs.telegram_config import (
    API_ID, API_HASH, SESSION_STRING,
    group_username, output_filename, specific_topic_id, media_dir_parth, last_dump_file
)


# 
#tg_dumper.tgrabber.
asyncio.run(main())
