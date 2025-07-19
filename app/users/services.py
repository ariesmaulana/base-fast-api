import os
from psycopg import Connection
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta, timezone
from jwt import encode, decode
from jwt.exceptions import InvalidTokenError
from psycopg.errors import UniqueViolation
from passlib.context import CryptContext

from .models import UserCreate, User, UserUpdatePassword
from . import common
from . import storage as user_storage
from .. import settings
from ..core.logger import AppLogger
from ..dependencies.logger import get_app_logger


from ..dependencies.logger import get_app_logger
from fastapi import Depends


def get_service_logger(
    logger: AppLogger = Depends(lambda: get_app_logger("service.users")),
):
    return logger


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def get_users(
    conn: Connection, trace_id: str, logger: AppLogger = Depends(get_service_logger)
) -> List[User]:
    logger.info({"trace_id": trace_id})
    db_users = user_storage.get_users(conn, trace_id, logger)
    return [User(**db_user.model_dump()) for db_user in db_users]


def create_user(
    conn: Connection,
    user: UserCreate,
    trace_id: str,
    logger: AppLogger = Depends(get_service_logger),
) -> Union[User, Tuple[None, ValueError]]:
    logger.info({"trace_id": trace_id, "email": user.email})
    hashed_password = pwd_context.hash(user.password)

    # No need to check if email or username already exists here,
    # we already handle that in schema validation.
    # Instead, we will retry if the user creation fails due to a unique constraint violation.
    # we can check if the user already exists in the database for the err message to user
    # but if we really want to check the user existence, we must lock the operation
    # to make sure when we get the user data, it is not being created by another request
    retry_count = 0
    while retry_count < 5:
        try:
            user.code = common.generate_user_code()
            with conn.transaction():
                db_user = user_storage.create_user(
                    conn, user, hashed_password, trace_id, logger
                )
            return User(**db_user.model_dump()), None
        except (Exception, UniqueViolation) as e:
            if isinstance(e, UniqueViolation):
                retry_count += 1
                # This is the expected case for duplicate email/username/code
                logger.warning(
                    {
                        "trace_id": trace_id,
                        "context": "Unique constraint violation, retrying...",
                        "error": str(e),
                    }
                )
                continue
            else:
                logger.error(
                    {
                        "trace_id": trace_id,
                        "context": f"Unexpected error during user creation, ",
                        "error": str(e),
                    }
                )
                return None, ValueError("Unexpected error during user creation")

    logger.error(
        {
            "trace_id": trace_id,
            "context": f"Failed to create user after {retry_count} attempts",
        }
    )
    return None, ValueError(f"Failed to create user after {retry_count} attempts")


def get_user_by_email(
    conn: Connection,
    email: str,
    trace_id: str,
    logger: AppLogger = Depends(get_service_logger),
) -> Union[User, Tuple[None, ValueError]]:
    logger.info({"trace_id": trace_id, "email": email})
    db_user = user_storage.get_user_by_email(conn, email, trace_id, logger)
    if not db_user:
        return None, ValueError("User not found")
    return User(**db_user.model_dump()), None


def authenticate_user(
    conn: Connection,
    email: str,
    password: str,
    trace_id: str,
    logger: AppLogger = Depends(get_service_logger),
) -> Union[User, Tuple[None, ValueError]]:
    logger.info({"trace_id": trace_id, "email": email})
    db_user = user_storage.get_user_by_email(conn, email, trace_id, logger)
    if not db_user or not pwd_context.verify(password, db_user.hashed_password):
        return None, ValueError("Invalid email or password")
    return User(**db_user.model_dump()), None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def update_password(
    conn: Connection,
    user_id: int,
    old_password: str,
    new_password: str,
    trace_id: str,
    logger: AppLogger = Depends(get_service_logger),
) -> Union[bool, Tuple[bool, ValueError]]:
    """
    Update a user's password after verifying the old password.
    Returns (True, None) on success, (False, ValueError) on failure.
    """
    logger.info({"trace_id": trace_id, "user_id": user_id})
    with conn.transaction():
        userLock = user_storage.lock_user(conn, user_id, trace_id, logger)
        if userLock is None:
            logger.warning(
                {"trace_id": trace_id, "user_id": user_id, "message": "User not found"}
            )
            return False, ValueError("User not found")
        if not pwd_context.verify(old_password, userLock.hashed_password):
            logger.warning(
                {
                    "trace_id": trace_id,
                    "user_id": user_id,
                    "message": "Password mismatch",
                }
            )
            return False, ValueError("Password mismatch")
        hashed_password = pwd_context.hash(new_password)
        success = user_storage.update_password(
            conn, user_id, hashed_password, trace_id, logger
        )
        if success:
            return True, None
        else:
            return False, ValueError("Failed to update password")


def get_user_by_id(
    conn: Connection,
    user_id: int,
    trace_id: str,
    logger: AppLogger = Depends(get_service_logger),
) -> Union[User, Tuple[None, ValueError]]:
    logger.info({"trace_id": trace_id, "user_id": user_id})
    db_user = user_storage.get_user_by_id(conn, user_id, trace_id, logger)
    if not db_user:
        return None, ValueError("User not found")
    return User(**db_user.model_dump()), None
