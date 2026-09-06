from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} with identifier '{identifier}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ValidationAppException(AppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


def make_error_response(code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    payload = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


async def app_exception_handler(request: Request, exc: AppException):
    return make_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    msg = "Request validation failed"
    if errors:
        first_err = errors[0]
        loc = " -> ".join(str(l) for l in first_err.get("loc", []))
        msg = f"{first_err.get('msg')} at {loc}"
    return make_error_response(
        code="VALIDATION_ERROR",
        message=msg,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": errors}
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return make_error_response(
        code="INTERNAL_SERVER_ERROR",
        message=str(exc) if not isinstance(exc, AssertionError) else "Internal assertion failure",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
