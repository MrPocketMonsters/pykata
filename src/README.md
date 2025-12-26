# Src Directory

Contains the core application code organized by concern:

- **api/** - FastAPI application with endpoints for local development
- **lambdas/** - AWS Lambda handlers for production deployment
- **models/** - Pydantic models for data validation and serialization
- **services/** - Business logic and external service integrations
- **data/** - Seed data and sample katas

## Services

### Execution Service (`execution_service.py`)

Provides isolated execution of user-submitted kata code with strict timeout enforcement and cross-platform compatibility.

#### Architecture

The execution service uses a **subprocess isolation strategy** rather than in-process sandboxing for resource control:

- **Separate Python Interpreter**: Each kata execution spawns a fresh Python subprocess, ensuring complete memory isolation from the parent process.
- **Template-Based Code Injection**: User code is injected into a pre-defined wrapper template (`__code_wrapper.py`) that handles:
  - Input stream redirection (replaces `sys.stdin` with user-provided input)
  - Execution timing measurement
  - Exception handling and error capture
  - Metadata reporting via special stderr markers
- **Timeout Enforcement**: Uses `subprocess.run(timeout=...)` for OS-level process termination if execution exceeds the allowed time.

#### Current Guarantees

1. **Process Isolation**: User code runs in a completely separate process with no access to the parent process memory, file handles, or state.
2. **Timeout Protection**: Long-running or infinite loops are forcefully terminated after the specified timeout.
3. **Resource Limits**: The subprocess inherits system resource limits and cannot exhaust parent process resources.
4. **Controlled Execution Environment**: Code runs in a fresh interpreter without access to parent process state or imported modules.

#### Implementation Details

**Wrapper Template (`__code_wrapper.py`)**:

- Contains two placeholders: `"USER_INPUT_PLACEHOLDER"` and `"EXEC_CODE_PLACEHOLDER"`
- Loaded at runtime and placeholders replaced with actual user input and code
- Captures execution time, success status, stdout, and stderr
- Reports metadata via special `__EXECUTION_TIME__` and `__SUCCESS__` markers in stderr

**Execution Flow**:

1. Load wrapper template from disk
2. Replace placeholders with repr-escaped user input and indented user code
3. Spawn subprocess: `python -c <filled_wrapper>`
4. Wait for completion or timeout
5. Parse stderr to extract metadata markers
6. Return `ExecutionResult` with success flag, stdout, stderr, and execution time

**Error Handling**:

- **Timeout**: Returns `ExecutionResult` with `stderr="Execution timed out."`
- **Wrapper Load Failure**: Returns error if template file cannot be read
- **User Code Exception**: Captured in stderr with concise error message
- **Subprocess Failure**: Returns generic "Execution failed" message

#### Cross-Platform Compatibility

This approach works identically on Windows, Linux, macOS, Docker, and AWS Lambda environments using a simple string-based interface that invokes a fresh Python interpreter for each execution.

#### Usage Example

```python
from src.services.execution_service import execute_kata_code

code = '''
name = input()
print(f"Hello, {name}!")
'''

result = execute_kata_code(
    code=code,
    user_input="Alice",
    timeout=5
)

print(f"Success: {result.success}")
print(f"Output: {result.stdout}")
print(f"Time: {result.execution_time_ms}ms")
```

#### Deployment Architecture

In production, this service will be deployed as a **dedicated Lambda function**, separate from the API Gateway Lambda. This architecture provides:

- **Network Isolation**: The execution Lambda will have no internet access or VPC connectivity, responding only to direct invocations from the API Lambda.
- **Blast Radius Containment**: If user code causes crashes or resource exhaustion, only the execution Lambda is affected—the API remains responsive.
- **Independent Scaling**: Execution workloads can scale independently from API traffic.
- **Invocation Pattern**: API Lambda → Direct Lambda Invocation → Execution Lambda → Return Result

#### Future Enhancements

- **Memory Limits**: Enforce via Lambda configuration limits and OS-level controls (`ulimit` on Linux, Windows Job Objects)
- **Disk I/O Restrictions**: Use read-only Lambda layers or container images with restricted filesystem access
- **Static Analysis Pre-check**: Scan for dangerous imports (`os`, `subprocess`, `socket`) before execution
- **Execution Quotas**: Per-user rate limiting and execution time budgets
