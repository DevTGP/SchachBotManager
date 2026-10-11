"""Leagues, their first season and registrations (E131, E132, E136)."""

import pytest
from conftest import T0
from league_world import add_bots, add_league, register

from sbm_store import league_setup, leagues, registrations, seasons
from sbm_store.names import JOBS, LEAGUES, MATCHES, REGISTRATIONS, SEASONS


def test_a_new_league_has_the_defaults_and_a_planned_first_season(db):
    league = add_league(db)

    stored = leagues.get(db, league["_id"])
    assert stored["tier_size"] == 10
    assert stored["priority"] == 50
    first = seasons.latest(db, league["_id"])
    assert (first["number"], first["status"], first["starts_after"]) == (1, seasons.PLANNED, None)


def test_league_names_are_unique_regardless_of_case(db):
    league = add_league(db)
    twin = leagues.new_league(
        {"name": "LIGA", "discipline_id": league["discipline_id"]}, created_by=None, now=T0
    )
    other = leagues.new_league(
        {"name": "Andere", "discipline_id": league["discipline_id"]}, created_by=None, now=T0
    )

    assert not league_setup.create(db, twin, T0)
    assert league_setup.create(db, other, T0)
    with pytest.raises(leagues.NameTaken):
        leagues.update(db, other["_id"], {"name": "liga"}, now=T0)


def test_settings_are_what_a_season_copies(db):
    league = add_league(db, tiers=2)

    copied = leagues.settings(leagues.get(db, league["_id"]))

    assert set(copied) == set(leagues.SETTINGS)
    assert copied["tiers"] == 2


def test_releasing_a_league_without_a_season_adds_the_first(db):
    league = add_league(db)
    db[SEASONS].delete_many({"league_id": league["_id"]})

    assert league_setup.start(db, league["_id"], T0)
    assert seasons.latest(db, league["_id"])["starts_after"] == T0


def test_a_bot_registers_once_per_league_and_may_come_back(db):
    league = add_league(db)
    other = add_league(db, "Andere")
    (bot,) = add_bots(db, 1)
    register(db, league, [bot])
    register(db, other, [bot])
    again = registrations.new_registration(league["_id"], bot["_id"], created_by=None, now=T0)

    assert not registrations.insert(db, again)
    left = registrations.leave(
        db, bot["_id"], registrations.DEREGISTERED, T0, target_id=league["_id"]
    )
    assert left == [league["_id"]]
    assert registrations.count_active(db, league["_id"]) == 0
    assert [entry["target_id"] for entry in registrations.active_of_bot(db, bot["_id"])] == [
        other["_id"]
    ]
    assert registrations.insert(db, again)


def test_league_indexes_exist(db):
    add_league(db)

    assert db[LEAGUES].index_information()["name_key_1"]["unique"]
    assert db[SEASONS].index_information()["league_id_1_number_1"]["unique"]
    registered = db[REGISTRATIONS].index_information()
    assert registered["target_type_1_target_id_1_bot_id_1"]["unique"]
    assert "context.season_id_1_context.tier_1_status_1" in db[MATCHES].index_information()
    assert "competition_1_claimed_at_1" in db[JOBS].index_information()
