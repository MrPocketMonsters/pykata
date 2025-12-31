"""Unit tests for API global exception handlers."""

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from src.api.exceptions import (
    validation_exception_handler,
    not_found_exception_handler,
    request_timeout_exception_handler,
    global_exception_handler,
)

# ==================== Test Application Setup ====================

# Create a separate FastAPI api with testing endpoints
app = FastAPI()

# Register global exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(404, not_found_exception_handler)
app.add_exception_handler(408, request_timeout_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# ==================== Testing Endpoints ====================


@app.get("/")
async def _root():
    return {"message": "Hello World"}


@app.get("/test/400")
async def _test_400_get(param: int):
    """Test 400 Bad Request - pass a non-integer value for param"""
    return {"message": "This should not be reached"}


@app.post("/test/validation")
async def _test_validation(param: int):
    """Test 400 Bad Request - pass a non-integer value for param"""
    return {"param": param}


@app.get("/test/408")
async def _test_408():
    """Test 408 Request Timeout - raises HTTPException with 408 status"""
    raise HTTPException(status_code=408, detail="Request Timeout for testing")


@app.get("/test/500")
async def _test_500():
    """Test 500 Internal Server Error - raises an unhandled exception"""
    raise ValueError("This is a test error to trigger 500 response")


# ==================== Test Client Setup ====================

# Use raise_server_exceptions=False to test exception handlers
client = TestClient(app, raise_server_exceptions=False)

# ==================== Test Cases ====================


class TestBadRequest:
    """Test 400 Bad Request exception handler."""

    def test_validation_error_returns_400(self):
        """Test that validation errors return 400 status code."""
        response = client.get("/test/400?param=not-an-integer")
        assert response.status_code == 400

    def test_validation_error_response_structure(self):
        """Test that 400 response has correct structure."""
        response = client.get("/test/400?param=not-an-integer")
        data = response.json()

        assert "status_code" in data
        assert data["status_code"] == 400
        assert "detail" in data
        assert data["detail"] == "Bad Request"
        assert "errors" in data

    def test_post_validation_error_returns_400(self):
        """Test that POST validation errors return 400."""
        response = client.post("/test/validation", json={"param": "not-an-integer"})

        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Bad Request"
        assert data["status_code"] == 400


class TestNotFound:
    """Test 404 Not Found exception handler."""

    def test_not_found_returns_404(self):
        """Test that non-existent routes return 404 status code."""
        response = client.get("/nonexistent-route")
        assert response.status_code == 404

    def test_not_found_response_structure(self):
        """Test that 404 response has correct structure."""
        response = client.get("/nonexistent-route")
        data = response.json()

        assert "status_code" in data
        assert data["status_code"] == 404
        assert "detail" in data
        assert data["detail"] == "Not Found"
        assert "path" in data
        assert data["path"] == "/nonexistent-route"

    def test_404_with_different_paths(self):
        """Test 404 handler with various non-existent paths."""
        paths = ["/api/missing", "/v1/nothere", "/test/does-not-exist"]
        for path in paths:
            response = client.get(path)
            assert response.status_code == 404
            data = response.json()
            assert data["path"] == path


class TestInternalServerError:
    """Test 500 Internal Server Error exception handler."""

    def test_unhandled_exception_returns_500(self):
        """Test that unhandled exceptions return 500."""
        response = client.get("/test/500")
        assert response.status_code == 500

    def test_internal_error_does_not_expose_traceback(self):
        """Test that 500 response does not expose internal error details."""
        response = client.get("/test/500")
        data = response.json()

        assert "ValueError" not in str(data)
        assert "This is a test error" not in str(data)

    def test_internal_error_response_structure(self):
        """Test that 500 response has correct structure."""
        response = client.get("/test/500")
        data = response.json()

        assert "status_code" in data
        assert data["status_code"] == 500
        assert "detail" in data
        assert data["detail"] == "Internal Server Error"


class TestHealthcheck:
    """Test that healthy endpoints still work."""

    def test_root_endpoint_returns_200(self):
        """Test that root endpoint works normally."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello World"


class TestRequestTimeout:
    """Test 408 Request Timeout exception handler."""

    def test_timeout_exception_returns_408(self):
        """Test that HTTPException with 408 status code returns proper response."""
        response = client.get("/test/408")
        assert response.status_code == 408

    def test_timeout_response_structure(self):
        """Test that 408 response has correct structure."""
        response = client.get("/test/408")
        data = response.json()

        assert "status_code" in data
        assert data["status_code"] == 408
        assert "detail" in data
        assert data["detail"] == "Request Timeout"
        assert "path" in data
        assert data["path"] == "/test/408"
