"""Main API module for the FastAPI application."""

from typing import Annotated

from fastapi import FastAPI, status, Request, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from time import time

from src.config import settings
from src.logger import get_logger
from src.models.kata import KataMetadata, KataExecution, ExecutionResult
from src.api.exceptions import (
    validation_exception_handler,
    not_found_exception_handler,
    request_timeout_exception_handler,
    global_exception_handler,
)
from src.services.dynamo_service import (
    check_health as check_dynamo_health,
    list_katas as dynamo_list_katas,
    get_kata as dynamo_get_kata,
    DynamoServiceError,
    TableNotFoundError,
    ItemNotFoundError,
)
from src.services.s3_service import (
    check_health as check_s3_health,
    download_kata_code as s3_get_kata_code,
    S3ServiceError,
    BucketNotFoundError,
    ObjectNotFoundError,
)
from src.services.execution_service import execute_kata_code as execute_kata

app = FastAPI()

# HTTP request/response logging middleware (1.6.6)
logger = get_logger(__name__)


def __fetch_kata_metadata(kata_id: str) -> KataMetadata:
    """
    Helper function to fetch kata metadata from DynamoDB.
    Args:
        kata_id (str): The unique identifier of the kata.
    Returns:
        KataMetadata: The metadata of the kata.
    Raises:
        ItemNotFoundError: If the kata with the given ID does not exist.
        Exception: For other unexpected errors.
    """
    try:
        kata_metadata: KataMetadata = dynamo_get_kata(kata_id=kata_id)
    except ItemNotFoundError as e:
        raise ItemNotFoundError(f"Kata with ID '{kata_id}' not found.") from e
    except (TableNotFoundError, DynamoServiceError) as e:
        raise Exception("DynamoDB service error") from e
    except Exception as e:
        raise Exception("Unexpected error occurred") from e

    return kata_metadata


def __fetch_kata_code(s3_key: str) -> str:
    """
    Helper function to fetch kata code from S3.
    Args:
        s3_key (str): The S3 key where the kata code is stored.
    Returns:
        str: The code content of the kata.
    Raises:
        ObjectNotFoundError: If the kata code does not exist in S3.
        Exception: For other unexpected errors.
    """
    try:
        kata_code: str = s3_get_kata_code(s3_key=s3_key)
    except ObjectNotFoundError as e:
        raise ObjectNotFoundError(
            f"Kata code for key '{s3_key}' not found in S3."
        ) from e
    except (BucketNotFoundError, S3ServiceError) as e:
        raise Exception("S3 service error") from e
    except Exception as e:
        raise Exception("Unexpected error occurred") from e

    return kata_code


@app.middleware("http")
async def http_logging_middleware(request: Request, call_next):
    """Log each HTTP request and corresponding response with latency.

    - Logs: HTTP method, path, client host, response status and latency in ms.
    - Does not buffer or log full bodies to avoid interfering with downstream handlers.
    """
    start = time()
    response = await call_next(request)
    latency_ms = (time() - start) * 1000.0
    client_addr = None

    try:
        client_addr = request.client.host if request.client else None
    except Exception:
        client_addr = None

    log_reg = f"{request.method} "
    log_reg += f"{request.url.path} "
    log_reg += f"client={client_addr} "
    log_reg += f"status={response.status_code} "
    log_reg += f"latency_ms={latency_ms:.2f}"
    logger.info(log_reg)
    return response


# Register global exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(408, request_timeout_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Register not found exception handlers
for error in [404, ItemNotFoundError, ObjectNotFoundError]:
    app.add_exception_handler(error, not_found_exception_handler)


@app.get("/health")
async def health():
    """
    Health check endpoint for service connectivity validation.

    Validates connections to DynamoDB and S3 services and returns their status.

    Returns:
        JSONResponse: Health status with component statuses and overall health.
            - `status`: "healthy" if all services are up, "degraded" otherwise
            - `services`: Object with `dynamodb` and `s3` boolean status fields
    """
    dynamo_ok = check_dynamo_health()
    s3_ok = check_s3_health()
    all_healthy = dynamo_ok and s3_ok

    return JSONResponse(
        status_code=(
            status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content={
            "status": "healthy" if all_healthy else "degraded",
            "services": {
                "dynamodb": dynamo_ok,
                "s3": s3_ok,
            },
        },
    )


@app.get("/")
async def root():
    """
    Root endpoint for basic health check.

    Returns:
        dict: A simple hello world message.
    """
    return {"message": "API is running"}


@app.get("/katas")
async def get_katas(
    limit: Annotated[int, Query(ge=0)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """
    List kata metadata with simple pagination.

    - Query params: `limit` (default 20), `offset` (default 0)
    - Returns: JSON list of kata metadata objects without code content (`s3_key` removed)
    """
    try:
        katas = dynamo_list_katas(limit=limit, offset=offset)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except (TableNotFoundError, DynamoServiceError) as e:
        raise Exception("DynamoDB service error") from e
    except Exception as e:
        raise Exception("Unexpected error occurred") from e

    # Convert to simple dicts and exclude code storage key to avoid exposing code
    result = []
    for k in katas:
        item = {
            "id": k.id,
            "title": k.title,
            "description": k.description,
            "tags": k.tags,
            "difficulty": k.difficulty,
        }
        result.append(item)

    return result


@app.get("/katas/{kata_id}")
async def get_single_kata(kata_id: str):
    """
    Retrieve a single kata metadata by its ID.

    - Path param: `kata_id`
    - Returns: JSON object of kata metadata without code content (`s3_key` removed)
    """

    kata_metadata = __fetch_kata_metadata(kata_id=kata_id)
    kata_code = __fetch_kata_code(s3_key=kata_metadata.s3_key)

    result = {
        "id": kata_metadata.id,
        "title": kata_metadata.title,
        "description": kata_metadata.description,
        "tags": kata_metadata.tags,
        "difficulty": kata_metadata.difficulty,
        "code": kata_code,
        "sample_input": kata_metadata.sample_input,
        "sample_output": kata_metadata.sample_output,
    }
    return result


@app.post("/katas/run")
async def run_kata(KataExec: KataExecution) -> ExecutionResult:
    """
    Execute a kata with provided input data.

    - Body: `KataExecution` model with `kata_id`, `user_input`, and optional `max_timeout`
    - Returns: `ExecutionResult` model with execution outcome and outputs
    """

    # Fetch kata metadata and code
    kata_metadata = __fetch_kata_metadata(kata_id=KataExec.kata_id)
    kata_code = __fetch_kata_code(s3_key=kata_metadata.s3_key)

    # Determine execution timeout
    timeout = max(0, KataExec.max_timeout or 0)
    timeout = min(timeout, settings.EXECUTION_TIMEOUT)

    # Execute kata code with user input and timeout
    execution_result: ExecutionResult = execute_kata(
        kata_code, KataExec.user_input, timeout
    )

    if (
        execution_result.success is False
        and execution_result.stderr == "Execution timed out."
    ):
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Kata execution timed out.",
        )

    return execution_result
