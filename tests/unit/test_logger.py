"""Unit tests for logger module utilities."""

import logging
import pytest
import time
from src.logger import (
    logger,
    get_logger,
    log_context,
    log_timer,
    log_call,
    _normalize_level,
)


class TestNormalizeLevel:
    """Test the _normalize_level helper function."""

    def test_normalize_string_level(self):
        """Test converting string log level names."""
        assert _normalize_level("DEBUG") == logging.DEBUG
        assert _normalize_level("INFO") == logging.INFO
        assert _normalize_level("WARNING") == logging.WARNING
        assert _normalize_level("ERROR") == logging.ERROR

    def test_normalize_integer_level(self):
        """Test that integer levels are returned as-is."""
        assert _normalize_level(logging.DEBUG) == logging.DEBUG
        assert _normalize_level(logging.INFO) == logging.INFO

    def test_normalize_invalid_defaults_to_info(self):
        """Test that invalid values default to INFO."""
        assert _normalize_level("INVALID") == logging.INFO
        assert _normalize_level("NONE") == logging.INFO
        assert _normalize_level(None) == logging.INFO


class TestLoggerInitialization:
    """Test logger initialization."""

    def test_logger_exists(self):
        """Test that logger instance is created."""
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance."""
        test_logger = get_logger("test.module")
        assert isinstance(test_logger, logging.Logger)
        assert test_logger.name == "test.module"


class TestLogContext:
    """Test log_context context manager."""

    def test_log_context_basic(self, caplog):
        """Test basic context entry/exit logging."""
        with caplog.at_level(logging.INFO):
            with log_context("test_operation"):
                pass

        log_text = caplog.text
        assert "Entering test_operation" in log_text
        assert "Exiting test_operation" in log_text

    def test_log_context_logs_exceptions(self, caplog):
        """Test that exceptions in context are logged."""
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                with log_context("failing_op"):
                    raise ValueError("Test error")

        log_text = caplog.text
        assert "Error in failing_op" in log_text

    def test_log_context_reraises_exceptions(self):
        """Test that context manager re-raises exceptions."""
        with pytest.raises(RuntimeError, match="Test error"):
            with log_context("operation"):
                raise RuntimeError("Test error")


class TestLogTimer:
    """Test log_timer context manager."""

    def test_log_timer_logs_completion(self, caplog):
        """Test that timer logs start and completion."""
        with caplog.at_level(logging.INFO):
            with log_timer("test_operation"):
                time.sleep(0.01)

        log_text = caplog.text
        assert "Starting test_operation" in log_text
        assert "test_operation completed in" in log_text

    def test_log_timer_custom_level(self, caplog):
        """Test timer with custom logging level."""
        with caplog.at_level(logging.DEBUG):
            with log_timer("debug_op", level=logging.DEBUG):
                pass

        log_text = caplog.text
        assert "Starting debug_op" in log_text

    def test_log_timer_logs_on_exception(self, caplog):
        """Test that timer logs completion even if exception occurs."""
        with caplog.at_level(logging.INFO):
            with pytest.raises(ValueError):
                with log_timer("failing_op"):
                    raise ValueError("Error")

        log_text = caplog.text
        assert "Starting failing_op" in log_text
        assert "failing_op completed" in log_text


class TestLogCall:
    """Test log_call decorator."""

    def test_log_call_decorator_logs_entry_exit(self, caplog):
        """Test that decorator logs function entry and exit."""

        @log_call
        def sample_func(x, y):
            return x + y

        with caplog.at_level(logging.DEBUG):
            result = sample_func(1, 2)

        log_text = caplog.text
        assert "Calling" in log_text
        assert "sample_func" in log_text
        assert "returned" in log_text
        assert result == 3

    def test_log_call_logs_exceptions(self, caplog):
        """Test that decorator logs exceptions."""

        @log_call
        def failing_func():
            raise ValueError("Test error")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                failing_func()

        log_text = caplog.text
        assert "Exception in" in log_text
        assert "failing_func" in log_text

    def test_log_call_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""

        @log_call
        def my_func():
            """Function docstring."""
            pass

        assert my_func.__name__ == "my_func"
        assert my_func.__doc__ == "Function docstring."


class TestLoggerUtilities:
    """Behavior tests for logger utilities."""

    def test_logger_methods_work(self, caplog):
        """Test that logger methods work correctly."""
        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")

        log_text = caplog.text
        assert "Debug message" in log_text
        assert "Info message" in log_text
        assert "Warning message" in log_text

    def test_get_logger_with_different_modules(self):
        """Test that get_logger creates different loggers for different modules."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1.name == "module1"
        assert logger2.name == "module2"
        assert logger1 is not logger2
