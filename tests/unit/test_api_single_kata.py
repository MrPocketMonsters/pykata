"""Unit tests for GET /kata/{kata_id} endpoint."""

from fastapi.testclient import TestClient

from src.api.main import app
from src.models.kata import KataMetadata
from src.services.dynamo_service import (
    DynamoServiceError,
    TableNotFoundError,
    ItemNotFoundError,
)


client = TestClient(app, raise_server_exceptions=False)


class TestSingleKataEndpoint:
    def _make_kata(self, idx: int) -> KataMetadata:
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

    def test_return_kata_correctly(self, monkeypatch):
        kata = self._make_kata(1)

        monkeypatch.setattr("src.api.main.dynamo_get_kata", lambda kata_id: kata)

        resp = client.get("/katas/kata-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "kata-1"

    def test_response_schema_contains_expected_fields(self, monkeypatch):
        kata = self._make_kata(42)
        monkeypatch.setattr("src.api.main.dynamo_get_kata", lambda kata_id: kata)

        resp = client.get("/katas/kata-42")
        assert resp.status_code == 200
        item = resp.json()
        expected = {
            "id",
            "title",
            "description",
            "tags",
            "difficulty",
            "s3_key",
            "sample_input",
            "sample_output",
        }
        assert expected.issubset(set(item.keys()))

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

    def test_item_not_found_maps_to_404(self, monkeypatch):
        # Specifically, item not found maps to 404
        monkeypatch.setattr(
            "src.api.main.dynamo_get_kata",
            lambda kata_id: (_ for _ in ()).throw(ItemNotFoundError("item not found")),
        )

        resp3 = client.get("/katas/kata-99")
        assert resp3.status_code == 404
        body3 = resp3.json()
        assert body3.get("detail") == "Not Found"
        assert body3.get("status_code") == 404
        assert "item not found" not in str(body3)

    def test_exceptions_do_not_expose_internal_details(self, monkeypatch):
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
