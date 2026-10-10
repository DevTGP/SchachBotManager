"""Bots as the API shows them (schemas Bot and BotDetail); source and owner stay hidden (E15).

The detail lists the versions of the name the viewer may see (E95). Owner and admins also get
the details: files, runtime versions, the report of the upload and those of rechecks (E153).
"""

from sbm_store import bots, jobs, ratings, users, verification_reports

from sbm_api import context
from sbm_api.rating_start import rating_start
from sbm_api.report_view import report_view
from sbm_api.timestamps import optional_timestamp, timestamp


def bot_view(bot: dict) -> dict:
    return {
        "id": str(bot["_id"]),
        "name": bot["name"],
        "version": bot["version"],
        "language": bot["language"],
        "status": bot["status"],
        "builtin": bots.is_builtin(bot),
        # Reference bots and bots from before E95 have none.
        "description": bot.get("description") or "",
        # Bots without a counted match have no rating stored yet (E103).
        "rating": ratings.current(bot, rating_start()),
        "created_at": timestamp(bot["created_at"]),
    }


def may_see_details(bot: dict, viewer: dict | None) -> bool:
    if viewer is None:
        return False
    return viewer["role"] == users.ADMIN or bot.get("owner_id") == viewer["_id"]


def may_see(bot: dict, viewer: dict | None) -> bool:
    return bot["status"] in bots.PUBLIC or may_see_details(bot, viewer)


def bot_detail_view(bot: dict, viewer: dict | None) -> dict:
    details = _details(bot) if may_see_details(bot, viewer) else None
    versions = [
        bot_view(version)
        for version in bots.versions_of(context.db(), bot["name"])
        if may_see(version, viewer)
    ]
    return {**bot_view(bot), "versions": versions, "details": details}


def _details(bot: dict) -> dict:
    db = context.db()
    # Reference bots have no owner, no files and no report (E72).
    owner = users.get(db, bot["owner_id"]) if bot.get("owner_id") else None
    report = verification_reports.get(db, bot["report_id"]) if bot.get("report_id") else None
    rejection = bot.get("rejection")
    return {
        "owner": owner["username"] if owner else None,
        "entry": bot.get("entry"),
        "files": [
            {"path": file["path"], "kind": file["kind"], "size": file["size"]}
            for file in bot.get("files", [])
        ],
        "sdk_version": bot.get("sdk_version"),
        "runtime_version": bot.get("runtime_version"),
        "verified_at": optional_timestamp(bot.get("verified_at")),
        "rejected_at": optional_timestamp(bot.get("rejected_at")),
        "rejection": (
            {"stage": rejection["stage"], "reason": rejection["reason"]} if rejection else None
        ),
        "overridden_at": optional_timestamp(bot.get("overridden_at")),
        "report": report_view(report) if report else None,
        "rechecks": [
            report_view(recheck) for recheck in verification_reports.rechecks_of(db, bot["_id"])
        ],
        # Uploads have their own pending verification; it shows in the status.
        "recheck_pending": bot["status"] not in bots.PIPELINE and jobs.verifying(db, bot["_id"]),
    }
