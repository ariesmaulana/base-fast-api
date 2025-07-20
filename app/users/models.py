from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    """
    Base model for user attributes.
    """

    username: str
    email: str
    code: str = None  # Optional, will be generated if not provided
    avatar_url: Optional[str] = None  # Optional, will be generated if not provided


class UserCreate(UserBase):
    """
    Model for creating a new user, includes password.
    """

    password: str


class UserUpdatePassword(BaseModel):
    """
    Model for updating user password.
    """

    user_id: int = None
    old_password: str
    new_password: str


class User(UserBase):
    """
    Represents a user in the system (public-facing).
    """

    id: int


class UserInDB(User):
    """
    Represents a user as stored in the database, including hashed password.
    """

    hashed_password: str


class Token(BaseModel):
    refresh_token: str
