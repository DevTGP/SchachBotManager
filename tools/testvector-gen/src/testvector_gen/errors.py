"""Errors of the bot API (spec/api/errors.json) as raised by the oracle."""

INVALID_ARGUMENT = "InvalidArgument"
INVALID_FEN = "InvalidFen"
INVALID_UCI = "InvalidUci"
ILLEGAL_MOVE = "IllegalMove"
INVALID_STATE = "InvalidState"


class ApiError(Exception):
    """A call fails with the API error `name`."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.name = name
