"""Unit tests for HTTP logging middleware in the FastAPI app."""

import logging
import re
from fastapi.testclient import TestClient

from src.api.main import app


def test_middleware_logs_root_request(caplog):
    """Middleware should log method, path and latency for root endpoint."""
    client = TestClient(app)
    caplog.set_level(logging.INFO, logger="src.api.main")

    resp = client.get("/")
    assert resp.status_code == 200

    # Find a log record emitted by the middleware
    records = [r.message for r in caplog.records if "latency_ms=" in r.message]
    assert records, "Expected middleware log with latency"
    assert any("GET /" in msg for msg in records)


def test_middleware_logs_health_status(caplog):
    """Middleware should include response status for health endpoint."""
    client = TestClient(app)
    caplog.set_level(logging.INFO, logger="src.api.main")

    resp = client.get("/health")
    assert resp.status_code in (200, 503)

    matched = None
    for r in caplog.records:
        if "/health" in r.message and "status=" in r.message:
            matched = r.message
            break

    assert matched is not None
    assert f"status={resp.status_code}" in matched


def test_middleware_latency_is_numeric(caplog):
    """Latency value should be present and parseable as float."""
    client = TestClient(app)
    caplog.set_level(logging.INFO, logger="src.api.main")

    client.get("/")

    for r in caplog.records:
        if "latency_ms=" in r.message:
            m = re.search(r"latency_ms=([0-9]+\.?[0-9]*)", r.message)
            assert m, "latency_ms= token should be present"
            float(m.group(1))
            return

    assert AssertionError("No log record with latency_ms= found")
