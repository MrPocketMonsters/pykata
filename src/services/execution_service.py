"""Service for executing katas based on user input."""

import subprocess
import sys

from src.models.kata import ExecutionResult
from pathlib import Path


def execute_kata_code(code: str, user_input: str, timeout: int) -> ExecutionResult:
    """
    Execute kata code in an isolated subprocess with timeout.

    The wrapper template lives in `__code_wrapper.py` next to this module and
    contains the placeholders `"USER_INPUT_PLACEHOLDER"` and
    `"EXEC_CODE_PLACEHOLDER"` which are replaced at runtime.

    Args:
        code (str): The user-submitted code to execute.
        user_input (str): The input to provide to the code via stdin.
        timeout (int): Maximum execution time in seconds.

    Returns:
        ExecutionResult: The result of the code execution.
    """

    # Load the wrapper template from file
    wrapper_path = Path(__file__).resolve().parent / "__code_wrapper.py"
    try:
        wrapper_text = wrapper_path.read_text(encoding="utf-8")
    except Exception as exc:
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Could not load wrapper: {exc}",
            execution_time_ms=0,
        )

    # replace the placeholders
    filled = wrapper_text.replace('"USER_INPUT_PLACEHOLDER"', repr(user_input)).replace(
        '"EXEC_CODE_PLACEHOLDER"', repr(code)
    )

    # Run the code in a subprocess
    try:
        result = subprocess.run(
            [sys.executable, "-c", filled],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Parse the special stderr lines for execution time and success
        stderr_lines = result.stderr.splitlines()
        execution_time_ms = int(timeout * 1000)
        success = False
        if stderr_lines[-2].startswith("__EXECUTION_TIME__:"):
            execution_time_ms = int(stderr_lines[-2].split(":", 1)[1])
            success = stderr_lines[-1].split(":", 1)[1] == "True"
            stderr_lines = stderr_lines[:-2]

        # Return the execution result
        return ExecutionResult(
            success=success,
            stdout=result.stdout,
            stderr="\n".join(stderr_lines),
            execution_time_ms=int(execution_time_ms),
        )

    # Handle timeouts and other exceptions
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            success=False,
            stdout="",
            stderr="Execution timed out.",
            execution_time_ms=int(timeout * 1000),
        )
    except Exception as exc:
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Execution failed: {exc}",
            execution_time_ms=0,
        )
