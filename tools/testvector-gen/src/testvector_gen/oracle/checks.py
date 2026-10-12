"""Range checks of arguments that raise InvalidArgument."""

from testvector_gen.codes import BLACK, NO_COLOR, NO_PIECE_TYPE, PIECE_TYPES, SQUARES
from testvector_gen.errors import INVALID_ARGUMENT, ApiError


def square(value: int) -> int:
    if not 0 <= value < SQUARES:
        raise ApiError(INVALID_ARGUMENT)
    return value


def color(value: int) -> int:
    if not 0 <= value <= BLACK:
        raise ApiError(INVALID_ARGUMENT)
    return value


def piece_type(value: int) -> int:
    if not 0 <= value < PIECE_TYPES:
        raise ApiError(INVALID_ARGUMENT)
    return value


def color_or_none(value: int) -> int | None:
    """A color, or None for NO_COLOR."""
    return None if value == NO_COLOR else color(value)


def piece_type_or_none(value: int) -> int | None:
    """A piece type, or None for NO_PIECE_TYPE."""
    return None if value == NO_PIECE_TYPE else piece_type(value)
