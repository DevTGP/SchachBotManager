"""Admin: the settings of coders, accounts, the rating rule and the queue estimate (E154).

Every change is logged. A changed rating rule asks for a recount of all ratings (E105).
"""

from dataclasses import asdict

from flask import Blueprint
from sbm_store import rating_recount

from sbm_api import admin_audit, body, context
from sbm_api.current_user import require_admin
from sbm_api.errors import invalid_parameter
from sbm_api.settings_groups import GROUPS, PROBLEMS, Group

blueprint = Blueprint("admin_settings", __name__)


@blueprint.get("/admin/settings")
def get_settings():
    require_admin()
    return _all_settings()


def _update(group: Group):
    admin = require_admin()
    data = body.json_object(tuple(group.module.LIMITS))
    values = {
        name: body.integer(data, name, low=low, high=high)
        for name, (low, high) in group.module.LIMITS.items()
    }
    settings = group.kind(**values)
    field = group.module.problem(settings)
    if field is not None:
        raise invalid_parameter(field, f"{field} {PROBLEMS[field]}")
    db = context.db()
    changed = group.module.get(db) != settings
    group.module.save(db, settings)
    if changed and group.name == "rating":
        rating_recount.request(db, context.now())
    admin_audit.record(admin, f"settings.{group.name}", None, asdict(settings))
    return _all_settings()


def _all_settings() -> dict:
    db = context.db()
    found = {group.name: asdict(group.module.get(db)) for group in GROUPS}
    return found | {"rating_recount_pending": rating_recount.is_requested(db)}


for _group in GROUPS:
    blueprint.add_url_rule(
        f"/admin/settings/{_group.name}",
        endpoint=f"update_{_group.name}",
        view_func=lambda group=_group: _update(group),
        methods=["PUT"],
    )
