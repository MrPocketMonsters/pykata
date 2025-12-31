# Tests Directory

Comprehensive test suite for validating the functionality of service layers, API endpoints, and Lambda handlers. Tests are organized by scope and executed via pytest with coverage tracking.

## Table of Contents

- [Directory Structure](#directory-structure)
- [Running Tests](#running-tests)
  - [Running Tests with Pytest Flags](#running-tests-with-pytest-flags)
- [Unit Tests](#unit-tests)
  - [Logger](#logger-unittest_loggerpy)
  - [Configuration](#configuration-unittest_configpy)
  - [Execution Service](#execution-service-unittest_execution_servicepy)
  - [Dynamo Service](#dynamo-service-unittest_dynamo_servicepy)
  - [S3 Service](#s3-service-unittest_s3_servicepy)
  - [API Exception Handlers](#api-exception-handlers-unittest_api_exceptionspy)
  - [API Middleware](#api-middleware-unittest_api_middlewarepy)
  - [API Health Check](#api-health-check-unittest_api_healthpy)
  - [Katas List Endpoint](#katas-list-endpoint-unittest_api_kataspy)
- [Integration Tests](#integration-tests)
  - [Prerequisites](#prerequisites)
  - [Running Integration Tests](#running-integration-tests)
  - [Dynamo Service Integration](#dynamo-service-integration-test_dynamo_integrationpy)
  - [S3 Service Integration](#s3-service-integration-test_s3_integrationpy)
- [End-to-End Tests](#end-to-end-tests)

## Directory Structure

```text
tests/
├── conftest.py               # Shared fixtures and test configuration
├── unit/                     # Unit tests for isolated components
├── integration/              # Integration tests (services + AWS mocks)
├── e2e/                      # End-to-end tests (full stack)
└── terraform/                # Infrastructure validation tests
```

## Running Tests

Execute all tests:

```bash
pytest
```

### Running Tests with Pytest Flags

- `-v` / `--verbose`: Show detailed output for each test
- `-vv`: Very verbose (even more detail)
- `-s`: Show print statements and output
- `-x`: Stop on first failure
- `-k "pattern"`: Run only tests matching the pattern
- `--cov=src`: Generate coverage report for `src/` directory
- `--cov-report=html`: Generate HTML coverage report

Example:

```bash
pytest tests/unit/test_config.py -v -s --cov=src
```

## Unit Tests

This are tests for isolated components without external dependencies. Mocks and stubs are used as needed.

### Running Unit Tests

Use the following command to run all unit tests with coverage:

```bash
pytest -m unit -v --cov=src --cov-report=term-missing
```

### Logger (`unit/test_logger.py`)

Tests for the application logging system (`src/logger.py`). Validates that logger utilities work correctly for production use, including context managers, decorators, and level normalization.

**Test Cases:**

- **`test_normalize_level_*`** (`TestNormalizeLevel`): Validates the `_normalize_level()` helper that converts string levels (DEBUG, INFO, WARNING, ERROR) and integer levels to valid logging constants. Defaults to INFO for invalid values.

- **`test_get_logger_*`** (`TestLoggerInitialization`): Verifies logger instances are created correctly and `get_logger(name)` returns properly named logger objects.

- **`test_log_context_*`** (`TestLogContext`): Tests the `log_context()` context manager for logging entry/exit of code blocks, capturing exceptions, and re-raising them after logging.

- **`test_log_timer_*`** (`TestLogTimer`): Validates the `log_timer()` context manager for measuring and logging operation execution time, respecting custom logging levels, and completing logging even with exceptions.

- **`test_log_call_*`** (`TestLogCall`): Tests the `@log_call` decorator for automatic logging of function entry/exit, exception capture, and metadata preservation (`__name__`, `__doc__`).

- **`test_logger_*`** (`TestLoggerIntegration`): Validates overall logger functionality including logger methods and different module logger instances.

**Coverage Target:**

- Target: ≥85% for logger module
- Focus: Helper functions, context managers, decorator behavior

### Configuration (`unit/test_config.py`)

Tests for the application configuration system (`src/config.py`). Validates that settings are correctly loaded from environment variables and `.env` files with proper type conversion.

**Shared Fixtures (from `conftest.py`):**

- `clean_env`: Removes config env vars and disables `.env` loading to test defaults.
- `force_valid_logging` (autouse): Forces a valid `LOG_LEVEL` and disables `.env` parsing for every test.
- `stubbed_client`: Provides a stubbed DynamoDB client using `botocore.stub.Stubber` for AWS-free tests.

**Usage**: Add `clean_env` to tests that need default settings:

```python
def test_default_app_name(self, clean_env):
  settings = Settings()
  assert settings.APP_NAME == 'pykata'
```

**Test Cases (reduced suite):**

- **Default Values** (`TestConfigDefaults`): Core defaults (APP_NAME, LOG_LEVEL, EXECUTION_TIMEOUT, AWS endpoints)
- **Environment Variables** (`TestEnvironmentVariables`): APP_NAME override, timeouts, APP_ENV normalization
- **Boolean Conversion** (`TestBooleanConversion`): Single true/false conversions for DEBUG
- **Type Conversion** (`TestTypeConversion`): Timeout string→int, invalid timeout, negative timeout
- **Validation** (`TestValidation`): Invalid/normalized LOG_LEVEL; invalid APP_ENV
- **AWS Configuration** (`TestAWSConfiguration`): Default LocalStack endpoints; override credentials
- **Model Behavior** (`TestConfigurationModel`): `model_dump()` shape; extra env vars ignored

**Coverage Target:**

- Target: ≥90% for configuration module
- Focus: Default values, type conversion, environment variable handling

### Execution Service (`unit/test_execution_service.py`)

Tests for the secure code execution sandbox (`src/services/execution_service.py`). These tests validate the core isolation, timeout, and I/O capture mechanisms.

**Test Cases:**

- **`test_execute_kata_success_stdout_and_time`**: Validates successful execution of code that reads input and prints output. Asserts:
  - `success=True`
  - stdout contains expected echo output
  - stderr is empty
  - execution time is measured and non-negative

- **`test_execute_kata_multiple_inputs_order`**: Verifies correct handling of multi-line user input. Asserts:
  - successive `input()` calls consume lines in correct order
  - stdout matches expected output sequence
  - stderr is empty

- **`test_execute_kata_exception_path`**: Tests exception handling and error capture. Asserts:
  - `success=False` when code raises an exception
  - exception message is captured in stderr
  - stdout is empty
  - execution time is recorded

- **`test_execute_kata_timeout_path`**: Validates subprocess timeout enforcement. Asserts:
  - Long-running/infinite code is forcefully terminated
  - `success=False`
  - stdout is empty
  - stderr contains "Execution timed out."
  - `execution_time_ms` reflects the timeout duration

### Dynamo Service (`unit/test_dynamo_service.py`)

Tests for DynamoDB metadata service (`src/services/dynamo_service.py`) organized by method-focused classes. Uses the shared `stubbed_client` fixture for isolated AWS interactions.

**Classes & Cases:**

- `TestGetKata`: happy path returns `KataMetadata`; raises `ItemNotFoundError` on missing items; maps `ResourceNotFound` to `TableNotFoundError`.
- `TestListKatas`: validates offset/limit slicing; propagates missing table errors during scans.
- `TestCreateKata`: persists new items; raises on missing table when writing.
- `TestGetKataErrorHandling`: Handles BotoCoreError and other exceptions gracefully.
- `TestListKatasErrorHandling`: Validates error paths for scan operations.
- `TestCreateKataErrorHandling`: Tests error handling for put_item operations.
- `TestCheckHealthDynamo`: Validates DynamoDB health check endpoint.

**Coverage Target:**

- Target: ≥80% for Dynamo service
- Focus: request/response mapping, error translation, pagination behavior

### S3 Service (`unit/test_s3_service.py`)

Tests for S3 code storage service (`src/services/s3_service.py`) organized by method-focused classes. Uses the shared `stubbed_s3_client` fixture for isolated AWS interactions.

**Classes & Cases:**

- `TestUploadKataCode`: successful upload returns S3 key; raises `BucketNotFoundError` for missing bucket; handles special characters and newlines in code.
- `TestDownloadKataCode`: successful download returns code content; raises `ObjectNotFoundError` for missing keys; raises `BucketNotFoundError` for missing bucket.
- `TestUploadKataCodeErrorHandling`: Handles BotoCoreError during upload operations.
- `TestDownloadKataCodeErrorHandling`: Tests error handling for download operations.
- `TestCheckHealthS3`: Validates S3 health check endpoint.

**Coverage Target:**

- Target: ≥80% for S3 service
- Focus: upload/download mapping, error translation, special character handling

### API Exception Handlers (`unit/test_api_exceptions.py`)

Tests for global exception handlers in the FastAPI application (`src/api/exceptions.py`). Validates that all HTTP error responses follow a consistent structure and properly handle different error scenarios.

**Test Application Setup:**

Creates a separate FastAPI instance with test endpoints specifically designed to trigger each exception type. Uses `raise_server_exceptions=False` in the test client to capture exception handler responses instead of re-raising exceptions.

**Test Endpoints:**

- `/`: Root endpoint returning `{"message": "Hello World"}`
- `/test/400`: Accepts `param: int` to trigger validation errors
- `/test/validation`: POST endpoint accepting `param: int` for body validation
- `/test/408`: Raises `HTTPException(408)` to trigger timeout handler
- `/test/500`: Raises `ValueError` to trigger global exception handler

**Test Classes:**

**`TestBadRequest`**: Validates 400 Bad Request handler for validation failures.

- `test_validation_error_returns_400`: Verifies 400 status code for invalid query params
- `test_validation_error_response_structure`: Checks response includes `status_code`, `detail`, and `errors` fields
- `test_post_validation_error_returns_400`: Validates POST body validation triggers same 400 response

**`TestNotFound`**: Validates 404 Not Found handler for non-existent routes.

- `test_not_found_returns_404`: Verifies 404 status code for missing routes
- `test_not_found_response_structure`: Checks response includes `status_code`, `detail`, and `path` fields
- `test_404_with_different_paths`: Validates handler works consistently across multiple non-existent paths

**`TestInternalServerError`**: Validates 500 handler for unhandled exceptions.

- `test_unhandled_exception_returns_500`: Verifies 500 status code for unexpected exceptions
- `test_internal_error_response_structure`: Checks response includes `status_code` and `detail` fields
- `test_internal_error_does_not_expose_traceback`: Ensures sensitive exception details are not exposed to clients

**`TestRequestTimeout`**: Validates 408 Request Timeout handler.

- `test_timeout_exception_returns_408`: Verifies 408 status code when timeout exception is raised
- `test_timeout_response_structure`: Checks response includes `status_code`, `detail`, and `path` fields

**`TestHealthcheck`**: Validates normal endpoint behavior is unaffected by exception handlers.

- `test_root_endpoint_returns_200`: Ensures healthy endpoints return 200 and expected response

**Coverage Target:**

- Target: ≥90% for exception handlers module
- Focus: Response structure consistency, status code accuracy, error detail exposure control

### API Middleware (`unit/test_api_middleware.py`)

Tests for the HTTP logging middleware that logs each incoming request and its response with latency.

**Test Cases:**

- `test_middleware_logs_root_request`: Verifies a request to `/` generates an INFO log containing method, path and `latency_ms=` token.
- `test_middleware_logs_health_status`: Verifies `/health` request logs include the returned status code.
- `test_middleware_latency_is_numeric`: Verifies the `latency_ms` value is present and parseable as a float.

**Coverage Target:**

- Target: ≥90% for API middleware tests
- Focus: Request/response logging, latency formatting, status propagation

### API Health Check (`unit/test_api_health.py`)

Tests for the health check endpoint in the FastAPI application (`src/api/main.py`). Validates the `GET /health` endpoint correctly reports service connectivity for DynamoDB and S3 with appropriate HTTP status codes.

**Test Application Setup:**

Uses the production FastAPI application instance imported from `src.api.main`. Fixtures from `conftest.py` mock the `check_dynamo_health()` and `check_s3_health()` functions using `monkeypatch.setattr()` to control service health states during testing.

**Shared Fixtures (from `conftest.py`):**

- `mock_dynamo_health_up`: Mocks DynamoDB health check to return `True`
- `mock_dynamo_health_down`: Mocks DynamoDB health check to return `False`
- `mock_s3_health_up`: Mocks S3 health check to return `True`
- `mock_s3_health_down`: Mocks S3 health check to return `False`

**Test Classes:**

**`TestHealthCheckAllServicesHealthy`**: Validates endpoint behavior when all services are healthy.

- `test_health_all_services_up`: Verifies endpoint returns 200 status code with `{"status": "healthy", "services": {"dynamodb": true, "s3": true}}`
- `test_health_response_structure`: Validates response structure includes required `status` and `services` fields

**`TestHealthCheckDynamoDown`**: Validates endpoint behavior when DynamoDB service is unavailable.

- `test_health_dynamodb_down`: Verifies endpoint returns 503 Unavailable status with S3 healthy but DynamoDB down
- `test_health_dynamodb_down_returns_unavailable`: Checks response includes `"status": "degraded"` when any service is down

**`TestHealthCheckS3Down`**: Validates endpoint behavior when S3 service is unavailable.

- `test_health_s3_down`: Verifies endpoint returns 503 Unavailable status with DynamoDB healthy but S3 down
- `test_health_s3_down_returns_unavailable`: Checks response includes `"status": "degraded"` when any service is down

**`TestHealthCheckAllServicesDown`**: Validates endpoint behavior when all services are unavailable.

- `test_health_all_services_down`: Verifies endpoint returns 503 Unavailable status with both services down

**`TestHealthCheckIntegration`**: Validates overall health check functionality and integration with root endpoint.

- `test_health_endpoint_exists`: Confirms the `/health` endpoint is accessible and defined
- `test_health_response_is_json`: Validates response has correct JSON content-type header
- `test_root_endpoint_still_works`: Ensures the root endpoint (`GET /`) still functions correctly after health check addition

**Coverage Target:**

- Target: ≥90% for health check endpoint
- Focus: Service status combinations, response structure, status code accuracy

### Katas List Endpoint (`unit/test_api_katas.py`)

Tests for the `GET /katas` endpoint that lists kata metadata with pagination. Validates response schema, pagination behavior, and error handling for service failures.

**Test Cases:**

- **`test_returns_list_with_default_pagination`**: Verifies endpoint returns 200 with JSON array containing metadata objects (id, title, description, tags, difficulty) and excludes `s3_key` field
- **`test_limit_and_offset_paginate_correctly`**: Validates custom `limit` and `offset` query params correctly slice and paginate results
- **`test_response_schema_contains_expected_fields_and_no_code`**: Confirms response contains all required metadata fields and `s3_key` is not present
- **`test_dynamo_errors_map_to_http_errors`**: Tests DynamoDB service errors return HTTP 500 with generic error message without exposing internal exception details

**Coverage Target:**

- Target: ≥90% for katas list endpoint
- Focus: Pagination logic, response filtering, error mapping, security (no data leakage)

## Integration Tests

Integration tests exercise real service interactions against a configured environment.

**Directory Structure:**

```text
integration/     # Both environments
├── dev/         # LocalStack + Terraform dev environment
└── prod/        # AWS production environment
```

### Prerequisites

- DynamoDB endpoint reachable (LocalStack via docker-compose, or AWS)
- Kata table provisioned. For LocalStack dev, apply: see [terraform/environments/dev](../terraform/environments/dev)

**Note:** Integration tests are excluded from the main pytest run in CI. The `integration` job ensures the dev environment is ready (Terraform applied) before running dev integration tests.

**Shared Fixtures (from `conftest.py`):**

- `ensure_dynamo_available`: Provides a configured DynamoDB client for integration tests.

### Running Integration Tests

- Dev suite (LocalStack or dev env):

```bash
pytest -m dev_integration -v -s
```

- Prod suite (AWS production):

```bash
pytest -m prod_integration -v -s
```

- All integration tests that are not production level:

```bash
pytest -m "integration and not prod_integration" -v -s
```

Note: CI workflow runs this set of tests after provisioning the dev environment.

### Dynamo Service Integration (`test_dynamo_integration.py`)

Tests that create a new kata with dummy info, list it, and fetch it:

- `test_create_and_get_kata_integration`: Creates a kata (unique ID), then fetches by ID.
- `test_list_contains_created_kata_integration`: Creates another kata, then verifies listing includes it.

Tests will fail if the DynamoDB endpoint or required table is not available (no skip behavior).

### S3 Service Integration (`test_s3_integration.py`)

Tests that upload and download kata code, verifying round-trip integrity:

- `test_upload_and_download_kata_code_integration`: Upload code with special characters, then download and verify content matches.
- `test_upload_multiple_katas_integration`: Upload multiple katas independently, then verify each can be downloaded with correct content.

Tests will fail if the S3 endpoint or required bucket is not available (no skip behavior).

### Execution Service Integration (`test_execution_integration.py`)

Integration tests for the code execution service combining DynamoDB metadata, S3 code storage, and subprocess execution into a complete kata pipeline:

- `test_full_kata_pipeline_integration`: Full end-to-end flow: (1) upload code to S3, (2) create metadata in DynamoDB, (3) fetch metadata and code, (4) execute retrieved code. Validates that all components integrate correctly.
- `test_kata_execution_with_exception_integration`: Pipeline scenario where uploaded code raises an exception during execution. Verifies exception capture and `success=False` status.
- `test_multiple_kata_executions_integration`: Create and execute multiple independent katas, ensuring isolation and correct content retrieval for each.

Tests will fail if DynamoDB, S3, or execution environment is unavailable.

**Fixtures Used:**

- `ensure_dynamo_available`: Real DynamoDB client
- `ensure_s3_available`: Real S3 client

## End-to-End Tests

Will test complete request-response flows through FastAPI endpoints and Lambda handlers against LocalStack or test AWS environment.

## Coverage Summary

The test suite achieves excellent coverage across all modules:

| Module | Coverage | Status |
| --- | --- | --- |
| API Exceptions | 100% | ✅ |
| API Main | 91% | ✅ |
| Config | 93% | ✅ |
| Logger | 98% | ✅ |
| Models | 100% | ✅ |
| DynamoDB Service | 96% | ✅ |
| Execution Service | 82% | ✅ |
| S3 Service | 100% | ✅ |
| **Total** | **95%** | **✅** |

**Excluded from Coverage:**

- `__code_wrapper.py`: Dynamic template execution (cannot be directly covered via unit tests)

**Target Metrics:**

- Minimum coverage per module: ≥80%
- Overall coverage target: ≥85%
- **Current achievement: 95% overall** ✅
