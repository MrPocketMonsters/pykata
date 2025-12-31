"""Unit tests for POST /katas/run endpoint (execute kata)."""

from fastapi.testclient import TestClient

from src.api.main import app
from src.config import settings
from src.models.kata import ExecutionResult
from src.services.dynamo_service import (
    DynamoServiceError,
    TableNotFoundError,
    ItemNotFoundError,
)
from src.services.s3_service import (
    S3ServiceError,
    BucketNotFoundError,
    ObjectNotFoundError,
)


client = TestClient(app, raise_server_exceptions=False)


class TestRunKataEndpointResponses:
    """Tests for POST /katas/run endpoint successful responses."""

    def test_code_execution_returns_expected_result(
        self, monkeypatch, kata_metadata, kata_execution, execution_result, kata_code
    ):
        """Test successful code execution returns expected result."""
        monkeypatch.setattr(
            "src.api.main.__fetch_kata_metadata",
            lambda kata_id: kata_metadata,
        )
        monkeypatch.setattr("src.api.main.__fetch_kata_code", lambda s3_key: kata_code)
        monkeypatch.setattr(
            "src.api.main.execute_kata",
            lambda code, input_data, timeout: execution_result,
        )

        resp = client.post("/katas/run", json=kata_execution.model_dump())
        assert resp.status_code == 200
        data = resp.json()
        assert data == execution_result.model_dump()

    def test_bad_request_on_invalid_payload(self):
        """Test that invalid request payloads return HTTP 400 Bad Request."""

        # 1) Missing required field 'user_input'
        invalid_payload = {
            "kata_id": "kata-1",
            # "user_input": "Expected output",
            "max_timeout": 3,
        }

        resp = client.post("/katas/run", json=invalid_payload)
        assert resp.status_code == 400  # Bad Request

        # 2) Wrong data type for 'max_timeout'
        invalid_payload2 = {
            "kata_id": "kata-1",
            "user_input": "Expected output",
            "max_timeout": "three",  # Should be an integer
        }

        resp2 = client.post("/katas/run", json=invalid_payload2)
        assert resp2.status_code == 400  # Bad Request

    def test_timeout_limits_are_enforced(
        self, monkeypatch, kata_metadata, kata_code, execution_result
    ):
        """Test that execution timeout limits are correctly enforced."""
        monkeypatch.setattr(
            "src.api.main.__fetch_kata_metadata",
            lambda kata_id: kata_metadata,
        )
        monkeypatch.setattr("src.api.main.__fetch_kata_code", lambda s3_key: kata_code)

        # Store the timeout passed to execute_kata for verification on each call
        captured_timeouts = []

        def stub_execute_kata(code, input_data, timeout):
            """Stub that captures timeout and returns dummy result."""
            captured_timeouts.append(timeout)
            return execution_result

        monkeypatch.setattr("src.api.main.execute_kata", stub_execute_kata)

        # 1) Excessive timeout
        excessive_timeout_payload = {
            "kata_id": "kata-1",
            "user_input": "Expected output",
            "max_timeout": settings.EXECUTION_TIMEOUT + 10,  # Exceeds max
        }
        resp = client.post("/katas/run", json=excessive_timeout_payload)
        assert resp.status_code == 200
        assert captured_timeouts[-1] == settings.EXECUTION_TIMEOUT

        # 2) Negative timeout
        negative_timeout_payload = {
            "kata_id": "kata-1",
            "user_input": "Expected output",
            "max_timeout": -5,  # Negative
        }
        resp2 = client.post("/katas/run", json=negative_timeout_payload)
        assert resp2.status_code == 200
        assert captured_timeouts[-1] == 0

    def test_execution_timeout_maps_to_408(
        self, monkeypatch, kata_metadata, kata_code, kata_execution
    ):
        """Test that execution timeouts return HTTP 408 Request Timeout."""
        monkeypatch.setattr(
            "src.api.main.__fetch_kata_metadata",
            lambda kata_id: kata_metadata,
        )
        monkeypatch.setattr("src.api.main.__fetch_kata_code", lambda s3_key: kata_code)

        monkeypatch.setattr(
            "src.api.main.execute_kata",
            lambda code, input_data, timeout: ExecutionResult(
                success=False,
                stdout="",
                stderr="Execution timed out.",
                execution_time_ms=0,
            ),
        )

        resp = client.post("/katas/run", json=kata_execution.model_dump())
        assert resp.status_code == 408  # Request Timeout
        data = resp.json()
        assert data["detail"] == "Request Timeout"


class TestRunKataEndpointExceptions:
    """Tests for POST /katas/run endpoint error handling."""

    def test_dynamo_errors_map_to_http_errors(self, monkeypatch, kata_execution):
        """Verify DynamoDB service errors map to appropriate HTTP errors."""

        # 1) Generic DynamoDB service error
        monkeypatch.setattr(
            "src.api.main.__fetch_kata_metadata",
            lambda kata_id: (_ for _ in ()).throw(DynamoServiceError("DynamoDB error")),
        )

        resp = client.post("/katas/run", json=kata_execution.model_dump())
        assert resp.status_code == 500
        data = resp.json()
        assert data["detail"] == "Internal Server Error"

        # 2) Table not found error
        monkeypatch.setattr(
            "src.api.main.__fetch_kata_metadata",
            lambda kata_id: (_ for _ in ()).throw(
                TableNotFoundError("Table not found")
            ),
        )

        resp2 = client.post("/katas/run", json=kata_execution.model_dump())
        assert resp2.status_code == 500
        data2 = resp2.json()
        assert data2["detail"] == "Internal Server Error"

    def test_dynamo_item_not_found_maps_to_404(self, monkeypatch, kata_execution):
        """Verify item not found error maps to HTTP 404 Not Found."""
        monkeypatch.setattr(
            "src.api.main.__fetch_kata_metadata",
            lambda kata_id: (_ for _ in ()).throw(ItemNotFoundError("Kata not found")),
        )

        resp = client.post("/katas/run", json=kata_execution.model_dump())
        assert resp.status_code == 404
        data = resp.json()
        assert data["detail"] == "Not Found"

    def test_s3_errors_map_to_http_errors(
        self, monkeypatch, kata_metadata, kata_execution
    ):
        """Verify S3 service errors map to appropriate HTTP errors."""

        # 1) Generic S3 service error
        monkeypatch.setattr(
            "src.api.main.__fetch_kata_metadata",
            lambda kata_id: kata_metadata,
        )
        monkeypatch.setattr(
            "src.api.main.__fetch_kata_code",
            lambda s3_key: (_ for _ in ()).throw(S3ServiceError("S3 error")),
        )

        resp = client.post("/katas/run", json=kata_execution.model_dump())
        assert resp.status_code == 500
        data = resp.json()
        assert data["detail"] == "Internal Server Error"

        # 2) Bucket not found error
        monkeypatch.setattr(
            "src.api.main.__fetch_kata_code",
            lambda s3_key: (_ for _ in ()).throw(
                BucketNotFoundError("Bucket not found")
            ),
        )

        resp2 = client.post("/katas/run", json=kata_execution.model_dump())
        assert resp2.status_code == 500
        data2 = resp2.json()
        assert data2["detail"] == "Internal Server Error"

    def test_s3_object_not_found_maps_to_404(
        self, monkeypatch, kata_metadata, kata_execution
    ):
        """Verify S3 object not found error maps to HTTP 404 Not Found."""
        monkeypatch.setattr(
            "src.api.main.__fetch_kata_metadata",
            lambda kata_id: kata_metadata,
        )
        monkeypatch.setattr(
            "src.api.main.__fetch_kata_code",
            lambda s3_key: (_ for _ in ()).throw(
                ObjectNotFoundError("Kata code not found")
            ),
        )

        resp = client.post("/katas/run", json=kata_execution.model_dump())
        assert resp.status_code == 404
        data = resp.json()
        assert data["detail"] == "Not Found"

    def test_exceptions_do_not_expose_internal_details(
        self, monkeypatch, kata_metadata, kata_code, execution_result, kata_execution
    ):
        """Verify that generic exceptions do not expose internal error details."""

        # 1) DynamoDB generic exception
        monkeypatch.setattr(
            "src.api.main.__fetch_kata_metadata",
            lambda kata_id: (_ for _ in ()).throw(Exception("Internal DynamoDB error")),
        )

        resp = client.post("/katas/run", json=kata_execution.model_dump())
        assert resp.status_code == 500
        data = resp.json()
        assert data["detail"] == "Internal Server Error"
        assert "Internal DynamoDB error" not in str(data)

        # 2) S3 generic exception
        monkeypatch.setattr(
            "src.api.main.__fetch_kata_metadata",
            lambda kata_id: kata_metadata,
        )
        monkeypatch.setattr(
            "src.api.main.__fetch_kata_code",
            lambda s3_key: (_ for _ in ()).throw(Exception("Internal S3 error")),
        )

        resp2 = client.post("/katas/run", json=kata_execution.model_dump())
        assert resp2.status_code == 500
        data2 = resp2.json()
        assert data2["detail"] == "Internal Server Error"
        assert "Internal S3 error" not in str(data2)

        # 3) Execution generic exception
        monkeypatch.setattr(
            "src.api.main.__fetch_kata_metadata",
            lambda kata_id: kata_metadata,
        )
        monkeypatch.setattr("src.api.main.__fetch_kata_code", lambda s3_key: kata_code)
        monkeypatch.setattr(
            "src.api.main.execute_kata",
            lambda code, input_data, timeout: (_ for _ in ()).throw(
                Exception("Execution error")
            ),
        )

        resp3 = client.post("/katas/run", json=kata_execution.model_dump())
        assert resp3.status_code == 500
        data3 = resp3.json()
        assert data3["detail"] == "Internal Server Error"
        assert "Execution error" not in str(data3)
