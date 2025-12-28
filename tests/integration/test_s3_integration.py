"""Integration tests for S3 kata code service (dev environment).

Prerequisites:
- S3 endpoint reachable via LocalStack
- Kata code bucket provisioned (Terraform dev applied)

All tests in this module inherit @pytest.mark.integration and @pytest.mark.dev_integration
via pytest_collection_modifyitems in tests/conftest.py.
"""

import uuid

from src.services.s3_service import upload_kata_code, download_kata_code


"""Fixture ensure_s3_available is provided by tests/conftest.py"""


def test_upload_and_download_kata_code_integration(ensure_s3_available):
    """Upload code, then download it and verify content matches."""

    kata_id = f"it-s3-{uuid.uuid4().hex[:8]}"
    code = 'name = input()\nprint(f"Hello, {name}!")'

    # Upload code
    s3_key = upload_kata_code(kata_id, code)

    assert s3_key == f"katas/{kata_id}.py"

    # Download and verify
    downloaded = download_kata_code(s3_key)

    assert downloaded == code


def test_upload_multiple_katas_integration(ensure_s3_available):
    """Upload multiple katas and verify each can be downloaded independently."""

    kata_id_1 = f"it-s3-{uuid.uuid4().hex[:8]}"
    kata_id_2 = f"it-s3-{uuid.uuid4().hex[:8]}"

    code_1 = "x = 5\nprint(x)"
    code_2 = "for i in range(10):\n    print(i)"

    # Upload both
    key_1 = upload_kata_code(kata_id_1, code_1)
    key_2 = upload_kata_code(kata_id_2, code_2)

    # Download and verify each
    downloaded_1 = download_kata_code(key_1)
    downloaded_2 = download_kata_code(key_2)

    assert downloaded_1 == code_1
    assert downloaded_2 == code_2
