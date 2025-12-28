"""Service for executing katas based on user input."""

import subprocess
import sys
from pathlib import Path

from src.models.kata import ExecutionResult
from src.logger import logger, log_call, log_timer, log_context


@log_call
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

    with log_context("execute_kata_code", timeout=timeout):
        # Load the wrapper template from file
        wrapper_path = Path(__file__).resolve().parent / "__code_wrapper.py"
        try:
            wrapper_text = wrapper_path.read_text(encoding="utf-8")
            logger.debug(f"Loaded wrapper template from {wrapper_path}")
        except Exception as exc:
            logger.error(f"Could not load wrapper template: {exc}")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Could not load wrapper: {exc}",
                execution_time_ms=0,
            )

        # Replace the placeholders
        filled = wrapper_text.replace(
            '"USER_INPUT_PLACEHOLDER"', repr(user_input)
        ).replace('"EXEC_CODE_PLACEHOLDER"', repr(code))

        # Run the code in a subprocess with timing
        try:
            with log_timer("subprocess_execution"):
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

            logger.info(
                f"Kata execution completed: success={success}, time={execution_time_ms}ms"
            )
            return ExecutionResult(
                success=success,
                stdout=result.stdout,
                stderr="\n".join(stderr_lines),
                execution_time_ms=int(execution_time_ms),
            )

        # Handle timeouts and other exceptions
        except subprocess.TimeoutExpired:
            logger.warning(f"Kata execution timed out after {timeout}s")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="Execution timed out.",
                execution_time_ms=int(timeout * 1000),
            )
        except Exception as exc:
            logger.error(f"Kata execution failed with exception: {exc}")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution failed: {exc}",
                execution_time_ms=0,
            )
