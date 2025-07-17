import os

# Database settings
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:localdb123@localhost/fast_db"
)

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "a_super_secret_key_that_should_be_in_env")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
