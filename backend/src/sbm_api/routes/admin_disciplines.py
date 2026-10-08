"""Admin: create, change and archive disciplines; they are never deleted (E100)."""

from flask import Blueprint
from sbm_store import disciplines

from sbm_api import admin_audit, context, discipline_request
from sbm_api.current_user import require_admin
from sbm_api.discipline_view import discipline_view
from sbm_api.errors import NAME_TAKEN, ApiError, not_found
from sbm_api.params import object_id

blueprint = Blueprint("admin_disciplines", __name__)


@blueprint.post("/admin/disciplines")
def create_discipline():
    admin = require_admin()
    settings = discipline_request.parse_new()
    discipline = disciplines.new_discipline(settings, created_by=admin["_id"], now=context.now())
    if not disciplines.insert(context.db(), discipline):
        raise name_taken()
    admin_audit.record(admin, "discipline.create", discipline["_id"], {"name": settings.name})
    return discipline_view(discipline), 201


@blueprint.patch("/admin/disciplines/<discipline_id>")
def update_discipline(discipline_id: str):
    admin = require_admin()
    target = object_id(discipline_id, "discipline_id")
    fields = discipline_request.parse_update()
    try:
        discipline = disciplines.update(context.db(), target, fields, now=context.now())
    except disciplines.NameTaken:
        raise name_taken() from None
    if discipline is None:
        raise not_found("no such discipline")
    admin_audit.record(admin, "discipline.update", target, fields)
    return discipline_view(discipline)


def name_taken() -> ApiError:
    return ApiError(409, NAME_TAKEN, "another discipline has the name", "name")
