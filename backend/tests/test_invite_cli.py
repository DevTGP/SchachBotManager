import pytest
from sbm_store import account_settings
from sbm_store.account_settings import AccountSettings
from sbm_store.names import AUDIT_LOG, INVITES
from sbm_store.tokens import token_hash

from sbm_api.invite_cli import main


@pytest.fixture
def environ(db, mongo_uri) -> dict[str, str]:
    return {
        "SBM_MONGO_URI": mongo_uri,
        "SBM_MONGO_DB": db.name,
        "SBM_PUBLIC_URL": "https://sbm.example/",
    }


def test_prints_a_link_for_the_first_admin(db, environ, capsys):
    assert main(["--role", "admin", "--valid-days", "2"], environ) == 0

    url = capsys.readouterr().out.strip()
    assert url.startswith("https://sbm.example/invite#")
    invite = db[INVITES].find_one({"token_hash": token_hash(url.split("#", 1)[1])})
    assert invite["role"] == "admin"
    assert invite["created_by"] is None
    assert (invite["expires_at"] - invite["created_at"]).days == 2
    entry = db[AUDIT_LOG].find_one()
    assert (entry["actor"], entry["action"], entry["target"]) == (
        "cli",
        "invite.create",
        invite["_id"],
    )


def test_needs_the_public_address(capsys):
    assert main([], {"SBM_MONGO_URI": "mongodb://localhost:1"}) == 2
    assert "SBM_PUBLIC_URL" in capsys.readouterr().err


def test_needs_the_database(capsys):
    assert main([], {"SBM_PUBLIC_URL": "https://sbm.example"}) == 2
    assert "SBM_MONGO_URI" in capsys.readouterr().err


def test_rejects_a_validity_out_of_range(db, environ, capsys):
    assert main(["--valid-days", "31"], environ) == 2
    assert "--valid-days" in capsys.readouterr().err
    assert db[INVITES].count_documents({}) == 0


def test_the_validity_comes_from_the_settings(db, environ, capsys):
    account_settings.save(db, AccountSettings(invite_days=3, invite_max_days=40))

    assert main([], environ) == 0
    assert main(["--valid-days", "40"], environ) == 0

    days = [(i["expires_at"] - i["created_at"]).days for i in db[INVITES].find().sort("_id", 1)]
    assert days == [3, 40]
