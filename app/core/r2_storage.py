"""
R2 (S3-compatible) storage utility for file uploads.
"""

from typing import Optional

import boto3
from botocore.client import Config

from app.settings import Settings

settings = Settings()


def get_r2_client() -> boto3.client:
    """
    Returns a boto3 S3 client configured for Cloudflare R2.
    """
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name=getattr(settings, "R2_REGION", "auto"),
    )


def upload_file_to_r2(
    file_obj,
    filename: str,
    bucket: Optional[str] = None,
    content_type: Optional[str] = None,
) -> str:
    """
    Uploads a file-like object to R2 and returns the public URL.

    Args:
        file_obj: File-like object to upload.
        filename (str): The key (path) to use in the bucket.
        bucket (Optional[str]): The R2 bucket name. Defaults to settings.R2_BUCKET_NAME.
        content_type (Optional[str]): Content type for the file.

    Returns:
        str: The public URL of the uploaded file.
    """
    bucket = bucket or settings.R2_BUCKET_NAME
    client = get_r2_client()
    extra_args = {"ACL": "public-read"}
    if content_type:
        extra_args["ContentType"] = content_type
    client.upload_fileobj(file_obj, bucket, filename, ExtraArgs=extra_args)
    public_url = f"{settings.R2_PUBLIC_BASE_URL.rstrip('/')}/{filename}"
    return public_url
