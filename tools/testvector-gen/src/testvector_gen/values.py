"""JSON encoding of values that JSON numbers cannot carry exactly (calls.schema.json)."""


def u64(value: int) -> str:
    """u64 and Bitboard as 0x plus 16 lower-case hex digits."""
    return f"0x{value:016x}"
