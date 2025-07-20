import json
import logging
import os
import sys
from datetime import datetime

from app.settings import settings


class AppLogger:
    def __init__(self, path: str):
        self.path = path
        self.logger = logging.getLogger(path)
        self.logger.setLevel(logging.INFO)

        is_testing = "pytest" in sys.modules
        is_production = settings.ENV == "production"

        # Ensure handlers are not duplicated if logger is retrieved multiple times
        if not self.logger.handlers:
            if is_production or is_testing:
                # Production: Stream logs to external system (e.g., Grafana)
                handler = logging.StreamHandler(
                    sys.stdout
                )  # Replace with Grafana integration
                formatter = logging.Formatter(
                    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
                )
            else:
                # Development: Log to JSON files in the logs directory with date-based filenames
                current_date = datetime.now().strftime("%Y-%m-%d")
                handler = logging.FileHandler(
                    f"logs/{current_date}_development_logs.json"
                )
                formatter = logging.Formatter(
                    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
                )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.propagate = False

    def info(self, message: dict):
        log_message = {"path": self.path, **message}
        self.logger.info(json.dumps(log_message))

    def error(self, message: dict):
        log_message = {"path": self.path, **message}
        self.logger.error(json.dumps(log_message))

    def warning(self, message: dict):
        log_message = {"path": self.path, **message}
        self.logger.warning(json.dumps(log_message))


def get_logger(path: str):
    return AppLogger(path)
