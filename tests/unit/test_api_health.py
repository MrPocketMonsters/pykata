"""Unit tests for API health check endpoint."""

from fastapi.testclient import TestClient
from src.api.main import app


client = TestClient(app, raise_server_exceptions=False)


class TestHealthCheckAllServicesHealthy:
    """Test health check when all services are operational."""

    def test_health_all_services_up(self, mock_dynamo_health_up, mock_s3_health_up):
        """Test health endpoint returns 200 when all services are healthy."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["dynamodb"] is True
        assert data["services"]["s3"] is True

    def test_health_response_structure(self, mock_dynamo_health_up, mock_s3_health_up):
        """Test health response has correct structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "services" in data
        assert isinstance(data["services"], dict)
        assert "dynamodb" in data["services"]
        assert "s3" in data["services"]


class TestHealthCheckDynamoDown:
    """Test health check when DynamoDB is unavailable."""

    def test_health_dynamodb_down(self, mock_dynamo_health_down, mock_s3_health_up):
        """Test health endpoint returns degraded status when DynamoDB is down."""
        response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["dynamodb"] is False
        assert data["services"]["s3"] is True

    def test_health_dynamodb_down_returns_unavailable(
        self, mock_dynamo_health_down, mock_s3_health_up
    ):
        """Test that 503 Service Unavailable is returned when DynamoDB fails."""
        response = client.get("/health")
        assert response.status_code == 503


class TestHealthCheckS3Down:
    """Test health check when S3 is unavailable."""

    def test_health_s3_down(self, mock_dynamo_health_up, mock_s3_health_down):
        """Test health endpoint returns degraded status when S3 is down."""
        response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["dynamodb"] is True
        assert data["services"]["s3"] is False

    def test_health_s3_down_returns_unavailable(
        self, mock_dynamo_health_up, mock_s3_health_down
    ):
        """Test that 503 Service Unavailable is returned when S3 fails."""
        response = client.get("/health")
        assert response.status_code == 503


class TestHealthCheckAllServicesDown:
    """Test health check when all services are unavailable."""

    def test_health_all_services_down(
        self, mock_dynamo_health_down, mock_s3_health_down
    ):
        """Test health endpoint when all services are down."""
        response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["dynamodb"] is False
        assert data["services"]["s3"] is False


class TestHealthCheckIntegration:
    """Integration tests for health check endpoint."""

    def test_health_endpoint_exists(self, mock_dynamo_health_up, mock_s3_health_up):
        """Test that health endpoint is accessible."""
        response = client.get("/health")
        assert response.status_code in [200, 503]

    def test_health_response_is_json(self, mock_dynamo_health_up, mock_s3_health_up):
        """Test that health response is valid JSON."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_root_endpoint_still_works(self):
        """Test that root endpoint works alongside health check."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "API is running"
