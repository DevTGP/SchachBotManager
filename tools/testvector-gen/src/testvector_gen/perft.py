"""Perft positions with node counts from published tables, recounted with python-chess.

Sources: Chess Programming Wiki, "Perft Results" (start position and positions 2 to 6), and the
edge-case collection by Martin Sedlak published on TalkChess (single depths).
"""

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import chess

from testvector_gen.fen_rules import parse_fen
from testvector_gen.position import START_FEN

SLOW_NODES = 5_000_000


@dataclass(frozen=True)
class PerftPosition:
    name: str
    fen: str
    nodes: dict[int, int]  # depth -> nodes

    def vectors(self) -> list[dict]:
        return [
            {"id": f"perft.{self.name}.d{depth}", "fen": self.fen, "depth": depth, "nodes": nodes}
            | ({"slow": True} if nodes > SLOW_NODES else {})
            for depth, nodes in sorted(self.nodes.items())
        ]


def _depths(*nodes: int) -> dict[int, int]:
    return {depth: count for depth, count in enumerate(nodes, start=1)}


POSITIONS = (
    PerftPosition("start", START_FEN, _depths(20, 400, 8902, 197281, 4865609, 119060324)),
    PerftPosition(
        "kiwipete",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        _depths(48, 2039, 97862, 4085603, 193690690),
    ),
    PerftPosition(
        "cpw3",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        _depths(14, 191, 2812, 43238, 674624, 11030083, 178633661),
    ),
    PerftPosition(
        "cpw4",
        "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
        _depths(6, 264, 9467, 422333, 15833292, 706045033),
    ),
    PerftPosition(
        "cpw4_mirrored",
        "r2q1rk1/pP1p2pp/Q4n2/bbp1p3/Np6/1B3NBn/pPPP1PPP/R3K2R b KQ - 0 1",
        _depths(6, 264, 9467, 422333, 15833292),
    ),
    PerftPosition(
        "cpw5",
        "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
        _depths(44, 1486, 62379, 2103487, 89941194),
    ),
    PerftPosition(
        "cpw6",
        "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
        _depths(46, 2079, 89890, 3894594, 164075551),
    ),
    PerftPosition("illegal_en_passant_1", "3k4/3p4/8/K1P4r/8/8/8/8 b - - 0 1", {6: 1134888}),
    PerftPosition("illegal_en_passant_2", "8/8/4k3/8/2p5/8/B2P2K1/8 w - - 0 1", {6: 1015133}),
    PerftPosition("en_passant_gives_check", "8/8/1k6/2b5/2pP4/8/5K2/8 b - d3 0 1", {6: 1440467}),
    PerftPosition("short_castling_gives_check", "5k2/8/8/8/8/8/8/4K2R w K - 0 1", {6: 661072}),
    PerftPosition("long_castling_gives_check", "3k4/8/8/8/8/8/8/R3K3 w Q - 0 1", {6: 803711}),
    PerftPosition(
        "castling_rights_lost", "r3k2r/1b4bq/8/8/8/8/7B/R3K2R w KQkq - 0 1", {4: 1274206}
    ),
    PerftPosition("castling_prevented", "r3k2r/8/3Q4/8/8/5q2/8/R3K2R b KQkq - 0 1", {4: 1720476}),
    PerftPosition("promote_out_of_check", "2K2r2/4P3/8/8/8/8/8/3k4 w - - 0 1", {6: 3821001}),
    PerftPosition("discovered_check", "8/8/1P2K3/8/2n5/1q6/8/5k2 b - - 0 1", {5: 1004658}),
    PerftPosition("promote_to_give_check", "4k3/1P6/8/8/8/8/K7/8 w - - 0 1", {6: 217342}),
    PerftPosition("underpromote_to_check", "8/P1k5/K7/8/8/8/8/8 w - - 0 1", {6: 92683}),
    PerftPosition("self_stalemate", "K1k5/8/P7/8/8/8/8/8 w - - 0 1", {6: 2217}),
    PerftPosition("stalemate_and_checkmate_1", "8/k1P5/8/1K6/8/8/8/8 w - - 0 1", {7: 567584}),
    PerftPosition("stalemate_and_checkmate_2", "8/8/2k5/5q2/5n2/8/5K2/8 b - - 0 1", {4: 23527}),
)


def vectors() -> list[dict]:
    return [vector for position in POSITIONS for vector in position.vectors()]


def count(fen: str, depth: int, first: str | None = None) -> int:
    """Leaf nodes of the legal move tree; with `first` only below that root move (UCI)."""
    board = parse_fen(fen)
    if first is None:
        return _count(board, depth)
    board.push_uci(first)
    return _count(board, depth - 1)


def _count(board: chess.Board, depth: int) -> int:
    """The last level only counts the legal moves (bulk counting)."""
    if depth == 1:
        return board.legal_moves.count()
    total = 0
    for move in list(board.legal_moves):
        board.push(move)
        total += _count(board, depth - 1)
        board.pop()
    return total


def _tasks(vector: dict) -> list[tuple[str, int, str | None]]:
    """One task per root move, so large counts spread over all processes."""
    fen, depth = vector["fen"], vector["depth"]
    if depth == 1:
        return [(fen, depth, None)]
    return [(fen, depth, move.uci()) for move in parse_fen(fen).legal_moves]


def verify(node_limit: int | None) -> list[str]:
    """Recounts every vector with at most `node_limit` nodes (all for None); returns mismatches."""
    selected = [v for v in vectors() if node_limit is None or v["nodes"] <= node_limit]
    tasks = [(vector["id"], task) for vector in selected for task in _tasks(vector)]
    counted = dict.fromkeys((vector["id"] for vector in selected), 0)
    with ProcessPoolExecutor() as pool:
        results = pool.map(count, *zip(*(task for _, task in tasks), strict=True))
        for (id, _), nodes in zip(tasks, results, strict=True):
            counted[id] += nodes
    return [
        f"{vector['id']}: table {vector['nodes']}, python-chess {counted[vector['id']]}"
        for vector in selected
        if counted[vector["id"]] != vector["nodes"]
    ]
