#!/usr/bin/env python3
import asyncio
from utils.import_to_db import update_messages_to_db

asyncio.run(update_messages_to_db())
