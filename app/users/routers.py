from psycopg import Connection
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from .models import User, UserCreate
from . import services
from ..database import get_db_dependency
from . import storage
from datetime import timedelta
from typing import List
from ..dependencies.auth import get_current_user
from ..middleware.trace_id import get_trace_id
from ..core.logger import AppLogger
from ..dependencies.logger import get_app_logger

auth_router = APIRouter(tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])


@auth_router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(
    user: UserCreate,
    conn: Connection = Depends(get_db_dependency),
    logger: AppLogger = Depends(lambda: get_app_logger("router.register_user")),
):
    """
    Register a new user.
    """
    trace_id = get_trace_id()
    db_user = storage.get_user_by_email(
        conn, email=user.email, trace_id=trace_id, logger=logger
    )
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Email already registered", "trace_id": trace_id},
        )
    return services.create_user(conn, user, trace_id, logger)


@auth_router.post("/login")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn: Connection = Depends(get_db_dependency),
    logger: AppLogger = Depends(
        lambda: get_app_logger("router.login_for_access_token")
    ),
):
    """
    Authenticate user and return an access token.
    """
    trace_id = get_trace_id()
    user = services.authenticate_user(
        conn,
        email=form_data.username,
        password=form_data.password,
        trace_id=trace_id,
        logger=logger,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Incorrect username or password", "trace_id": trace_id},
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=services.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = services.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@users_router.get("/", response_model=List[User])
def read_users(
    conn: Connection = Depends(get_db_dependency),
    logger: AppLogger = Depends(lambda: get_app_logger("router.read_users")),
) -> List[User]:
    """
    Retrieve all users.
    """
    trace_id = get_trace_id()
    return services.get_users(conn, trace_id, logger)


@users_router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get the current logged-in user.
    """
    return current_user
