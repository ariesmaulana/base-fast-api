# Base FastAPI Project

This is a base project for a FastAPI application with user authentication.

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

*   `POST /auth/register`: Register a new user.
    *   **Request Body:**
        ```json
        {
          "username": "yourusername",
          "email": "user@example.com",
          "password": "yourpassword"
        }
        ```
*   `POST /auth/login`: Log in to get an access token.
    *   **Request Body (form-data):**
        *   `username`: Your email
        *   `password`: Your password

### Users

*   `GET /users/`: Get a list of users.

## Testing

To run the tests, you'll need a separate test database. Set the `TEST_DATABASE_URL` environment variable:
```bash
export TEST_DATABASE_URL="postgresql://postgres:localdb123@localhost/test_db_1"
```

Then, run the tests:
```bash
pytest
```
