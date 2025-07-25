import threading
import time

from psycopg import Connection
from psycopg_pool import ConnectionPool

from app.dependencies.logger import get_app_logger
from app.users import common
from app.users import storage as user_storage
from app.users.models import UserCreate, UserInDB


def test_create_user_and_get_user_by_id(db_conn: Connection):
    """
    Test creating a user directly in the storage layer.
    """

    logger = get_app_logger("test.storage.create_user")
    user_to_create = UserCreate(
        username="storage_user", email="storage@example.com", password="password"
    )

    user_to_create.code = common.generate_user_code()
    hashed_password = "a_very_hashed_password"
    created_user_id = user_storage.create_user(
        db_conn, user_to_create, hashed_password, "dummy_trace_id", logger
    )

    expected_user = UserInDB(
        id=created_user_id,
        username=user_to_create.username,
        email=user_to_create.email,
        code=user_to_create.code,
        hashed_password=hashed_password,
        avatar_url=None,
    )

    retrieved_user = user_storage.get_user_by_id(
        db_conn, created_user_id, "dummy_trace_id", logger
    )

    assert created_user_id != 0
    assert retrieved_user == expected_user


def test_get_user_by_email(db_conn: Connection):
    """
    Test retrieving a user by email from the storage layer.
    """
    user_to_create = UserCreate(
        username="storage_user", email="storage@example.com", password="password"
    )
    user_to_create.code = common.generate_user_code()
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
    user_to_create.code = common.generate_user_code()
    user_storage.create_user(
        db_conn, user_to_create, "hashed_password_1", "dummy_trace_id", logger
    )

    # Verify one user is returned
    users = user_storage.get_users(db_conn, "dummy_trace_id", logger)
    assert len(users) == 1
    assert users[0].email == "storage@example.com"


def test_update_password(db_conn: Connection):
    """
    Test updating a user's password in the storage layer.
    """
    logger = get_app_logger("test.storage.update_passwords")

    # 1. Create user
    user_to_create = UserCreate(
        username="storage_user",
        email="storage@example.com",
        password="password",
    )
    user_to_create.code = common.generate_user_code()
    hashed_password = "a_very_hashed_password"

    created_user_id = user_storage.create_user(
        db_conn, user_to_create, hashed_password, "dummy_trace_id", logger
    )
    db_conn.commit()  # Ensure user is visible to other connections

    # Assume user exists
    success = user_storage.update_password(
        db_conn, created_user_id, hashed_password, "dummy_trace_id", logger
    )

    assert success is True


def test_update_password_user_not_found(db_conn: Connection):
    """
    Test updating a password for a non-existent user.
    """
    user_id = 9999  # Non-existent user ID
    hashed_password = "new_hashed_password"
    logger = get_app_logger("test.storage.update_password_user_not_found")

    success = user_storage.update_password(
        db_conn, user_id, hashed_password, "dummy_trace_id", logger
    )

    assert success is False


def test_lock_user_blocks_other_transaction(
    db_conn: Connection, db_pool: ConnectionPool
):
    """
    Test that locking a user with FOR UPDATE blocks other concurrent locks.
    """
    logger = get_app_logger("test.storage.lock_user")

    # 1. Create user
    user_to_create = UserCreate(
        username="storage_user",
        email="storage@example.com",
        password="password",
    )
    user_to_create.code = common.generate_user_code()
    hashed_password = "a_very_hashed_password"

    created_user_id = user_storage.create_user(
        db_conn, user_to_create, hashed_password, "dummy_trace_id", logger
    )
    user_id = created_user_id
    db_conn.commit()  # Ensure user is visible to other connections

    # Extract schema name to use in both transactions
    schema_name = db_conn.execute("SHOW search_path").fetchone()["search_path"]

    # Use these to coordinate between threads
    lock_acquired = threading.Event()
    second_txn_started = threading.Event()
    result = {}

    # First transaction that acquires and holds the lock
    def first_txn():
        try:
            with db_pool.connection() as conn1:
                conn1.execute(f"SET search_path TO {schema_name}")
                lock_a = user_storage.lock_user(
                    conn1, user_id, "dummy_trace_id", logger
                )
                if lock_a is not None:
                    result["first_txn_success"] = True
                    lock_acquired.set()
                    second_txn_started.wait(timeout=2)
                    time.sleep(3)
        except Exception as e:
            result["first_txn_error"] = str(e)

    # Second transaction that tries to acquire the lock while it's held
    def second_txn():
        try:
            if not lock_acquired.wait(timeout=2):
                result["second_txn_error"] = (
                    "First transaction didn't acquire lock in time"
                )
                return
            second_txn_started.set()
            with db_pool.connection() as conn2:
                conn2.execute(f"SET search_path TO {schema_name}")
                t0 = time.time()
                try:
                    lock_b = user_storage.lock_user(
                        conn2, user_id, "dummy_trace_id", logger
                    )
                    if lock_b is not None:
                        result["second_txn_success"] = True
                except Exception as e:
                    result["second_txn_error"] = str(e)
                finally:
                    t1 = time.time()
                    result["delay"] = t1 - t0
        except Exception as e:
            result["connection_error"] = str(e)

    thread1 = threading.Thread(target=first_txn)
    thread2 = threading.Thread(target=second_txn)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    for key, value in result.items():
        print(f"{key}: {value}")
    # Tidy assertions and output
    assert result.get("first_txn_success"), result.get(
        "first_txn_error", "First transaction should succeed"
    )
    assert "delay" in result, result.get(
        "second_txn_error", "Second transaction did not execute properly"
    )
    min_delay = 2.5
    assert (
        result["delay"] >= min_delay
    ), f"Expected locking delay of at least {min_delay}s, got {result['delay']:.2f} seconds"
    print(f"Test completed. Lock delay: {result['delay']:.2f}s")


def test_update_avatar_url(db_conn: Connection):
    """
    Test updating a user's avatar URL in the storage layer.
    """
    user_to_create = UserCreate(
        username="storage_user", email="storage@example.com", password="password"
    )
    user_to_create.code = common.generate_user_code()
    hashed_password = "a_very_hashed_password"

    logger = get_app_logger("test.storage.update_avatar_url")
    created_user_id = user_storage.create_user(
        db_conn, user_to_create, hashed_password, "dummy_trace_id", logger
    )

    update_avatar = user_storage.update_avatar_url(
        db_conn, created_user_id, "avatar.jpg", "dummy_trace_id", logger
    )

    expected_user = UserInDB(
        id=created_user_id,
        username=user_to_create.username,
        email=user_to_create.email,
        code=user_to_create.code,
        hashed_password=hashed_password,
        avatar_url="avatar.jpg",
    )

    retrieved_user = user_storage.get_user_by_id(
        db_conn, created_user_id, "dummy_trace_id", logger
    )

    assert update_avatar is True
    assert retrieved_user == expected_user
