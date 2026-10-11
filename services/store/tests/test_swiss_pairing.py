"""The pairing of one round of the Swiss system (E175)."""

from sbm_store.swiss_pairing import BLACK, WHITE, Player, pair


def players(*points: float, **extra) -> list[Player]:
    return [Player(bot_id=f"B{index}", points=value, **extra) for index, value in enumerate(points)]


def test_the_first_round_pairs_top_half_against_bottom_half_with_alternating_colours():
    paired = pair(players(0, 0, 0, 0), set(), first_round=True)

    assert paired.bye is None
    assert paired.pairs == [("B0", "B2"), ("B3", "B1")]


def test_the_bye_goes_to_the_lowest_bot_without_one():
    field = [
        Player("A", 2.0),
        Player("B", 1.0),
        Player("C", 1.0, had_bye=True),
    ]

    paired = pair(field, set())

    assert paired.bye == "B"
    assert paired.pairs == [("A", "C")] or paired.pairs == [("C", "A")]


def test_bots_with_the_same_points_meet_and_repeats_are_avoided():
    field = players(2, 2, 1, 1)
    played = {frozenset(("B0", "B1"))}

    paired = pair(field, played)

    met = {frozenset(each) for each in paired.pairs}
    assert met == {frozenset(("B0", "B2")), frozenset(("B1", "B3"))}


def test_a_repeat_is_allowed_when_nothing_else_is_left():
    field = players(1, 1)

    paired = pair(field, {frozenset(("B0", "B1"))})

    assert {frozenset(each) for each in paired.pairs} == {frozenset(("B0", "B1"))}


def test_white_goes_to_the_bot_with_fewer_whites_then_to_who_had_black_last():
    fewer = [Player("A", 1.0, whites=2, blacks=1), Player("B", 1.0, whites=1, blacks=2)]
    assert pair(fewer, set()).pairs == [("B", "A")]

    alternating = [
        Player("A", 1.0, whites=1, blacks=1, last_color=WHITE),
        Player("B", 1.0, whites=1, blacks=1, last_color=BLACK),
    ]
    assert pair(alternating, set()).pairs == [("B", "A")]
