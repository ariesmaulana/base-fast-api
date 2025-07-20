import json
import logging
import sys
import time
from typing import Any, Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

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


def sanitize_body(request: Request, body: bytes) -> Dict[str, Any]:
    """
    Sanitizes sensitive keys from a request or response body.

    Args:
        request: The original request object
        body: Raw request body bytes

    Returns:
        Dictionary with sanitized values
    """
    if not body:
        return {}

    # Check content type
    content_type = request.headers.get("content-type", "")

    # Handle multipart form data
    if "multipart/form-data" in content_type:
        return {"detail": "Multipart form data, not logged"}

    # Handle application/x-www-form-urlencoded
    if "application/x-www-form-urlencoded" in content_type:
        try:
            form_data = body.decode("utf-8")
            if "=" in form_data:
                parts = form_data.split("&")
                form_dict = {}
                for part in parts:
                    if "=" in part:
                        key, value = part.split("=", 1)
                        if key.lower() in SENSITIVE_KEYS:
                            form_dict[key] = "[REDACTED]"
                        else:
                            form_dict[key] = value
                return {"form_data": form_dict}
        except UnicodeDecodeError:
            return {"detail": "Invalid form data encoding, not logged"}

    # Try to parse as JSON
    try:
        data = json.loads(body)
        if not isinstance(data, dict):
            return data

        sanitized_data = {}
        for key, value in data.items():
            if key.lower() in SENSITIVE_KEYS:
                sanitized_data[key] = "[REDACTED]"
            else:
                sanitized_data[key] = value
        return sanitized_data
    except (json.JSONDecodeError, UnicodeDecodeError):
        # For other content types or binary data
        return {"detail": "Non-JSON body, not logged"}


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        request_body_bytes = await request.body()

        # To allow the request body to be read again by the endpoint
        async def receive():
            return {
                "type": "http.request",
                "body": request_body_bytes,
                "more_body": False,
            }

        modified_request = Request(request.scope, receive)

        response = await call_next(modified_request)

        process_time = time.time() - start_time

        log_dict = {
            "trace_id": get_trace_id(),
            "request": {
                "method": request.method,
                "path": request.url.path,
                "body": sanitize_body(request, request_body_bytes),
            },
            "response": {
                "status_code": response.status_code,
            },
            "process_time_seconds": round(process_time, 4),
        }

        logger.info(json.dumps(log_dict))

        return response
