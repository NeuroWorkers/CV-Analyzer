import asyncio

import jsonify
from flask import Flask
from configs.server_config import *
from auto_run import auto_complete_dump
from apscheduler.schedulers.background import BackgroundScheduler
from backend.question_analyzer import fetch_all_messages, question_analyzer


app = Flask(__name__)
scheduler = BackgroundScheduler()


scheduler.add_job(auto_complete_dump, 'cron', hour=SERVER_DUMP_HOUR, minute=SERVER_DUMP_MINUTE)
scheduler.start()


@app.route("/")
def home():
    return "Flask-приложение работает. Задача по расписанию запущена."


@app.route("/get_all_nodes/<int:page_number>", methods=['GET'])
async def get_all_nodes(page_number: int = 0):
    nodes = await fetch_all_messages()
    results = []
    count = 0
    for node in nodes:
        if (page_number - 1) * 6 <= count < page_number * 6:
            results.append({"author": node.author,
                            "date": node.created_at,
                            "content": node.content})
        count += 1
    return results


@app.route('/get_relevant_nodes/<query>/<int:page_number>', methods=['GET'])
def get_relevant_nodes(query: str, page_number: int = 0):
    nodes = question_analyzer(query)
    results = []
    count = 0
    for node in nodes:
        if (page_number - 1) * 6 <= count < page_number * 6:
            results.append({"author": node["author"],
                            "date": node["created_at"],
                            "content": node["content"]})
        count += 1
    return nodes


if __name__ == "__main__":
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=SERVER_DEBUG_MODE)
