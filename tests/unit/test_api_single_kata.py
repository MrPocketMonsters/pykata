"""Unit tests for GET /kata/{kata_id} endpoint."""

from fastapi.testclient import TestClient

from src.api.main import app
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


class TestSingleKataEndpointResponses:
    """Tests for GET /kata/{kata_id} endpoint successful responses."""

    def test_return_kata_correctly(self, monkeypatch, kata_metadata_factory, kata_code):
        kata = kata_metadata_factory(1)
        monkeypatch.setattr("src.api.main.dynamo_get_kata", lambda kata_id: kata)
        monkeypatch.setattr("src.api.main.s3_get_kata_code", lambda s3_key: kata_code)

        resp = client.get("/katas/kata-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "kata-1"

    def test_response_schema_contains_expected_fields(
        self, monkeypatch, kata_metadata_factory, kata_code
    ):
        kata = kata_metadata_factory(42)
        monkeypatch.setattr("src.api.main.dynamo_get_kata", lambda kata_id: kata)
        monkeypatch.setattr("src.api.main.s3_get_kata_code", lambda s3_key: kata_code)

        resp = client.get("/katas/kata-42")
        assert resp.status_code == 200
        item = resp.json()
        expected = {
            "id",
            "title",
            "description",
            "tags",
            "difficulty",
            "code",
            "sample_input",
            "sample_output",
        }
        assert expected.issubset(set(item.keys()))
        assert "s3_key" not in item

    def test_code_content_is_returned(
        self, monkeypatch, kata_metadata_factory, kata_code
    ):
        kata = kata_metadata_factory(7)
        monkeypatch.setattr("src.api.main.dynamo_get_kata", lambda kata_id: kata)
        monkeypatch.setattr("src.api.main.s3_get_kata_code", lambda s3_key: kata_code)

        resp = client.get("/katas/kata-7")
        assert resp.status_code == 200
        item = resp.json()
        assert item["code"] == kata_code


class TestSingleKataEndpointExceptions:
    """Tests for GET /kata/{kata_id} endpoint error handling."""

    def test_dynamo_errors_map_to_http_errors(self, monkeypatch):
        # Generic Dynamo error maps to 500
        monkeypatch.setattr(
            "src.api.main.dynamo_get_kata",
            lambda kata_id: (_ for _ in ()).throw(DynamoServiceError("boom")),
        )

        resp = client.get("/katas/kata-99")
        assert resp.status_code == 500
        # Global exception handler should return a generic error body
        body = resp.json()
        assert body.get("detail") == "Internal Server Error"
        assert body.get("status_code") == 500
        # Do not expose original exception message or traceback
        assert "boom" not in str(body)

        # Table not found also maps to 500
        monkeypatch.setattr(
            "src.api.main.dynamo_get_kata",
            lambda kata_id: (_ for _ in ()).throw(TableNotFoundError("missing")),
        )

        resp2 = client.get("/katas/kata-99")
        assert resp2.status_code == 500
        body2 = resp2.json()
        assert body2.get("detail") == "Internal Server Error"
        assert body2.get("status_code") == 500
        assert "missing" not in str(body2)

    def test_dynamo_item_not_found_maps_to_404(self, monkeypatch):
        # Specifically, item not found maps to 404
        monkeypatch.setattr(
            "src.api.main.dynamo_get_kata",
            lambda kata_id: (_ for _ in ()).throw(ItemNotFoundError("item not found")),
        )

        resp = client.get("/katas/kata-99")
        assert resp.status_code == 404
        body = resp.json()
        assert body.get("detail") == "Not Found"
        assert body.get("status_code") == 404
        assert "item not found" not in str(body)

    def test_s3_errors_map_to_http_errors(self, monkeypatch, kata_metadata_factory):
        # Generic S3 error maps to 500
        kata = kata_metadata_factory(99)
        monkeypatch.setattr("src.api.main.dynamo_get_kata", lambda kata_id: kata)

        monkeypatch.setattr(
            "src.api.main.s3_get_kata_code",
            lambda s3_key: (_ for _ in ()).throw(S3ServiceError("boom")),
        )

        resp = client.get("/katas/kata-99")
        assert resp.status_code == 500
        # Global exception handler should return a generic error body
        body = resp.json()
        assert body.get("detail") == "Internal Server Error"
        assert body.get("status_code") == 500
        # Do not expose original exception message or traceback
        assert "boom" not in str(body)

        # Bucket not found also maps to 500
        monkeypatch.setattr(
            "src.api.main.s3_get_kata_code",
            lambda s3_key: (_ for _ in ()).throw(BucketNotFoundError("missing")),
        )

        resp2 = client.get("/katas/kata-99")
        assert resp2.status_code == 500
        body2 = resp2.json()
        assert body2.get("detail") == "Internal Server Error"
        assert body2.get("status_code") == 500
        assert "missing" not in str(body2)

    def test_s3_object_not_found_maps_to_404(self, monkeypatch, kata_metadata_factory):
        # Specifically, object not found maps to 404
        kata = kata_metadata_factory(100)
        monkeypatch.setattr("src.api.main.dynamo_get_kata", lambda kata_id: kata)

        monkeypatch.setattr(
            "src.api.main.s3_get_kata_code",
            lambda s3_key: (_ for _ in ()).throw(
                ObjectNotFoundError("object not found")
            ),
        )

        resp = client.get("/katas/kata-100")
        assert resp.status_code == 404
        body = resp.json()
        assert body.get("detail") == "Not Found"
        assert body.get("status_code") == 404
        assert "object not found" not in str(body)

    def test_exceptions_do_not_expose_internal_details(
        self, monkeypatch, kata_metadata_factory
    ):
        # Generic exception from Dynamo maps to 500
        monkeypatch.setattr(
            "src.api.main.dynamo_get_kata",
            lambda kata_id: (_ for _ in ()).throw(Exception("internal error")),
        )

        resp = client.get("/katas/kata-100")
        assert resp.status_code == 500
        body = resp.json()
        assert body.get("detail") == "Internal Server Error"
        assert body.get("status_code") == 500
        # Do not expose original exception message or traceback
        assert "internal error" not in str(body)

        # Generic exception from S3 maps to 500
        kata = kata_metadata_factory(100)
        monkeypatch.setattr("src.api.main.dynamo_get_kata", lambda kata_id: kata)
        monkeypatch.setattr(
            "src.api.main.s3_get_kata_code",
            lambda s3_key: (_ for _ in ()).throw(Exception("internal error")),
        )

        resp2 = client.get("/katas/kata-100")
        assert resp2.status_code == 500
        body2 = resp2.json()
        assert body2.get("detail") == "Internal Server Error"
        assert body2.get("status_code") == 500
        # Do not expose original exception message or traceback
        assert "internal error" not in str(body)
