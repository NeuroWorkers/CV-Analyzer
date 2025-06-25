import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.question_analyzer import fetch_all_messages, question_analyzer
from starlette.requests import Request
from configs.server_config import SERVER_PORT, SERVER_HOST, SERVER_DEBUG_MODE

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
MEDIA_DIR = os.path.join(PROJECT_ROOT, 'database', 'media')
print(MEDIA_DIR)

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
    return {"message": "FastAPI-приложение работает. Задача по расписанию запущена."}


app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")


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
                if request:
                    media_url = str(request.url_for("media", path=filename))
                else:
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
async def get_relevant_nodes(query: str, page_number: int = 0):
    nodes = question_analyzer(query)
    results = []
    count = 0
    for node in nodes:
        if (page_number - 1) * 6 <= count < page_number * 6:
            results.append({
                "author": node["author"],
                "date": node["created_at"],
                "content": node["content"]
            })
        count += 1

    results.append({"count": count})
    return results


if __name__ == "__main__":
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
