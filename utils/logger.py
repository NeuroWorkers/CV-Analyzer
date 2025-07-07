import logging
import os
from logging.handlers import RotatingFileHandler


class MyLogger:
    def __init__(self, name, level=logging.INFO, console=True, max_bytes=10*1024*1024, backup_count=5):
        self.logger = logging.getLogger(name)
        if not self.logger.hasHandlers():
            self.setup_logger(name, level, console, max_bytes, backup_count)

    def setup_logger(self, name, level, console, max_bytes, backup_count):
        log_file_name = f"logs/{name}_log.txt"
        os.makedirs('logs', exist_ok=True)

        # Настройка уровня логирования
        self.logger.setLevel(level)

        # Форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Файловый хандлер с ротацией
        file_handler = RotatingFileHandler(
            log_file_name, 
            maxBytes=max_bytes, 
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Консольный хандлер (опционально)
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    def warning(self, message):
        self.logger.warning(message)

    def debug(self, message):
        self.logger.debug(message)
