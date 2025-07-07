import logging
import os


class MyLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        if not self.logger.hasHandlers():
            self.setup_logger(name)

    def setup_logger(self, name):
        log_file_name = f"logs/{name}_log.txt"
        os.makedirs('logs', exist_ok=True)

        handler = logging.FileHandler(log_file_name)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    def warning(self, message):
        self.logger.warning(message)

    def debug(self, message):
        self.logger.debug(message)
