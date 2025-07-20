from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["Settings", "settings"]


class Settings(BaseSettings):
    """
    Application configuration using Pydantic BaseSettings.

    Attributes:
        DATABASE_URL (str): PostgreSQL database URL.
        TEST_DATABASE_URL (str): PostgreSQL test database URL.
        SECRET_KEY (str): Secret key for application security.
        ALGORITHM (str): Algorithm used for JWT.
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Token expiration time in minutes.
        ENV (str): Application environment.
        R2_ENDPOINT_URL (str): Cloudflare R2 endpoint URL.
        R2_ACCESS_KEY_ID (str): Cloudflare R2 access key ID.
        R2_SECRET_ACCESS_KEY (str): Cloudflare R2 secret access key.
        R2_BUCKET_NAME (str): Cloudflare R2 bucket name.
        R2_PUBLIC_BASE_URL (str): Cloudflare R2 public base URL.
        R2_REGION (str): Cloudflare R2 region.
        GEMINI_API_KEY (str): Gemini API key.
    """

    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    TEST_DATABASE_URL: str = Field(..., env="TEST_DATABASE_URL")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field(..., env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(..., env="ACCESS_TOKEN_EXPIRE_MINUTES")
    ENV: str = Field(..., env="ENV")
    R2_ENDPOINT_URL: str = Field(..., env="R2_ENDPOINT_URL")
    R2_ACCESS_KEY_ID: str = Field(..., env="R2_ACCESS_KEY_ID")
    R2_SECRET_ACCESS_KEY: str = Field(..., env="R2_SECRET_ACCESS_KEY")
    R2_BUCKET_NAME: str = Field(..., env="R2_BUCKET_NAME")
    R2_PUBLIC_BASE_URL: str = Field(..., env="R2_PUBLIC_BASE_URL")
    R2_REGION: str = Field(..., env="R2_REGION")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
