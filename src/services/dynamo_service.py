"""DynamoDB service for kata metadata storage."""

from __future__ import annotations

from typing import List, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.config import settings
from src.logger import get_logger, log_call, log_timer
from src.models.kata import KataMetadata

logger = get_logger(__name__)


class DynamoServiceError(Exception):
    """Base exception for DynamoDB service errors."""


class TableNotFoundError(DynamoServiceError):
    """Raised when the configured DynamoDB table does not exist."""


class ItemNotFoundError(DynamoServiceError):
    """Raised when a requested item is not found in the table."""


def _get_client():
    """Create a DynamoDB client using settings configuration."""

    return boto3.client(
        "dynamodb",
        endpoint_url=settings.AWS_ENDPOINT,
        region_name=settings.AWS_DEFAULT_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def _raise_from_client_error(exc: ClientError, table_name: str) -> None:
    """Map a ClientError to a service-specific exception."""

    error_code = exc.response.get("Error", {}).get("Code", "")
    if error_code in {"ResourceNotFoundException", "ResourceNotFound"}:
        raise TableNotFoundError(f"DynamoDB table '{table_name}' not found") from exc
    raise DynamoServiceError(f"DynamoDB operation failed: {error_code}") from exc


def _from_item(item: dict) -> KataMetadata:
    """Convert DynamoDB item to KataMetadata."""

    return KataMetadata(
        id=item["id"]["S"],
        title=item["title"]["S"],
        description=item.get("description", {}).get("S", ""),
        tags=[tag["S"] for tag in item.get("tags", {}).get("L", [])],
        difficulty=item["difficulty"]["S"],
        s3_key=item["s3_key"]["S"],
        sample_input=item.get("sample_input", {}).get("S", ""),
        sample_output=item.get("sample_output", {}).get("S", ""),
    )


def _to_item(metadata: KataMetadata) -> dict:
    """Convert KataMetadata to DynamoDB item structure."""

    return {
        "id": {"S": metadata.id},
        "title": {"S": metadata.title},
        "description": {"S": metadata.description},
        "tags": {"L": [{"S": tag} for tag in metadata.tags]},
        "difficulty": {"S": metadata.difficulty},
        "s3_key": {"S": metadata.s3_key},
        "sample_input": {"S": metadata.sample_input},
        "sample_output": {"S": metadata.sample_output},
    }


@log_call
def get_kata(
    kata_id: str,
    *,
    client=None,
    table_name: Optional[str] = None,
) -> KataMetadata:
    """Retrieve a kata by id.

    Raises:
        TableNotFoundError: When the DynamoDB table does not exist.
        ItemNotFoundError: When the kata does not exist in the table.
        DynamoServiceError: For other DynamoDB-related errors.
    """

    dynamo = client or _get_client()
    table = table_name or settings.DYNAMODB_TABLE_NAME

    try:
        with log_timer("dynamo_get_item"):
            response = dynamo.get_item(TableName=table, Key={"id": {"S": kata_id}})
    except ClientError as exc:  # pragma: no cover - exercised via mapping helper
        _raise_from_client_error(exc, table)
    except BotoCoreError as exc:
        raise DynamoServiceError("Failed to fetch kata") from exc

    item = response.get("Item")
    if not item:
        raise ItemNotFoundError(f"Kata with id '{kata_id}' not found")

    return _from_item(item)


@log_call
def list_katas(
    limit: int,
    offset: int = 0,
    *,
    client=None,
    table_name: Optional[str] = None,
) -> List[KataMetadata]:
    """List kata metadata with simple offset/limit paging."""

    if limit < 0 or offset < 0:
        raise ValueError("limit and offset must be non-negative")

    dynamo = client or _get_client()
    table = table_name or settings.DYNAMODB_TABLE_NAME
    scan_limit = max(limit + offset, 1)

    try:
        with log_timer("dynamo_scan"):
            response = dynamo.scan(TableName=table, Limit=scan_limit)
    except ClientError as exc:  # pragma: no cover - exercised via mapping helper
        _raise_from_client_error(exc, table)
    except BotoCoreError as exc:
        raise DynamoServiceError("Failed to list katas") from exc

    items = response.get("Items", [])
    sliced = items[offset : offset + limit if limit else None]
    return [_from_item(item) for item in sliced]


@log_call
def create_kata(
    metadata: KataMetadata,
    *,
    client=None,
    table_name: Optional[str] = None,
) -> bool:
    """Create a new kata record.

    Returns True when the item is successfully stored.
    """

    dynamo = client or _get_client()
    table = table_name or settings.DYNAMODB_TABLE_NAME

    try:
        dynamo.put_item(TableName=table, Item=_to_item(metadata))
        return True
    except ClientError as exc:  # pragma: no cover - exercised via mapping helper
        _raise_from_client_error(exc, table)
    except BotoCoreError as exc:
        raise DynamoServiceError("Failed to create kata") from exc

    return False


@log_call
def check_health(client=None, table_name: str = None) -> bool:
    """
    Check if DynamoDB service is accessible.

    Attempts to describe the configured DynamoDB table to verify connectivity
    and table availability.

    Args:
        client: Optional boto3 DynamoDB client (for testing).
        table_name: Optional table name override (defaults to settings).

    Returns:
        bool: True if the table is accessible, False otherwise.
    """
    dynamo = client or _get_client()
    table = table_name or settings.DYNAMODB_TABLE_NAME

    try:
        dynamo.describe_table(TableName=table)
        logger.debug(f"DynamoDB health check passed for table '{table}'")
        return True
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        logger.warning(
            f"DynamoDB health check failed for table '{table}': {error_code}"
        )
        return False
    except BotoCoreError as exc:
        logger.warning(f"DynamoDB health check failed: {exc}")
        return False
    except Exception as exc:
        logger.warning(f"DynamoDB health check failed with unexpected error: {exc}")
        return False
