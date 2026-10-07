"""The error format of the API: {code, message, field?}; the frontend translates the code (E32)."""

import logging

from flask import Flask
from pymongo.errors import ConnectionFailure
from werkzeug.exceptions import HTTPException

log = logging.getLogger(__name__)

INVALID_PARAMETER = "invalid_parameter"
NOT_FOUND = "not_found"
UNAVAILABLE = "unavailable"
INTERNAL = "internal"


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.field = field


def invalid_parameter(field: str, message: str) -> ApiError:
    return ApiError(400, INVALID_PARAMETER, message, field)


def not_found(message: str) -> ApiError:
    return ApiError(404, NOT_FOUND, message)


def body(code: str, message: str, field: str | None = None) -> dict:
    error = {"code": code, "message": message}
    if field is not None:
        error["field"] = field
    return error


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def api_error(error: ApiError):
        return body(error.code, error.message, error.field), error.status

    @app.errorhandler(HTTPException)
    def http_error(error: HTTPException):
        # Unknown paths and methods; the API has no other client errors yet.
        code = NOT_FOUND if error.code in (404, 405) else INVALID_PARAMETER
        return body(code, error.description or error.name), error.code

    @app.errorhandler(ConnectionFailure)
    def database_unavailable(error: ConnectionFailure):
        log.warning("database unavailable: %s", error)
        return body(UNAVAILABLE, "the database is unavailable"), 503

    @app.errorhandler(Exception)
    def internal_error(error: Exception):
        log.exception("unhandled error")
        return body(INTERNAL, "internal error"), 500
