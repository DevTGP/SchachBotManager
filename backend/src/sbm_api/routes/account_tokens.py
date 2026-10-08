"""GET/POST /account/tokens and DELETE /account/tokens/{id}: a coder's API tokens (E116)."""

import re

from flask import Blueprint
from sbm_store import api_tokens

from sbm_api import body, context
from sbm_api.current_user import require_coder
from sbm_api.errors import invalid_parameter, not_found
from sbm_api.params import object_id
from sbm_api.token_view import token_view

blueprint = Blueprint("account_tokens", __name__)

MAX_NAME = 40
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")


@blueprint.get("/account/tokens")
def list_tokens():
    user = require_coder()
    return {
        "items": [token_view(token) for token in api_tokens.active_of(context.db(), user["_id"])]
    }


@blueprint.post("/account/tokens")
def create_token():
    user = require_coder()
    db, now = context.db(), context.now()
    name = body.string(body.json_object(("name",)), "name", max_length=MAX_NAME).strip()
    if not name or CONTROL.search(name):
        raise invalid_parameter("name", f"name must be 1 to {MAX_NAME} characters")
    if len(api_tokens.active_of(db, user["_id"])) >= api_tokens.MAX_PER_USER:
        raise invalid_parameter("name", f"an account has at most {api_tokens.MAX_PER_USER} tokens")
    token, document = api_tokens.new_token(user["_id"], name, now=now)
    api_tokens.insert(db, document)
    return token_view(document) | {"token": token}, 201


@blueprint.delete("/account/tokens/<token_id>")
def revoke_token(token_id: str):
    user = require_coder()
    db, now = context.db(), context.now()
    if not api_tokens.revoke(db, object_id(token_id, "token_id"), user["_id"], now=now):
        raise not_found("no such token")
    return "", 204
