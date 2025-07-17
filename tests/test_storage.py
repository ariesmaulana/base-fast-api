from psycopg import Connection
from app.users import storage as user_storage
from app.users.models import UserCreate
from app.core.logger import AppLogger
from app.dependencies.logger import get_app_logger


def test_create_user(db_conn: Connection):
    """
    Test creating a user directly in the storage layer.
    """
    user_to_create = UserCreate(
        username="storage_user", email="storage@example.com", password="password"
    )
    hashed_password = "a_very_hashed_password"
    logger = get_app_logger("test.storage.create_user")
    created_user = user_storage.create_user(
        db_conn, user_to_create, hashed_password, "dummy_trace_id", logger
    )

    assert created_user is not None
    assert created_user.email == user_to_create.email
    assert created_user.username == user_to_create.username
    assert created_user.hashed_password == hashed_password


def test_create_user_duplicate(db_conn: Connection):
    """
    Test creating a user directly in the storage layer.
    """
    user_to_create = UserCreate(
        username="storage_user", email="storage@example.com", password="password"
    )
    hashed_password = "a_very_hashed_password"
    logger = get_app_logger("test.storage.create_user_duplicate")
    created_user = user_storage.create_user(
        db_conn, user_to_create, hashed_password, "dummy_trace_id", logger
    )

    assert created_user is not None
    assert created_user.email == user_to_create.email
    assert created_user.username == user_to_create.username
    assert created_user.hashed_password == hashed_password


def test_get_user_by_email(db_conn: Connection):
    """
    Test retrieving a user by email from the storage layer.
    """
    user_to_create = UserCreate(
        username="storage_user", email="storage@example.com", password="password"
    )
    hashed_password = "a_very_hashed_password"

    logger = get_app_logger("test.storage.get_user_by_email")
    user_storage.create_user(
        db_conn, user_to_create, hashed_password, "dummy_trace_id", logger
    )

    retrieved_user = user_storage.get_user_by_email(
        db_conn, "storage@example.com", "dummy_trace_id", logger
    )
    assert retrieved_user is not None
    assert retrieved_user.email == user_to_create.email


def test_get_user_by_email_not_found(db_conn: Connection):
    """
    Test retrieving a non-existent user by email.
    """
    logger = get_app_logger("test.storage.get_user_by_email_not_found")
    retrieved_user = user_storage.get_user_by_email(
        db_conn, "nonexistent@example.com", "dummy_trace_id", logger
    )
    assert retrieved_user is None


def test_get_users(db_conn: Connection):
    """
    Test retrieving all users from the storage layer.
    """
    logger = get_app_logger("test.storage.get_users")
    # Initially, no users
    assert user_storage.get_users(db_conn, "dummy_trace_id", logger) == []

    # Add a user
    user_to_create = UserCreate(
        username="storage_user", email="storage@example.com", password="password"
    )
    user_storage.create_user(
        db_conn, user_to_create, "hashed_password_1", "dummy_trace_id", logger
    )

    # Verify one user is returned
    users = user_storage.get_users(db_conn, "dummy_trace_id", logger)
    assert len(users) == 1
    assert users[0]["email"] == "storage@example.com"
