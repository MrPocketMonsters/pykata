"""Unit tests for application configuration."""

import pytest
from src.config import Settings


class TestConfigDefaults:
    """Test default configuration values."""

    def test_default_app_name(self, clean_env):
        """Test default APP_NAME value."""
        settings = Settings()
        assert settings.APP_NAME == "pykata"

    def test_default_log_level(self, clean_env):
        """Test default LOG_LEVEL value."""
        settings = Settings()
        assert settings.LOG_LEVEL == "INFO"

    def test_default_execution_timeout(self, clean_env):
        """Test default EXECUTION_TIMEOUT value."""
        settings = Settings()
        assert settings.EXECUTION_TIMEOUT == 300

    def test_default_aws_endpoints(self, clean_env):
        """Test default AWS endpoints point to LocalStack."""
        settings = Settings()
        assert settings.AWS_ENDPOINT == "http://localhost:4566"
        assert settings.AWS_S3_ENDPOINT == "http://s3.localhost.localstack.cloud:4566"


class TestEnvironmentVariables:
    """Test configuration loading from environment variables."""

    def test_env_override_app_name(self, monkeypatch):
        """Test that APP_NAME can be overridden via environment variable."""
        monkeypatch.setenv("APP_NAME", "custom-app")
        settings = Settings()
        assert settings.APP_NAME == "custom-app"

    def test_env_override_timeouts(self, monkeypatch):
        """Test that timeout values can be overridden as integers."""
        monkeypatch.setenv("LAMBDA_TIMEOUT", "30")
        monkeypatch.setenv("EXECUTION_TIMEOUT", "600")
        settings = Settings()
        assert settings.LAMBDA_TIMEOUT == 30
        assert settings.EXECUTION_TIMEOUT == 600

    def test_env_override_app_env_normalizes(self, monkeypatch):
        """APP_ENV values are normalized to lowercase and validated."""
        monkeypatch.setenv("APP_ENV", "Production")
        settings = Settings()
        assert settings.APP_ENV == "production"


class TestBooleanConversion:
    """Test DEBUG boolean conversion from various formats."""

    def test_debug_string_true(self, monkeypatch):
        """Test that DEBUG='true' converts to True."""
        monkeypatch.setenv("DEBUG", "true")
        settings = Settings()
        assert settings.DEBUG is True

    def test_debug_string_false(self, monkeypatch):
        """Test that DEBUG='false' converts to False."""
        monkeypatch.setenv("DEBUG", "false")
        settings = Settings()
        assert settings.DEBUG is False


class TestTypeConversion:
    """Test automatic type conversion for configuration values."""

    def test_timeout_string_to_int(self, monkeypatch):
        """Test that string timeout values are converted to integers."""
        monkeypatch.setenv("LAMBDA_TIMEOUT", "25")
        settings = Settings()
        assert isinstance(settings.LAMBDA_TIMEOUT, int)
        assert settings.LAMBDA_TIMEOUT == 25

    def test_invalid_timeout_raises_error(self, monkeypatch):
        """Test that invalid integer values raise validation error."""
        monkeypatch.setenv("LAMBDA_TIMEOUT", "not_a_number")
        with pytest.raises(ValueError):
            Settings()

    def test_negative_timeout_raises_error(self, monkeypatch):
        """Timeouts must be positive integers."""
        monkeypatch.setenv("EXECUTION_TIMEOUT", "-5")
        with pytest.raises(ValueError):
            Settings()


class TestValidation:
    """Test validation constraints for configuration values."""

    def test_invalid_log_level_raises_error(self, monkeypatch):
        """LOG_LEVEL must be a known logging level."""
        monkeypatch.setenv("LOG_LEVEL", "VERBOSE")
        with pytest.raises(ValueError):
            Settings()

    def test_valid_log_level_is_normalized(self, monkeypatch):
        """LOG_LEVEL strings are normalized to uppercase."""
        monkeypatch.setenv("LOG_LEVEL", "debug")
        settings = Settings()
        assert settings.LOG_LEVEL == "DEBUG"

    def test_invalid_app_env_raises_error(self, monkeypatch):
        """APP_ENV must be one of the allowed environments."""
        monkeypatch.setenv("APP_ENV", "qa")
        with pytest.raises(ValueError):
            Settings()


class TestAWSConfiguration:
    """Test AWS-related configuration."""

    def test_aws_endpoint_defaults(self, clean_env):
        """Test that AWS endpoints point to LocalStack by default."""
        settings = Settings()
        assert settings.AWS_ENDPOINT == "http://localhost:4566"
        assert settings.AWS_S3_ENDPOINT == "http://s3.localhost.localstack.cloud:4566"

    def test_env_override_aws_credentials(self, monkeypatch):
        """Test that AWS credentials can be overridden via environment."""
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
        monkeypatch.setenv(
            "AWS_SECRET_ACCESS_KEY", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        )
        settings = Settings()
        assert settings.AWS_ACCESS_KEY_ID == "AKIAIOSFODNN7EXAMPLE"
        assert (
            settings.AWS_SECRET_ACCESS_KEY == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        )


class TestConfigurationModel:
    """Test configuration model behavior."""

    def test_settings_model_dump(self, clean_env):
        """Test that all settings can be dumped to a dictionary."""
        settings = Settings()
        config_dict = settings.model_dump()
        assert isinstance(config_dict, dict)
        assert "APP_NAME" in config_dict
        assert "DEBUG" in config_dict
        assert "EXECUTION_TIMEOUT" in config_dict

    def test_case_insensitive_env_vars(self, monkeypatch):
        """Test that extra environment variables are ignored."""
        monkeypatch.setenv("RANDOM_UNDEFINED_VAR", "should_be_ignored")
        # Should not raise an error
        settings = Settings()
        assert not hasattr(settings, "RANDOM_UNDEFINED_VAR")
