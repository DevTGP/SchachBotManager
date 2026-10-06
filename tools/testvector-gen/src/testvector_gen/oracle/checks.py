"""Range checks of arguments that raise InvalidArgument."""

from testvector_gen.codes import BLACK, PIECE_TYPES, SQUARES
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
