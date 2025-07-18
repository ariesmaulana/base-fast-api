"""
This module contains the database operations for users.
"""

from psycopg import Connection
from typing import List, Dict, Any, Optional
from .models import UserCreate, UserInDB
from ..core.logger import AppLogger
from ..dependencies.logger import get_app_logger
from fastapi import Depends


def get_users(
    conn: Connection, trace_id: str, logger: AppLogger
) -> List[Dict[str, Any]]:
    logger.info({"trace_id": trace_id})
    with conn.cursor() as cur:
        cur.execute("SELECT id, username, email FROM users;")
        return (
            cur.fetchall()
        )  # result: list[dict] karena row_factory sudah diset global


def get_user_by_email(
    conn: Connection,
    email: str,
    trace_id: str,
    logger: AppLogger,
) -> Optional[UserInDB]:
    logger.info({"trace_id": trace_id, "email": email})
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, username, email, hashed_password FROM users WHERE email = %s;",
            (email,),
        )
        row = cur.fetchone()
        if row:
            return UserInDB(**row)
        return None


def create_user(
    conn: Connection,
    user: UserCreate,
    hashed_password: str,
    trace_id: str,
    logger: AppLogger,
) -> UserInDB:
    logger.info({"trace_id": trace_id, "email": user.email})
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (username, email, hashed_password)
            VALUES (%s, %s, %s)
            RETURNING id, username, email, hashed_password;
            """,
            (user.username, user.email, hashed_password),
        )
        row = cur.fetchone()
        return UserInDB(**row)
