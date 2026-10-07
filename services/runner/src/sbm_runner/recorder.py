"""Writes each move to the match while the game runs, so viewers see it at once."""

from bson import ObjectId
from pymongo.database import Database
from sbm.referee import MoveRecord
from sbm_store import matches


def move_document(record: MoveRecord) -> dict:
    return {
        "ply": record.ply,
        "uci": record.uci,
        "san": record.san,
        "fen": record.fen,
        "spent_ms": record.elapsed_ms,
        "clock_ms": record.remaining_ms,
        "info": record.info,
    }


class Recorder:
    def __init__(self, db: Database, match_id: ObjectId) -> None:
        self._db = db
        self._match_id = match_id

    def on_move(self, record: MoveRecord) -> None:
        matches.append_move(self._db, self._match_id, move_document(record))
