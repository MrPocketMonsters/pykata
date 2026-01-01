# Src Directory

Contains the core application code organized by concern:

- **api/** - FastAPI application with endpoints for local development
- **lambdas/** - AWS Lambda handlers for production deployment
- **models/** - Pydantic models for data validation and serialization
- **services/** - Business logic and external service integrations
- **data/** - Seed data and sample katas

## Table of Contents

- [API](#api-api)
  - [Main Application](#main-application-apimainpy)
  - [Health Check Service](#health-check-service-get-health)
  - [Katas List Endpoint](#katas-list-endpoint-get-katas)
  - [Single Kata Endpoint](#single-kata-endpoint-get-kataskata_id)
  - [Kata Execution Endpoint](#kata-execution-endpoint-post-katasrun)
  - [Exception Handlers](#exception-handlers-apiexceptionspy)
- [Configuration](#configuration-configpy)
- [Logger](#logger-loggerpy)
- [Services](#services)
  - [Dynamo Service](#dynamo-service-servicesdynamo_servicepy)
  - [S3 Service](#s3-service-servicess3_servicepy)
  - [Execution Service](#execution-service-execution_servicepy)

## API (`api/`)

### Main Application (`api/main.py`)

The FastAPI application entrypoint that configures global exception handlers and defines API endpoints including health checks.

**How It Works:**

The application bootstraps by registering global exception handlers for consistent error responses across all endpoints.

**Registered Handlers:**

- `RequestValidationError` → 400 Bad Request with validation details
- `404` → Not Found with requested path
- `408` → Request Timeout with requested path
- `Exception` → 500 Internal Server Error with generic message

### Health Check Service (`GET /health`)

Provides service connectivity validation by checking both DynamoDB and S3 availability.

**Response:**

- **Status 200** (Healthy): All services operational

  ```json
  {
    "status": "healthy",
    "services": {
      "dynamodb": true,
      "s3": true
    }
  }
  ```

- **Status 503** (Degraded): One or more services unavailable

  ```json
  {
    "status": "degraded",
    "services": {
      "dynamodb": false,
      "s3": true
    }
  }
  ```

**How It Works:**

The endpoint calls `check_health()` methods from both DynamoDB and S3 services to verify connectivity. Returns 200 if all healthy, 503 if any degraded.

**Usage Example:**

```bash
$ curl http://localhost:8000/health
{"status":"healthy","services":{"dynamodb":true,"s3":true}}
```

### Katas List Endpoint (`GET /katas`)

Provides paginated listing of kata metadata without code content. Returns metadata records only — code retrieval is a separate operation.

**Query Parameters:**

- `limit` (int, default: 20): Maximum number of items to return
- `offset` (int, default: 0): Starting offset for pagination

**Response:**

- **Status 200** (Success): JSON array of kata metadata objects

  ```json
  [
    {
      "id": "kata-123",
      "title": "Reverse String",
      "description": "Reverse a given string",
      "tags": ["strings", "algorithms"],
      "difficulty": "beginner"
    }
  ]
  ```

  Note: The `s3_key`, `sample_input`, and `sample_output` fields are intentionally excluded to reduce payload size and avoid exposing code storage locations.

**Error Responses:**

- **400 Bad Request**: Invalid query parameters (negative limit/offset)
- **500 Internal Server Error**: DynamoDB service errors (table unavailable, client errors)

**How It Works:**

The endpoint invokes `list_katas(limit, offset)` from the DynamoDB service to scan and paginate metadata records. Each record is filtered to exclude the `s3_key` field before returning to the client, ensuring code content remains inaccessible through this endpoint.

**Usage Example:**

```bash
$ curl "http://localhost:8000/katas?limit=10&offset=0"
[{"id":"kata-1","title":"Hello World",...}]
```

### Single Kata Endpoint (`GET /katas/{kata_id}`)

Provides retrieval of a single kata's metadata by its unique identifier with code content and sample I/O included.

**Path Parameters:**

- `kata_id` (str): Unique identifier of the kata to retrieve

**Response:**

- **Status 200** (Success): JSON object of kata metadata

  ```json
  {
    "id": "kata-123",
    "title": "Reverse String",
    "description": "Reverse a given string",
    "tags": ["strings", "algorithms"],
    "difficulty": "beginner",
    "code": "print(input()[::-1])",
    "sample_input": "hello",
    "sample_output": "olleh"
  }
  ```

**Error Responses:**

- **404 Not Found**: Kata with specified `kata_id` does not exist
- **500 Internal Server Error**: DynamoDB service errors (table unavailable, client errors)

**How It Works:**

The endpoint invokes `get_kata(kata_id)` from the DynamoDB service to fetch the metadata record. If found, it stores the metadata and then uses the `s3_key` field invoke `download_kata_code(s3_key)` from the S3 service to retrieve the actual code content. The final response includes all metadata fields plus the retrieved code except for `s3_key` to avoid exposing code storage locations.

**Usage Example:**

```bash
$ curl "http://localhost:8000/katas/kata-123"
{"id":"kata-123","title":"Reverse String",...}
```

### Kata Execution Endpoint (`POST /katas/run`)

Provides execution of a kata associated to a user-submitted kata ID, input data and execution timeout, returning the execution result including output, errors, and execution time.

**Request Body:**

```json
{
  "kata_id": "kata-123",
  "user_input": "sample input data",
  "max_timeout": 10 // seconds
}
```

**Response:**

- **Status 200** (Success): JSON object with execution result

  Correct execution:

  ```json
  {
    "success": true,
    "stdout": "output from code",
    "stderr": "",
    "execution_time_ms": 150 // milliseconds
  }
  ```

  Execution with errors:

  ```json
  {
    "success": false,
    "stdout": "output from code before error",
    "stderr": "error message from code",
    "execution_time_ms": 50 // milliseconds
  }
  ```

**Error Responses:**

- **404 Not Found**: Kata with specified `kata_id` does not exist
- **500 Internal Server Error**: DynamoDB, S3 service errors (table/bucket unavailable, client errors) or execution service failures.

**How It Works:**

The endpoint accepts a `KataExecution` request body containing the `kata_id`, `user_input`, and optional `max_timeout`. It first retrieves the kata metadata using `get_kata(kata_id)` from the DynamoDB service. If found, it downloads the kata code using `download_kata_code(s3_key)` from the S3 service. Finally, it invokes `execute_kata(code, user_input, timeout)` from the execution service to run the code with the provided input and timeout. The execution result, including success status, stdout, stderr, and execution time, is returned in the response.

**Usage Example:**

```bash
$ curl -X POST "http://localhost:8000/katas/run" \
  -H "Content-Type: application/json" \
  -d '{"kata_id": "kata-123", "user_input": "hello"}'
{"success":true,"stdout":"olleh","stderr":"","execution_time_ms":120}
```

**Notes:**

- The `max_timeout` field is optional; if not provided, a default timeout from configuration is used.
- If the `max_timeout` in negative or exceeds allowed limits, it is clamped to valid values.
- It is not possible to run malicious code that affects the server due to the private storage code retrieval. If user-submitted code is allowed in the future, additional sandboxing and security measures must be implemented.

### Exception Handlers (`api/exceptions.py`)

Provides centralized exception handling for the FastAPI application with standardized JSON responses and comprehensive logging.

**Response Structure:**

All exception handlers return JSON with the following fields:

- **`detail`**: Human-readable error message or description
- **`status_code`**: HTTP status code (400, 404, 408, 500)
- **`errors`** (400 only): List of validation errors with field details
- **`path`** (404, 408 only): The requested path that triggered the error

#### Available Handlers

**`validation_exception_handler(request, exc)`**:

Handles FastAPI validation errors (400 Bad Request) when request parameters or body fail Pydantic validation.

- **Triggered by**: Invalid query params, path params, or request body
- **Logs**: Warning with full validation error details
- **Response**: `{"detail": "Bad Request", "status_code": 400, "errors": [...]}`

**`not_found_exception_handler(request, exc)`**:

Handles requests to non-existent routes (404 Not Found).

- **Triggered by**: Routes that don't match any defined endpoint
- **Logs**: Warning with requested path
- **Response**: `{"detail": "Not Found", "status_code": 404, "path": "/requested/path"}`

**`request_timeout_exception_handler(request, exc)`**:

Handles request timeout errors (408 Request Timeout) when operations exceed allowed time.

- **Triggered by**: Long-running operations that exceed timeout thresholds
- **Logs**: Warning with requested path
- **Response**: `{"detail": "Request Timeout", "status_code": 408, "path": "/requested/path"}`

**`global_exception_handler(request, exc)`**:

Catches all unhandled exceptions (500 Internal Server Error) as a safety net.

- **Triggered by**: Any unhandled Python exception in endpoint code
- **Logs**: Error with full exception traceback for debugging
- **Response**: `{"detail": "Internal Server Error", "status_code": 500}` (no sensitive details exposed)

**Best Practices:**

1. **Raise HTTPException explicitly**: Use `raise HTTPException(status_code=408)` for controlled timeouts
2. **Let validation happen automatically**: Pydantic will trigger 400 for invalid input types
3. **Don't catch everything**: Let unexpected exceptions bubble up to the 500 handler for proper logging
4. **Use appropriate status codes**: 400 for client errors, 408 for timeouts, 500 for server errors
5. **Never expose sensitive data**: The 500 handler deliberately hides exception details from clients

## Configuration (`config.py`)

Provides centralized configuration management for the PyKata application using Pydantic's `BaseSettings`.

**How It Works:**

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

**Best Practices:**

1. **Import settings once at module level**: Avoids repeated file I/O from `.env` parsing
2. **Use defaults for development**: Only override settings in `.env` when necessary
3. **Separate configs per environment**: Use different `.env` files or export environment variables in CI/CD
4. **Validate on startup**: Pydantic catches type/validation errors immediately on import
5. **Never commit `.env` file**: Add `.env` to `.gitignore` and provide `.env.example` template

## Logger (`logger.py`)

Provides structured logging utilities with context management, timing, and function call tracking for consistent logging across the application.

**How It Works:**

The logger initializes on import and provides utilities for different logging scenarios:

```python
from src.logger import get_logger, log_context, log_timer, log_call

# Get a logger for your module
logger = get_logger(__name__)

# Instrument a function with automatic logging
@log_call
def execute_kata_code(code, user_input, timeout=300):
    with log_context('execute_kata_code', timeout=timeout):
        with log_timer('subprocess_execution'):
            result = subprocess.run(...)
        return result
```

### Logger Utilities

**`get_logger(name=None)`**:
Returns a logger instance for the specified module name. Level is configured from `settings.LOG_LEVEL`.

**`log_context(context_name, **context_vars)`**:
Context manager that logs operation entry/exit with optional context variables. Automatically logs and re-raises exceptions.

**`log_timer(operation_name, level=logging.INFO)`**:
Context manager that measures and logs operation execution time.

**`@log_call`**:
Decorator that automatically logs function entry with arguments, return values, and exceptions. Preserves function metadata.

### Configuration

Valid log levels (from `settings.LOG_LEVEL`): `DEBUG`, `INFO`, `WARNING`, `ERROR`. Invalid values default to `INFO`.

**Best Practices:**

1. **Use `@log_call` on public functions**: Automatically logs entry/exit without manual log statements
2. **Use `log_context` for workflows**: Groups related logs and captures operation context
3. **Use `log_timer` for performance-sensitive code**: Automatically measures and reports execution time
4. **Avoid log spam**: Log at appropriate levels (DEBUG for detailed info, INFO for milestones, WARNING/ERROR for issues)
5. **Include context variables**: Use `log_context(**kwargs)` to add searchable metadata for tracing

## Services

### Dynamo Service (`services/dynamo_service.py`)

Encapsulates DynamoDB access for kata metadata. Uses `boto3` with endpoints sourced from `settings` so it works against LocalStack or AWS transparently.

**Capabilities:**

- `get_kata(kata_id)`: Fetch a single kata record; raises `ItemNotFoundError` when absent and `TableNotFoundError` for missing tables.
- `list_katas(limit, offset=0)`: Scan-based pagination using simple offset/limit slicing.
- `create_kata(metadata)`: Persist a new `KataMetadata` item; returns `True` on success.
- `check_health()`: Verify DynamoDB table accessibility; returns `bool` without raising exceptions.

**Error Handling:**

- Maps DynamoDB `ResourceNotFound` errors to `TableNotFoundError`.
- Wraps other client errors in `DynamoServiceError` for consistent upstream handling.
- Health check gracefully handles all exceptions and returns boolean result.

**Usage:**

```python
from src.services.dynamo_service import get_kata, list_katas, create_kata, check_health
from src.models.kata import KataMetadata

# 1) Validate DynamoDB service connectivity for health checks
is_healthy = check_health()

# 2) Retrieve a kata by ID (point lookup)
metadata = get_kata("kata-123")

# 3) Browse katas with simple pagination (scan + slice)
#    'limit' = page size; 'offset' = starting offset
items = list_katas(limit=10, offset=0)

# 4) Create a new kata (returns True on success)
#    Example: clone an existing one and adjust fields
new_metadata = KataMetadata(
   id="kata-123-copy",
   title=f"Copy of {metadata.title}",
   description=metadata.description,
   tags=metadata.tags,
   difficulty=metadata.difficulty,
   s3_key="katas/copy.py",
   sample_input=metadata.sample_input,
   sample_output=metadata.sample_output,
)
created = create_kata(new_metadata)
```

**Error Handling:**

- Maps DynamoDB `ResourceNotFound` errors to `TableNotFoundError`.
- Wraps other client errors in `DynamoServiceError` for consistent upstream handling.

**Usage:**

```python
from src.services.dynamo_service import get_kata, list_katas, create_kata
from src.models.kata import KataMetadata

# 1) Retrieve a kata by ID (point lookup)
metadata = get_kata("kata-123")

# 2) Browse katas with simple pagination (scan + slice)
#    'limit' = page size; 'offset' = starting offset
items = list_katas(limit=10, offset=0)

# 3) Create a new kata (returns True on success)
#    Example: clone an existing one and adjust fields
new_metadata = KataMetadata(
   id="kata-123-copy",
   title=f"Copy of {metadata.title}",
   description=metadata.description,
   tags=metadata.tags,
   difficulty=metadata.difficulty,
   s3_key="katas/copy.py",
   sample_input=metadata.sample_input,
   sample_output=metadata.sample_output,
)
created = create_kata(new_metadata)
```

### S3 Service (`services/s3_service.py`)

Encapsulates S3 access for kata code storage. Uses `boto3` with endpoints sourced from `settings` so it works against LocalStack or AWS transparently.

**Capabilities:**

- `upload_kata_code(kata_id, s3_key, code)`: Store kata code in S3 and return the given S3 key.
- `download_kata_code(s3_key)`: Retrieve kata code from S3 by key.
- `check_health()`: Validate connectivity to the configured S3 bucket. Returns `True` if accessible, `False` if unavailable. Handles all exceptions gracefully without raising errors, suitable for health check endpoints.

**Error Handling:**

- Maps S3 `NoSuchBucket` errors to `BucketNotFoundError`.
- Maps S3 `NoSuchKey` errors to `ObjectNotFoundError`.
- Wraps other client errors in `S3ServiceError` for consistent upstream handling.

**Usage:**

```python
from src.services.s3_service import upload_kata_code, download_kata_code, check_health

# 1) Validate S3 service connectivity for health checks
is_healthy = check_health()  # Returns True if S3 bucket is accessible, False otherwise

# 2) Upload kata code (returns S3 key)
code = "print('hello')"
s3_key = upload_kata_code("kata-123", "katas/kata-123.py", code)  # Returns: "katas/kata-123.py"

# 3) Download kata code (retrieve by key)
retrieved_code = download_kata_code(s3_key)
```

### Execution Service (`execution_service.py`)

Provides isolated execution of user-submitted kata code with strict timeout enforcement and cross-platform compatibility.

#### Architecture

The execution service uses a **subprocess isolation strategy** rather than in-process sandboxing for resource control:

- **Separate Python Interpreter**: Each kata execution spawns a fresh Python subprocess, ensuring complete memory isolation from the parent process.
- **File-based Wrapper Execution**: The kata source is written to a temporary file and executed by a small wrapper script (`__code_wrapper.py`) which reads the kata file path from its first argument and runs it. The wrapper is responsible for timing, exception capture and emitting metadata markers on stderr.
- **Stdin for User Input**: User-provided input is sent to the wrapper process via stdin; this avoids fragile command-line quoting and escaping when code or input contains quotes, triple-quotes or multi-line content.
- **Timeout Enforcement**: Uses `subprocess.run(timeout=...)` for OS-level process termination if execution exceeds the allowed time.

#### Current Guarantees

1. **Process Isolation**: User code runs in a completely separate process with no access to the parent process memory, file handles, or state.
2. **Timeout Protection**: Long-running or infinite loops are forcefully terminated after the specified timeout.
3. **Resource Limits**: The subprocess inherits system resource limits and cannot exhaust parent process resources.
4. **Controlled Execution Environment**: Code runs in a fresh interpreter without access to parent process state or imported modules.

#### Implementation Details

**Wrapper Script (`__code_wrapper.py`)**:

- The wrapper reads the path to the kata file from `sys.argv[1]` and executes it using `exec()` inside a measured context.
- It writes two metadata markers to stderr at the end of execution: `__EXECUTION_TIME__:<ms>` and `__SUCCESS__:<True|False>`.
- It does not embed user input into the code; user input must be provided via stdin by the caller.

**Execution Flow**:

1. Write the kata `code` to a secure temporary file.
2. Spawn the wrapper subprocess: `python __code_wrapper.py /path/to/temp_kata.py`, passing the input via stdin.
3. Wait for completion or timeout.
4. Parse stderr to extract the `__EXECUTION_TIME__` and `__SUCCESS__` markers; remaining stderr is treated as user error output.
5. Return `ExecutionResult` with success flag, stdout, stderr, and execution time.

**Error Handling**:

- **Timeout**: Returns `ExecutionResult` with `stderr="Execution timed out."` and `success=False`.
- **Wrapper Load Failure**: Returns error if the wrapper or temporary file cannot be read or executed.
- **User Code Exception**: Captured in stderr by the wrapper; execution result reports `success=False`.
- **Subprocess Failure**: Returns a generic `Execution failed` message including the exception.

#### Cross-Platform Compatibility

This approach works identically on Windows, Linux, macOS, Docker, and AWS Lambda environments using a file-based interface and stdin for input.

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

In production, this service can be deployed as a **dedicated execution component** (for example a separate Lambda or container) to provide blast-radius containment, independent scaling and improved isolation.

#### Future Enhancements

- **Memory Limits**: Enforce via Lambda configuration limits and OS-level controls (`ulimit` on Linux, Windows Job Objects).
- **Disk I/O Restrictions**: Use read-only Lambda layers or container images with restricted filesystem access.
- **Static Analysis Pre-check**: Scan for dangerous imports (`os`, `subprocess`, `socket`) before execution.
- **Execution Quotas**: Per-user rate limiting and execution time budgets.
