"""
Standardized Application Errors & Exception Handlers
"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = exc.errors()
    first_error = details[0] if details else {}
    msg = first_error.get("msg", "Invalid request parameters")
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "E9", "message": f"Validation failed: {msg}"}},
    )
