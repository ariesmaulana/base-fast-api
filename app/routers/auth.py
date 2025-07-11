from psycopg import Connection
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import User, UserCreate
from app.services import user_service
from app.database import get_db_dependency
from app.storage import user_storage
from datetime import timedelta

router = APIRouter()

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, conn: Connection = Depends(get_db_dependency)):
    """
    Register a new user.
    """
    db_user = user_storage.get_user_by_email(conn, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    return user_service.create_user(conn, user)


@router.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), conn: Connection = Depends(get_db_dependency)):
    """
    Authenticate user and return an access token.
    """
    user = user_service.authenticate_user(conn, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=user_service.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = user_service.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
