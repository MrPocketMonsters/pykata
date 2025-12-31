"""Main API module for the FastAPI application."""

from typing import Annotated

from fastapi import FastAPI, status, Request, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from time import time

from src.logger import get_logger
from src.api.exceptions import (
    validation_exception_handler,
    not_found_exception_handler,
    request_timeout_exception_handler,
    global_exception_handler,
)
from src.services.dynamo_service import (
    check_health as check_dynamo_health,
    list_katas as dynamo_list_katas,
    DynamoServiceError,
    TableNotFoundError,
)
from src.services.s3_service import check_health as check_s3_health

app = FastAPI()

# HTTP request/response logging middleware (1.6.6)
logger = get_logger(__name__)


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
app.add_exception_handler(404, not_found_exception_handler)
app.add_exception_handler(408, request_timeout_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


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
