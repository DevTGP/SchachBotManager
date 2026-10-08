"""API tokens as the account page shows them (E116); the token itself only once, when made."""

from sbm_api.timestamps import optional_timestamp, timestamp


def token_view(document: dict) -> dict:
    return {
        "id": str(document["_id"]),
        "name": document["name"],
        "created_at": timestamp(document["created_at"]),
        "last_used_at": optional_timestamp(document["last_used_at"]),
    }
