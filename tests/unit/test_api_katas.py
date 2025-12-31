"""Unit tests for GET /katas endpoint (list)."""

from fastapi.testclient import TestClient

from src.api.main import app
from src.models.kata import KataMetadata
from src.services.dynamo_service import DynamoServiceError, TableNotFoundError


client = TestClient(app, raise_server_exceptions=False)


class TestListKatasEndpoint:
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

    def test_returns_list_with_default_pagination(self, monkeypatch):
        sample = [self._make_kata(i) for i in range(3)]

        monkeypatch.setattr(
            "src.api.main.dynamo_list_katas", lambda limit, offset: sample
        )

        resp = client.get("/katas")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == len(sample)

        for item in data:
            assert "id" in item
            assert "title" in item
            assert "description" in item
            assert "tags" in item
            assert "difficulty" in item
            # code storage key must not be exposed
            assert "s3_key" not in item

    def test_limit_and_offset_paginate_correctly(self, monkeypatch):
        sample = [self._make_kata(i) for i in range(5)]

        def stub(limit, offset):
            # emulate service behavior: return slice
            return sample[offset : offset + limit]

        monkeypatch.setattr("src.api.main.dynamo_list_katas", stub)

        resp = client.get("/katas?limit=2&offset=1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["id"] == "kata-1"

    def test_response_schema_contains_expected_fields_and_no_code(self, monkeypatch):
        kata = self._make_kata(42)
        monkeypatch.setattr(
            "src.api.main.dynamo_list_katas", lambda limit, offset: [kata]
        )

        resp = client.get("/katas")
        assert resp.status_code == 200
        item = resp.json()[0]
        expected = {"id", "title", "description", "tags", "difficulty"}
        assert expected.issubset(set(item.keys()))
        assert "s3_key" not in item

    def test_dynamo_errors_map_to_http_errors(self, monkeypatch):
        monkeypatch.setattr(
            "src.api.main.dynamo_list_katas",
            lambda limit, offset: (_ for _ in ()).throw(DynamoServiceError("boom")),
        )

        resp = client.get("/katas")
        assert resp.status_code == 500
        # Global exception handler should return a generic error body
        body = resp.json()
        assert body.get("detail") == "Internal Server Error"
        assert body.get("status_code") == 500
        # Do not expose original exception message or traceback
        assert "boom" not in str(body)

        # table not found also maps to 500
        monkeypatch.setattr(
            "src.api.main.dynamo_list_katas",
            lambda limit, offset: (_ for _ in ()).throw(TableNotFoundError("missing")),
        )

        resp2 = client.get("/katas")
        assert resp2.status_code == 500
        body2 = resp2.json()
        assert body2.get("detail") == "Internal Server Error"
        assert body2.get("status_code") == 500
        assert "missing" not in str(body2)
