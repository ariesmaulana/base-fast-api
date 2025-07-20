import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = str(uuid.uuid4())
        trace_id_var.set(trace_id)

        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        return response


def get_trace_id() -> str:
    return trace_id_var.get()
