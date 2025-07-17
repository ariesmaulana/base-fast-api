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
    assert data["detail"]["message"] == "Email already registered"
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
