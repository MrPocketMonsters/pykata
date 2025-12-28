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

### Configuration (`unit/test_config.py`)

Tests for the application configuration system (`src/config.py`). Validates that settings are correctly loaded from environment variables and `.env` files with proper type conversion.

#### Shared Fixtures

**`clean_env` (defined in `conftest.py`)**:
A pytest fixture that provides a clean testing environment by:

- Removing all configuration-related environment variables
- Patching the `Settings` class to disable `.env` file loading
- Automatically restoring the original configuration after each test

This ensures tests read actual default values instead of values from the `.env` file.

**`force_valid_logging` (autouse, defined in `conftest.py`)**:
Applied to every test. It disables `.env` loading for the Settings model and forces `LOG_LEVEL=INFO` to avoid failures when a local `.env` contains invalid log levels during test collection.

**Usage**: Add `clean_env` parameter to any test that needs to verify default behavior:

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

**Coverage Target:**

- Target: ≥80% for execution service
- Focus: Subprocess isolation, timeout mechanism, I/O capture, error handling

## Integration Tests

Will test service layers with mocked AWS clients (DynamoDB, S3) and verified interactions between components.

## End-to-End Tests

Will test complete request-response flows through FastAPI endpoints and Lambda handlers against LocalStack or test AWS environment.
