from datetime import timedelta

import pytest
from bson import ObjectId
from conftest import BLITZ, START_FEN, T0

from sbm_store import disciplines, matches
from sbm_store.discipline import STANDARD_FEN, Discipline
from sbm_store.enqueue import enqueue_match
from sbm_store.migrate import migrate

OTHER_FEN = "4k3/8/8/8/8/8/8/4K2R w K - 0 1"


def add(db, name: str, **settings) -> dict:
    discipline = disciplines.new_discipline(
        Discipline(name, initial_time_ms=60_000, **settings), created_by=None, now=T0
    )
    assert disciplines.insert(db, discipline)
    return discipline


def test_a_new_discipline_takes_the_defaults(db):
    migrate(db)
    stored = disciplines.get(db, add(db, "Blitz")["_id"])

    assert stored["name"] == "Blitz"
    assert (stored["increment_ms"], stored["startup_ms"], stored["tolerance_ms"]) == (0, 10_000, 20)
    assert stored["max_moves"] == 500
    assert not stored["archived"]
    assert stored["created_at"] == stored["updated_at"]


def test_names_are_unique_regardless_of_case(db):
    migrate(db)
    add(db, "Blitz")
    rapid = add(db, "Rapid")

    duplicate = Discipline("BLITZ", initial_time_ms=1000)
    assert not disciplines.insert(
        db, disciplines.new_discipline(duplicate, created_by=None, now=T0)
    )
    with pytest.raises(disciplines.NameTaken):
        disciplines.update(db, rapid["_id"], {"name": "blitz"}, now=T0)


def test_listed_by_name_with_or_without_the_archived_ones(db):
    migrate(db)
    for name in ("rapid", "Blitz", "classic"):
        add(db, name)
    archived = add(db, "Bullet")
    disciplines.update(db, archived["_id"], {"archived": True}, now=T0)

    assert [d["name"] for d in disciplines.all_by_name(db)] == [
        "Blitz",
        "Bullet",
        "classic",
        "rapid",
    ]
    assert [d["name"] for d in disciplines.all_by_name(db, archived=False)] == [
        "Blitz",
        "classic",
        "rapid",
    ]


def test_update_returns_the_changed_discipline(db):
    migrate(db)
    blitz = add(db, "Blitz")
    later = T0 + timedelta(hours=1)

    changed = disciplines.update(
        db, blitz["_id"], {"name": "Blitz 3+2", "increment_ms": 2000}, now=later
    )

    assert (changed["name"], changed["name_key"], changed["increment_ms"]) == (
        "Blitz 3+2",
        "blitz 3+2",
        2000,
    )
    assert (changed["created_at"], changed["updated_at"]) == (T0, later)
    assert disciplines.update(db, ObjectId(), {"archived": True}, now=T0) is None


def test_a_match_copies_the_discipline_and_its_id(db, reference_bots):
    blitz = add(db, "Blitz", increment_ms=1000)

    match_id = enqueue_match(
        db, *reference_bots, disciplines.snapshot(blitz), start_fen=STANDARD_FEN, now=T0
    )

    snapshot = matches.get(db, match_id)["discipline_snapshot"]
    assert snapshot["discipline_id"] == blitz["_id"]
    assert (snapshot["name"], snapshot["increment_ms"]) == ("Blitz", 1000)
    assert Discipline.from_document(snapshot) == disciplines.snapshot(blitz)


def test_only_a_discipline_from_the_standard_position_is_rated(db, reference_bots):
    blitz = disciplines.snapshot(add(db, "Blitz"))

    def rated(discipline, start_fen):
        match_id = enqueue_match(db, *reference_bots, discipline, start_fen=start_fen, now=T0)
        return matches.get(db, match_id)["rated"]

    assert rated(blitz, STANDARD_FEN)
    assert not rated(blitz, OTHER_FEN)
    assert not rated(BLITZ, START_FEN)


def test_old_snapshots_have_no_discipline(db):
    old = BLITZ.to_document()
    del old["discipline_id"]

    assert Discipline.from_document(old).discipline_id is None
