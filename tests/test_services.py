from psycopg import Connection
from app.users import services as user_service
from app.users.models import UserCreate
from jwt import decode
from app import settings
from fastapi.testclient import TestClient

def test_create_user_service(db_conn: Connection):
    """
    Test the user creation service to ensure it hashes passwords
    and returns a proper User model.
    """
    user_to_create = UserCreate(username="service_user", email="service@example.com", password="plain_password")
    
    created_user = user_service.create_user(db_conn, user_to_create)
    
    assert created_user is not None
    assert created_user.email == user_to_create.email
    assert not hasattr(created_user, "password")
    assert not hasattr(created_user, "hashed_password")

    # Verify password was hashed in the DB
    from app.users import storage as user_storage
    db_user = user_storage.get_user_by_email(db_conn, user_to_create.email)
    assert db_user is not None
    assert db_user.hashed_password != "plain_password"
    assert user_service.pwd_context.verify("plain_password", db_user.hashed_password)

def test_authenticate_user_service(db_conn: Connection):
    """
    Test the user authentication service.
    """
    user_to_create = UserCreate(username="auth_user", email="auth@example.com", password="correct_password")
    user_service.create_user(db_conn, user_to_create)
    
    # Test successful authentication
    authenticated_user = user_service.authenticate_user(db_conn, user_to_create.email, "correct_password")
    assert authenticated_user is not None
    assert authenticated_user.email == user_to_create.email
    
    # Test failed authentication (wrong password)
    unauthenticated_user = user_service.authenticate_user(db_conn, user_to_create.email, "wrong_password")
    assert unauthenticated_user is None

def test_create_access_token_service():
    """
    Test the access token creation service. This test does not need DB access.
    """
    email = "test@example.com"
    token = user_service.create_access_token(data={"sub": email})
    
    assert token is not None
    decoded_token = decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded_token["sub"] == email
