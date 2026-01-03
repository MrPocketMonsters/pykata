"""Integration tests for GET /katas endpoint.

Tests validate endpoint behavior with mocked AWS service responses.
"""

from unittest.mock import patch
from fastapi.testclient import TestClient
from botocore.exceptions import ClientError

from src.api.main import app

client = TestClient(app, raise_server_exceptions=False)


class TestKatasListSuccess:
    """Test successful kata listing scenarios."""

    def test_katas_list_returns_items_with_correct_structure(
        self, mock_boto_factory, mock_dynamo_scan
    ):
        """Test listing returns katas with correct structure and excludes s3_key."""
        with patch("boto3.client") as mock_boto:
            mock_boto.side_effect = mock_boto_factory(
                dynamo_response=mock_dynamo_scan(items_count=2)
            )

            response = client.get("/katas?limit=20&offset=0")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["id"] == "kata-1"
            assert "title" in data[0]
            assert "s3_key" not in data[0]  # Should be excluded

    def test_katas_list_returns_empty_when_no_katas(
        self, mock_boto_factory, mock_dynamo_scan
    ):
        """Test listing returns empty array when no katas exist."""
        with patch("boto3.client") as mock_boto:
            mock_boto.side_effect = mock_boto_factory(
                dynamo_response=mock_dynamo_scan(items_count=0)
            )

            response = client.get("/katas")

            assert response.status_code == 200
            assert response.json() == []

    def test_katas_list_handles_pagination_parameters(
        self, mock_boto_factory, mock_dynamo_scan
    ):
        """Test pagination parameters are accepted."""
        with patch("boto3.client") as mock_boto:
            mock_boto.side_effect = mock_boto_factory(
                dynamo_response=mock_dynamo_scan(items_count=4)
            )

            # Offset is beyond available items
            response = client.get("/katas?limit=2&offset=5")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
            assert len(response.json()) == 0

            # Valid limit and offset
            response = client.get("/katas?limit=2&offset=1")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
            assert len(response.json()) == 2
            assert response.json()[0]["id"] == "kata-2"


class TestKatasListErrors:
    """Test error scenarios for kata listing."""

    def test_katas_list_handles_dynamodb_errors(self, mock_boto_factory):
        """Test HTTP 500 when DynamoDB service fails."""
        with patch("boto3.client") as mock_boto:
            mock_boto.side_effect = mock_boto_factory(
                dynamo_error=ClientError(
                    {"Error": {"Code": "ServiceUnavailable"}},
                    "Scan",
                )
            )

            response = client.get("/katas")
            assert response.status_code == 500

    def test_katas_list_validates_parameters_and_handles_exceptions(
        self, mock_boto_factory
    ):
        """Test validation errors and unexpected exception handling."""
        # Test negative limit validation
        response = client.get("/katas?limit=-1")
        assert response.status_code == 400

        # Test negative offset validation
        response = client.get("/katas?offset=-5")
        assert response.status_code == 400

        # Test unexpected exception handling
        with patch("boto3.client") as mock_boto:
            mock_boto.side_effect = mock_boto_factory(
                dynamo_error=Exception("Unexpected")
            )

            response = client.get("/katas")
            assert response.status_code == 500
            # Should not expose internal details
            assert "Unexpected" not in str(response.json())
