import asyncio
import time
from datetime import timedelta
from typing import List

import jwt
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from psycopg import Connection

from app.settings import settings

from ..core.logger import AppLogger
from ..core.r2_storage import upload_file_to_r2
from ..database import get_db_dependency
from ..dependencies.auth import get_current_user
from ..dependencies.logger import get_app_logger
from ..middleware.trace_id import get_trace_id
from . import services
from .models import Token, User, UserCreate, UserUpdatePassword

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
    new_user, err = services.create_user(conn, user, trace_id, logger)
    if err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(err), "trace_id": trace_id},
        )
    return new_user


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
    user, err = services.authenticate_user(
        conn,
        email=form_data.username,
        password=form_data.password,
        trace_id=trace_id,
        logger=logger,
    )
    if err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Incorrect username or password", "trace_id": trace_id},
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=services.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = services.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(minutes=services.REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = services.create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }


@auth_router.post("/refresh")
def refresh_access_token(
    token: Token,
    conn: Connection = Depends(get_db_dependency),
    logger: AppLogger = Depends(lambda: get_app_logger("router.refresh_access_token")),
):
    """
    Refresh the access token.
    """
    trace_id = get_trace_id()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"message": "Could not validate credentials", "trace_id": trace_id},
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("type") != "refresh":
            raise credentials_exception
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user, err = services.get_user_by_email(conn, email, trace_id, logger)
    if err:
        raise credentials_exception
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


@auth_router.post(
    "/update-password", response_model=User, status_code=status.HTTP_200_OK
)
def update_password(
    user: UserUpdatePassword,
    conn: Connection = Depends(get_db_dependency),
    current_user: User = Depends(get_current_user),
    logger: AppLogger = Depends(lambda: get_app_logger("router.update_password")),
):
    """
    Update user password.
    """
    trace_id = get_trace_id()
    _, err = services.update_password(
        conn, current_user.id, user.old_password, user.new_password, trace_id, logger
    )
    if err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(err), "trace_id": trace_id},
        )
    user, err = services.get_user_by_id(conn, current_user.id, trace_id, logger)
    if err is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "User not found", "trace_id": trace_id},
        )
    return user


@users_router.post("/me/avatar", response_model=User)
async def upload_avatar(
    file: UploadFile = File(...),
    conn: Connection = Depends(get_db_dependency),
    current_user: User = Depends(get_current_user),
    logger: AppLogger = Depends(lambda: get_app_logger("router.upload_avatar")),
):
    """
    Upload a new avatar for the current user. Handles file upload to R2 and updates avatar_url.
    """
    trace_id = get_trace_id()
    ext = file.filename.split(".")[-1] if "." in file.filename else ""
    filename = f"avatars/user_{current_user.id}_{int(time.time())}.{ext}"
    # Ensure file.file is at the beginning
    file.file.seek(0)
    # Ensure bucket is set, raise clear error if not
    bucket = settings.R2_BUCKET_NAME
    if not bucket:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "R2_BUCKET_NAME environment variable is not set",
                "trace_id": trace_id,
            },
        )
    loop = asyncio.get_running_loop()
    public_url = await loop.run_in_executor(
        None,
        lambda: upload_file_to_r2(
            file.file, filename, bucket=bucket, content_type=file.content_type
        ),
    )
    success, err = services.update_avatar_url(
        conn, current_user.id, public_url, trace_id, logger
    )
    if err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(err), "trace_id": trace_id},
        )
    user, err = services.get_user_by_id(conn, current_user.id, trace_id, logger)
    if err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "User not found", "trace_id": trace_id},
        )
    return user
