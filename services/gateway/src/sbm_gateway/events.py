"""Server-sent events of the live channel (E102, E142), as text ready to write."""

import json

# The browser connects again after this many milliseconds if the stream breaks.
RETRY = "retry: 3000\n\n"
PING = ": ping\n\n"
END = "event: end\ndata: {}\n\n"


def move(data: dict) -> str:
    """The id is the ply, so a reconnecting EventSource asks for the moves after it."""
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: move\nid: {data['ply']}\ndata: {text}\n\n"
