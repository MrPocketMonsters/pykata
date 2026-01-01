"""Service for executing katas based on user input."""

import subprocess
import sys
from tempfile import NamedTemporaryFile
from pathlib import Path

from src.models.kata import ExecutionResult
from src.logger import logger, log_call, log_timer, log_context


@log_call
def execute_kata_code(code: str, user_input: str, timeout: int) -> ExecutionResult:
    """
    Execute kata code in an isolated subprocess with timeout.

    The execution wrapper is a small script (`__code_wrapper.py`) that reads
    the path to the kata file from its first command-line argument and
    executes it while measuring execution time and capturing exceptions.

    This function writes the kata `code` to a temporary file and invokes
    the wrapper with the temporary file path. The `user_input` is provided
    to the subprocess via stdin (not embedded into the code string), which
    avoids fragile quoting/escaping when the kata or input contains
    multi-line strings or quotes.

    Args:
        code (str): The user-submitted code to execute.
        user_input (str): The input to provide to the code via stdin.
        timeout (int): Maximum execution time in seconds.

    Returns:
        ExecutionResult: The result of the code execution.
    """

    with log_context("execute_kata_code", timeout=timeout):
        # Load the wrapper template from file
        template_path = Path(__file__).resolve().parent / "__code_wrapper.py"

        # Store the kata code in a temporary file.
        with NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(code)
            temp_path = temp_file.name

        # Run the wrapper subprocess and send the normalized input via stdin
        try:
            with log_timer("subprocess_execution"):
                result = subprocess.run(
                    [sys.executable, str(template_path), str(temp_path)],
                    input=user_input,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )

            # Parse stderr for execution metadata markers written by the wrapper
            stderr_lines = result.stderr.splitlines()
            execution_time_ms = int(timeout * 1000)
            success = False

            # Guard against malformed/missing markers
            if len(stderr_lines) >= 2 and stderr_lines[-2].startswith(
                "__EXECUTION_TIME__:"
            ):
                try:
                    execution_time_ms = int(stderr_lines[-2].split(":", 1)[1])
                    success = stderr_lines[-1].split(":", 1)[1] == "True"
                    stderr_lines = stderr_lines[:-2]
                except Exception:
                    # If parsing fails, keep defaults and include full stderr
                    logger.debug("Failed to parse execution metadata from stderr")

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

        # Clean up the temporary file
        finally:
            try:
                Path(temp_path).unlink()
            except Exception as exc:
                logger.warning(f"Could not delete temporary file {temp_path}: {exc}")
