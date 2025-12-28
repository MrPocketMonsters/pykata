"""DynamoDB and S3 integration service for kata code and metadata management.

Provides upload/download operations for user kata code with error handling.
"""

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from src.config import settings
from src.logger import get_logger, log_call

logger = get_logger(__name__)


class S3ServiceError(Exception):
    """Base exception for S3 service errors."""


class BucketNotFoundError(S3ServiceError):
    """Raised when the S3 bucket does not exist."""


class ObjectNotFoundError(S3ServiceError):
    """Raised when the requested object (key) does not exist in the bucket."""


def _get_client():
    """Create and return a boto3 S3 client from settings.

    The client uses the endpoint configured in settings to work transparently
    with LocalStack (dev/test) or AWS (prod).
    """
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_ENDPOINT,
        region_name=settings.AWS_DEFAULT_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def _raise_from_client_error(error: ClientError, operation: str) -> None:
    """Map ClientError to domain-specific exceptions.

    Args:
        error: The boto3 ClientError to map
        operation: Description of the operation (for logging)

    Raises:
        BucketNotFoundError: If the bucket does not exist
        ObjectNotFoundError: If the object (key) does not exist
        S3ServiceError: For other S3 errors
    """
    error_code = error.response.get("Error", {}).get("Code", "Unknown")

    if error_code == "NoSuchBucket":
        raise BucketNotFoundError(
            f"S3 bucket '{settings.S3_BUCKET_NAME}' does not exist"
        )
    elif error_code == "NoSuchKey":
        raise ObjectNotFoundError(f"S3 object not found: {operation}")
    else:
        raise S3ServiceError(f"S3 error during {operation}: {error}")


@log_call
def upload_kata_code(kata_id: str, code: str) -> str:
    """Upload kata code to S3 and return the generated S3 key.

    Args:
        kata_id: Unique kata identifier
        code: The kata code content to upload

    Returns:
        The S3 key (path) where the code was stored

    Raises:
        BucketNotFoundError: If the S3 bucket does not exist
        S3ServiceError: For other S3 errors
    """
    s3_key = f"katas/{kata_id}.py"

    try:
        client = _get_client()
        client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key,
            Body=code,
        )
    except ClientError as e:
        _raise_from_client_error(e, f"upload_kata_code(kata_id={kata_id})")
    except BotoCoreError as e:
        raise S3ServiceError(f"S3 communication error during upload: {e}")

    logger.info(f"Uploaded kata code to {s3_key}")
    return s3_key


@log_call
def download_kata_code(s3_key: str) -> str:
    """Download kata code from S3 by key.

    Args:
        s3_key: The S3 key (path) of the object to retrieve

    Returns:
        The content of the code file

    Raises:
        BucketNotFoundError: If the S3 bucket does not exist
        ObjectNotFoundError: If the object (key) does not exist
        S3ServiceError: For other S3 errors
    """
    try:
        client = _get_client()
        response = client.get_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key,
        )
        code: str = response["Body"].read().decode("utf-8")
    except ClientError as e:
        _raise_from_client_error(e, f"download_kata_code(s3_key={s3_key})")
    except BotoCoreError as e:
        raise S3ServiceError(f"S3 communication error during download: {e}")

    logger.info(f"Downloaded kata code from {s3_key}")
    return code
