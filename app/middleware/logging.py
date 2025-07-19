import logging
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import sys
from .trace_id import get_trace_id

# Configure logger to output JSON
log_formatter = logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(log_formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
# Prevent duplicate logs in some environments
logger.propagate = False


SENSITIVE_KEYS = [
    "password",
    "email",
    "current_password",
    "new_password",
    "confirm_password",
]


def sanitize_body(body: bytes) -> dict:
    """
    Sanitizes sensitive keys from a request or response body.
    """
    try:
        if not body:
            return {}

        data = json.loads(body)
        if not isinstance(data, dict):
            return data

        sanitized_data = {}
        for key, value in data.items():
            if key in SENSITIVE_KEYS:
                sanitized_data[key] = "[REDACTED]"
            else:
                sanitized_data[key] = value
        return sanitized_data
    except json.JSONDecodeError:
        return {"detail": "Non-JSON body, not logged"}


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        request_body_bytes = await request.body()

        # To allow the request body to be read again by the endpoint
        async def receive():
            return {"type": "http.request", "body": request_body_bytes}

        request = Request(request.scope, receive)

        response = await call_next(request)

        process_time = time.time() - start_time

        log_dict = {
            "trace_id": get_trace_id(),
            "request": {
                "method": request.method,
                "path": request.url.path,
                "body": sanitize_body(request_body_bytes),
            },
            "response": {
                "status_code": response.status_code,
            },
            "process_time_seconds": round(process_time, 4),
        }

        logger.info(json.dumps(log_dict))

        return response
