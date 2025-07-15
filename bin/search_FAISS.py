#!/bin/bash
cd "$(dirname "$0")/../"

source ./bin/begin.sh

python3 -c '
import asyncio
import sys
from backend.search_FAISS import full_pipeline, init_resources

question_default="Валера"

async def main():
    backend.create_FAISS.init_resources()
    q=sys.argv[1]
    if str(q) == "" :
        q=question_default
    res=full_pipeline(q)
    print(res)

asyncio.run(main())
'