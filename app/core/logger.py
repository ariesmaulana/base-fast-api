import logging
import json
import sys


class AppLogger:
    def __init__(self, path: str):
        self.path = path
        self.logger = logging.getLogger(path)
        self.logger.setLevel(logging.INFO)

        # Ensure handlers are not duplicated if logger is retrieved multiple times
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.propagate = False

    def info(self, message: dict):
        log_message = {"path": self.path, **message}
        self.logger.info(json.dumps(log_message))


def get_logger(path: str):
    return AppLogger(path)
