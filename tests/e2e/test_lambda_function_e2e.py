"""End-to-end tests for Lambda health function.

Prerequisites:
- Lambda endpoint reachable
- Lambda function provisioned (name from settings)

All tests in this module inherit @pytest.mark.e2e
via pytest_collection_modifyitems in tests/conftest.py.
"""

import json
import time
from typing import Any

import pytest

from src.config import settings


"""Fixture ensure_lambda_available is provided by tests/conftest.py"""


def test_lambda_health_invocation_e2e(ensure_lambda_available):
    """Invoke the health Lambda and verify the expected response."""

    client = ensure_lambda_available

    event = {
        "version": "2.0",
        "requestContext": {
            "http": {
                "method": "GET",
                "path": "/health",
                "protocol": "HTTP/1.1",
                "sourceIp": "127.0.0.1",
                "userAgent": "curl",
            },
        },
    }

    # Short retries in case the function is not yet ready
    payload_str: str | None = None
    last_exception: Any = None
    for _ in range(6):
        try:
            resp = client.invoke(
                FunctionName=settings.LAMBDA_FUNCTION_NAME,
                Payload=json.dumps(event).encode("utf-8"),
            )
            body_bytes = resp["Payload"].read()
            payload_str = body_bytes.decode("utf-8")
            break
        except Exception as exc:  # pragma: no cover - network/localstack timing
            last_exception = exc
            time.sleep(2)

    if payload_str is None:
        pytest.fail(f"Could not invoke Lambda: {last_exception}")

    result = json.loads(payload_str)

    # Should be ok and contain expected body
    assert result.get("statusCode") == 200
    body = json.loads(result.get("body"))
    assert body == {"status": "ok"}
