"""Protection against cross-site requests: every request other than GET carries a header (E84).

Another site can send a form or a simple request, but not a custom header without a CORS
preflight, which the API never allows. SameSite=Strict on the cookie is the second layer.
"""

from flask import Flask, request

from sbm_api.errors import CSRF_FAILED, ApiError

HEADER = "X-SBM-CSRF"
VALUE = "1"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def register(app: Flask) -> None:
    @app.before_request
    def check_header() -> None:
        # Unknown paths and methods stay 404 for the error handler.
        if request.method in SAFE_METHODS or request.url_rule is None:
            return
        if request.headers.get(HEADER) != VALUE:
            raise ApiError(403, CSRF_FAILED, f"the header {HEADER}: {VALUE} is missing")
