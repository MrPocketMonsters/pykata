# Src Directory

Contains the core application code organized by concern:

- **api/** - FastAPI application with endpoints for local development
- **lambdas/** - AWS Lambda handlers for production deployment
- **models/** - Pydantic models for data validation and serialization
- **services/** - Business logic and external service integrations
- **data/** - Seed data and sample katas

## Configuration (`config.py`)

Provides centralized configuration management for the PyKata application using Pydantic's `BaseSettings`.

### How It Works

Configuration values are loaded from environment variables with an optional `.env` file for local development:

```python
from src.config import settings

# Access any configuration value
app_name = settings.APP_NAME  # 'pykata'
debug = settings.DEBUG  # True
timeout = settings.EXECUTION_TIMEOUT  # 300
```

### Configuration Categories

**Application Settings**:

- `APP_NAME`: Application identifier (default: `'pykata'`)
- `APP_ENV`: Deployment environment - dev, staging, or prod (default: `'dev'`)
- `LOG_LEVEL`: Logging verbosity - DEBUG, INFO, WARNING, ERROR (default: `'INFO'`)
- `DEBUG`: Enable debug mode (default: `True`)

**AWS Credentials & Endpoints**:

- `AWS_ACCESS_KEY_ID`: AWS account access key (default: `'test'`)
- `AWS_SECRET_ACCESS_KEY`: AWS account secret key (default: `'test'`)
- `AWS_DEFAULT_REGION`: Default AWS region (default: `'us-east-1'`)
- `AWS_ENDPOINT`: LocalStack endpoint for AWS-compatible mock services (default: `'http://localhost:4566'`)
- `AWS_S3_ENDPOINT`: S3-specific LocalStack endpoint (default: `'http://s3.localhost.localstack.cloud:4566'`)

**AWS Resources**:

- `DYNAMODB_TABLE_NAME`: DynamoDB table for kata metadata (default: `'kata'`)
- `S3_BUCKET_NAME`: S3 bucket for user code storage (default: `'kata-code'`)

**Execution Timeouts** (in seconds):

- `LAMBDA_TIMEOUT`: Maximum time for Lambda function execution (default: `10`)
- `EXECUTION_TIMEOUT`: Maximum time for user kata code execution (default: `300`)

### Environment Setup

1. Copy `.env.example` to `.env`:

   ```bash
   cp .env.example .env
   ```

2. Update values in `.env` as needed for your environment:
   - For **local development** with LocalStack, use the provided defaults
   - For **production**, set actual AWS credentials and endpoints
   - For **debug mode**, set `DEBUG=1`, `DEBUG=true`, or `DEBUG=True` (all work equivalently)

3. Pydantic will automatically:
   - Load the `.env` file on startup
   - Validate and convert values to correct types (strings to ints, booleans, etc.)
   - Use defaults if environment variables are not set
   - Ignore any extra environment variables not defined in Settings

### Validation

- `LOG_LEVEL` must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL (case-insensitive)
- `APP_ENV` is normalized to lowercase and must be one of: dev, staging, prod, production
- `LAMBDA_TIMEOUT` and `EXECUTION_TIMEOUT` must be positive integers; string inputs are converted, invalid values raise on first settings access

### Accessing Settings

A lazy, cached `settings` proxy defers instantiation until first access (avoids import-time failures if local `.env` is invalid):

```python
from src.config import settings

# Application config
if settings.APP_ENV == 'production':
   print(f"Running {settings.APP_NAME} in production")

# AWS resources
table = dynamodb.Table(settings.DYNAMODB_TABLE_NAME)
s3_bucket = s3.Bucket(settings.S3_BUCKET_NAME)

# Execution control
timeout = settings.EXECUTION_TIMEOUT
```

### Best Practices

1. **Import settings once at module level**: Avoids repeated file I/O from `.env` parsing
2. **Use defaults for development**: Only override settings in `.env` when necessary
3. **Separate configs per environment**: Use different `.env` files or export environment variables in CI/CD
4. **Validate on startup**: Pydantic catches type/validation errors immediately on import
5. **Never commit `.env` file**: Add `.env` to `.gitignore` and provide `.env.example` template

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
