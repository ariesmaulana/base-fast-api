from psycopg import Connection
from app.storage import user_storage
from app.models.user import UserCreate

def test_create_user(db_conn: Connection):
    """
    Test creating a user directly in the storage layer.
    """
    user_to_create = UserCreate(username="storage_user", email="storage@example.com", password="password")
    hashed_password = "a_very_hashed_password"
    
    created_user = user_storage.create_user(db_conn, user_to_create, hashed_password)
    
    assert created_user is not None
    assert created_user.email == user_to_create.email
    assert created_user.username == user_to_create.username
    assert created_user.hashed_password == hashed_password

def test_create_user_duplicate(db_conn: Connection):
    """
    Test creating a user directly in the storage layer.
    """
    user_to_create = UserCreate(username="storage_user", email="storage@example.com", password="password")
    hashed_password = "a_very_hashed_password"
    
    created_user = user_storage.create_user(db_conn, user_to_create, hashed_password)
    
    assert created_user is not None
    assert created_user.email == user_to_create.email
    assert created_user.username == user_to_create.username
    assert created_user.hashed_password == hashed_password

def test_get_user_by_email(db_conn: Connection):
    """
    Test retrieving a user by email from the storage layer.
    """
    user_to_create = UserCreate(username="storage_user", email="storage@example.com", password="password")
    hashed_password = "a_very_hashed_password"
    
    user_storage.create_user(db_conn, user_to_create, hashed_password)
    
    retrieved_user = user_storage.get_user_by_email(db_conn, "storage@example.com")
    assert retrieved_user is not None
    assert retrieved_user.email == user_to_create.email

def test_get_user_by_email_not_found(db_conn: Connection):
    """
    Test retrieving a non-existent user by email.
    """
    retrieved_user = user_storage.get_user_by_email(db_conn, "nonexistent@example.com")
    assert retrieved_user is None

def test_get_users(db_conn: Connection):
    """
    Test retrieving all users from the storage layer.
    """
    # Initially, no users
    assert user_storage.get_users(db_conn) == []
    
    # Add a user
    user_to_create = UserCreate(username="storage_user", email="storage@example.com", password="password")
    user_storage.create_user(db_conn, user_to_create, "hashed_password_1")
    
    # Verify one user is returned
    users = user_storage.get_users(db_conn)
    assert len(users) == 1
    assert users[0]["email"] == "storage@example.com"
