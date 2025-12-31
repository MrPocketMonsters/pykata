"""Unit tests for DynamoDB kata service."""

import pytest
from botocore.exceptions import BotoCoreError
from unittest.mock import MagicMock

from src.models.kata import KataMetadata
from src.services import dynamo_service
from src.services.dynamo_service import (
    DynamoServiceError,
    ItemNotFoundError,
    TableNotFoundError,
    create_kata,
    get_kata,
    list_katas,
    check_health,
)


def _sample_item(id_value: str = "kata-1") -> dict:
    return {
        "id": {"S": id_value},
        "title": {"S": "Two Sum"},
        "description": {"S": "Find indices that sum."},
        "tags": {"L": [{"S": "arrays"}, {"S": "math"}]},
        "difficulty": {"S": "beginner"},
        "s3_key": {"S": "katas/two-sum.py"},
        "sample_input": {"S": "1 2 3"},
        "sample_output": {"S": "3"},
    }


class TestGetKata:
    """Tests for retrieving kata metadata via Dynamo service."""

    def test_returns_metadata(self, stubbed_client):
        """Returns KataMetadata when the item exists."""
        client, stubber = stubbed_client
        stubber.add_response(
            "get_item",
            {"Item": _sample_item("kata-123")},
            {"TableName": "kata", "Key": {"id": {"S": "kata-123"}}},
        )

        result = get_kata("kata-123", client=client)

        assert isinstance(result, KataMetadata)
        assert result.id == "kata-123"
        assert result.tags == ["arrays", "math"]

    def test_missing_item_raises(self, stubbed_client):
        """Raises ItemNotFoundError when no item is returned."""
        client, stubber = stubbed_client
        stubber.add_response(
            "get_item",
            {},
            {"TableName": "kata", "Key": {"id": {"S": "missing"}}},
        )

        with pytest.raises(ItemNotFoundError):
            get_kata("missing", client=client)

    def test_table_not_found(self, stubbed_client):
        """Maps Dynamo ResourceNotFound to TableNotFoundError."""
        client, stubber = stubbed_client
        stubber.add_client_error(
            "get_item",
            service_error_code="ResourceNotFoundException",
            service_message="Table not found",
            expected_params={"TableName": "kata", "Key": {"id": {"S": "42"}}},
        )

        with pytest.raises(TableNotFoundError):
            get_kata("42", client=client)


class TestListKatas:
    """Tests for listing katas with pagination and errors."""

    def test_respects_offset_and_limit(self, stubbed_client):
        """Slices scan results according to offset and limit."""
        client, stubber = stubbed_client
        items = [_sample_item("kata-1"), _sample_item("kata-2"), _sample_item("kata-3")]
        stubber.add_response(
            "scan",
            {"Items": items},
            {"TableName": "kata", "Limit": 2},
        )

        result = list_katas(limit=1, offset=1, client=client)

        assert len(result) == 1
        assert result[0].id == "kata-2"

    def test_table_not_found(self, stubbed_client):
        """Raises TableNotFoundError when scan reports missing table."""
        client, stubber = stubbed_client
        stubber.add_client_error(
            "scan",
            service_error_code="ResourceNotFoundException",
            service_message="missing",
            expected_params={"TableName": "kata", "Limit": 1},
        )

        with pytest.raises(TableNotFoundError):
            list_katas(limit=1, client=client)


class TestCreateKata:
    """Tests for creating kata metadata records."""

    def test_success(self, stubbed_client):
        """Persists kata metadata successfully."""
        client, stubber = stubbed_client
        metadata = KataMetadata(
            id="kata-9",
            title="Palindrome",
            description="Check palindrome",
            tags=["strings"],
            difficulty="beginner",
            s3_key="katas/palindrome.py",
            sample_input="aba",
            sample_output="True",
        )

        stubber.add_response(
            "put_item",
            {},
            {"TableName": "kata", "Item": dynamo_service._to_item(metadata)},
        )

        assert create_kata(metadata, client=client) is True

    def test_table_not_found(self, stubbed_client):
        """Raises TableNotFoundError when table is missing on write."""
        client, stubber = stubbed_client
        metadata = KataMetadata(
            id="kata-10",
            title="FizzBuzz",
            description="",
            tags=["numbers"],
            difficulty="beginner",
            s3_key="katas/fizzbuzz.py",
            sample_input="3",
            sample_output="1 2 fizz",
        )

        stubber.add_client_error(
            "put_item",
            service_error_code="ResourceNotFoundException",
            service_message="missing",
            expected_params={
                "TableName": "kata",
                "Item": dynamo_service._to_item(metadata),
            },
        )

        with pytest.raises(TableNotFoundError):
            create_kata(metadata, client=client)


class TestGetKataErrorHandling:
    """Tests for error handling in get_kata (BotoCoreError, etc)."""

    def test_get_kata_botocore_error(self):
        """Raises DynamoServiceError on BotoCoreError."""
        client = MagicMock()
        client.get_item.side_effect = BotoCoreError()

        with pytest.raises(DynamoServiceError):
            get_kata("kata-1", client=client)


class TestListKatasErrorHandling:
    """Tests for error handling in list_katas (BotoCoreError, etc)."""

    def test_list_katas_botocore_error(self):
        """Raises DynamoServiceError on BotoCoreError during scan."""
        client = MagicMock()
        client.scan.side_effect = BotoCoreError()

        with pytest.raises(DynamoServiceError):
            list_katas(limit=10, client=client)


class TestCreateKataErrorHandling:
    """Tests for error handling in create_kata (BotoCoreError, etc)."""

    def test_create_kata_botocore_error(self):
        """Raises DynamoServiceError on BotoCoreError."""
        client = MagicMock()
        client.put_item.side_effect = BotoCoreError()
        metadata = KataMetadata(
            id="kata-x",
            title="Test",
            description="",
            tags=[],
            difficulty="beginner",
            s3_key="test.py",
            sample_input="",
            sample_output="",
        )

        with pytest.raises(DynamoServiceError):
            create_kata(metadata, client=client)


class TestCheckHealthDynamo:
    """Tests for DynamoDB health check."""

    def test_check_health_success(self):
        """Returns True when table is accessible."""
        client = MagicMock()
        client.describe_table.return_value = {"Table": {"TableName": "kata"}}

        result = check_health(client=client)

        assert result is True
        client.describe_table.assert_called_once()

    def test_check_health_table_not_found(self):
        """Returns False when table does not exist."""
        from botocore.exceptions import ClientError

        client = MagicMock()
        error_response = {
            "Error": {"Code": "ResourceNotFoundException", "Message": "not found"}
        }
        client.describe_table.side_effect = ClientError(error_response, "DescribeTable")

        result = check_health(client=client)

        assert result is False

    def test_check_health_botocore_error(self):
        """Returns False on BotoCoreError."""
        client = MagicMock()
        client.describe_table.side_effect = BotoCoreError()

        result = check_health(client=client)

        assert result is False

    def test_check_health_generic_exception(self):
        """Returns False on unexpected exceptions."""
        client = MagicMock()
        client.describe_table.side_effect = Exception("Unexpected error")

        result = check_health(client=client)

        assert result is False
