"""Invites as the API shows them (schema Invite); the token hash stays hidden."""

from sbm_api.timestamps import timestamp


def invite_view(invite: dict) -> dict:
    return {
        "id": str(invite["_id"]),
        "role": invite["role"],
        "created_by": invite["created_by_name"],
        "created_at": timestamp(invite["created_at"]),
        "expires_at": timestamp(invite["expires_at"]),
    }
