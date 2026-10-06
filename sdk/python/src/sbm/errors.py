"""Errors of the bot API (spec/api/errors.json, E49), all derived from ChessError."""


class ChessError(Exception):
    """Base class of all errors of the bot API; also raised for internal errors of the core."""


class InvalidArgumentError(ChessError):
    """A value is outside its range, e.g. a square above 63."""


class InvalidFenError(ChessError):
    """A FEN string is malformed or describes an impossible position."""


class InvalidUciError(ChessError):
    """A string is not a move in UCI notation."""


class IllegalMoveError(ChessError):
    """A well-formed move is not legal in the current position."""


class InvalidStateError(ChessError):
    """The operation is not possible in the current state, e.g. undo without history."""


class DataNotFoundError(ChessError):
    """load_data found no data file with that name."""
