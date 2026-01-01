"""Integration tests for GET /katas/{kata_id} endpoint.

Tests validate endpoint behavior with mocked DynamoDB and S3 responses.
"""

import textwrap
from unittest.mock import patch
from fastapi.testclient import TestClient
from botocore.exceptions import ClientError

from src.api.main import app

client = TestClient(app, raise_server_exceptions=False)


class TestSingleKataSuccess:
    """Test successful single kata retrieval scenarios."""

    def test_single_kata_returns_complete_data(
        self, mock_boto_factory, mock_dynamo_get_item, mock_s3_get_object
    ):
        """Test retrieving a single kata returns complete metadata and code."""
        with patch("boto3.client") as mock_boto:
            mock_boto.side_effect = mock_boto_factory(
                dynamo_response=mock_dynamo_get_item(kata_id="kata-123"),
                s3_response=mock_s3_get_object(code="print('hello')"),
            )

            response = client.get("/katas/kata-123")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "kata-123"
            assert data["title"] == "Test Kata"
            assert data["code"] == "print('hello')"
            assert "s3_key" not in data

    def test_single_kata_with_multiline_code(
        self, mock_boto_factory, mock_dynamo_get_item, mock_s3_get_object
    ):
        """Test kata retrieval with multiline code."""
        code = textwrap.dedent(
            """
            def factorial(n):
                if n <= 1:
                    return 1
                return n * factorial(n-1)
            """
        )
        with patch("boto3.client") as mock_boto:
            mock_boto.side_effect = mock_boto_factory(
                dynamo_response=mock_dynamo_get_item(),
                s3_response=mock_s3_get_object(code=code),
            )

            response = client.get("/katas/kata-1")

            assert response.status_code == 200
            assert len(response.json()["code"].splitlines()) == 5
            assert "def factorial" in response.json()["code"]

    def test_single_kata_with_empty_tags(
        self, mock_boto_factory, mock_dynamo_get_item, mock_s3_get_object
    ):
        """Test kata retrieval with empty tags list."""
        with patch("boto3.client") as mock_boto:
            mock_boto.side_effect = mock_boto_factory(
                dynamo_response=mock_dynamo_get_item(tags=[]),
                s3_response=mock_s3_get_object(),
            )

            response = client.get("/katas/kata-1")

            assert response.status_code == 200
            assert response.json()["tags"] == []


class TestSingleKataErrors:
    """Test error scenarios for single kata retrieval."""

    def test_single_kata_not_found_in_dynamodb(self, mock_boto_factory):
        """Test HTTP 404 when kata ID does not exist."""
        with patch("boto3.client") as mock_boto:
            mock_boto.side_effect = mock_boto_factory(dynamo_response={})

            response = client.get("/katas/nonexistent")

            assert response.status_code == 404

    def test_single_kata_s3_errors(self, mock_boto_factory, mock_dynamo_get_item):
        """Test HTTP 404 when kata code is missing from S3."""
        with patch("boto3.client") as mock_boto:

            # 1) Kata missing in DynamoDB
            mock_boto.side_effect = mock_boto_factory(dynamo_response={})
            response = client.get("/katas/kata-1")
            assert response.status_code == 404

            # 2) Kata code missing in S3
            mock_boto.side_effect = mock_boto_factory(
                dynamo_response=mock_dynamo_get_item(),
                s3_error=ClientError(
                    {"Error": {"Code": "NoSuchKey"}},
                    "GetObject",
                ),
            )
            response = client.get("/katas/kata-1")
            assert response.status_code == 404

    def test_single_kata_service_errors(self, mock_boto_factory):
        """Test HTTP 500 for DynamoDB and S3 service failures."""
        # Test DynamoDB error
        with patch("boto3.client") as mock_boto:
            mock_boto.side_effect = mock_boto_factory(
                dynamo_error=ClientError(
                    {"Error": {"Code": "ServiceUnavailable", "Message": "Boom"}},
                    "GetItem",
                )
            )

            response = client.get("/katas/kata-1")

            assert response.status_code == 500
            assert "Internal Server Error" in response.text
            # Insure internal error details are not exposed
            assert "ServiceUnavailable" not in response.text
            assert "Boom" not in response.text
