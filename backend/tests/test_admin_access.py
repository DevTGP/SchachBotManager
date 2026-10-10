"""Every admin route refuses guests (401) and coders (403)."""

import pytest

from accounts import CSRF

USER = "0123456789abcdef01234567"
ADMIN_ROUTES = [
    ("get", "/api/v1/admin/users", None),
    ("patch", f"/api/v1/admin/users/{USER}", {"active": False}),
    ("post", f"/api/v1/admin/users/{USER}/password-reset", None),
    ("get", "/api/v1/admin/invites", None),
    ("post", "/api/v1/admin/invites", {"role": "coder"}),
    ("delete", f"/api/v1/admin/invites/{USER}", None),
    ("post", "/api/v1/admin/matches", {}),
    ("patch", f"/api/v1/admin/matches/{USER}", {"priority": 1}),
    ("post", f"/api/v1/admin/matches/{USER}/cancel", None),
    ("post", f"/api/v1/admin/matches/{USER}/repeat", None),
    ("patch", f"/api/v1/admin/bots/{USER}", {"status": "disabled"}),
    ("delete", f"/api/v1/admin/bots/{USER}", None),
    ("post", f"/api/v1/admin/bots/{USER}/recheck", None),
    ("post", f"/api/v1/admin/bots/{USER}/override", None),
    ("post", "/api/v1/admin/bots/recheck", {"language": "python"}),
    ("patch", "/api/v1/admin/queue", {"paused": True}),
    ("get", "/api/v1/admin/audit", None),
    ("get", "/api/v1/admin/settings", None),
    ("put", "/api/v1/admin/settings/coders", {}),
    ("put", "/api/v1/admin/settings/accounts", {}),
    ("put", "/api/v1/admin/settings/rating", {}),
    ("put", "/api/v1/admin/settings/estimate", {}),
]


@pytest.mark.parametrize(("method", "path", "body"), ADMIN_ROUTES)
def test_guests_must_log_in(client, method, path, body):
    response = getattr(client, method)(path, json=body, headers=CSRF)

    assert response.status_code == 401
    assert response.json["code"] == "unauthenticated"


@pytest.mark.parametrize(("method", "path", "body"), ADMIN_ROUTES)
def test_coders_are_refused(login, method, path, body):
    client, _ = login()

    response = getattr(client, method)(path, json=body, headers=CSRF)

    assert response.status_code == 403
    assert response.json["code"] == "forbidden"
