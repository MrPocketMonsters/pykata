"""Integration tests for POST /katas/run endpoint.

Tests validate endpoint behavior with mocked AWS and subprocess responses.
"""

from unittest.mock import patch
from fastapi.testclient import TestClient
from botocore.exceptions import ClientError
import subprocess

from src.api.main import app
from src.config import settings

client = TestClient(app, raise_server_exceptions=False)


class TestKataRunSuccess:
    """Test successful kata execution scenarios."""

    def test_kata_run_executes_successfully(
        self,
        mock_boto_factory,
        mock_dynamo_get_item,
        mock_s3_get_object,
        mock_subprocess_result,
    ):
        """Test successful kata execution with valid input."""
        with (
            patch("boto3.client") as mock_boto,
            patch("src.services.execution_service.subprocess.run") as mock_subprocess,
        ):
            mock_boto.side_effect = mock_boto_factory(
                dynamo_response=mock_dynamo_get_item(),
                s3_response=mock_s3_get_object(code="print(input())"),
            )
            mock_subprocess.return_value = mock_subprocess_result(
                stdout="hello", success=True
            )

            response = client.post(
                "/katas/run",
                json={"kata_id": "kata-1", "user_input": "hello", "max_timeout": 5},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "hello" in data["stdout"]

    def test_kata_run_with_multiline_output(
        self,
        mock_boto_factory,
        mock_dynamo_get_item,
        mock_s3_get_object,
        mock_subprocess_result,
    ):
        """Test kata execution with multiline output."""
        with (
            patch("boto3.client") as mock_boto,
            patch("src.services.execution_service.subprocess.run") as mock_subprocess,
        ):
            mock_boto.side_effect = mock_boto_factory(
                dynamo_response=mock_dynamo_get_item(),
                s3_response=mock_s3_get_object(),
            )
            mock_subprocess.return_value = mock_subprocess_result(
                stdout="1\n2\n3", success=True, exec_time=55
            )

            response = client.post(
                "/katas/run",
                json={"kata_id": "kata-1", "user_input": "3", "max_timeout": 5},
            )

            assert response.status_code == 200
            assert "1\n2\n3" in response.json()["stdout"]

    def test_kata_run_respects_timeout_configuration(
        self,
        mock_boto_factory,
        mock_dynamo_get_item,
        mock_s3_get_object,
        mock_subprocess_result,
    ):
        """Test that timeout parameter is validated and capped."""
        with (
            patch("boto3.client") as mock_boto,
            patch("src.services.execution_service.subprocess.run") as mock_subprocess,
        ):
            mock_boto.side_effect = mock_boto_factory(
                dynamo_response=mock_dynamo_get_item(),
                s3_response=mock_s3_get_object(),
            )
            mock_subprocess.return_value = mock_subprocess_result(stdout="done")

            # High timeout should be capped
            response = client.post(
                "/katas/run",
                json={
                    "kata_id": "kata-1",
                    "user_input": "",
                    "max_timeout": settings.EXECUTION_TIMEOUT + 20,  # Exceeds max
                },
            )

            # Verify subprocess called with capped timeout
            assert mock_subprocess.call_args[1]["timeout"] == settings.EXECUTION_TIMEOUT
            assert response.status_code == 200


class TestKataRunErrors:
    """Test error scenarios for kata execution."""

    def test_kata_run_handles_runtime_errors(
        self,
        mock_boto_factory,
        mock_dynamo_get_item,
        mock_s3_get_object,
        mock_subprocess_result,
    ):
        """Test kata execution with runtime error in code."""
        with (
            patch("boto3.client") as mock_boto,
            patch("src.services.execution_service.subprocess.run") as mock_subprocess,
        ):
            mock_boto.side_effect = mock_boto_factory(
                dynamo_response=mock_dynamo_get_item(),
                s3_response=mock_s3_get_object(),
            )
            mock_subprocess.return_value = mock_subprocess_result(
                stderr="ValueError: Test error", success=False, exec_time=30
            )

            response = client.post(
                "/katas/run",
                json={"kata_id": "kata-1", "user_input": "", "max_timeout": 5},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "ValueError" in data["stderr"]

    def test_kata_run_handles_timeout(
        self, mock_boto_factory, mock_dynamo_get_item, mock_s3_get_object
    ):
        """Test kata execution timeout returns HTTP 408."""
        with (
            patch("boto3.client") as mock_boto,
            patch("src.services.execution_service.subprocess.run") as mock_subprocess,
        ):
            mock_boto.side_effect = mock_boto_factory(
                dynamo_response=mock_dynamo_get_item(),
                s3_response=mock_s3_get_object(),
            )
            mock_subprocess.side_effect = subprocess.TimeoutExpired(
                cmd="python", timeout=5
            )

            response = client.post(
                "/katas/run",
                json={"kata_id": "kata-1", "user_input": "", "max_timeout": 5},
            )

            assert response.status_code == 408

    def test_kata_run_handles_missing_resources(
        self, mock_boto_factory, mock_dynamo_get_item
    ):
        """Test HTTP 404 when kata or code not found."""
        # Kata not in DynamoDB
        with patch("boto3.client") as mock_boto:

            # 1) Kata missing in DynamoDB
            mock_boto.side_effect = mock_boto_factory(dynamo_response={})
            response = client.post(
                "/katas/run",
                json={"kata_id": "nonexistent", "user_input": "test", "max_timeout": 5},
            )
            assert response.status_code == 404

            # 2) Kata code missing in S3
            mock_boto.side_effect = mock_boto_factory(
                dynamo_response=mock_dynamo_get_item(),
                s3_error=ClientError(
                    {"Error": {"Code": "NoSuchKey"}},
                    "GetObject",
                ),
            )
            response2 = client.post(
                "/katas/run",
                json={"kata_id": "kata-1", "user_input": "test", "max_timeout": 5},
            )
            assert response2.status_code == 404

    def test_kata_run_handles_service_errors_and_validation(self, mock_boto_factory):
        """Test HTTP 500 for service failures and HTTP 400 for validation errors."""
        # Test DynamoDB service error
        with patch("boto3.client") as mock_boto:
            mock_boto.side_effect = mock_boto_factory(
                dynamo_error=ClientError(
                    {"Error": {"Code": "ServiceUnavailable"}},
                    "GetItem",
                )
            )
            response = client.post(
                "/katas/run",
                json={"kata_id": "kata-1", "user_input": "test", "max_timeout": 5},
            )
            assert response.status_code == 500

        # Test invalid request body validation
        response = client.post("/katas/run", json={"invalid": "data"})
        assert response.status_code == 400
