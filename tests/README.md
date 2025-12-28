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
- [Integration Tests](#integration-tests)
  - [Prerequisites](#prerequisites)
  - [Running Integration Tests](#running-integration-tests)
  - [Dynamo Service Integration](#dynamo-service-integration-test_dynamo_integrationpy)
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
pytest -m unit -v -s --cov=src
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

≥85% for logger module. Focus: Helper functions, context managers, decorator behavior.

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

**Coverage Target:**

- Target: ≥80% for Dynamo service
- Focus: request/response mapping, error translation, pagination behavior

### S3 Service (`unit/test_s3_service.py`)

Tests for S3 code storage service (`src/services/s3_service.py`) organized by method-focused classes. Uses the shared `stubbed_s3_client` fixture for isolated AWS interactions.

**Classes & Cases:**

- `TestUploadKataCode`: successful upload returns S3 key; raises `BucketNotFoundError` for missing bucket; handles special characters and newlines in code.
- `TestDownloadKataCode`: successful download returns code content; raises `ObjectNotFoundError` for missing keys; raises `BucketNotFoundError` for missing bucket.

**Coverage Target:**

- Target: ≥80% for S3 service
- Focus: upload/download mapping, error translation, special character handling

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

## End-to-End Tests

Will test complete request-response flows through FastAPI endpoints and Lambda handlers against LocalStack or test AWS environment.
