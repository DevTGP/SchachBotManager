"""The role player plays against bots and does nothing else (E103, E115)."""

from accounts import CSRF


def test_players_cannot_upload_or_set_games(login, reference_bots):
    player, _ = login("pat", "player")

    assert player.get("/api/v1/account/bots").status_code == 403
    assert player.post("/api/v1/bots", data={}, headers=CSRF).status_code == 403
    request = {
        "white_bot_id": str(reference_bots[0]["_id"]),
        "black_bot_id": str(reference_bots[1]["_id"]),
        "initial_time_ms": 60_000,
    }
    assert player.post("/api/v1/matches", json=request, headers=CSRF).status_code == 403
    patch = player.patch(
        f"/api/v1/bots/{reference_bots[0]['_id']}", json={"description": "x"}, headers=CSRF
    )
    assert patch.status_code == 403


def test_players_see_their_session_and_change_their_password(login):
    player, _ = login("pat", "player")
    assert player.get("/api/v1/session").json["user"]["role"] == "player"


def test_admins_invite_players(admin):
    response = admin.post("/api/v1/admin/invites", json={"role": "player"}, headers=CSRF)
    assert response.status_code == 201
