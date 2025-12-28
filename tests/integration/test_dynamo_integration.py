"""Integration tests for DynamoDB kata service against a configured environment.

Prerequisites:
- DynamoDB endpoint reachable (LocalStack or AWS)
- Kata table provisioned (e.g., Terraform dev applied or equivalent)

All tests in this module inherit @pytest.mark.integration and @pytest.mark.dev_integration
from tests/integration/__init__.py.
"""

import uuid

from src.models.kata import KataMetadata
from src.services.dynamo_service import create_kata, get_kata, list_katas


"""Fixture ensure_dynamo_available is provided by tests/conftest.py"""


def test_create_and_get_kata_integration(ensure_dynamo_available):
    """Create a kata, then fetch it by ID using the service layer."""

    kata_id = f"it-kata-{uuid.uuid4().hex[:8]}"
    metadata = KataMetadata(
        id=kata_id,
        title="Integration Dummy Kata",
        description="Dummy description for integration test",
        tags=["integration", "dummy"],
        difficulty="beginner",
        s3_key="katas/integration_dummy.py",
        sample_input="foo",
        sample_output="bar",
    )

    assert create_kata(metadata) is True

    fetched = get_kata(kata_id)
    assert fetched.id == kata_id
    assert fetched.title == metadata.title
    assert fetched.tags == metadata.tags


def test_list_contains_created_kata_integration(ensure_dynamo_available):
    """Create a kata, then verify list includes it (simple pagination)."""

    kata_id = f"it-kata-{uuid.uuid4().hex[:8]}"
    metadata = KataMetadata(
        id=kata_id,
        title="Integration Dummy Kata #2",
        description="Another dummy description for integration test",
        tags=["integration", "dummy"],
        difficulty="beginner",
        s3_key="katas/integration_dummy2.py",
        sample_input="alpha",
        sample_output="beta",
    )

    assert create_kata(metadata) is True

    items = list_katas(limit=100, offset=0)
    assert any(k.id == kata_id for k in items)
