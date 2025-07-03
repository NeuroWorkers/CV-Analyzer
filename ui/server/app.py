import logging
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

from configs.project_paths import *
from configs.server_config import SERVER_PORT, SERVER_HOST, SEARCH_MODE

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

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('app2.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if SEARCH_MODE == "FAISS":
        init_resources()
    yield


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
async def get_all_nodes(page_number: int = 0, request: Request = None):
    """
    Возвращает страницу с узлами (резюме) с пагинацией.

    Args:
        page_number (int): Номер страницы (начинается с 1).
        request (Request, optional): Объект запроса (не используется).

    Returns:
        JSONResponse: Список узлов с автором, датой, текстом и ссылкой на фото.
    """
    try:
        nodes = await fetch_all_messages()
        results = []
        start = (page_number - 1) * 6
        end = page_number * 6

        for idx, node in enumerate(nodes[start:end]):
            media_url = None
            if node.media_path:
                media_path = node.media_path
                current_media_path = os.path.join(DATA_PATH, str(media_path))
                if os.path.exists(current_media_path):
                    media_url = f"/media/{os.path.basename(current_media_path)}"
                    logger.info(f"media_url = {media_url}")

            results.append({
                "author": node.author,
                "date": node.created_at.isoformat() if node.created_at else None,
                "text": node.content,
                "photo": media_url
            })

        results.append({"count": len(nodes)})
        return JSONResponse(results)
    except Exception as e:
        logging.error("Произошла ошибка:\n%s", traceback.format_exc())


@app.get("/get_relevant_nodes/{query}/{page_number}")
async def get_relevant_nodes(query: str, page_number: int = 0, request: Request = None):
    """
    Возвращает релевантные узлы (резюме) по запросу с подсветкой и пагинацией.

    Args:
        query (str): Текст поискового запроса.
        page_number (int): Номер страницы (начинается с 1).
        request (Request, optional): Объект запроса (не используется).

    Returns:
        JSONResponse: Список релевантных узлов с автором, датой, текстом,
                      подсветкой и ссылкой на фото.
    """
    try:
        nodes, highlights = await full_pipeline(query)

        results = []
        start = (page_number - 1) * 6
        end = page_number * 6

        logger.info("\n\n\n HIGHLIGHTS (МАССИВ): \n\n\n")
        logger.info(highlights)
        logger.info("\n\n\n HIGHLIGHTS (МАССИВ): \n\n\n")

        for idx, node in enumerate(nodes[start:end]):
            media_url = None
            if node['media_path']:
                media_path = node['media_path']
                current_media_path = os.path.join(DATA_PATH, str(media_path))
                if os.path.exists(current_media_path):
                    media_url = f"/media/{os.path.basename(current_media_path)}"

            results.append({
                "author": node['author'],
                "date": node['created_at'].isoformat() if node['created_at'] else None,
                "text": node['content'],
                "highlight_text": highlights,
                "photo": media_url
            })
            logger.info("\n\n\n HIGHLIGHTS (ИНДЕКС): \n\n\n")
            logger.info(highlights)
            logger.info("\n\n\n HIGHLIGHTS (ИНДЕКС): \n\n\n")

        results.append({"count": len(nodes)})

        return JSONResponse(results)
    except Exception as e:
        logging.error("Произошла ошибка:\n%s", traceback.format_exc())


if __name__ == "__main__":
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
