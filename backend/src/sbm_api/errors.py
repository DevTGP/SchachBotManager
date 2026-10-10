"""The error format of the API: {code, message, field?, path?}; the frontend translates the code
(E32).
"""

import logging
import math
from datetime import datetime

from flask import Flask
from pymongo.errors import ConnectionFailure
from werkzeug.exceptions import HTTPException

log = logging.getLogger(__name__)

INVALID_PARAMETER = "invalid_parameter"
NOT_FOUND = "not_found"
UNAVAILABLE = "unavailable"
INTERNAL = "internal"
UNAUTHENTICATED = "unauthenticated"
FORBIDDEN = "forbidden"
CSRF_FAILED = "csrf_failed"
INVALID_CREDENTIALS = "invalid_credentials"
INVALID_TOKEN = "invalid_token"
USERNAME_TAKEN = "username_taken"
TOO_MANY_ATTEMPTS = "too_many_attempts"
NAME_TAKEN = "name_taken"
UPLOAD_CONFLICT = "upload_conflict"
INVALID_UPLOAD = "invalid_upload"
TOO_LARGE = "too_large"
BUILTIN_BOT = "builtin_bot"
BOT_VERIFYING = "bot_verifying"
BOT_PLAYING = "bot_playing"
# Interactive games (E115).
NO_CAPACITY = "no_capacity"
TOO_MANY_GAMES = "too_many_games"
# Admin interventions in a match (E152).
MATCH_STATE = "match_state"
NOT_REPEATABLE = "not_repeatable"
# Override of a bot that is not rejected (E153).
BOT_STATE = "bot_state"


class ApiError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        field: str | None = None,
        headers: dict[str, str] | None = None,
        *,
        path: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.field = field
        self.headers = headers or {}
        self.path = path


def invalid_parameter(field: str, message: str) -> ApiError:
    return ApiError(400, INVALID_PARAMETER, message, field)


def not_found(message: str) -> ApiError:
    return ApiError(404, NOT_FOUND, message)


def unauthenticated() -> ApiError:
    return ApiError(401, UNAUTHENTICATED, "log in first")


def forbidden(message: str) -> ApiError:
    return ApiError(403, FORBIDDEN, message)


def invalid_credentials() -> ApiError:
    return ApiError(401, INVALID_CREDENTIALS, "wrong name or password")


def invalid_token() -> ApiError:
    return ApiError(400, INVALID_TOKEN, "the link is unknown, used or expired", "token")


def too_many_attempts(now: datetime, retry_at: datetime) -> ApiError:
    seconds = max(1, math.ceil((retry_at - now).total_seconds()))
    return ApiError(
        429,
        TOO_MANY_ATTEMPTS,
        "too many attempts, try again later",
        headers={"Retry-After": str(seconds)},
    )


def no_capacity() -> ApiError:
    return ApiError(503, NO_CAPACITY, "all places for interactive games are taken, try again soon")


def too_many_games() -> ApiError:
    return ApiError(429, TOO_MANY_GAMES, "finish your running game before you start another")


def invalid_upload(message: str, path: str | None) -> ApiError:
    """The files break an upload rule; the message is the detail the frontend shows."""
    return ApiError(400, INVALID_UPLOAD, message, path=path)


def body(code: str, message: str, field: str | None = None, path: str | None = None) -> dict:
    error = {"code": code, "message": message}
    if field is not None:
        error["field"] = field
    if path is not None:
        error["path"] = path
    return error


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def api_error(error: ApiError):
        error_body = body(error.code, error.message, error.field, error.path)
        return error_body, error.status, error.headers

    @app.errorhandler(HTTPException)
    def http_error(error: HTTPException):
        # Unknown paths and methods, and uploads beyond their limit.
        if error.code in (404, 405):
            code = NOT_FOUND
        elif error.code == 413:
            code = TOO_LARGE
        else:
            code = INVALID_PARAMETER
        return body(code, error.description or error.name), error.code

    @app.errorhandler(ConnectionFailure)
    def database_unavailable(error: ConnectionFailure):
        log.warning("database unavailable: %s", error)
        return body(UNAVAILABLE, "the database is unavailable"), 503

    @app.errorhandler(Exception)
    def internal_error(error: Exception):
        log.exception("unhandled error")
        return body(INTERNAL, "internal error"), 500
