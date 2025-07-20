"""
This module contains the database operations for users.
"""

from typing import List, Optional

from psycopg import Connection

from ..core.logger import AppLogger
from .models import UserCreate, UserInDB


def get_users(conn: Connection, trace_id: str, logger: AppLogger) -> List[UserInDB]:
    logger.info({"trace_id": trace_id})
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, username, email, code, hashed_password, avatar_url FROM users;"
        )
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
            "SELECT id, username, email, code, hashed_password, avatar_url FROM users WHERE email = %s;",
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
            "SELECT id, username, email, code, hashed_password, avatar_url FROM users WHERE id = %s;",
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
) -> int:
    logger.info({"trace_id": trace_id, "email": user.email})
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (username, email, code, hashed_password)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (user.username, user.email, user.code, hashed_password),
        )
        row = cur.fetchone()
        if row and "id" in row:
            return row["id"]
        return 0


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
            "SELECT id, username, email, code, hashed_password, avatar_url FROM users WHERE id = %s FOR UPDATE;",
            (user_id,),
        )
        row = cur.fetchone()
        if row:
            return UserInDB(**row)
        return None


def update_avatar_url(
    conn: Connection,
    user_id: int,
    avatar_url: str,
    trace_id: str,
    logger: AppLogger,
) -> bool:
    logger.info({"trace_id": trace_id, "user_id": user_id, "avatar_url": avatar_url})
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET avatar_url = %s WHERE id = %s;",
            (avatar_url, user_id),
        )
        if cur.rowcount == 0:
            logger.warning(
                {"trace_id": trace_id, "user_id": user_id, "message": "User not found"}
            )
            return False
        return True
