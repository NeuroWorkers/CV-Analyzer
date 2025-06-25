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


@app.route("/get_all_nodes", methods=['GET'])
async def get_all_nodes():
    nodes = await fetch_all_messages()
    results = []
    for node in nodes:
        results.append({"author": node.author,
                        "date": node.created_at,
                        "content": node.content})
    return results


@app.route('/get_relevant_nodes/<query>', methods=['GET'])
def get_relevant_nodes(query: str):
    nodes = question_analyzer(query)
    results = []
    for node in nodes:
        results.append({"author": node["author"],
                        "date": node["created_at"],
                        "content": node["content"]})
    return nodes


if __name__ == "__main__":
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=SERVER_DEBUG_MODE)
