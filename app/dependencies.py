from psycopg import Connection
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.services import user_service
from app.models.user import User
from app.database import get_db_dependency
from app.storage import user_storage

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), conn: Connection = Depends(get_db_dependency)) -> User:
    """
    Dependency to get the current user from a JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, user_service.SECRET_KEY, algorithms=[user_service.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = user_storage.get_user_by_email(conn, email=email)
    
    if user is None:
        raise credentials_exception
    
    return User(**user.model_dump())
