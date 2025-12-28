# Tests Directory

Comprehensive test suite for validating the functionality of service layers, API endpoints, and Lambda handlers. Tests are organized by scope and executed via pytest with coverage tracking.

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

#### Shared Fixtures (from `conftest.py`)

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

## Integration Tests

Will test service layers with mocked AWS clients (DynamoDB, S3) and verified interactions between components.

## End-to-End Tests

Will test complete request-response flows through FastAPI endpoints and Lambda handlers against LocalStack or test AWS environment.
