from sbm_store.names import AUDIT_LOG, INVITES
from sbm_store.tokens import token_hash

from sbm_api.invite_cli import main


def test_prints_a_link_for_the_first_admin(db, mongo_uri, capsys):
    environ = {
        "SBM_MONGO_URI": mongo_uri,
        "SBM_MONGO_DB": db.name,
        "SBM_PUBLIC_URL": "https://sbm.example/",
    }

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


def test_rejects_a_validity_out_of_range(capsys):
    assert main(["--valid-days", "31"], {}) == 2
    assert "--valid-days" in capsys.readouterr().err
