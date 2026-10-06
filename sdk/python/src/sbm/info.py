"""Info as the info object of a move message, within the limits of the protocol (E43, E63).

A field outside its limits would make the referee score a protocol violation, although info is
display only. The SDK therefore truncates pv and text and leaves out other invalid fields with a
warning.
"""

import operator

from sbm.errors import ChessError
from sbm.log import Log
from sbm.records import Info

MAX_PV_MOVES = 32
MAX_TEXT_LENGTH = 256

# Field: inclusive range from move.schema.json
INTEGER_LIMITS = {
    "depth": (0, 1024),
    "seldepth": (0, 1024),
    "score_cp": (-100_000, 100_000),
    "score_mate": (-1024, 1024),
    "nodes": (0, 2**53 - 1),
}


def _integer(name: str, value: object) -> int | None:
    low, high = INTEGER_LIMITS[name]
    try:
        number = operator.index(value)
    except TypeError:
        number = None
    if number is None or not low <= number <= high or (name == "score_mate" and number == 0):
        Log.warn(f"report: {name}={value!r} is outside the protocol limits and is not sent")
        return None
    return number


def _pv(moves: object) -> list[str]:
    try:
        moves = list(moves)
    except TypeError:
        Log.warn(f"report: pv={moves!r} is not a list of moves and is not sent")
        return []
    if len(moves) > MAX_PV_MOVES:
        Log.debug(f"report: pv truncated to {MAX_PV_MOVES} moves")
    pv = []
    for move in moves[:MAX_PV_MOVES]:
        try:
            pv.append(move.uci())
        except (AttributeError, ChessError):
            Log.warn(f"report: pv ends before {move!r}, which has no UCI form")
            break
    return pv


def _text(text: object) -> str | None:
    if not isinstance(text, str):
        Log.warn(f"report: text={text!r} is not a str and is not sent")
        return None
    # Lone surrogates have no UTF-8 form.
    return text[:MAX_TEXT_LENGTH].encode("utf-8", "replace").decode("utf-8")


def info_fields(info: Info) -> dict:
    """The info object for the move message; empty if no field is set."""
    fields: dict = {}
    for name in INTEGER_LIMITS:
        value = getattr(info, name)
        if value is not None and (number := _integer(name, value)) is not None:
            fields[name] = number
    if "score_cp" in fields and "score_mate" in fields:
        Log.warn("report: score_cp and score_mate are both set; only score_mate is sent")
        del fields["score_cp"]
    if info.pv is not None:
        fields["pv"] = _pv(info.pv)
    if info.text is not None and (text := _text(info.text)) is not None:
        fields["text"] = text
    return fields
