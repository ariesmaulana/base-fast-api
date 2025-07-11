from psycopg import Connection
from fastapi import APIRouter, Depends
from app.models.user import User
from app.services import user_service
from app.dependencies import get_current_user
from app.database import get_db_dependency
from typing import List

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/", response_model=List[User])
def read_users(conn: Connection = Depends(get_db_dependency)) -> List[User]:
    """
    Retrieve all users.
    """
    return user_service.get_users(conn)

@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get the current logged-in user.
    """
    return current_user
