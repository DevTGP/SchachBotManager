from datetime import timedelta

from bson import ObjectId
from conftest import T0

from sbm_store import api_tokens
from sbm_store.migrate import migrate


def test_a_token_is_stored_only_as_its_hash_and_found_by_itself(db):
    migrate(db)
    user_id = ObjectId()
    token, document = api_tokens.new_token(user_id, "laptop", now=T0)
    api_tokens.insert(db, document)

    assert token.startswith("sbm_") and len(token) == 47
    assert token not in str(db["api_tokens"].find_one())
    found = api_tokens.find(db, token, now=T0 + timedelta(minutes=1))
    assert found["_id"] == document["_id"]
    assert db["api_tokens"].find_one()["last_used_at"] == T0 + timedelta(minutes=1)
    assert api_tokens.find(db, token + "x", now=T0) is None


def test_a_revoked_token_opens_nothing(db):
    migrate(db)
    user_id = ObjectId()
    token, document = api_tokens.new_token(user_id, "laptop", now=T0)
    api_tokens.insert(db, document)

    assert not api_tokens.revoke(db, document["_id"], ObjectId(), now=T0)
    assert api_tokens.revoke(db, document["_id"], user_id, now=T0)
    assert not api_tokens.revoke(db, document["_id"], user_id, now=T0)
    assert api_tokens.find(db, token, now=T0) is None
    assert api_tokens.active_of(db, user_id) == []
