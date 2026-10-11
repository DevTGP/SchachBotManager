"""The seasons of a bot version with its place there (E139)."""

import random
from datetime import timedelta

from conftest import T0
from league_world import add_bots, add_league, play_out, register, stronger

from sbm_store import bot_seasons, league_lineup, league_setup, season_end, season_start, seasons

END = T0 + timedelta(hours=1)


def test_finished_and_running_seasons_newest_first(db):
    entrants = add_bots(db, 3)
    league = add_league(db)
    register(db, league, entrants)
    league_setup.release(db, league["_id"], T0)
    season_start.start_due(db, T0 + timedelta(minutes=1), random.Random(1))
    first = seasons.latest(db, league["_id"])
    play_out(db, first["_id"], stronger(entrants))
    season_end.finish_done(db, END)
    season_start.start_due(db, END + timedelta(hours=2), random.Random(2))

    found = bot_seasons.of_bot(db, entrants[1]["_id"])

    assert [each.season["number"] for each in found] == [2, 1]
    running, finished = found
    assert (running.season["status"], running.tier, running.tier_size) == (seasons.RUNNING, 1, 3)
    assert (running.row["games"], running.row["points"], running.row["outcome"]) == (0, 0, None)
    assert finished.season["status"] == seasons.FINISHED
    assert (finished.row["rank"], finished.row["points"]) == (2, 2)
    assert finished.row["outcome"] == league_lineup.STAYED


def test_a_running_season_shows_the_current_place(db):
    entrants = add_bots(db, 3)
    league = add_league(db)
    register(db, league, entrants)
    league_setup.release(db, league["_id"], T0)
    season_start.start_due(db, T0 + timedelta(minutes=1), random.Random(1))
    play_out(db, seasons.latest(db, league["_id"])["_id"], stronger(list(reversed(entrants))))

    (current,) = bot_seasons.of_bot(db, entrants[2]["_id"])

    assert (current.row["rank"], current.row["points"], current.row["games"]) == (1, 4, 4)


def test_a_bot_without_seasons(db):
    league = add_league(db)
    (waiting,) = add_bots(db, 1)
    register(db, league, [waiting])

    assert bot_seasons.of_bot(db, waiting["_id"]) == []
