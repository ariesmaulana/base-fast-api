"""
This module contains the database operations for users.
"""

from psycopg import Connection
from typing import List, Optional
from .models import UserCreate, UserInDB
from ..core.logger import AppLogger


def get_users(conn: Connection, trace_id: str, logger: AppLogger) -> List[UserInDB]:
    logger.info({"trace_id": trace_id})
    with conn.cursor() as cur:
        cur.execute("SELECT id, username, email, code, hashed_password FROM users;")
        rows = cur.fetchall()
        return [UserInDB(**row) for row in rows]


def get_user_by_email(
    conn: Connection,
    email: str,
    trace_id: str,
    logger: AppLogger,
) -> Optional[UserInDB]:
    logger.info({"trace_id": trace_id, "email": email})
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, username, email, code, hashed_password FROM users WHERE email = %s;",
            (email,),
        )
        row = cur.fetchone()
        if row:
            return UserInDB(**row)
        return None

def get_user_by_id(
    conn: Connection,
    user_id: int,
    trace_id: str,
    logger: AppLogger,
) -> Optional[UserInDB]:
    logger.info({"trace_id": trace_id, "user_id": user_id})
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, username, email, code, hashed_password FROM users WHERE id = %s;",
            (user_id,),
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
            INSERT INTO users (username, email, code, hashed_password)
            VALUES (%s, %s, %s, %s)
            RETURNING id, username, email, code, hashed_password;
            """,
            (user.username, user.email, user.code, hashed_password),
        )
        row = cur.fetchone()
        return UserInDB(**row)


def update_password(
    conn: Connection,
    user_id: int,
    hashed_password: str,
    trace_id: str,
    logger: AppLogger,
) -> bool:
    logger.info({"trace_id": trace_id, "user_id": user_id})
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET hashed_password = %s WHERE id = %s;",
            (hashed_password, user_id),
        )
        if cur.rowcount == 0:
            logger.warning(
                {"trace_id": trace_id, "user_id": user_id, "message": "User not found"}
            )
            return False
        return True


def lock_user(
    conn: Connection,
    user_id: int,
    trace_id: str,
    logger: AppLogger,
) -> Optional[UserInDB]:
    logger.info({"trace_id": trace_id, "id": user_id})
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, username, email, code, hashed_password FROM users WHERE id = %s FOR UPDATE;",
            (user_id,),
        )
        row = cur.fetchone()
        if row:
            return UserInDB(**row)
        return None
