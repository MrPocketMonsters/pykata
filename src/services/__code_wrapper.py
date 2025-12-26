"""
Wrapper to execute user-submitted code safely and measure execution time.

This script is intended to be used as a template where the placeholders
`"USER_INPUT_PLACEHOLDER"` and `"EXEC_CODE_PLACEHOLDER"` are replaced at
runtime before execution.
"""

import sys
import time
from io import StringIO


sys.stdin = StringIO("USER_INPUT_PLACEHOLDER")

start_time = time.time()
success = False
try:
    exec("EXEC_CODE_PLACEHOLDER")
    success = True
except Exception as exc:
    print(f"Error during execution: {exc}", file=sys.stderr)
finally:
    execution_time_ms = int((time.time() - start_time) * 1000)
    print(f"__EXECUTION_TIME__:{execution_time_ms}", file=sys.stderr)
    print(f"__SUCCESS__:{success}", file=sys.stderr)
