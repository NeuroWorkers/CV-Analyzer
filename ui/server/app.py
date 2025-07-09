import os
import backend
import uvicorn
import traceback
from fastapi import FastAPI
from starlette.requests import Request
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.question_analyzer_FAISS_2 import init_resources

from configs.cfg import relevant_media_path, DATA_PATH
from configs.cfg import SERVER_PORT, SERVER_HOST, SEARCH_MODE

from backend.question_analyzer_FAISS_2 import fetch_all_messages, full_pipeline

from utils.logger import setup_logger

logger = setup_logger("server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application lifespan")
    init_resources()
    logger.info("FAISS resources initialized successfully")
    logger.info("Application startup completed")
    yield
    logger.info("Application shutdown completed")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def home():
    """
    Корневая точка API для проверки статуса сервера.

    Returns:
        dict: Сообщение о успешном запуске сервера.
    """
    return {"message": "BACKEND SERVER SUCCESSFULLY STARTED"}


app.mount("/media", StaticFiles(directory=relevant_media_path), name="media")


@app.get("/init437721")
async def init437721():
    """
    Тестовая точка API для проверки статуса.

    Returns:
        dict: Статус "ok".
    """
    return {"status": "ok"}


@app.get("/get_all_nodes/{session_id}/{page_number}")
async def get_all_nodes(session_id: str, page_number: int = 1, request: Request = None):
    logger.info(f"GET /get_all_nodes/{session_id}/{page_number} - Client IP: {request.client.host if request else 'unknown'}")

    try:
        nodes = await fetch_all_messages()

        start = (page_number - 1) * 6
        end = page_number * 6
        results = []

        logger.debug(f"Processing nodes from index {start} to {end}")

        for idx, node in enumerate(nodes[start:end]):
            media_url = None
            if node.media_path:
                current_media_path = os.path.join(DATA_PATH, str(node.media_path))
                if os.path.exists(current_media_path):
                    media_url = f"/media/{os.path.basename(current_media_path)}"
                    logger.debug(f"Found media file for node {idx}: {media_url}")

            results.append({
                "author": node.author,
                "date": node.created_at.isoformat() if node.created_at else None,
                "text": node.content,
                "photo": media_url
            })

        count = len(nodes)
        logger.info(f"Returning {len(results)} nodes out of {count} total (page {page_number})")

        res_struct = {
            "data": results,
            "count": count,
            "session_id": session_id
        }

        return JSONResponse(content=res_struct)

    except Exception as e:
        logger.error(f"Error in get_all_nodes: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


session_cache = {}
nodes = None
highlights = None


@app.get("/get_relevant_nodes/{session_id}/{query}/{page_number}")
async def get_relevant_nodes(session_id: str, query: str, page_number: int = 1, request: Request = None):
    logger.info(
        f"GET /get_relevant_nodes/{session_id}/'{query}'/{page_number} - Client IP: {request.client.host if request else 'unknown'}")

    try:
        if session_id in session_cache:
            if query in session_cache[session_id]:
                nodes, highlights = session_cache[session_id][query]
                other_queries = list(session_cache[session_id].keys())
                for other_query in other_queries:
                    if other_query != query:
                        del session_cache[session_id][other_query]
            else:
                nodes, highlights = await full_pipeline(query)
                session_cache[session_id][query] = (nodes, highlights)
        else:
            session_cache[session_id] = {}
            nodes, highlights = await full_pipeline(query)
            session_cache[session_id][query] = (nodes, highlights)

        start = (page_number - 1) * 6
        end = page_number * 6
        results = []

        logger.debug(f"Processing relevant nodes from index {start} to {end}")

        for idx, node in enumerate(nodes[start:end]):
            media_url = None
            print(node)
            if node['media_path']:
                current_media_path = os.path.join(DATA_PATH, str(node['media_path']))
                if os.path.exists(current_media_path):
                    media_url = f"/media/{os.path.basename(current_media_path)}"
                    logger.debug(f"Found media file for relevant node {idx}: {media_url}")

            results.append({
                "author": node['meta']['author'],
                "date": node['id'] if node['id'] else None,
                "text": node['text'],
                "photo": media_url
            })

        count = len(nodes)

        page_highlights_nested = highlights[start:end] if highlights else []
        page_highlights = [word for sublist in page_highlights_nested for word in sublist]

        logger.info(
            f"Returning {len(results)} relevant nodes out of {count} total for query '{query}' (page {page_number})")
        logger.debug(f"Page highlights: {page_highlights}")

        res_struct = {
            "data": results,
            "count": count,
            "highlight_text": page_highlights,
            "session_id": session_id
        }

        logger.debug(f"\n\n\n\n{page_highlights}\n\n\n\n")

        return JSONResponse(content=res_struct)

    except Exception as e:
        logger.error(f"Error in get_relevant_nodes for query '{query}': {str(e)}\n{traceback.format_exc()}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    logger.info(f"Starting CV-Analyzer server on {SERVER_HOST}:{SERVER_PORT}")
    logger.info(f"Search mode: {SEARCH_MODE}")
    logger.debug(f"Media path: {relevant_media_path}")
    logger.debug(f"Data path: {DATA_PATH}")

    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
