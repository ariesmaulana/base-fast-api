from fastapi import FastAPI
from app.routers import users, auth
from app.middleware.logging import LoggingMiddleware

app = FastAPI()

app.add_middleware(LoggingMiddleware)

app.include_router(users.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
def read_root():
    return {"Hello": "World"}
