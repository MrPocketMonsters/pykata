"""Unit tests for S3 kata code service.

Tests use botocore.stub.Stubber to mock S3 operations without real AWS calls.
"""

import pytest

from src.services.s3_service import (
    upload_kata_code,
    download_kata_code,
    S3ServiceError,
    BucketNotFoundError,
    ObjectNotFoundError,
)


class TestUploadKataCode:
    """Tests for upload_kata_code() method."""

    def test_upload_success(self, stubbed_s3_client, monkeypatch):
        """Successful upload returns the generated S3 key."""
        client, stubber = stubbed_s3_client

        # Patch the _get_client function to return our stubber client
        import src.services.s3_service

        monkeypatch.setattr(src.services.s3_service, "_get_client", lambda: client)

        # Register expected S3 put_object call
        stubber.add_response(
            "put_object",
            service_response={},
            expected_params={
                "Bucket": "kata-code",
                "Key": "katas/kata-123.py",
                "Body": "print('hello')",
            },
        )

        s3_key = upload_kata_code("kata-123", "print('hello')")

        assert s3_key == "katas/kata-123.py"

    def test_upload_bucket_not_found(self, stubbed_s3_client, monkeypatch):
        """Upload raises BucketNotFoundError when bucket does not exist."""
        client, stubber = stubbed_s3_client

        import src.services.s3_service

        monkeypatch.setattr(src.services.s3_service, "_get_client", lambda: client)

        stubber.add_client_error(
            "put_object",
            service_error_code="NoSuchBucket",
            service_message="The specified bucket does not exist",
        )

        with pytest.raises(BucketNotFoundError):
            upload_kata_code("kata-123", "print('hello')")

    def test_upload_generic_error(self, stubbed_s3_client, monkeypatch):
        """Upload raises S3ServiceError for non-bucket errors."""
        client, stubber = stubbed_s3_client

        import src.services.s3_service

        monkeypatch.setattr(src.services.s3_service, "_get_client", lambda: client)

        stubber.add_client_error(
            "put_object",
            service_error_code="AccessDenied",
            service_message="Access denied",
        )

        with pytest.raises(S3ServiceError):
            upload_kata_code("kata-123", "print('hello')")

    def test_upload_with_special_characters(self, stubbed_s3_client, monkeypatch):
        """Upload handles code with special characters and newlines."""
        client, stubber = stubbed_s3_client

        import src.services.s3_service

        monkeypatch.setattr(src.services.s3_service, "_get_client", lambda: client)

        code = 'name = input("Enter name: ")\nprint(f"Hello, {name}!")'

        stubber.add_response(
            "put_object",
            service_response={},
            expected_params={
                "Bucket": "kata-code",
                "Key": "katas/kata-456.py",
                "Body": code,
            },
        )

        s3_key = upload_kata_code("kata-456", code)

        assert s3_key == "katas/kata-456.py"


class TestDownloadKataCode:
    """Tests for download_kata_code() method."""

    def test_download_success(self, stubbed_s3_client, monkeypatch):
        """Successful download returns the code content."""
        client, stubber = stubbed_s3_client

        import src.services.s3_service

        monkeypatch.setattr(src.services.s3_service, "_get_client", lambda: client)

        code = "print('hello')"

        stubber.add_response(
            "get_object",
            service_response={
                "Body": type("obj", (), {"read": lambda self: code.encode("utf-8")})(),
            },
            expected_params={
                "Bucket": "kata-code",
                "Key": "katas/kata-123.py",
            },
        )

        result = download_kata_code("katas/kata-123.py")

        assert result == code

    def test_download_object_not_found(self, stubbed_s3_client, monkeypatch):
        """Download raises ObjectNotFoundError when key does not exist."""
        client, stubber = stubbed_s3_client

        import src.services.s3_service

        monkeypatch.setattr(src.services.s3_service, "_get_client", lambda: client)

        stubber.add_client_error(
            "get_object",
            service_error_code="NoSuchKey",
            service_message="The specified key does not exist",
        )

        with pytest.raises(ObjectNotFoundError):
            download_kata_code("katas/nonexistent.py")

    def test_download_bucket_not_found(self, stubbed_s3_client, monkeypatch):
        """Download raises BucketNotFoundError when bucket does not exist."""
        client, stubber = stubbed_s3_client

        import src.services.s3_service

        monkeypatch.setattr(src.services.s3_service, "_get_client", lambda: client)

        stubber.add_client_error(
            "get_object",
            service_error_code="NoSuchBucket",
            service_message="The specified bucket does not exist",
        )

        with pytest.raises(BucketNotFoundError):
            download_kata_code("katas/kata-123.py")

    def test_download_with_multiline_code(self, stubbed_s3_client, monkeypatch):
        """Download handles multiline code correctly."""
        client, stubber = stubbed_s3_client

        import src.services.s3_service

        monkeypatch.setattr(src.services.s3_service, "_get_client", lambda: client)

        code = 'n = int(input())\nif n > 0:\n    print("positive")'

        stubber.add_response(
            "get_object",
            service_response={
                "Body": type("obj", (), {"read": lambda self: code.encode("utf-8")})(),
            },
            expected_params={
                "Bucket": "kata-code",
                "Key": "katas/kata-789.py",
            },
        )

        result = download_kata_code("katas/kata-789.py")

        assert result == code
