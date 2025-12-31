"""Global exception handlers for the FastAPI application."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.logger import get_logger

logger = get_logger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle 400 Bad Request errors for validation failures.

    Catches FastAPI validation errors and returns a standardized JSON response
    with the validation error details.

    Args:
        request (Request): The incoming HTTP request.
        exc (RequestValidationError): The validation error exception.

    Returns:
        JSONResponse: A 400 status response with error details.
    """
    logger.warning(f"Bad request: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Bad Request",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "errors": exc.errors(),
        },
    )


async def not_found_exception_handler(request: Request, exc):
    """
    Handle 404 Not Found errors.

    Catches requests to non-existent routes and returns a standardized
    JSON response with the requested path.

    Args:
        request (Request): The incoming HTTP request.
        exc: The not found exception.

    Returns:
        JSONResponse: A 404 status response with the requested path.
    """
    logger.warning(f"Not found: {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": "Not Found",
            "status_code": status.HTTP_404_NOT_FOUND,
            "path": str(request.url.path),
        },
    )


async def request_timeout_exception_handler(request: Request, exc):
    """
    Handle 408 Request Timeout errors.

    Catches request timeout exceptions and returns a standardized JSON
    response indicating the request exceeded the allowed time.

    Args:
        request (Request): The incoming HTTP request.
        exc: The timeout exception.

    Returns:
        JSONResponse: A 408 status response with the requested path.
    """
    logger.warning(f"Request timeout: {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_408_REQUEST_TIMEOUT,
        content={
            "detail": "Request Timeout",
            "status_code": status.HTTP_408_REQUEST_TIMEOUT,
            "path": str(request.url.path),
        },
    )


async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle 500 Internal Server Error for unexpected exceptions.

    Catches all unhandled exceptions and returns a generic error response
    without exposing internal error details. Logs the full exception with
    traceback for debugging.

    Args:
        request (Request): The incoming HTTP request.
        exc (Exception): The unhandled exception.

    Returns:
        JSONResponse: A 500 status response with a generic error message.
    """
    logger.error(f"Internal server error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal Server Error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )
