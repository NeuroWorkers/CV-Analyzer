import uvicorn
from fastapi import FastAPI
from configs.project_paths import *
from starlette.requests import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from configs.server_config import SERVER_PORT, SERVER_HOST
from backend.question_analyzer import fetch_all_messages, full_pipeline

import logging

logger = logging.getLogger(__name__)  
logger.setLevel(logging.DEBUG)  
file_handler = logging.FileHandler('app2.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def home():
    return {"message": "BACKEND SERVER SUCCESSFULLY STARTED"}


app.mount("/media", StaticFiles(directory=relevant_media_path), name="media")


@app.get("/init437721")
async def init437721():
    return {"status": "ok"}


@app.get("/get_all_nodes/{page_number}")
async def get_all_nodes(page_number: int = 0, request: Request = None):
    nodes = await fetch_all_messages()
    results = []
    count = 0

    for node in nodes:
        if (page_number - 1) * 6 <= count < page_number * 6:
            media_url = None
            logger.info("node.media_path = " + str(node.media_path))
            curent_media_path=os.path.join(DATA_PATH,str(node.media_path))
            if node.media_path and os.path.exists(curent_media_path):
                filename = os.path.basename(curent_media_path)
                media_url = f"/media/{filename}"
                logger.info("media_url = " + media_url)

            results.append({
                "author": node.author,
                "date": node.created_at.isoformat() if node.created_at else None,
                "text": node.content,
                "photo": media_url
            })
        count += 1

    results.append({"count": count})
    return JSONResponse(results)


@app.get("/get_relevant_nodes/{query}/{page_number}")
async def get_relevant_nodes(query: str, page_number: int = 0, request: Request = None):
    nodes, ht = await full_pipeline(query)
    results = []

    start = (page_number - 1) * 6
    end = page_number * 6

    for node in nodes[start:end]:
        media_url = None
        if node.media_path and os.path.exists(node.media_path):
            filename = os.path.basename(node.media_path)
            media_url = f"/media/{filename}" 

        results.append({
            "author": node.author,
            "date": node.created_at.isoformat() if node.created_at else None,
            "text": node.content,
            "highlight_text": ht[idx] if idx < len(ht) else [],
            "photo": media_url
        })

    results.append({"count": len(nodes)})
    return JSONResponse(results)
    
    # __old__ version code ...

    # count = 0
    # for node in nodes:
    #     if (page_number - 1) * 6 <= count < page_number * 6:
    #         media_url = None
    #         if node.media_path and os.path.exists(node.media_path):
    #             filename = os.path.basename(node.media_path)
    #             media_url = f"/media/{filename}"  

    #         results.append({
    #             "author": node.author,
    #             "date": node.created_at.isoformat() if node.created_at else None,
    #             "text": node.content,
    #             "highlight_text": ht[idx] if idx < len(ht) else [],
    #             "photo": media_url
    #         })
    #         idx += 1
    #     count += 1

    # results.append({"count": count})
    # return JSONResponse(results)

if __name__ == "__main__":
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
