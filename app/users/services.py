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

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_users(conn: Connection) -> List[Dict[str, Any]]:
    return user_storage.get_users(conn)


def create_user(conn: Connection, user: UserCreate) -> User:
    """
    Creates a user in a DB transaction. Rolls back on error.
    """
    hashed_password = pwd_context.hash(user.password)
    with conn.transaction():  # ✅ transaksi dikendalikan di sini
        db_user = user_storage.create_user(conn, user, hashed_password)
    return User(**db_user.model_dump())


def authenticate_user(conn: Connection, email: str, password: str) -> Optional[User]:
    db_user = user_storage.get_user_by_email(conn, email)
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
