"""One group of settings as a document of the settings collection (E154).

A group is a frozen dataclass of integers with defaults; a field missing from the document keeps
its default, so a new field needs no migration.
"""

from dataclasses import asdict, fields

from pymongo.database import Database

from sbm_store.names import SETTINGS


def load[T](db: Database, document_id: str, kind: type[T]) -> T:
    document = db[SETTINGS].find_one({"_id": document_id}) or {}
    defaults = kind()
    values = {
        field.name: document.get(field.name, getattr(defaults, field.name))
        for field in fields(kind)
    }
    return kind(**values)


def store(db: Database, document_id: str, settings: object) -> None:
    db[SETTINGS].update_one({"_id": document_id}, {"$set": asdict(settings)}, upsert=True)
