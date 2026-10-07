"""Password hashes with argon2id (E84)."""

from functools import cache

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """True once the hash parameters are weaker than the current ones."""
    return _hasher.check_needs_rehash(password_hash)


def verify_nothing(password: str) -> None:
    """Spends the time of a check for an unknown name, so the answer time reveals nothing."""
    verify(_dummy_hash(), password)


@cache
def _dummy_hash() -> str:
    return _hasher.hash("no account has this password")
