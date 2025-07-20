import io
from unittest.mock import patch

from fastapi.testclient import TestClient
from psycopg import Connection


def test_register_user(test_app_with_db: TestClient, db_conn: Connection):
    """
    Test user registration through the API.
    """
    response = test_app_with_db.post(
        "/register",
        json={
            "username": "test_router_user",
            "email": "router@example.com",
            "password": "testpassword",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "router@example.com"
    assert "id" in data
    assert "X-Trace-ID" in response.headers


def test_register_user_duplicate_email(
    test_app_with_db: TestClient, db_conn: Connection
):
    """
    Test registration with a duplicate email.
    """
    # Register first user
    test_app_with_db.post(
        "/register",
        json={
            "username": "test_router_user_dup",
            "email": "duplicate@example.com",
            "password": "testpassword",
        },
    )

    # Attempt to register with the same email
    response = test_app_with_db.post(
        "/register",
        json={
            "username": "test_router_user_dup2",
            "email": "duplicate@example.com",
            "password": "anotherpassword",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["message"] == "Failed to create user after 5 attempts"
    assert "trace_id" in data["detail"]
    assert "X-Trace-ID" in response.headers


def test_login_for_access_token(test_app_with_db: TestClient, db_conn: Connection):
    """
    Test user login and access token retrieval.
    """
    # Register a user first
    test_app_with_db.post(
        "/register",
        json={
            "username": "login_user",
            "email": "login@example.com",
            "password": "loginpassword",
        },
    )

    # Attempt to log in
    response = test_app_with_db.post(
        "/login", data={"username": "login@example.com", "password": "loginpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert "X-Trace-ID" in response.headers


def test_login_for_access_token_incorrect_password(
    test_app_with_db: TestClient, db_conn: Connection
):
    """
    Test login with incorrect password.
    """
    # Register a user first
    test_app_with_db.post(
        "/register",
        json={
            "username": "wrong_pass_user",
            "email": "wrongpass@example.com",
            "password": "correctpassword",
        },
    )

    # Attempt to log in with wrong password
    response = test_app_with_db.post(
        "/login",
        data={"username": "wrongpass@example.com", "password": "incorrectpassword"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["message"] == "Incorrect username or password"
    assert "trace_id" in data["detail"]
    assert "X-Trace-ID" in response.headers


def test_read_users(test_app_with_db: TestClient, db_conn: Connection):
    """
    Test retrieving all users.
    """
    # Register a user first
    test_app_with_db.post(
        "/register",
        json={
            "username": "read_user_1",
            "email": "read1@example.com",
            "password": "readpassword",
        },
    )
    test_app_with_db.post(
        "/register",
        json={
            "username": "read_user_2",
            "email": "read2@example.com",
            "password": "readpassword",
        },
    )

    response = test_app_with_db.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # Assuming some users might already exist from other tests
    assert "X-Trace-ID" in response.headers


def test_read_users_me(test_app_with_db: TestClient, db_conn: Connection):
    """
    Test retrieving the current logged-in user.
    """
    # Register and login a user
    test_app_with_db.post(
        "/register",
        json={
            "username": "me_user",
            "email": "me@example.com",
            "password": "mepassword",
        },
    )
    login_response = test_app_with_db.post(
        "/login", data={"username": "me@example.com", "password": "mepassword"}
    )
    token = login_response.json()["access_token"]

    response = test_app_with_db.get(
        "/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert "X-Trace-ID" in response.headers


def test_read_users_me_unauthorized(test_app_with_db: TestClient, db_conn: Connection):
    """
    Test retrieving current user without authentication.
    """
    response = test_app_with_db.get("/users/me")
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "X-Trace-ID" in response.headers


def test_update_password(test_app_with_db: TestClient, db_conn: Connection):
    """
    Test user registration through the API.
    """
    # Register a user first
    test_app_with_db.post(
        "/register",
        json={
            "username": "read_user_1",
            "email": "read1@example.com",
            "password": "readpassword",
        },
    )

    login_response = test_app_with_db.post(
        "/login", data={"username": "read1@example.com", "password": "readpassword"}
    )
    token = login_response.json()["access_token"]

    response = test_app_with_db.post(
        "/update-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "old_password": "readpassword",
            "new_password": "newpassword",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "read1@example.com"
    assert "id" in data
    assert "X-Trace-ID" in response.headers


def test_upload_avatar(test_app_with_db: TestClient, db_conn: Connection):
    """
    Test uploading a user avatar.
    """
    # Register a user first
    test_app_with_db.post(
        "/register",
        json={
            "username": "avatar_user",
            "email": "avatar@example.com",
            "password": "avatarpassword",
        },
    )

    # Login to get access token
    login_response = test_app_with_db.post(
        "/login", data={"username": "avatar@example.com", "password": "avatarpassword"}
    )
    token = login_response.json()["access_token"]

    # Create a mock file for upload
    file_content = b"fake image content"
    file = io.BytesIO(file_content)

    # Mock the R2 storage client
    with patch(
        "app.users.routers.upload_file_to_r2", return_value="avatar/user123.jpg"
    ) as mock_upload:
        response = test_app_with_db.post(
            "/users/me/avatar",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("avatar.jpg", file, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["avatar_url"] is not None
        assert "avatar/user" in data["avatar_url"]
        assert "X-Trace-ID" in response.headers
        mock_upload.assert_called_once()


def test_upload_avatar_no_bucket(test_app_with_db: TestClient, db_conn: Connection):
    """
    Test avatar upload when R2_BUCKET_NAME is not set.
    """
    # Register a user first
    test_app_with_db.post(
        "/register",
        json={
            "username": "no_bucket_user",
            "email": "nobucket@example.com",
            "password": "nobucketpassword",
        },
    )

    # Login to get access token
    login_response = test_app_with_db.post(
        "/login",
        data={"username": "nobucket@example.com", "password": "nobucketpassword"},
    )
    token = login_response.json()["access_token"]

    # Create a mock file for upload
    file_content = b"fake image content"
    file = io.BytesIO(file_content)

    # Mock settings to simulate no bucket name
    with patch("app.users.routers.settings.R2_BUCKET_NAME", new=None):
        response = test_app_with_db.post(
            "/users/me/avatar",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("avatar.jpg", file, "image/jpeg")},
        )

        assert response.status_code == 500
        data = response.json()
        assert (
            data["detail"]["message"]
            == "R2_BUCKET_NAME environment variable is not set"
        )
        assert "trace_id" in data["detail"]
        assert "X-Trace-ID" in response.headers


def test_refresh_access_token(test_app_with_db: TestClient, db_conn: Connection):
    """
    Test refreshing the access token.
    """
    # Register a user first
    test_app_with_db.post(
        "/register",
        json={
            "username": "refresh_user",
            "email": "refresh@example.com",
            "password": "refreshpassword",
        },
    )

    # Login to get tokens
    login_response = test_app_with_db.post(
        "/login",
        data={"username": "refresh@example.com", "password": "refreshpassword"},
    )
    login_data = login_response.json()
    refresh_token = login_data["refresh_token"]
    old_access_token = login_data["access_token"]

    # Refresh the access token
    response = test_app_with_db.post(
        "/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["access_token"] != old_access_token
    assert "X-Trace-ID" in response.headers