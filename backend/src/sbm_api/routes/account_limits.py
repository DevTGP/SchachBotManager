"""GET /account/limits: the limits for uploads and own matches of coders (E154)."""

from dataclasses import asdict

from flask import Blueprint
from sbm_store import coder_settings

from sbm_api import context
from sbm_api.current_user import require_coder

blueprint = Blueprint("account_limits", __name__)


@blueprint.get("/account/limits")
def own_limits():
    require_coder()
    limits = asdict(coder_settings.get(context.db()))
    del limits["priority"]
    return limits
