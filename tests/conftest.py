"""
conftest.py - Schema-per-test isolation for FastAPI

Each test runs in its own PostgreSQL schema to ensure full isolation.
"""

import os
import glob
import uuid
from pathlib import Path
from typing import Generator
import pytest
from psycopg import Connection
from psycopg_pool import ConnectionPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db_dependency
from psycopg.rows import dict_row
import time

@pytest.fixture(scope="module")
def db_pool() -> Generator[ConnectionPool, None, None]:
    """
    Session-scoped fixture to create and share a database pool.
    """
    database_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:localdb123@localhost/test_db_1"
    )

    pool = ConnectionPool(
        conninfo=database_url,
        min_size=1,
        max_size=20,
        kwargs={"row_factory": dict_row},
        open=True,  
    )

    yield pool
    pool.close()


@pytest.fixture(scope="function")
def db_conn(db_pool: ConnectionPool) -> Generator[Connection, None, None]:
    """
    Function-scoped fixture that creates a unique schema per test,
    applies migrations, and drops the schema after test completes.
    """
    schema_name = f"test_{uuid.uuid4().hex[:8]}"
    with db_pool.connection() as conn:
        conn.execute(f"CREATE SCHEMA {schema_name};")
        conn.execute(f"SET search_path TO {schema_name};")

        # Apply migrations
        schema_path = Path("schema")
        sql_files = sorted(glob.glob(str(schema_path / "*.sql")))
        for sql_file in sql_files:
            with open(sql_file, 'r', encoding='utf-8') as f:
                conn.execute(f.read())
                
        conn.commit()

        try:
            yield conn
        finally:
            conn.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE;")
            conn.commit()


@pytest.fixture(scope="function")
def test_app_with_db(db_conn: Connection) -> Generator[TestClient, None, None]:
    """
    Provides a FastAPI TestClient that uses the test database schema.
    """
    app.dependency_overrides[get_db_dependency] = lambda: db_conn

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
