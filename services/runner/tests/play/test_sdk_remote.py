"""The SDK's remote transport against the real gateway and play runner (E116)."""

import threading
import time

from sbm import Bot
from sbm.game import Game
from sbm.remote.channel import RemoteChannel
from sbm.remote.game_request import Seat
from sbm_store import matches


class FirstMove(Bot):
    def choose_move(self, board, clock):
        return board.legal_moves()[0]


def test_an_sdk_bot_plays_a_remote_game(db, gateway, play_worker, create_remote):
    match_id, seat = create_remote()
    errors = []

    def local_bot():
        try:
            with RemoteChannel.join(Seat(str(match_id), seat, "white", gateway.url)) as channel:
                Game(FirstMove(), channel).play()
        except Exception as error:  # reported below, a thread cannot fail the test
            errors.append(error)

    thread = threading.Thread(target=local_bot, daemon=True)
    thread.start()
    time.sleep(0.2)
    assert play_worker.step()
    thread.join(20)

    assert errors == []
    deadline = time.monotonic() + 10
    while matches.get(db, match_id)["status"] == matches.RUNNING and time.monotonic() < deadline:
        time.sleep(0.05)
    match = matches.get(db, match_id)
    assert (match["status"], match["termination"]) == (matches.FINISHED, "max_moves")
    assert match["white"]["lang"] == "python"
