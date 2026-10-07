"""The session cookie: HttpOnly, SameSite=Strict, only sent to the API (E84)."""

from datetime import timedelta

from flask import Response, request

from sbm_api import context

NAME = "sbm_session"
PATH = "/api/"
LIFETIME = timedelta(days=14)


def read() -> str | None:
    return request.cookies.get(NAME)


def put(response: Response, token: str) -> None:
    response.set_cookie(
        NAME,
        token,
        max_age=int(LIFETIME.total_seconds()),
        path=PATH,
        secure=context.secure_cookies(),
        httponly=True,
        samesite="Strict",
    )


def remove(response: Response) -> None:
    response.delete_cookie(
        NAME, path=PATH, secure=context.secure_cookies(), httponly=True, samesite="Strict"
    )
