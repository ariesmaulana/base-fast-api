import os
from psycopg import Connection
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from jwt import encode, decode
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

from .models import UserCreate, User
from . import storage as user_storage
from .. import settings
from ..core.logger import AppLogger
from ..dependencies.logger import get_app_logger


from ..dependencies.logger import get_app_logger
from fastapi import Depends


def get_service_logger(logger: AppLogger = Depends(lambda: get_app_logger("service"))):
    return logger


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def get_users(
    conn: Connection, trace_id: str, logger: AppLogger = Depends(get_service_logger)
) -> List[Dict[str, Any]]:
    logger.info({"trace_id": trace_id})
    return user_storage.get_users(conn, trace_id, logger)


def create_user(
    conn: Connection,
    user: UserCreate,
    trace_id: str,
    logger: AppLogger = Depends(get_service_logger),
) -> User:
    logger.info({"trace_id": trace_id, "email": user.email})
    hashed_password = pwd_context.hash(user.password)
    with conn.transaction():
        db_user = user_storage.create_user(
            conn, user, hashed_password, trace_id, logger
        )
    return User(**db_user.model_dump())


def authenticate_user(
    conn: Connection,
    email: str,
    password: str,
    trace_id: str,
    logger: AppLogger = Depends(get_service_logger),
) -> Optional[User]:
    logger.info({"trace_id": trace_id, "email": email})
    db_user = user_storage.get_user_by_email(conn, email, trace_id, logger)
    if not db_user or not pwd_context.verify(password, db_user.hashed_password):
        return None
    return User(**db_user.model_dump())


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
