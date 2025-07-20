import os
from contextlib import contextmanager

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.settings import settings

# Global connection pool
pool: ConnectionPool = None


def get_db_pool() -> ConnectionPool:
    """
    Returns the global connection pool, creating it if necessary.
    """
    global pool
    if pool is None:
        pool = ConnectionPool(
            conninfo=f"{settings.DATABASE_URL}?options=-c%20search_path%3Dpublic",
            min_size=1,
            max_size=10,
            kwargs={"row_factory": dict_row},
            open=True,
        )
    return pool


def set_db_pool(db_pool: ConnectionPool):
    """
    Sets the global connection pool. Used for testing.
    """
    global pool
    pool = db_pool


@contextmanager
def get_db_connection_context():
    """
    Provides a database connection from the pool as a context manager.
    This is what the service layer will use.
    """
    db_pool = get_db_pool()
    with db_pool.connection() as conn:
        yield conn


def get_db_dependency():
    """
    A FastAPI dependency that provides a database connection from the pool.
    This is what the router layer will use.
    """
    db_pool = get_db_pool()
    with db_pool.connection() as conn:
        yield conn
