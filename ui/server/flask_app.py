import jsonify
from flask import Flask
from datetime import datetime
from auto_run import auto_complete_dump
from apscheduler.schedulers.background import BackgroundScheduler
from configs.server_config import *

app = Flask(__name__)
scheduler = BackgroundScheduler()


scheduler.add_job(auto_complete_dump, 'cron', hour=SERVER_DUMP_HOUR, minute=SERVER_DUMP_MINUTE)
scheduler.start()


@app.route("/")
def home():
    return "Flask-приложение работает. Задача по расписанию запущена."


def analyze_answer():
    return jsonify({'': ''}), 200


if __name__ == "__main__":
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=SERVER_DEBUG_MODE)
