from pydantic import BaseModel

class UserBase(BaseModel):
    """
    Base model for user attributes.
    """
    username: str
    email: str

class UserCreate(UserBase):
    """
    Model for creating a new user, includes password.
    """
    password: str

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