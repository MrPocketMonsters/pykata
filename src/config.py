"""Application configuration settings.

This module provides centralized configuration management for the PyKata application.
Configuration values are loaded from environment variables (or a .env file) using Pydantic's
BaseSettings, which provides type validation and helpful error messages.

Example:
    >>> from src.config import settings
    >>> print(settings.APP_NAME)  # Access any configuration value
    'pykata'

Environment Variables:
    - Create a .env file in the project root with configuration values
    - See .env.example for available options
    - Pydantic will automatically convert string environment variables to correct types
"""

from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Provides type-safe access to configuration with sensible defaults.
    All values can be overridden via environment variables or a .env file.

    Attributes:
        Application Configuration:
            APP_NAME: Application identifier used in logs and telemetry
            APP_ENV: Deployment environment (dev, staging, prod)
            LOG_LEVEL: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
            DEBUG: Enable debug mode for development (disables in production)

        AWS Credentials & Endpoints:
            AWS_ACCESS_KEY_ID: AWS account access key
            AWS_SECRET_ACCESS_KEY: AWS account secret key
            AWS_DEFAULT_REGION: Default AWS region for all services
            AWS_ENDPOINT: LocalStack endpoint for local development (AWS-compatible mock)
            AWS_S3_ENDPOINT: S3-specific endpoint for LocalStack

        AWS Service Resources:
            DYNAMODB_TABLE_NAME: DynamoDB table for kata metadata storage
            S3_BUCKET_NAME: S3 bucket for user code storage
            LAMBDA_FUNCTION_NAME: Name of the Lambda function for health checks and execution

        Execution Configuration:
            LAMBDA_TIMEOUT: Timeout for Lambda function execution (seconds)
            EXECUTION_TIMEOUT: Timeout for user kata code execution (seconds)
    """

    # Application Configuration
    APP_NAME: str = "pykata"
    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True

    # AWS Credentials (defaults use LocalStack for local development)
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"
    AWS_DEFAULT_REGION: str = "us-east-1"
    AWS_ENDPOINT: str = "http://localhost:4566"
    AWS_S3_ENDPOINT: str = "http://s3.localhost.localstack.cloud:4566"

    # AWS Resource Names
    DYNAMODB_TABLE_NAME: str = "kata"
    S3_BUCKET_NAME: str = "kata-code"
    LAMBDA_FUNCTION_NAME: str = "pykata_lambda_function"

    # Execution Timeouts (in seconds)
    LAMBDA_TIMEOUT: int = 10
    EXECUTION_TIMEOUT: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",  # Load values from .env file if it exists
        env_file_encoding="utf-8",  # UTF-8 encoding for .env file
        env_prefix="",  # No prefix required for environment variables
        case_sensitive=False,  # Environment variable names are case-insensitive
        extra="ignore",  # Ignore extra environment variables not defined in this class
    )

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Validate LOG_LEVEL is a valid logging level."""
        if isinstance(value, str):
            normalized = value.upper()
            valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
            if normalized not in valid_levels:
                raise ValueError(
                    f"LOG_LEVEL must be one of {valid_levels}, got '{value}'"
                )
            return normalized
        return value

    @field_validator("APP_ENV", mode="before")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        """Validate APP_ENV is a recognized environment."""
        if isinstance(value, str):
            normalized = value.lower()
            valid_envs = {"dev", "staging", "prod", "production"}
            if normalized not in valid_envs:
                raise ValueError(f"APP_ENV must be one of {valid_envs}, got '{value}'")
            return normalized
        return value

    @field_validator("LAMBDA_TIMEOUT", "EXECUTION_TIMEOUT", mode="before")
    @classmethod
    def validate_timeouts(cls, value: int) -> int:
        """Validate timeouts are positive integers."""
        # Normalize string inputs to int before validation
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                raise ValueError(f"Timeout must be an integer, got '{value}'")

        if isinstance(value, int):
            if value <= 0:
                raise ValueError(f"Timeout must be positive, got {value}")
            return value

        raise ValueError(f"Timeout must be an integer, got {value!r}")


@lru_cache
def _get_settings() -> Settings:
    """Return a cached Settings instance (lazy singleton)."""

    return Settings()


class _SettingsProxy:
    """Lazy proxy to defer Settings instantiation until first access."""

    def __getattr__(self, name):
        return getattr(_get_settings(), name)

    def __getitem__(self, key):
        return getattr(_get_settings(), key)


# Proxy exported as settings; avoids constructing Settings at import time
# and prevents failures if environment variables are invalid during collection.
settings = _SettingsProxy()
