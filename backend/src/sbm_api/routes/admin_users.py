"""Admin: list accounts, change role or active flag, create a reset link (E83, E85)."""

from datetime import timedelta

from flask import Blueprint
from sbm_store import password_resets, sessions, users

from sbm_api import admin_audit, body, context
from sbm_api.current_user import require_admin
from sbm_api.errors import invalid_parameter, not_found
from sbm_api.links import RESET_PAGE, one_time_link
from sbm_api.params import object_id
from sbm_api.timestamps import timestamp
from sbm_api.user_view import user_view

blueprint = Blueprint("admin_users", __name__)

RESET_VALID = timedelta(hours=24)


@blueprint.get("/admin/users")
def list_users():
    require_admin()
    return {"items": [user_view(user) for user in users.all_by_name(context.db())]}


@blueprint.patch("/admin/users/<user_id>")
def update_user(user_id: str):
    admin = require_admin()
    target = object_id(user_id, "user_id")
    data = body.json_object(("role", "active"))
    if not data:
        raise invalid_parameter("body", "change role or active")
    if target == admin["_id"]:
        raise invalid_parameter("user_id", "admins cannot change their own account")
    fields = {}
    if "role" in data:
        fields["role"] = body.choice(data, "role", users.ROLES)
    if "active" in data:
        fields["active"] = body.boolean(data, "active")
    db = context.db()
    user = users.update(db, target, fields)
    if user is None:
        raise not_found("no such account")
    if not user["active"]:
        sessions.delete_for_user(db, target)
    admin_audit.record(admin, "user.update", target, fields)
    return user_view(user)


@blueprint.post("/admin/users/<user_id>/password-reset")
def create_password_reset(user_id: str):
    admin = require_admin()
    db, now = context.db(), context.now()
    user = users.get(db, object_id(user_id, "user_id"))
    if user is None:
        raise not_found("no such account")
    reset, token = password_resets.create(
        db, user["_id"], created_by=admin["_id"], now=now, expires_at=now + RESET_VALID
    )
    admin_audit.record(admin, "password_reset.create", user["_id"], {})
    url = one_time_link(context.public_url(), RESET_PAGE, token)
    return {"url": url, "expires_at": timestamp(reset["expires_at"])}, 201
