"""
This module contains the database operations for users.
"""

from psycopg import Connection
from typing import List, Dict, Any, Optional
from .models import UserCreate, UserInDB

def get_users(conn: Connection) -> List[Dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute("SELECT id, username, email FROM users;")
        return cur.fetchall()  # result: list[dict] karena row_factory sudah diset global

def get_user_by_email(conn: Connection, email: str) -> Optional[UserInDB]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, username, email, hashed_password FROM users WHERE email = %s;",
            (email,)
        )
        row = cur.fetchone()
        if row:
            return UserInDB(**row)
        return None

def create_user(conn: Connection, user: UserCreate, hashed_password: str) -> UserInDB:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (username, email, hashed_password)
            VALUES (%s, %s, %s)
            RETURNING id, username, email, hashed_password;
            """,
            (user.username, user.email, hashed_password)
        )
        row = cur.fetchone()
        return UserInDB(**row)
