"""Admin: list, create and revoke invites (E4, E83, E85); validity from the settings (E154)."""

from datetime import timedelta

from flask import Blueprint
from sbm_store import account_settings, invites, users

from sbm_api import admin_audit, body, context
from sbm_api.current_user import require_admin
from sbm_api.errors import not_found
from sbm_api.invite_view import invite_view
from sbm_api.links import INVITE_PAGE, one_time_link
from sbm_api.params import object_id

blueprint = Blueprint("admin_invites", __name__)


@blueprint.get("/admin/invites")
def list_invites():
    require_admin()
    found = invites.open_invites(context.db(), context.now())
    return {"items": [invite_view(invite) for invite in found]}


@blueprint.post("/admin/invites")
def create_invite():
    admin = require_admin()
    data = body.json_object(("role", "valid_days"))
    role = body.choice(data, "role", users.ROLES)
    db = context.db()
    limits = account_settings.get(db)
    days = body.integer(
        data, "valid_days", low=1, high=limits.invite_max_days, default=limits.invite_days
    )
    now = context.now()
    invite, token = invites.create(
        db,
        role,
        created_by=admin["_id"],
        created_by_name=admin["username"],
        now=now,
        expires_at=now + timedelta(days=days),
    )
    admin_audit.record(admin, "invite.create", invite["_id"], {"role": role, "valid_days": days})
    url = one_time_link(context.public_url(), INVITE_PAGE, token)
    return {"invite": invite_view(invite), "url": url}, 201


@blueprint.delete("/admin/invites/<invite_id>")
def revoke_invite(invite_id: str):
    admin = require_admin()
    target = object_id(invite_id, "invite_id")
    if not invites.revoke(context.db(), target):
        raise not_found("no such open invite")
    admin_audit.record(admin, "invite.revoke", target, {})
    return "", 204
