"""Whether a JSON value of a test vector encodes a value of an API type (calls.schema.json).

Integers stay within the range of their primitive, u64 values are written as 0x plus 16 lower-case
hex digits, a Board as its FEN and list<T> as an array. A Move never carries the unused flags 6
and 7 (E34), so no API call can take or return such a value.
"""

import re

from spec_check.api import LIST_TYPE, RANGES, primitive_of

HEX64 = re.compile(r"0x[0-9a-f]{16}")
BOARD = "Board"
MOVE = "Move"
UNUSED_MOVE_FLAGS = (6, 7)


def fits(value: object, type_name: str, types: dict[str, dict]) -> bool:
    match = LIST_TYPE.match(type_name)
    if match:
        element = match.group(1)
        return isinstance(value, list) and all(fits(item, element, types) for item in value)
    if type_name == BOARD:
        return isinstance(value, str)
    primitive = primitive_of(type_name, types)
    if primitive == "bool":
        return isinstance(value, bool)
    if primitive == "u64":
        return isinstance(value, str) and HEX64.fullmatch(value) is not None
    if primitive in RANGES:
        low, high = RANGES[primitive]
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
            and low <= value <= high
            and (type_name != MOVE or value >> 12 not in UNUSED_MOVE_FLAGS)
        )
    return primitive == "string" and isinstance(value, str)
