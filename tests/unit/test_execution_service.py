"""Unit tests for kata execution service."""

import textwrap

from src.services.execution_service import execute_kata_code


def test_execute_kata_success_stdout_and_time():
    code = textwrap.dedent(
        """
        user_val = input()
        print(f"Echo: {user_val}")
        """
    )

    result = execute_kata_code(code, "hello", timeout=1)

    assert result.success is True
    assert "Echo: hello" in result.stdout
    assert result.stderr == ""
    assert result.execution_time_ms >= 0


def test_execute_kata_multiple_inputs_order():
    code = textwrap.dedent(
        """
        first = input()
        second = input()
        print(first)
        print(second)
        """
    )

    result = execute_kata_code(code, "alpha\nbeta", timeout=1)

    assert result.success is True
    assert result.stdout.splitlines() == ["alpha", "beta"]
    assert result.stderr == ""


def test_execute_kata_exception_path():
    code = "raise ValueError('boom')"

    result = execute_kata_code(code, "", timeout=1)

    assert result.success is False
    assert "boom" in result.stderr
    assert result.stdout == ""
    assert result.execution_time_ms >= 0


def test_execute_kata_timeout_path():
    code = textwrap.dedent(
        """
        while True:
            pass
        """
    )

    result = execute_kata_code(code, "", timeout=0.2)

    assert result.success is False
    assert result.stdout == ""
    assert result.stderr == "Execution timed out."
    assert result.execution_time_ms == 0.2 * 1000
