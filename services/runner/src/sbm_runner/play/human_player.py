"""A person in the browser as a side of the game (play-v1, E114).

The referee speaks the bot protocol to it as to any bot; this adapter answers ready itself,
turns turn and game_over into state messages for the browser and the browser's move and resign
into protocol lines. Legal moves come from the core, so the browser needs no rules of its own.
It also sees every move of the game through observe, which the runner calls from on_move, so
the browser shows the bot's moves and clocks at once.
"""

import json
import threading

from sbm import Board
from sbm.referee import MoveRecord, Player

from sbm_runner.play.relay_connection import RelayConnection

VERSION = 1
PROTOCOL_VERSION = 1
COLORS = ("white", "black")
# The SDK fields of ready; a person has no SDK.
READY = {"type": "ready", "v": PROTOCOL_VERSION, "sdk": "0.0.0", "lang": "python"}


def _encode(message: dict) -> str:
    return json.dumps(message, ensure_ascii=False, separators=(",", ":"))


def _side_to_move(fen: str) -> str:
    return "white" if fen.split(" ")[1] == "w" else "black"


class HumanPlayer(Player):
    def __init__(self, name: str, connection: RelayConnection, *, absent_grace: float) -> None:
        super().__init__(name)
        self._connection = connection
        self._absent_grace = absent_grace
        self._lock = threading.Lock()
        self._state: str | None = None
        self._ready_due = False
        self._my_turn = False
        self._resign_requested = False
        self._legal: list[str] = []
        self._color = "white"
        self._names = {"white": "", "black": ""}
        self._start_fen = ""
        self._fen = ""
        self._uci: list[str] = []
        self._san: list[str] = []
        self._clock = {"white": 0, "black": 0}
        self._running: str | None = None
        self._increment_ms = 0
        self._result: str | None = None
        self._termination: str | None = None
        connection.on_present = self._resend

    # From the referee

    def send(self, message: dict) -> None:
        kind = message["type"]
        if kind == "init":
            self._start(message)
        elif kind == "turn":
            self._turn(message)
        elif kind == "game_over":
            self._my_turn, self._legal, self._running = False, [], None
            self._result, self._termination = message["result"], message["termination"]
        else:
            return  # errors of the referee concern bots that break the protocol
        self._publish()

    def _start(self, init: dict) -> None:
        self._color = init["color"]
        other = COLORS[1 - COLORS.index(self._color)]
        self._names = {self._color: self.name, other: init["opponent_name"]}
        self._start_fen = self._fen = init["start_fen"]
        self._clock = {color: init["initial_time_ms"] for color in COLORS}
        self._increment_ms = init["increment_ms"]
        self._running = _side_to_move(self._start_fen)
        self._ready_due = True

    def _turn(self, turn: dict) -> None:
        other = COLORS[1 - COLORS.index(self._color)]
        self._fen = turn["fen"]
        self._clock[self._color] = turn["remaining_ms"]
        self._clock[other] = turn["opponent_remaining_ms"]
        self._legal = [move.uci() for move in Board.from_fen(self._fen).legal_moves()]
        self._running = self._color
        self._my_turn = True

    def observe(self, record: MoveRecord) -> None:
        """Every accepted move of either side, in the game's thread."""
        mover = _side_to_move(self._fen)
        self._uci.append(record.uci)
        self._san.append(record.san)
        self._fen = record.fen
        self._clock[mover] = record.remaining_ms
        self._running = _side_to_move(record.fen)
        if mover == self._color:
            self._my_turn, self._legal = False, []
        self._publish()

    # From the browser

    def receive(self, deadline_ns: int | None) -> bytes:
        if self._ready_due:
            self._ready_due = False
            return _encode(READY).encode()
        while True:
            if self._my_turn and self._resign_requested:
                self._my_turn = False
                return _encode({"type": "resign", "v": PROTOCOL_VERSION}).encode()
            answer = self._read(self._connection.receive(deadline_ns, self._absent_grace))
            if answer is not None:
                return answer

    def _read(self, line: str) -> bytes | None:
        """The protocol line for the browser's message, or None after telling it why not."""
        try:
            message = json.loads(line)
        except ValueError:
            message = None
        kind = message.get("type") if isinstance(message, dict) else None
        if kind == "resign" and set(message) == {"type", "v"} and message["v"] is VERSION:
            self._resign_requested = True
            if not self._my_turn:
                return None
            self._my_turn = False
            return _encode({"type": "resign", "v": PROTOCOL_VERSION}).encode()
        if kind != "move" or set(message) != {"type", "v", "move"} or message["v"] is not VERSION:
            self._error("invalid_message", "expected move or resign")
            return None
        move = message["move"]
        if not self._my_turn:
            self._error("not_your_turn", "wait for your turn")
            return None
        if move not in self._legal:
            self._error("illegal_move", f"{str(move)[:16]} is not a legal move")
            return None
        self._my_turn = False
        return _encode({"type": "move", "v": PROTOCOL_VERSION, "move": move}).encode()

    def close(self) -> None:
        self._connection.close()

    # To the browser

    def _publish(self) -> None:
        state = _encode(
            {
                "type": "state",
                "v": VERSION,
                "color": self._color,
                "white": self._names["white"],
                "black": self._names["black"],
                "start_fen": self._start_fen,
                "fen": self._fen,
                "moves": " ".join(self._uci),
                "san": " ".join(self._san),
                "clock": dict(self._clock),
                "running": self._running,
                "increment_ms": self._increment_ms,
                "legal_moves": " ".join(self._legal),
                "result": self._result,
                "termination": self._termination,
            }
        )
        with self._lock:
            self._state = state
            self._connection.send_line(state)

    def _resend(self) -> None:
        with self._lock:
            if self._state is not None:
                self._connection.send_line(self._state)

    def _error(self, code: str, text: str) -> None:
        self._connection.send_line(
            _encode({"type": "error", "v": VERSION, "code": code, "message": text})
        )
