"""Converts values between the encoding of the call vectors and Python (E55)."""

import sbm

# Types whose vector value is the string 0x plus 16 hex digits.
HEX_TYPES = {"u64", "Bitboard"}


def decode(value, type_name: str):
    """A vector argument as the Python value passed to the binding."""
    if type_name == "Move":
        return sbm.Move.from_value(value)
    return value


def encode(value, type_name: str):
    """A value returned by the binding in the encoding of the vectors."""
    if type_name.startswith("list<"):
        item = type_name[len("list<") : -1]
        return [encode(entry, item) for entry in value]
    if type_name == "Move":
        return value.value()
    if type_name == "Board":
        return value.fen()
    if type_name in HEX_TYPES:
        return f"0x{value:016x}"
    return value
