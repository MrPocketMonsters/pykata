"""End-to-end tests for DynamoDB kata service against a configured environment.

Prerequisites:
- DynamoDB endpoint reachable
- Kata table provisioned

All tests in this module inherit @pytest.mark.e2e
via pytest_collection_modifyitems in tests/conftest.py.
"""

import uuid

from src.models.kata import KataMetadata
from src.services.dynamo_service import create_kata, get_kata, list_katas


"""Fixture ensure_dynamo_available is provided by tests/conftest.py"""


def test_create_and_get_kata_e2e(ensure_dynamo_available):
    """Create a kata, then fetch it by ID using the service layer."""

    kata_id = f"it-kata-{uuid.uuid4().hex[:8]}"
    metadata = KataMetadata(
        id=kata_id,
        title="End-to-end Dummy Kata",
        description="Dummy description for end-to-end test",
        tags=["e2e", "dummy"],
        difficulty="beginner",
        s3_key="katas/e2e_dummy.py",
        sample_input="foo",
        sample_output="bar",
    )

    assert create_kata(metadata) is True

    fetched = get_kata(kata_id)
    assert fetched.id == kata_id
    assert fetched.title == metadata.title
    assert fetched.tags == metadata.tags


def test_list_contains_created_kata_e2e(ensure_dynamo_available):
    """Create a kata, then verify list includes it (simple pagination)."""

    kata_id = f"it-kata-{uuid.uuid4().hex[:8]}"
    metadata = KataMetadata(
        id=kata_id,
        title="End-to-end Dummy Kata #2",
        description="Another dummy description for end-to-end test",
        tags=["e2e", "dummy"],
        difficulty="beginner",
        s3_key="katas/e2e_dummy2.py",
        sample_input="alpha",
        sample_output="beta",
    )

    assert create_kata(metadata) is True

    items = list_katas(limit=100, offset=0)
    assert any(k.id == kata_id for k in items)
