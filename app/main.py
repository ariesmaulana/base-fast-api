from fastapi import FastAPI
from app.users.routers import users_router, auth_router
from app.middleware.logging import LoggingMiddleware

app = FastAPI()

app.add_middleware(LoggingMiddleware)

app.include_router(users_router)
app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"Hello": "World"}
