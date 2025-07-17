from psycopg import Connection
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from ..database import get_db_dependency
from ..users import storage as user_storage
from .. import settings
from ..users.models import User
from ..middleware.trace_id import get_trace_id
from ..core.logger import AppLogger
from .logger import get_app_logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    conn: Connection = Depends(get_db_dependency),
    logger: AppLogger = Depends(lambda: get_app_logger("auth.get_current_user")),
) -> User:
    """
    Dependency to get the current user from a JWT token.
    """
    trace_id = get_trace_id()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"message": "Could not validate credentials", "trace_id": trace_id},
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    user = user_storage.get_user_by_email(
        conn, email=email, trace_id=trace_id, logger=logger
    )

    if user is None:
        raise credentials_exception

    return User(**user.model_dump())
