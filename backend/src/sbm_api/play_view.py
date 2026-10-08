"""The answer to a new interactive game: where and with which seat to join it (gateway-v1)."""

SOCKET_PATH = "/api/v1/play/socket"


def seat_view(match_id, seat: str, color: str) -> dict:
    return {"match_id": str(match_id), "seat": seat, "color": color, "socket_path": SOCKET_PATH}
