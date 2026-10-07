import re

from sbm_store.tokens import new_token, token_hash


def test_tokens_are_url_safe_and_unique():
    tokens = {new_token() for _ in range(100)}
    assert len(tokens) == 100
    assert all(re.fullmatch(r"[A-Za-z0-9_-]{43}", token) for token in tokens)


def test_the_hash_is_stable_and_hides_the_token():
    token = new_token()
    assert token_hash(token) == token_hash(token)
    assert token not in token_hash(token)
    assert len(token_hash(token)) == 64
