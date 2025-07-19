from psycopg.errors import UniqueViolation
from unittest.mock import patch
from psycopg import Connection
from app.users import services as user_service
from app.users.models import UserCreate, UserInDB
from jwt import decode
from app import settings
from fastapi.testclient import TestClient
from app.core.logger import AppLogger
from app.dependencies.logger import get_app_logger


def test_create_user_service(db_conn: Connection):
    """
    Test the user creation service to ensure it hashes passwords
    and returns a proper User model.
    """
    user_to_create = UserCreate(
        username="service_user", email="service@example.com", password="plain_password"
    )

    logger = get_app_logger("test.service.create_user")
    created_user, err = user_service.create_user(
        db_conn, user_to_create, "dummy_trace_id", logger
    )

    assert err is None
    assert created_user is not None
    assert created_user.email == user_to_create.email
    assert not hasattr(created_user, "password")
    assert not hasattr(created_user, "hashed_password")

    # Verify password was hashed in the DB
    from app.users import storage as user_storage

    db_user = user_storage.get_user_by_email(
        db_conn, user_to_create.email, "dummy_trace_id", logger
    )
    assert db_user is not None
    assert db_user.hashed_password != "plain_password"
    assert user_service.pwd_context.verify("plain_password", db_user.hashed_password)


def test_authenticate_user_service(db_conn: Connection):
    """
    Test the user authentication service.
    """
    user_to_create = UserCreate(
        username="auth_user", email="auth@example.com", password="correct_password"
    )
    logger = get_app_logger("test.service.authenticate_user")
    user_service.create_user(db_conn, user_to_create, "dummy_trace_id", logger)

    # Test successful authentication
    authenticated_user, err = user_service.authenticate_user(
        db_conn, user_to_create.email, "correct_password", "dummy_trace_id", logger
    )
    assert err is None
    assert authenticated_user is not None
    assert authenticated_user.email == user_to_create.email

    # Test failed authentication (wrong password)
    unauthenticated_user, err = user_service.authenticate_user(
        db_conn, user_to_create.email, "wrong_password", "dummy_trace_id", logger
    )
    assert unauthenticated_user is None
    assert err is not None


def test_create_access_token_service():
    """
    Test the access token creation service. This test does not need DB access.
    """
    email = "test@example.com"
    token = user_service.create_access_token(data={"sub": email})

    assert token is not None
    decoded_token = decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded_token["sub"] == email


def test_create_user_with_retry(db_conn: Connection):
    """
    Test that the create_user service retries on failure.
    """
    user_to_create = UserCreate(
        username="retry_user", email="retry@example.com", password="password"
    )
    logger = get_app_logger("test.service.retry")

    # Mock the storage layer to simulate database errors
    with patch("app.users.storage.create_user") as mock_create_user:
        # Simulate failure on the first 2 attempts, then success
        mock_create_user.side_effect = [
            UniqueViolation("DB error 1"),
            UniqueViolation("DB error 2"),
            UserInDB(
                id=1,
                username=user_to_create.username,
                email=user_to_create.email,
                code="testcode",
                hashed_password="hashed_password",
            ),
        ]

        created_user, err = user_service.create_user(
            db_conn, user_to_create, "dummy_trace_id", logger
        )

        # Assert that the service retried 3 times
        assert mock_create_user.call_count == 3
        assert err is None
        assert created_user is not None
        assert created_user.email == user_to_create.email


def test_get_user_by_email_service(db_conn: Connection):
    """
    Test the get user by email service.
    """
    user_to_create = UserCreate(
        username="get_user_service",
        email="get_user@example.com",
        password="password",
    )
    logger = get_app_logger("test.service.get_user_by_email")
    user_service.create_user(db_conn, user_to_create, "dummy_trace_id", logger)

    # Test found
    found_user, err = user_service.get_user_by_email(
        db_conn, user_to_create.email, "dummy_trace_id", logger
    )
    assert err is None
    assert found_user is not None
    assert found_user.email == user_to_create.email

    # Test not found
    not_found_user, err = user_service.get_user_by_email(
        db_conn, "nonexistent@example.com", "dummy_trace_id", logger
    )
    assert isinstance(err, ValueError)
    assert str(err) == 'User not found'
    assert not_found_user is None


def test_update_password_service(db_conn: Connection):
    """
    Test the update password service.
    """
    user_to_create = UserCreate(
        username="get_user_service",
        email="get_user@example.com",
        password="password",
    )
    logger = get_app_logger("test.service.get_user_by_email")
    user_service.create_user(db_conn, user_to_create, "dummy_trace_id", logger)

    # Test found
    found_user, err = user_service.get_user_by_email(
        db_conn, user_to_create.email, "dummy_trace_id", logger
    )
    assert err is None

    result, err = user_service.update_password(
        db_conn, found_user.id, "password", "new_password", "dummy_trace_id", logger
    )
    assert result is True
    assert err is None

def test_get_user_by_id_service(db_conn: Connection):
    """
    Test the get user by ID service.
    """
    user_to_create = UserCreate(
        username="get_user_service",
        email="get_user@example.com",
        password="password",
    )
    logger = get_app_logger("test.service.get_user_by_email")
    new_user, err = user_service.create_user(db_conn, user_to_create, "dummy_trace_id", logger)
    assert err is None

    # Test found
    found_user, err = user_service.get_user_by_id(
        db_conn, 1, "dummy_trace_id", logger
    )
    assert err is None
    assert found_user is not None
    assert found_user.email == user_to_create.email

    # Test not found
    not_found_user, err = user_service.get_user_by_id(
        db_conn, 99, "dummy_trace_id", logger
    )
    assert isinstance(err, ValueError)
    assert str(err) == 'User not found'
    assert not_found_user is None