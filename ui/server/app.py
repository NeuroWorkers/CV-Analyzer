import uvicorn
from fastapi import FastAPI
from configs.project_paths import *
from starlette.requests import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from configs.server_config import SERVER_PORT, SERVER_HOST
from backend.question_analyzer import fetch_all_messages, full_pipeline

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
            if node.media_path and os.path.exists(node.media_path):
                filename = os.path.basename(node.media_path)
                media_url = f"/media/{filename}"  

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
    nodes = await full_pipeline(query)
    results = []
    count = 0
    for node in nodes:
        if (page_number - 1) * 6 <= count < page_number * 6:
            media_url = None
            if node.media_path and os.path.exists(node.media_path):
                filename = os.path.basename(node.media_path)
                media_url = f"/media/{filename}"  
            results.append({
                "author": node.author,
                "date": node.created_at.isoformat() if node.created_at else None,
                "text": node.content,
                "photo": media_url
            })
        count += 1

    results.append({"count": count})
    return JSONResponse(results)

if __name__ == "__main__":
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
