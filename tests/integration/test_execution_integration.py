"""Integration tests for execution service (dev environment).

Tests the full kata pipeline: DynamoDB metadata → S3 code storage → execution.

Prerequisites:
- DynamoDB endpoint reachable via LocalStack
- S3 endpoint reachable via LocalStack
- Both tables/buckets provisioned (Terraform dev applied)

All tests in this module inherit @pytest.mark.integration and @pytest.mark.dev_integration
via pytest_collection_modifyitems in tests/conftest.py.
"""

import uuid

from src.services.dynamo_service import create_kata, get_kata
from src.services.s3_service import upload_kata_code, download_kata_code
from src.services.execution_service import execute_kata_code
from src.models.kata import KataMetadata


"""Fixtures ensure_dynamo_available and ensure_s3_available are provided by tests/conftest.py"""


def test_full_kata_pipeline_integration(ensure_dynamo_available, ensure_s3_available):
    """Execute full pipeline: create metadata → upload code → download → execute."""

    kata_id = f"it-exec-{uuid.uuid4().hex[:8]}"
    code = "x = int(input())\nprint(x * 2)"

    # 1) Upload code to S3
    s3_key = upload_kata_code(kata_id, code)
    assert s3_key == f"katas/{kata_id}.py"

    # 2) Create kata metadata in DynamoDB
    metadata = KataMetadata(
        id=kata_id,
        title="Double Number",
        description="Doubles the input number",
        tags=["math", "integration"],
        difficulty="beginner",
        s3_key=s3_key,
        sample_input="5",
        sample_output="10",
    )
    assert create_kata(metadata) is True

    # 3) Fetch metadata from DynamoDB
    fetched = get_kata(kata_id)
    assert fetched.id == kata_id
    assert fetched.s3_key == s3_key

    # 4) Download code from S3
    retrieved_code = download_kata_code(fetched.s3_key)
    assert retrieved_code == code

    # 5) Execute the code
    result = execute_kata_code(retrieved_code, "5", timeout=5)
    assert result.success is True
    assert "10" in result.stdout


def test_kata_execution_with_exception_integration(
    ensure_dynamo_available, ensure_s3_available
):
    """Full pipeline where uploaded code raises an exception."""

    kata_id = f"it-exec-{uuid.uuid4().hex[:8]}"
    code = "n = int(input())\nif n < 0:\n    raise ValueError('Negative not allowed')\nprint(n)"

    # Upload and create metadata
    s3_key = upload_kata_code(kata_id, code)
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
    create_kata(metadata)

    # Fetch and download
    fetched = get_kata(kata_id)
    retrieved_code = download_kata_code(fetched.s3_key)

    # Execute with bad input
    result = execute_kata_code(retrieved_code, "-1", timeout=5)
    assert result.success is False
    assert "ValueError" in result.stderr or "Negative not allowed" in result.stderr


def test_multiple_kata_executions_integration(
    ensure_dynamo_available, ensure_s3_available
):
    """Create and execute multiple katas independently."""

    # Create two different katas
    kata_1_id = f"it-exec-{uuid.uuid4().hex[:8]}"
    kata_2_id = f"it-exec-{uuid.uuid4().hex[:8]}"

    code_1 = "print('Hello')"
    code_2 = "n = int(input())\nprint(n ** 2)"

    # Upload and create both
    s3_key_1 = upload_kata_code(kata_1_id, code_1)
    s3_key_2 = upload_kata_code(kata_2_id, code_2)

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

    create_kata(meta_1)
    create_kata(meta_2)

    # Fetch and execute both
    fetched_1 = get_kata(kata_1_id)
    fetched_2 = get_kata(kata_2_id)

    retrieved_1 = download_kata_code(fetched_1.s3_key)
    retrieved_2 = download_kata_code(fetched_2.s3_key)

    result_1 = execute_kata_code(retrieved_1, "", timeout=5)
    result_2 = execute_kata_code(retrieved_2, "3", timeout=5)

    assert result_1.success is True
    assert "Hello" in result_1.stdout

    assert result_2.success is True
    assert "9" in result_2.stdout
