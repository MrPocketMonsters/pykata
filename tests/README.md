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

With coverage report:

```bash
pytest --cov=src
```

Specific test file:

```bash
pytest tests/unit/test_execution_service.py -v
```

## Unit Tests

### Execution Service (`unit/test_execution_service.py`)

Tests for the secure code execution sandbox (`src/services/execution_service.py`). These tests validate the core isolation, timeout, and I/O capture mechanisms.

#### Test Cases

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

#### Coverage Target

- Target: ≥80% for execution service
- Focus: Subprocess isolation, timeout mechanism, I/O capture, error handling

## Integration Tests

Will test service layers with mocked AWS clients (DynamoDB, S3) and verified interactions between components.

## End-to-End Tests

Will test complete request-response flows through FastAPI endpoints and Lambda handlers against LocalStack or test AWS environment.
