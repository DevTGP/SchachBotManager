"""Finishing seasons, promotion and relegation, and the following season (E132, E133, E135)."""

import random
from datetime import timedelta

from conftest import T0
from league_world import add_bots, add_league, play_out, register, stronger

from sbm_store import league_lineup, league_setup, recurrence, season_end, season_start, seasons

LATER = T0 + timedelta(minutes=1)
END = T0 + timedelta(hours=1)


CALENDAR = recurrence.new_recurrence(T0, 2)


def run_first_season(db, entrants, **settings):
    league = add_league(db, recurrence=CALENDAR, **settings)
    register(db, league, entrants)
    league_setup.start(db, league["_id"], T0)
    season_start.start_due(db, LATER, random.Random(1))
    return league, seasons.latest(db, league["_id"])


def test_a_season_with_open_games_goes_on(db):
    _, season = run_first_season(db, add_bots(db, 3))

    assert season_end.finish_done(db, END) == []
    assert seasons.get(db, season["_id"])["status"] == seasons.RUNNING


def test_a_finished_season_stores_its_table_and_plans_the_next(db):
    entrants = add_bots(db, 3)
    league, season = run_first_season(db, entrants)
    play_out(db, season["_id"], stronger(entrants))

    assert season_end.finish_done(db, END) == [season["_id"]]
    assert season_end.finish_done(db, END) == []

    finished = seasons.get(db, season["_id"])
    assert finished["status"] == seasons.FINISHED
    table = finished["final"][0]["table"]
    assert [row["bot"]["bot_id"] for row in table] == [bot["_id"] for bot in entrants]
    assert [row["points"] for row in table] == [4, 2, 0]
    assert [row["rank"] for row in table] == [1, 2, 3]
    assert {row["outcome"] for row in table} == {league_lineup.STAYED}
    following = seasons.latest(db, league["_id"])
    assert following["number"] == 2
    assert following["status"] == seasons.PLANNED
    assert following["starts_after"] == T0 + timedelta(hours=2)
    assert following["seeds"] == [[bot["_id"] for bot in entrants]]


def test_bots_move_between_tiers_and_start_there_next_season(db):
    a, b, c, d = add_bots(db, 4)
    league, season = run_first_season(db, [a, b, c, d], tiers=2, tier_size=2, promotions=1)
    play_out(db, season["_id"], stronger([b, a, d, c]))

    season_end.finish_done(db, END)

    final = seasons.get(db, season["_id"])["final"]
    outcomes = {row["bot"]["name"]: row["outcome"] for tier in final for row in tier["table"]}
    assert outcomes == {
        b["name"]: league_lineup.STAYED,
        a["name"]: league_lineup.RELEGATED,
        d["name"]: league_lineup.PROMOTED,
        c["name"]: league_lineup.STAYED,
    }
    following = seasons.latest(db, league["_id"])
    assert following["seeds"] == [[b["_id"], d["_id"]], [c["_id"], a["_id"]]]

    started = season_start.start_due(db, END + timedelta(hours=2), random.Random(2))

    assert started == [following["_id"]]
    tiers = seasons.get(db, following["_id"])["tiers"]
    placed = [[entry["bot_id"] for entry in tier["entries"]] for tier in tiers]
    assert placed == [[b["_id"], d["_id"]], [c["_id"], a["_id"]]]


def test_without_a_calendar_the_next_season_waits_for_an_admin(db):
    entrants = add_bots(db, 3)
    league = add_league(db)
    register(db, league, entrants)
    league_setup.start(db, league["_id"], T0)
    season_start.start_due(db, LATER, random.Random(1))
    play_out(db, seasons.latest(db, league["_id"])["_id"], stronger(entrants))

    season_end.finish_done(db, END)

    following = seasons.latest(db, league["_id"])
    assert following["starts_after"] is None
    assert season_start.start_due(db, END + timedelta(days=30), random.Random(2)) == []
    assert league_setup.start(db, league["_id"], END)
    assert season_start.start_due(db, END, random.Random(2)) == [following["_id"]]
