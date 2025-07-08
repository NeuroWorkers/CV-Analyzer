import time
import logging
from typing import Dict, Tuple

import os
import uvicorn
import backend
import traceback
from fastapi import FastAPI
from starlette.requests import Request
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.question_analyzer_FAISS import init_resources

from utils.logger import MyLogger

from configs.cfg import relevant_media_path, DATA_PATH
from configs.cfg import SERVER_PORT, SERVER_HOST, SEARCH_MODE

logger = MyLogger("ui.server.app", level=logging.INFO, console=True)

if SEARCH_MODE == "" or not hasattr(backend, "SEARCH_MODE"):
    from backend.question_analyzer_LLM import fetch_all_messages, full_pipeline
elif SEARCH_MODE == "LLM":
    from backend.question_analyzer_LLM import fetch_all_messages, full_pipeline
elif SEARCH_MODE == "EDGE_EMBED":
    from backend.question_analyzer_EDGE import fetch_all_messages, full_pipeline
elif SEARCH_MODE == "FAISS":
    from backend.create_FAISS import build_or_update_index

    build_or_update_index()
    from backend.question_analyzer_FAISS import fetch_all_messages, full_pipeline


cached_all_nodes: Dict[str, Tuple[float, list]] = {}
cached_relevant_nodes: Dict[str, Tuple[float, Tuple[list, list]]] = {}

CACHE_TTL = 300


def is_cache_valid(timestamp: float) -> bool:
    return time.time() - timestamp < CACHE_TTL


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application lifespan")
    
    if SEARCH_MODE == "FAISS":
        logger.info("Initializing FAISS resources...")
        init_resources()
        logger.info("FAISS resources initialized successfully")
    else:
        logger.info(f"Using search mode: {SEARCH_MODE}")
    
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


@app.get("/get_all_nodes/{page_number}")
async def get_all_nodes(page_number: int = 1, request: Request = None):
    logger.info(f"GET /get_all_nodes/{page_number} - Client IP: {request.client.host if request else 'unknown'}")
    
    try:
        cache = cached_all_nodes.get("all")
        if cache and is_cache_valid(cache[0]):
            logger.debug("Using cached data for all nodes")
            nodes = cache[1]
        else:
            logger.debug("Fetching fresh data from database")
            nodes = await fetch_all_messages()
            cached_all_nodes["all"] = (time.time(), nodes)
            logger.debug(f"Cached {len(nodes)} nodes")

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
            "count": count
        }

        return JSONResponse(content=res_struct)

    except Exception as e:
        logger.error(f"Error in get_all_nodes: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/get_relevant_nodes/{query}/{page_number}")
async def get_relevant_nodes(query: str, page_number: int = 1, request: Request = None):
    logger.info(f"GET /get_relevant_nodes/'{query}'/{page_number} - Client IP: {request.client.host if request else 'unknown'}")
    
    try:
        cache = cached_relevant_nodes.get(query)
        if cache and is_cache_valid(cache[0]):
            logger.debug(f"Using cached search results for query: '{query}'")
            nodes, highlights = cache[1]
        else:
            logger.debug(f"Performing fresh search for query: '{query}'")
            nodes, highlights = await full_pipeline(query)
            cached_relevant_nodes[query] = (time.time(), (nodes, highlights))
            logger.debug(f"Cached search results: {nodes} nodes, {len(highlights)} highlight sets")

        start = (page_number - 1) * 6
        end = page_number * 6
        results = []

        logger.debug(f"Processing relevant nodes from index {start} to {end}")

        for idx, node in enumerate(nodes[start:end]):
            media_url = None
            if node['media_path']:
                current_media_path = os.path.join(DATA_PATH, str(node['media_path']))
                if os.path.exists(current_media_path):
                    media_url = f"/media/{os.path.basename(current_media_path)}"
                    logger.debug(f"Found media file for relevant node {idx}: {media_url}")

            results.append({
                "author": node['author'],
                "date": node['created_at'].isoformat() if node['created_at'] else None,
                "text": node['content'],
                "photo": media_url
            })

        count = len(nodes)
        # Получаем highlights для текущей страницы
        page_highlights = highlights[start:end] if highlights else []
        
        logger.info(f"Returning {len(results)} relevant nodes out of {count} total for query '{query}' (page {page_number})")
        logger.debug(f"Page highlights: {page_highlights}")

        res_struct = {
            "data": results,
            "count": count,
            "highlight_text": page_highlights
        }

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
