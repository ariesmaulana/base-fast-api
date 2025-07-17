# Base FastAPI Project

This is a base project for a FastAPI application with user authentication.

## Project Structure

The project is structured as follows:

```
/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── database.py             # Database connection setup
│   ├── users/
│   │   ├── __init__.py
│   │   ├── models.py           # Pydantic models
│   │   ├── routers.py          # API Endpoint/handler
│   │   ├── services.py         # Service or main business logic
│   │   └── storage.py          # Raw query
│   ├── dependencies/
│   │   └── auth.py             # FastAPI dependencies for authentication
│   └── middleware/
│       └── logging.py          # Logging middleware
├── schema/
│   └── 001_create_users.sql    # Database schema files
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Test configuration
│   ├── test_services.py        # Service layer tests
│   └── test_storage.py         # Storage layer tests
├── .gitignore
├── pyproject.toml
├─��� pytest.ini
├── README.md
└── uv.lock
```

## Setup

1.  Install dependencies:
    ```bash
    uv install
    ```

2.  Set up the database URL environment variable. For local development, you can use:
    ```bash
    export DATABASE_URL="postgresql://postgres:localdb123@localhost/fast_db"
    ```
    Alternatively, you can create a `.env` file and the application will load it.

3.  Run the application:
    ```bash
    uvicorn app.main:app --reload
    ```

## API Endpoints

### Authentication

*   `POST /register`: Register a new user.
    *   **Request Body:**
        ```json
        {
          "username": "yourusername",
          "email": "user@example.com",
          "password": "yourpassword"
        }
        ```
*   `POST /login`: Log in to get an access token.
    *   **Request Body (form-data):**
        *   `username`: Your email
        *   `password`: Your password

### Users

*   `GET /users/`: Get a list of users.
*   `GET /users/me`: Get the current logged-in user.

## Testing

To run the tests, you'll need a separate test database. Set the `TEST_DATABASE_URL` environment variable:
```bash
export TEST_DATABASE_URL="postgresql://postgres:localdb123@localhost/test_db_1"
```

Then, run the tests:
```bash
pytest
```