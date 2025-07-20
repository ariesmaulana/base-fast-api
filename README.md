# Base FastAPI Project

This is a base project for a FastAPI application, currently only have feature user authentication.

## Project Structure

The project is structured as follows:

```
/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── settings.py             # FastAPI centralized settings
│   ├── database.py             # Database connection setup
│   ├── core/
│   │   └── logger.py           # Centralized logging utility
│   ├── users/
│   │   ├── __init__.py
│   │   ├── models.py           # Pydantic models
│   │   ├── routers.py          # API Endpoint/handler
│   │   ├── services.py         # Service or main business logic
│   │   └── storage.py          # Raw query
│   ├── dependencies/
│   │   ├── auth.py             # FastAPI dependencies for authentication
│   │   └── logger.py           # Logger dependency injection
│   └── middleware/
│       ├── logging.py          # Logging middleware
│       └── trace_id.py         # Trace ID middleware
├── schema/
│   └── 001_create_users.sql    # Database schema files
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Test configuration
│   ├── test_services.py        # Service layer tests
│   ├── test_storage.py         # Storage layer tests
│   └── test_routers.py         # Router/Handler integration tests
├── .gitignore
├── pyproject.toml
├── pytest.ini
├── README.md
└── uv.lock
```

# Install

1. Clone this repo

2. Install uv package manager

## Setup

1.  Install dependencies:
    ```bash
    uv sync
    ```

2.  Set up the database URL environment variable. For local development, you can use:
    ```bash
    export DATABASE_URL="postgresql://postgres:localdb123@localhost/fast_db"
    ```
    Alternatively, you can create a `.env` file and the application will load it.
    
    Example `.env` file:
    ```
    DATABASE_URL="postgresql://postgres:localdb123@localhost/fast_db"
    TEST_DATABASE_URL="postgresql://postgres:localdb123@localhost/test_db_1"
    ```

3. Run the test:
   ```
   uv run pytest
   ```
4.  Run the application:
    ```bash
    uv run uvicorn app.main:app --reload
    ```

## Centralized Logging

This project uses a centralized logging utility (`app/core/logger.py`) and FastAPI's dependency injection system (`app/dependencies/logger.py`) to ensure consistent log formatting and easier debugging. The `AppLogger` class provides a simplified interface for logging messages with a predefined structure, including the `path` of the log origin.

Example usage in service/storage layer functions:
```python
from fastapi import Depends
from ..core.logger import AppLogger
from ..dependencies.logger import get_app_logger

# For service layer
def get_service_logger(logger: AppLogger = Depends(lambda: get_app_logger("service"))):
    return logger

def my_service_function(logger: AppLogger = Depends(get_service_logger)):
    logger.info({"key": "value"})

# For storage layer
def get_users(conn: Connection, trace_id: str, logger: AppLogger) -> List[Dict[str, Any]]:
    logger.info({"trace_id": trace_id})
    with conn.cursor() as cur:
        cur.execute("SELECT id, username, email FROM users;")
        return cur.fetchall()

# Storage layer functions now use the logger passed from the service layer instead of re-initializing it.
```

This will produce a log entry similar to:
```json
{"timestamp": "...", "level": "INFO", "message": "{"path": "service.my_function", "key": "value"}"}
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
    *   **Error Responses:** Include a `trace_id` for debugging.
*   `POST /login`: Log in to get an access token.
    *   **Request Body (form-data):**
        *   `username`: Your email
        *   `password`: Your password
    *   **Error Responses:** Include a `trace_id` for debugging.
*   `POST /refresh`: Refresh an access token.
    *   **Request Body:**
        ```json
        {
          "refresh_token": "your_refresh_token"
        }
        ```
    *   **Error Responses:** Include a `trace_id` for debugging.

### Trace ID Middleware

A `TraceIdMiddleware` is implemented to inject a unique `trace_id` into every request. This `trace_id` is:
- Included in the `X-Trace-ID` response header.
- Propagated through the application layers (handler, service, storage) for consistent logging.
- Included in error responses to aid in debugging.

Example log entry with `trace_id`:
```json
{"timestamp": "...", "level": "INFO", "message": "{"trace_id": "...", "request": {...}, "response": {...}, "process_time_seconds": ...}"}
```

Example error response with `trace_id`:
```json
{
  "detail": {
    "message": "Email already registered",
    "trace_id": "..."
  }
}
```

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
uv run pytest
```

### Integration Tests

Integration tests (`tests/test_routers.py`) verify the end-to-end flow through the API endpoints, including middleware, service, and storage interactions. These tests ensure that the `trace_id` is correctly handled in requests, responses, and error details.

### TODO
- Refactor Trace and Logger
- Add more basic functionality:
    - CRUD users
    - Authorization
- Dockerize