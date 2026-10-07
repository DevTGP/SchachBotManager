"""One-time links to pages of the SPA; the token follows the #, so no server logs it (E83)."""

INVITE_PAGE = "invite"
RESET_PAGE = "reset-password"


def one_time_link(public_url: str, page: str, token: str) -> str:
    return f"{public_url.rstrip('/')}/{page}#{token}"
