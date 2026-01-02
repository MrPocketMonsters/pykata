"""Pytest configuration and shared fixtures for all tests."""

import boto3
import pytest
from botocore.stub import Stubber
from pydantic_settings import SettingsConfigDict
from unittest.mock import MagicMock


def pytest_collection_modifyitems(items):
    """Apply markers to tests based on their file location.

    Unit tests (tests/unit/*) get @pytest.mark.unit
    Integration tests (tests/integration/*) get @pytest.mark.integration
    End-to-end tests (tests/e2e/*) get @pytest.mark.e2e
    """
    for item in items:
        file_path = str(item.fspath).replace("\\", "/")
        if "/unit/" in file_path:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in file_path:
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in file_path:
            item.add_marker(pytest.mark.e2e)


@pytest.fixture
def clean_env(monkeypatch):
    """Fixture to clean environment variables and disable .env file loading.

    This ensures that tests read actual defaults instead of values from .env file.
    - Removes all configuration environment variables
    - Patches Settings class to not load .env file
    - Provides clean slate for testing default behavior
    """

    # Define all configuration environment variables
    env_vars = [
        "APP_NAME",
        "APP_ENV",
        "LOG_LEVEL",
        "DEBUG",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_DEFAULT_REGION",
        "AWS_ENDPOINT",
        "AWS_S3_ENDPOINT",
        "DYNAMODB_TABLE_NAME",
        "S3_BUCKET_NAME",
        "LAMBDA_TIMEOUT",
        "EXECUTION_TIMEOUT",
        "app_name",
        "app_env",
        "log_level",
        "debug",  # Lowercase versions too
    ]

    # Remove all environment variables to ensure we test defaults
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)

    # Patch the Settings model to not load .env file
    # Import here to avoid circular imports
    from src.config import Settings

    original_config = Settings.model_config

    # Create new config without env_file
    new_config = SettingsConfigDict(
        env_file=None,  # Disable .env file loading
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    monkeypatch.setattr(Settings, "model_config", new_config)

    yield monkeypatch

    # Restore original config
    monkeypatch.setattr(Settings, "model_config", original_config)


@pytest.fixture(autouse=True)
def force_valid_logging(monkeypatch):
    """Ensure LOG_LEVEL is valid and .env is ignored during tests.

    Prevents validation errors when a developer has an invalid LOG_LEVEL in a local .env.
    Applies to every test to avoid accidental leakage of developer-specific env values.
    """

    # Always disable .env loading for tests
    from src.config import Settings

    new_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )
    monkeypatch.setattr(Settings, "model_config", new_config)

    # Force a valid LOG_LEVEL so validation passes even if .env had bad value
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    yield


@pytest.fixture
def stubbed_client():
    """Provide a Stubber-backed DynamoDB client so tests run without real AWS calls.

    Yields a tuple of (client, stubber) so tests can register expected responses and
    assertions while avoiding network traffic or live AWS credentials.
    """

    client = boto3.client(
        "dynamodb",
        region_name="us-east-1",
        endpoint_url="http://localhost:4566",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    stubber = Stubber(client)
    stubber.activate()
    try:
        yield client, stubber
    finally:
        stubber.deactivate()


@pytest.fixture
def stubbed_s3_client():
    """Provide a Stubber-backed S3 client so tests run without real AWS calls.

    Yields a tuple of (client, stubber) so tests can register expected responses and
    assertions while avoiding network traffic or live AWS credentials.
    """

    client = boto3.client(
        "s3",
        region_name="us-east-1",
        endpoint_url="http://localhost:4566",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    stubber = Stubber(client)
    stubber.activate()
    try:
        yield client, stubber
    finally:
        stubber.deactivate()


@pytest.fixture(scope="module")
def ensure_dynamo_available():
    """Provide a DynamoDB client for integration tests.

    Assumes the endpoint is available (CI ensures this via job ordering).
    Integration tests run only in dev environment with LocalStack via CI.
    """
    from src.config import settings

    client = boto3.client(
        "dynamodb",
        endpoint_url=settings.AWS_ENDPOINT,
        region_name=settings.AWS_DEFAULT_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    return client


@pytest.fixture(scope="module")
def ensure_s3_available():
    """Provide an S3 client for integration tests.

    Assumes the endpoint is available (CI ensures this via job ordering).
    Integration tests run only in dev environment with LocalStack via CI.
    """
    from src.config import settings

    client = boto3.client(
        "s3",
        endpoint_url=settings.AWS_ENDPOINT,
        region_name=settings.AWS_DEFAULT_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    return client


@pytest.fixture(scope="module")
def ensure_lambda_available():
    """Provide a Lambda client for integration/e2e tests.

    Assumes the endpoint is available (CI ensures this via job ordering).
    Integration tests run only in dev environment with LocalStack via CI.
    """
    from src.config import settings

    client = boto3.client(
        "lambda",
        endpoint_url=settings.AWS_ENDPOINT,
        region_name=settings.AWS_DEFAULT_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    return client


@pytest.fixture
def mock_dynamo_health_up(monkeypatch):
    """Mock DynamoDB health check to return healthy (True)."""
    monkeypatch.setattr(
        "src.api.main.check_dynamo_health",
        lambda: True,
    )


@pytest.fixture
def mock_dynamo_health_down(monkeypatch):
    """Mock DynamoDB health check to return unhealthy (False)."""
    monkeypatch.setattr(
        "src.api.main.check_dynamo_health",
        lambda: False,
    )


@pytest.fixture
def mock_s3_health_up(monkeypatch):
    """Mock S3 health check to return healthy (True)."""
    monkeypatch.setattr(
        "src.api.main.check_s3_health",
        lambda: True,
    )


@pytest.fixture
def mock_s3_health_down(monkeypatch):
    """Mock S3 health check to return unhealthy (False)."""
    monkeypatch.setattr(
        "src.api.main.check_s3_health",
        lambda: False,
    )


# ============================================================================
# Fixtures for API endpoint tests
# ============================================================================


@pytest.fixture
def kata_metadata_factory():
    """Factory fixture to create KataMetadata instances for testing."""
    from src.models.kata import KataMetadata

    def _make_kata(idx: int) -> KataMetadata:
        return KataMetadata(
            id=f"kata-{idx}",
            title=f"Title {idx}",
            description=f"Desc {idx}",
            tags=["arrays", "strings"],
            difficulty="beginner",
            s3_key=f"katas/kata-{idx}.py",
            sample_input="",
            sample_output="",
        )

    return _make_kata


@pytest.fixture
def kata_metadata(kata_metadata_factory):
    """Fixture providing a default kata metadata instance."""
    return kata_metadata_factory(1)


@pytest.fixture
def kata_execution():
    """Fixture providing a default kata execution request."""
    from src.models.kata import KataExecution

    return KataExecution(kata_id="kata-1", user_input="Expected output", max_timeout=3)


@pytest.fixture
def execution_result():
    """Fixture providing a default execution result."""
    from src.models.kata import ExecutionResult

    return ExecutionResult(
        success=True, stdout="Expected output", stderr="", execution_time_ms=123
    )


@pytest.fixture
def kata_code():
    """Fixture providing default kata code."""
    return "print(input())"


# ============================================================================
# Integration test fixtures for mocking AWS and subprocess
# ============================================================================


@pytest.fixture
def mock_dynamo_get_item():
    """Factory fixture to create mock DynamoDB get_item responses."""

    def _create_response(kata_id="kata-1", title="Test Kata", tags=None):
        if tags is None:
            tags = ["test"]
        return {
            "Item": {
                "id": {"S": kata_id},
                "title": {"S": title},
                "description": {"S": f"Description for {kata_id}"},
                "tags": {"L": [{"S": tag} for tag in tags]},
                "difficulty": {"S": "beginner"},
                "s3_key": {"S": f"katas/{kata_id}.py"},
                "sample_input": {"S": "test input"},
                "sample_output": {"S": "test output"},
            }
        }

    return _create_response


@pytest.fixture
def mock_dynamo_scan():
    """Factory fixture to create mock DynamoDB scan responses."""

    def _create_response(items_count=2):
        items = []
        for i in range(items_count):
            items.append(
                {
                    "id": {"S": f"kata-{i+1}"},
                    "title": {"S": f"Kata {i+1}"},
                    "description": {"S": f"Description {i+1}"},
                    "tags": {"L": [{"S": "test"}]},
                    "difficulty": {"S": "beginner"},
                    "s3_key": {"S": f"katas/kata-{i+1}.py"},
                    "sample_input": {"S": "input"},
                    "sample_output": {"S": "output"},
                }
            )
        return {"Items": items, "Count": len(items)}

    return _create_response


@pytest.fixture
def mock_s3_get_object():
    """Factory fixture to create mock S3 get_object responses."""

    def _create_response(code="print(input())"):
        return {"Body": MagicMock(read=lambda: code.encode("utf-8"))}

    return _create_response


@pytest.fixture
def mock_subprocess_result():
    """Factory fixture to create mock subprocess results."""

    def _create_result(stdout="output", stderr="", success=True, exec_time=50):
        result = MagicMock()
        result.returncode = 0 if success else 1
        result.stdout = stdout
        # Add execution metadata markers for proper parsing
        metadata = f"__EXECUTION_TIME__:{exec_time}\n__SUCCESS__:{success}"
        result.stderr = f"{stderr}\n{metadata}" if stderr else metadata
        return result

    return _create_result


@pytest.fixture
def mock_boto_factory():
    """Factory fixture to create mock boto3 clients with dynamo and s3."""

    def _create_mock(
        dynamo_response=None, s3_response=None, dynamo_error=None, s3_error=None
    ):
        """Create mock boto3 client factory.

        Args:
            dynamo_response: Response for DynamoDB operations (get_item, scan, etc.)
            s3_response: Response for S3 get_object
            dynamo_error: Exception to raise for DynamoDB operations
            s3_error: Exception to raise for S3 operations
        """
        mock_clients = {}

        def client_factory(service_name, **kwargs):
            if service_name == "dynamodb":
                if "dynamodb" not in mock_clients:
                    mock_clients["dynamodb"] = MagicMock()
                    if dynamo_error:
                        mock_clients["dynamodb"].get_item.side_effect = dynamo_error
                        mock_clients["dynamodb"].scan.side_effect = dynamo_error
                    elif dynamo_response is not None:
                        # Check if response is explicitly empty dict (not found case)
                        if isinstance(dynamo_response, dict) and not dynamo_response:
                            mock_clients["dynamodb"].get_item.return_value = {}
                            mock_clients["dynamodb"].scan.return_value = {}
                        else:
                            mock_clients["dynamodb"].get_item.return_value = (
                                dynamo_response
                            )
                            mock_clients["dynamodb"].scan.return_value = dynamo_response
                return mock_clients["dynamodb"]
            elif service_name == "s3":
                if "s3" not in mock_clients:
                    mock_clients["s3"] = MagicMock()
                    if s3_error:
                        mock_clients["s3"].get_object.side_effect = s3_error
                    elif s3_response is not None:
                        mock_clients["s3"].get_object.return_value = s3_response
                return mock_clients["s3"]

        return client_factory

    return _create_mock
