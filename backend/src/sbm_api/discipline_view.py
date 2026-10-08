"""Disciplines as the API shows them (schema StoredDiscipline)."""

from sbm_store.disciplines import SETTINGS

from sbm_api.timestamps import timestamp


def discipline_view(discipline: dict) -> dict:
    settings = {field: discipline[field] for field in SETTINGS}
    return (
        {"id": str(discipline["_id"])}
        | settings
        | {
            "archived": discipline["archived"],
            "created_at": timestamp(discipline["created_at"]),
            "updated_at": timestamp(discipline["updated_at"]),
        }
    )
