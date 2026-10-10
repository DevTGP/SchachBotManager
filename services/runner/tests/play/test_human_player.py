import time
from dataclasses import replace

from bson import ObjectId
from conftest import QUICK, Person
from sbm_store import bots, jobs, matches, play, ratings
from sbm_store.names import JOBS


def wait_for(predicate, seconds: float = 15) -> None:
    deadline = time.monotonic() + seconds
    while not predicate():
        assert time.monotonic() < deadline, "timed out"
        time.sleep(0.05)


def finished(db, match_id) -> bool:
    return matches.get(db, match_id)["status"] in (matches.FINISHED, matches.ABORTED)


def play_out(db, gateway, play_worker, create_remote, *, user_id=None, discipline=QUICK, **options):
    match_id, seat = create_remote(play.HUMAN, user_id=user_id, discipline=discipline)
    person = Person(gateway.url, match_id, seat, **options)
    person.start()
    assert play_worker.step()
    wait_for(lambda: finished(db, match_id))
    person.join(10)
    return matches.get(db, match_id), person


def test_a_person_plays_a_whole_game_in_the_browser(db, gateway, play_worker, create_remote):
    match, person = play_out(db, gateway, play_worker, create_remote)

    assert (match["status"], match["termination"]) == (matches.FINISHED, "max_moves")
    assert (match["white"]["sdk"], match["white"]["lang"]) == (None, None)
    assert match["black"]["lang"] == "python"
    first, last = person.states[0], person.states[-1]
    assert (first["color"], first["white"], first["black"]) == ("white", "alice", "Random")
    assert first["moves"] == "" and any(state["legal_moves"] for state in person.states)
    assert last["moves"].split() == [move["uci"] for move in match["moves"]]
    assert last["san"].split() == [move["san"] for move in match["moves"]]
    assert (last["result"], last["termination"], last["running"]) == ("1/2-1/2", "max_moves", None)
    assert last["legal_moves"] == ""
    assert db[JOBS].find_one({"payload.match_id": match["_id"]})["status"] == jobs.DONE


def test_the_bots_moves_reach_the_browser_at_once(db, gateway, play_worker, create_remote):
    _match, person = play_out(db, gateway, play_worker, create_remote)

    after_bot = [state for state in person.states if state["moves"].count(" ") == 1]
    assert after_bot, "a state after the bot's first reply"
    assert after_bot[0]["running"] == "white"


def test_an_illegal_move_is_refused_and_the_game_goes_on(db, gateway, play_worker, create_remote):
    match, person = play_out(db, gateway, play_worker, create_remote, first_try="e2e5")

    assert [error["code"] for error in person.errors] == ["illegal_move"]
    assert match["termination"] == "max_moves"


def test_a_move_out_of_turn_is_refused_without_losing(db, gateway, play_worker, create_remote):
    match, person = play_out(db, gateway, play_worker, create_remote, early=True)

    assert "not_your_turn" in [error["code"] for error in person.errors]
    assert match["termination"] == "max_moves"


def test_a_person_can_resign(db, gateway, play_worker, create_remote):
    match, person = play_out(db, gateway, play_worker, create_remote, resign_after=1)

    assert (match["result"], match["termination"]) == ("0-1", "resignation")
    assert person.states[-1]["result"] == "0-1"


def test_a_reload_gets_the_whole_game_again(db, gateway, play_worker, create_remote):
    match_id, seat = create_remote(play.HUMAN)
    first = Person(gateway.url, match_id, seat, leave_after=1)
    first.start()
    assert play_worker.step()
    first.join(10)
    second = Person(gateway.url, match_id, seat)
    second.start()
    wait_for(lambda: finished(db, match_id))
    second.join(10)

    assert second.states[0]["moves"].startswith(first.states[-1]["moves"])
    assert matches.get(db, match_id)["termination"] == "max_moves"


def test_a_rated_game_of_an_account_is_counted_at_once(db, gateway, play_worker, create_remote):
    user_id = ObjectId()
    db["users"].insert_one({"_id": user_id, "username": "alice"})
    stored = replace(QUICK, discipline_id=ObjectId())

    match, _person = play_out(
        db, gateway, play_worker, create_remote, user_id=user_id, discipline=stored, resign_after=1
    )

    wait_for(lambda: "rating" in matches.get(db, match["_id"]))
    assert match["rated"] is True
    assert ratings.current(db["users"].find_one({"_id": user_id}), 2500) == {
        "value": 2450,
        "games": 1,
    }
    assert ratings.current(bots.get(db, match["black"]["bot_id"]), 2500)["value"] == 2550
