import json
import time

import pytest
from conftest import MATCH_ID, SEAT, join, receive
from websockets.exceptions import ConnectionClosed, InvalidStatus

OTHER_SEAT = "A" * 43


def test_a_client_that_joins_first_waits_for_the_runner(gateway):
    with gateway.client() as client:
        join(client)
        relay = gateway.relay()
        relay.attach()
        assert receive(client) == {"type": "joined", "v": 1, "match_id": MATCH_ID}
        assert relay.receive() == {"type": "present"}
        relay.close()


def test_lines_pass_both_ways_unchanged(gateway):
    relay = gateway.relay()
    relay.attach()
    with gateway.client() as client:
        join(client)
        assert receive(client)["type"] == "joined"
        assert relay.receive() == {"type": "present"}
        relay.line('{"type":"init","ü":1}')
        assert client.recv(timeout=5) == '{"type":"init","ü":1}'
        client.send('{"type":"ready"}')
        assert relay.receive() == {"type": "line", "data": '{"type":"ready"}'}
    relay.close()


def test_the_end_of_the_relay_ends_the_client_after_the_last_line(gateway):
    relay = gateway.relay()
    relay.attach()
    with gateway.client() as client:
        join(client)
        receive(client)
        relay.receive()
        relay.line("game_over")
        relay.close()
        assert client.recv(timeout=5) == "game_over"
        with pytest.raises(ConnectionClosed) as closed:
            client.recv(timeout=5)
        assert closed.value.rcvd.code == 1000


def test_lines_wait_for_an_absent_client_and_follow_joined(gateway):
    relay = gateway.relay()
    relay.attach()
    relay.line("first")
    with gateway.client() as client:
        join(client)
        assert receive(client)["type"] == "joined"
        assert client.recv(timeout=5) == "first"
    assert relay.receive() == {"type": "present"}
    assert relay.receive() == {"type": "absent"}
    relay.line("while away")
    with gateway.client() as client:
        join(client)
        assert receive(client)["type"] == "joined"
        assert client.recv(timeout=5) == "while away"
        assert relay.receive() == {"type": "present"}
    relay.close()


def test_a_newer_connection_replaces_the_older(gateway):
    relay = gateway.relay()
    relay.attach()
    with gateway.client() as older, gateway.client() as newer:
        join(older)
        receive(older)
        relay.receive()
        join(newer)
        assert receive(newer)["type"] == "joined"
        refused = receive(older)
        assert (refused["type"], refused["code"]) == ("refused", "replaced")
        assert relay.receive() == {"type": "present"}
        newer.send("from newer")
        assert relay.receive() == {"type": "line", "data": "from newer"}
    relay.close()


def test_a_wrong_seat_never_joins(gateway):
    relay = gateway.relay()
    relay.attach()
    with gateway.client() as client:
        join(client, seat=OTHER_SEAT)
        refused = receive(client)
        assert (refused["type"], refused["code"]) == ("refused", "no_game")
    relay.close()


def test_a_bad_first_message_is_refused(gateway):
    with gateway.client() as client:
        client.send("hello")
        refused = receive(client)
        assert (refused["type"], refused["code"]) == ("refused", "invalid_message")
        with pytest.raises(ConnectionClosed) as closed:
            client.recv(timeout=5)
        assert closed.value.rcvd.code == 1008


def test_a_second_attach_of_the_same_seat_is_refused(gateway):
    first = gateway.relay()
    first.attach()
    time.sleep(0.1)
    second = gateway.relay()
    second.attach()
    assert second.receive()["code"] == "attached"
    assert second.receive() is None
    first.close()
    second.close()


def test_a_bad_attach_is_refused(gateway):
    relay = gateway.relay()
    relay.send({"type": "attach", "v": 1, "match_id": MATCH_ID, "seat": SEAT})
    assert relay.receive()["code"] == "invalid_message"
    relay.close()


def test_a_relay_that_breaks_the_protocol_ends_the_game(gateway):
    relay = gateway.relay()
    relay.attach()
    with gateway.client() as client:
        join(client)
        receive(client)
        relay.send({"type": "present"})
        with pytest.raises(ConnectionClosed):
            while True:
                client.recv(timeout=5)
    relay.close()


def test_binary_messages_close_the_connection(gateway):
    relay = gateway.relay()
    relay.attach()
    with gateway.client() as client:
        join(client)
        receive(client)
        relay.receive()
        client.send(b"\x00")
        with pytest.raises(ConnectionClosed) as closed:
            client.recv(timeout=5)
        assert closed.value.rcvd.code == 1003
    assert relay.receive() == {"type": "absent"}
    relay.close()


def test_other_paths_do_not_upgrade(gateway):
    from websockets.sync.client import connect

    with pytest.raises(InvalidStatus) as refused:
        connect(f"ws://127.0.0.1:{gateway.gateway.socket_port}/other", open_timeout=5)
    assert refused.value.response.status_code == 404


def test_stopping_refuses_waiting_clients(config):
    from conftest import RunningGateway

    running = RunningGateway(config)
    with running.client() as client:
        join(client)
        time.sleep(0.2)
        running.stop()
        refused = json.loads(client.recv(timeout=5))
        assert refused["code"] == "shutdown"
