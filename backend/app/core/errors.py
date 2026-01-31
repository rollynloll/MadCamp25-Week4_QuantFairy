from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class APIError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        detail: str | None = None,
        details: list[dict[str, str]] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail
        self.details = details
        self.status_code = status_code


def api_error_response(
    code: str,
    message: str,
    detail: str | None,
    details: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        payload["details"] = details
    else:
        payload["detail"] = detail
    return {"error": payload}


def add_exception_handlers(app) -> None:
    @app.exception_handler(APIError)
    async def _handle_api_error(request: Request, exc: APIError):  # noqa: ARG001
        return JSONResponse(
            status_code=exc.status_code,
            content=api_error_response(
                exc.code, exc.message, exc.detail, exc.details
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        request: Request, exc: RequestValidationError
    ):  # noqa: ARG001
        return JSONResponse(
            status_code=422,
            content=api_error_response(
                "VALIDATION_ERROR", "Request validation failed", str(exc)
            ),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected_error(request: Request, exc: Exception):  # noqa: ARG001
        return JSONResponse(
            status_code=500,
            content=api_error_response("INTERNAL_ERROR", "Unexpected error", str(exc)),
        )
