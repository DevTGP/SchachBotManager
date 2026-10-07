"""Accounts as the API shows them (schemas CurrentUser, User); the hash never leaves."""

from sbm_api.timestamps import optional_timestamp, timestamp


def current_user_view(user: dict) -> dict:
    return {"id": str(user["_id"]), "username": user["username"], "role": user["role"]}


def session_view(user: dict | None) -> dict:
    return {"user": None if user is None else current_user_view(user)}


def user_view(user: dict) -> dict:
    return current_user_view(user) | {
        "active": user["active"],
        "created_at": timestamp(user["created_at"]),
        "last_login_at": optional_timestamp(user["last_login_at"]),
    }
