"""Asks the web API for a remote game (POST /api/v1/remote/matches, E116)."""

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

API_PATH = "/api/v1/remote/matches"
TIMEOUT_SECONDS = 15


class RemoteError(Exception):
    """The web API did not start the game; code is its error code, e.g. too_many_games."""

    def __init__(self, message: str, code: str = "network") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Seat:
    match_id: str
    seat: str
    color: str
    socket_url: str


def request_game(base_url: str, token: str, body: dict) -> Seat:
    """base_url is the site, e.g. https://schachbotmanager.example.org."""
    parts = urlsplit(base_url.rstrip("/"))
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise RemoteError(f"--remote needs an http or https address, not {base_url!r}", "usage")
    request = urllib.request.Request(
        urlunsplit((parts.scheme, parts.netloc, parts.path + API_PATH, "", "")),
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-SBM-CSRF": "1",
            "User-Agent": "schachbotmanager",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            answer = json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise _api_error(error) from None
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise RemoteError(f"cannot reach {base_url}: {error}") from None
    scheme = "wss" if parts.scheme == "https" else "ws"
    socket_url = urlunsplit((scheme, parts.netloc, parts.path + answer["socket_path"], "", ""))
    return Seat(answer["match_id"], answer["seat"], answer["color"], socket_url)


def _api_error(error: urllib.error.HTTPError) -> RemoteError:
    try:
        answer = json.loads(error.read())
        code, message = answer["code"], answer["message"]
        if answer.get("field"):
            message = f"{answer['field']}: {message}"
    except (ValueError, KeyError, TypeError, OSError):
        code, message = "network", f"HTTP {error.code}"
    return RemoteError(f"the server refused the game ({code}): {message}", code)
