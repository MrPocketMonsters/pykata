"""
Wrapper to execute user-submitted code safely and measure execution time.

This script is intended to be used as a wrapper that loads user code and
executes it while measuring execution time.

Execute it as a subprocess, passing the path to the wrapped code file as
the first argument and providing user input via stdin.
"""

import sys
import time


with open(sys.argv[1], "r", encoding="utf-8") as wrapped_file:
    execution_code = wrapped_file.read()

start_time = time.time()
success = False
try:
    exec(execution_code, {"__name__": "__main__"})
    success = True
except Exception as exc:
    print(f"Error during execution: {exc}", file=sys.stderr)
finally:
    execution_time_ms = int((time.time() - start_time) * 1000)
    print(f"__EXECUTION_TIME__:{execution_time_ms}", file=sys.stderr)
    print(f"__SUCCESS__:{success}", file=sys.stderr)
