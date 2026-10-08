"""Public: the disciplines matches are played under (E100)."""

from flask import Blueprint
from sbm_store import disciplines

from sbm_api import context
from sbm_api.discipline_view import discipline_view
from sbm_api.errors import not_found
from sbm_api.params import object_id

blueprint = Blueprint("disciplines", __name__)


@blueprint.get("/disciplines")
def list_disciplines():
    return {"items": [discipline_view(item) for item in disciplines.all_by_name(context.db())]}


@blueprint.get("/disciplines/<discipline_id>")
def get_discipline(discipline_id: str):
    discipline = disciplines.get(context.db(), object_id(discipline_id, "discipline_id"))
    if discipline is None:
        raise not_found("no such discipline")
    return discipline_view(discipline)
