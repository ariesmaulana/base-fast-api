import os
from psycopg import Connection
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext

from app.models.user import UserCreate, User
from app.storage import user_storage

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "a_super_secret_key_that_should_be_in_env")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


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
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
