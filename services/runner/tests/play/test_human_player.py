import time

from conftest import Person
from sbm_store import jobs, matches, play
from sbm_store.names import JOBS


def wait_for(predicate, seconds: float = 15) -> None:
    deadline = time.monotonic() + seconds
    while not predicate():
        assert time.monotonic() < deadline, "timed out"
        time.sleep(0.05)


def finished(db, match_id) -> bool:
    return matches.get(db, match_id)["status"] in (matches.FINISHED, matches.ABORTED)


def play_out(db, gateway, play_worker, create_remote, **person_options):
    match_id, seat = create_remote(play.HUMAN)
    person = Person(gateway.url, match_id, seat, **person_options)
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
