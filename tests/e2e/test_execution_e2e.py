"""End-to-end tests for execution service.

Tests the full kata pipeline: DynamoDB metadata → S3 code storage → execution.

Prerequisites:
- DynamoDB endpoint reachable
- S3 endpoint reachable
- Both tables/buckets provisioned

All tests in this module inherit @pytest.mark.e2e
via pytest_collection_modifyitems in tests/conftest.py.
"""

import uuid

from src.services.dynamo_service import (
    create_kata as dynamo_create_kata,
    get_kata as dynamo_get_kata,
)
from src.services.s3_service import (
    upload_kata_code as s3_upload_kata_code,
    download_kata_code as s3_download_kata_code,
)
from src.services.execution_service import (
    execute_kata_code as xser_execute_kata_code,
)
from src.models.kata import KataMetadata


"""Fixtures ensure_dynamo_available and ensure_s3_available are provided by tests/conftest.py"""


def test_full_kata_pipeline_e2e(ensure_dynamo_available, ensure_s3_available):
    """Execute full pipeline: create metadata → upload code → download → execute."""

    kata_id = f"it-exec-{uuid.uuid4().hex[:8]}"
    code = "x = int(input())\nprint(x * 2)"

    # 1) Upload code to S3
    s3_key = s3_upload_kata_code(kata_id, f"katas/{kata_id}.py", code)
    assert s3_key == f"katas/{kata_id}.py"

    # 2) Create kata metadata in DynamoDB
    metadata = KataMetadata(
        id=kata_id,
        title="Double Number",
        description="Doubles the input number",
        tags=["math", "e2e"],
        difficulty="beginner",
        s3_key=s3_key,
        sample_input="5",
        sample_output="10",
    )
    assert dynamo_create_kata(metadata) is True

    # 3) Fetch metadata from DynamoDB
    fetched = dynamo_get_kata(kata_id)
    assert fetched.id == kata_id
    assert fetched.s3_key == s3_key

    # 4) Download code from S3
    retrieved_code = s3_download_kata_code(fetched.s3_key)
    assert retrieved_code == code

    # 5) Execute the code
    result = xser_execute_kata_code(retrieved_code, "5", timeout=5)
    assert result.success is True
    assert "10" in result.stdout


def test_kata_execution_with_exception_e2e(
    ensure_dynamo_available, ensure_s3_available
):
    """Full pipeline where uploaded code raises an exception."""

    kata_id = f"it-exec-{uuid.uuid4().hex[:8]}"
    code = "n = int(input())\nif n < 0:\n    raise ValueError('Negative not allowed')\nprint(n)"

    # Upload and create metadata
    s3_key = s3_upload_kata_code(kata_id, f"katas/{kata_id}.py", code)
    metadata = KataMetadata(
        id=kata_id,
        title="Positive Check",
        description="Rejects negative numbers",
        tags=["math", "validation"],
        difficulty="beginner",
        s3_key=s3_key,
        sample_input="-1",
        sample_output="error",
    )
    dynamo_create_kata(metadata)

    # Fetch and download
    fetched = dynamo_get_kata(kata_id)
    retrieved_code = s3_download_kata_code(fetched.s3_key)
    # Execute with bad input
    result = xser_execute_kata_code(retrieved_code, "-1", timeout=5)
    assert result.success is False
    assert "ValueError" in result.stderr or "Negative not allowed" in result.stderr


def test_multiple_kata_executions_e2e(ensure_dynamo_available, ensure_s3_available):
    """Create and execute multiple katas independently."""

    # Create two different katas
    kata_1_id = f"it-exec-{uuid.uuid4().hex[:8]}"
    kata_2_id = f"it-exec-{uuid.uuid4().hex[:8]}"

    code_1 = "print('Hello')"
    code_2 = "n = int(input())\nprint(n ** 2)"

    # Upload and create both
    s3_key_1 = s3_upload_kata_code(kata_1_id, f"katas/{kata_1_id}.py", code_1)
    s3_key_2 = s3_upload_kata_code(kata_2_id, f"katas/{kata_2_id}.py", code_2)

    meta_1 = KataMetadata(
        id=kata_1_id,
        title="Hello",
        description="Prints hello",
        tags=["greeting"],
        difficulty="beginner",
        s3_key=s3_key_1,
        sample_input="",
        sample_output="Hello",
    )
    meta_2 = KataMetadata(
        id=kata_2_id,
        title="Square",
        description="Squares input",
        tags=["math"],
        difficulty="beginner",
        s3_key=s3_key_2,
        sample_input="3",
        sample_output="9",
    )

    dynamo_create_kata(meta_1)
    dynamo_create_kata(meta_2)

    # Fetch and execute both
    fetched_1 = dynamo_get_kata(kata_1_id)
    fetched_2 = dynamo_get_kata(kata_2_id)

    retrieved_1 = s3_download_kata_code(fetched_1.s3_key)
    retrieved_2 = s3_download_kata_code(fetched_2.s3_key)

    result_1 = xser_execute_kata_code(retrieved_1, "", timeout=5)
    result_2 = xser_execute_kata_code(retrieved_2, "3", timeout=5)

    assert result_1.success is True
    assert "Hello" in result_1.stdout

    assert result_2.success is True
    assert "9" in result_2.stdout
