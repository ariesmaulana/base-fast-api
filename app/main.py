from fastapi import FastAPI

from app.middleware.logging import LoggingMiddleware
from app.middleware.trace_id import TraceIdMiddleware
from app.users.routers import auth_router, users_router

app = FastAPI()

app.add_middleware(LoggingMiddleware)
app.add_middleware(TraceIdMiddleware)

app.include_router(users_router)
app.include_router(auth_router)


@app.get("/")
def read_root():
    return {"Hello": "World"}
