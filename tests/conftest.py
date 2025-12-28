"""Pytest configuration and shared fixtures for unit tests."""

import pytest
from pydantic_settings import SettingsConfigDict


@pytest.fixture
def clean_env(monkeypatch):
    """Fixture to clean environment variables and disable .env file loading.

    This ensures that tests read actual defaults instead of values from .env file.
    - Removes all configuration environment variables
    - Patches Settings class to not load .env file
    - Provides clean slate for testing default behavior
    """

    # Define all configuration environment variables
    env_vars = [
        "APP_NAME",
        "APP_ENV",
        "LOG_LEVEL",
        "DEBUG",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_DEFAULT_REGION",
        "AWS_ENDPOINT",
        "AWS_S3_ENDPOINT",
        "DYNAMODB_TABLE_NAME",
        "S3_BUCKET_NAME",
        "LAMBDA_TIMEOUT",
        "EXECUTION_TIMEOUT",
        "app_name",
        "app_env",
        "log_level",
        "debug",  # Lowercase versions too
    ]

    # Remove all environment variables to ensure we test defaults
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)

    # Patch the Settings model to not load .env file
    # Import here to avoid circular imports
    from src.config import Settings

    original_config = Settings.model_config

    # Create new config without env_file
    new_config = SettingsConfigDict(
        env_file=None,  # Disable .env file loading
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    monkeypatch.setattr(Settings, "model_config", new_config)

    yield monkeypatch

    # Restore original config
    monkeypatch.setattr(Settings, "model_config", original_config)


@pytest.fixture(autouse=True)
def force_valid_logging(monkeypatch):
    """Ensure LOG_LEVEL is valid and .env is ignored during tests.

    Prevents validation errors when a developer has an invalid LOG_LEVEL in a local .env.
    Applies to every test to avoid accidental leakage of developer-specific env values.
    """

    # Always disable .env loading for tests
    from src.config import Settings

    new_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )
    monkeypatch.setattr(Settings, "model_config", new_config)

    # Force a valid LOG_LEVEL so validation passes even if .env had bad value
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    yield
