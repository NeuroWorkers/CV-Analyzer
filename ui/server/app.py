import os
import traceback
import uvicorn

from fastapi import FastAPI
from starlette.requests import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.question_analyzer_FAISS_2 import (
    init_resources,
    fetch_all_messages,
    full_pipeline
)
from configs.cfg import (
    relevant_media_path,
    DATA_PATH,
    SERVER_PORT,
    SERVER_HOST,
    SEARCH_MODE
)
from utils.logger import setup_logger

logger = setup_logger("server")

session_cache = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Жизненный цикл приложения FastAPI:
    инициализация FAISS-ресурсов при запуске и логирование завершения при остановке.
    """
    logger.info("Starting application lifespan")
    init_resources()
    logger.info("FAISS resources initialized successfully")
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

app.mount("/media", StaticFiles(directory=relevant_media_path), name="media")


@app.get("/")
async def home():
    """
    Корневая точка API. Проверка статуса сервера.

    Returns:
        dict: Сообщение об успешной инициализации.
    """
    return {"message": "BACKEND SERVER SUCCESSFULLY STARTED"}


@app.get("/init437721")
async def init437721():
    """
    Вспомогательная ручка для тестирования доступности сервера.

    Returns:
        dict: Статус OK.
    """
    return {"status": "ok"}


@app.get("/get_all_nodes/{session_id}/{page_number}")
async def get_all_nodes(session_id: str, page_number: int = 1, request: Request = None):
    """
    Возвращает все доступные записи (узлы) постранично.

    Args:
        session_id (str): Идентификатор пользовательской сессии.
        page_number (int): Номер страницы.
        request (Request): Объект запроса для получения IP клиента.

    Returns:
        JSONResponse: Список всех узлов на текущей странице.
    """
    logger.info(
        f"GET /get_all_nodes/{session_id}/{page_number} - Client IP: {request.client.host if request else 'unknown'}")

    try:
        nodes = await fetch_all_messages()
        start = (page_number - 1) * 6
        end = page_number * 6
        results = []

        for idx, node in enumerate(nodes[start:end]):
            media_url = None
            if node.media_path:
                media_path = os.path.join(DATA_PATH, str(node.media_path))
                if os.path.exists(media_path):
                    media_url = f"/media/{os.path.basename(media_path)}"

            results.append({
                "author": node.author,
                "date": node.created_at.isoformat() if node.created_at else None,
                "text": node.content,
                "photo": media_url
            })

        response = {
            "data": results,
            "count": len(nodes),
            "session_id": session_id
        }
        logger.info(f"Returned {len(results)} nodes out of {len(nodes)}")

        return JSONResponse(content=response)

    except Exception as e:
        logger.error(f"Error in get_all_nodes: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/get_relevant_nodes/{session_id}/{query}")
async def get_relevant_nodes(session_id: str, query: str, request: Request = None):
    """
    Возвращает релевантные записи на основе запроса, включая подсвеченные фрагменты.

    Args:
        session_id (str): Идентификатор пользовательской сессии.
        query (str): Поисковый запрос.
        page_number (int): Номер страницы.
        request (Request): Объект запроса.

    Returns:
        JSONResponse: Результаты поиска с подсветкой.
    """
    logger.info(
        f"GET /get_relevant_nodes/{session_id}/'{query}' - Client IP: {request.client.host if request else 'unknown'}")

    try:
        if session_id not in session_cache:
            session_cache[session_id] = {}

        if query in session_cache[session_id]:
            nodes, highlights = session_cache[session_id][query]
            session_cache[session_id] = {query: (nodes, highlights)}
        else:
            nodes, highlights = await full_pipeline(query)
            session_cache[session_id][query] = (nodes, highlights)

        results = []

        for idx, node in enumerate(nodes):
            media_url = None
            if node["media_path"]:
                media_path = os.path.join(DATA_PATH, str(node["media_path"]))
                if os.path.exists(media_path):
                    media_url = f"/media/{os.path.basename(media_path)}"

            results.append({
                "date": node["date"],
                "text": node["content"],
                "author": node["author"],
                "hl": highlights[idx] if highlights[idx] else [],
                "photo": media_url
            })

        response = {
            "data": results,
            "count": len(nodes),
            "session_id": session_id
        }

        logger.info(f"Returned {len(results)} relevant nodes for query '{query}'")
        return JSONResponse(content=response)

    except Exception as e:
        logger.error(f"Error in get_relevant_nodes for query '{query}': {str(e)}\n{traceback.format_exc()}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    logger.info(f"Starting CV-Analyzer server on {SERVER_HOST}:{SERVER_PORT}")
    logger.info(f"Search mode: {SEARCH_MODE}")
    logger.debug(f"Media path: {relevant_media_path}")
    logger.debug(f"Data path: {DATA_PATH}")

    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
