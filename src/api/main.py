"""Main API module for the FastAPI application."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from src.api.exceptions import (
    validation_exception_handler,
    not_found_exception_handler,
    request_timeout_exception_handler,
    global_exception_handler,
)

app = FastAPI()

# Register global exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(404, not_found_exception_handler)
app.add_exception_handler(408, request_timeout_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


@app.get("/")
async def root():
    """Root endpoint for first health check."""
    return {"message": "Hello World"}
