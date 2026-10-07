"""Secret tokens for sessions, invites and reset links; only their hash is stored (E83, E84)."""

import hashlib
import secrets

TOKEN_BYTES = 32


def new_token() -> str:
    """43 URL-safe characters."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
