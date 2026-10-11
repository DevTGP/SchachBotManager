from bson import ObjectId

from sbm_store.league_table import Game, counted_games, table

POINTS = {"win": 1, "draw": 0.5, "loss": 0}
A, B, C, D = (ObjectId() for _ in range(4))
NAMES = {A: "A", B: "B", C: "C", D: "D"}


def entries(*lots: tuple[ObjectId, int]) -> list[dict]:
    return [{"bot_id": bot, "name": NAMES[bot], "version": "1", "lot": lot} for bot, lot in lots]


def game(white, black, score, *, plies=40, forfeit=False) -> Game:
    return Game(white, black, score, forfeit, 0 if forfeit else plies)


def names(rows) -> list[str]:
    return [row.bot["name"] for row in rows]


def test_counts_games_and_points():
    rows = table(
        entries((A, 1), (B, 2), (C, 3)),
        [game(A, B, 1.0), game(B, C, 0.5), game(C, A, 1.0)],
        points={"win": 3, "draw": 1, "loss": 0},
        tiebreaks=[],
    )

    by_name = {row.bot["name"]: row for row in rows}
    assert (by_name["C"].games, by_name["C"].wins, by_name["C"].draws) == (2, 1, 1)
    assert (by_name["A"].wins, by_name["A"].losses, by_name["A"].points) == (1, 1, 3)
    assert by_name["C"].points == 4
    assert names(rows) == ["C", "A", "B"]
    assert [row.rank for row in rows] == [1, 2, 3]


def test_only_finished_matches_with_a_result_count():
    side = {"white": {"bot_id": A}, "black": {"bot_id": B}}
    matches = [
        {**side, "status": "finished", "result": "1-0", "termination": "checkmate", "ply_count": 9},
        {**side, "status": "aborted", "result": "*", "termination": "aborted"},
        {**side, "status": "queued", "result": None, "termination": None},
        {**side, "status": "finished", "result": "0-1", "termination": "forfeit_withdrawn"},
    ]

    games = counted_games(matches)

    assert games == [Game(A, B, 1.0, False, 9), Game(A, B, 0.0, True, 0)]


def test_the_lot_decides_without_tiebreaks():
    rows = table(entries((A, 7), (B, 3)), [game(A, B, 0.5)], points=POINTS, tiebreaks=[])

    assert names(rows) == ["B", "A"]


def test_wins_before_draws():
    rows = table(
        entries((A, 1), (B, 2), (C, 3), (D, 4)),
        [game(A, C, 1.0), game(A, D, 0.0), game(B, C, 0.5), game(B, D, 0.5)],
        points=POINTS,
        tiebreaks=["wins"],
    )

    assert names(rows) == ["D", "A", "B", "C"]


def test_head_to_head_among_the_bots_level():
    # A and B both have 1 point; B beat A.
    rows = table(
        entries((A, 1), (B, 2), (C, 3)),
        [game(A, B, 0.0), game(A, C, 1.0)],
        points=POINTS,
        tiebreaks=["head_to_head"],
    )

    assert names(rows) == ["B", "A", "C"]


def test_forfeits_count_as_wins_but_not_for_head_to_head():
    rows = table(
        entries((A, 1), (B, 2)),
        [game(A, B, 1.0, forfeit=True), game(B, A, 1.0)],
        points=POINTS,
        tiebreaks=["head_to_head"],
    )

    by_name = {row.bot["name"]: row for row in rows}
    assert (by_name["A"].wins, by_name["A"].forfeit_wins) == (1, 1)
    # Level on points; head to head counts only B's played win.
    assert names(rows) == ["B", "A"]


def test_sonneborn_berger_weighs_the_opponents_points():
    # A and B have 1.5 points each; A beat C (2 points), B beat D (1 point).
    rows = table(
        entries((A, 2), (B, 1), (C, 3), (D, 4)),
        [
            game(A, C, 1.0),
            game(B, D, 1.0),
            game(C, D, 1.0),
            game(C, B, 1.0),
            game(D, A, 1.0),
            game(A, B, 0.5),
        ],
        points=POINTS,
        tiebreaks=["sonneborn_berger"],
    )

    assert names(rows) == ["C", "A", "B", "D"]


def test_fewer_moves_and_then_the_lot():
    rows = table(
        entries((A, 1), (B, 2), (C, 3), (D, 4)),
        [game(A, C, 1.0, plies=80), game(B, D, 1.0, plies=20)],
        points=POINTS,
        tiebreaks=["fewer_moves"],
    )

    assert names(rows) == ["B", "A", "D", "C"]


def test_tiebreaks_apply_in_order():
    # A and B level on points and wins; head to head is level, fewer moves decides.
    rows = table(
        entries((A, 1), (B, 2), (C, 3)),
        [game(A, B, 0.5, plies=10), game(A, C, 1.0, plies=90), game(B, C, 1.0, plies=30)],
        points=POINTS,
        tiebreaks=["wins", "head_to_head", "fewer_moves"],
    )

    assert names(rows) == ["B", "A", "C"]


def test_withdrawn_bots_stand_at_the_end_without_rank():
    rows = table(
        entries((A, 1), (B, 2), (C, 3)),
        [game(A, B, 0.0), game(A, C, 0.0, forfeit=True)],
        points=POINTS,
        tiebreaks=[],
        withdrawn=[B],
    )

    assert names(rows) == ["C", "A", "B"]
    assert [row.rank for row in rows] == [1, 2, None]
    assert rows[2].to_document()["withdrawn"] is True


def test_games_against_bots_outside_the_tier_are_ignored():
    rows = table(entries((A, 1), (B, 2)), [game(A, C, 1.0)], points=POINTS, tiebreaks=[])

    assert [row.games for row in rows] == [0, 0]


def test_byes_give_a_win_and_buchholz_sums_the_opponents_points():
    rows = table(
        entries((A, 1), (B, 2), (C, 3), (D, 4)),
        [game(A, B, 1.0), game(C, D, 0.5), game(A, C, 0.5), game(B, D, 0.0, forfeit=True)],
        points=POINTS,
        tiebreaks=["buchholz"],
        byes={B: 1},
    )

    by_name = {row.bot["name"]: row for row in rows}
    assert (by_name["B"].byes, by_name["B"].points) == (1, 1.0)
    assert by_name["D"].points == 1.5
    # A met B (1.0) and C (1.0); a forfeit does not count for Buchholz.
    assert by_name["A"].buchholz == 2.0
    assert by_name["D"].buchholz == 1.0
    assert by_name["D"].to_edition_document()["byes"] == 0
    assert "outcome" not in by_name["D"].to_edition_document()
