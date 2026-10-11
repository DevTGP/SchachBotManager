from sbm_store.league_lineup import (
    PROMOTED,
    RELEGATED,
    STAYED,
    WITHDRAWN,
    candidates,
    lineup,
    moves,
)


def tier(*bots: str, gone: str = "") -> list[tuple[str, bool]]:
    return [(bot, bot in gone) for bot in bots]


def test_candidates_keep_the_seeds_before_the_waiting_list():
    order = candidates([["a", "b"], ["c"]], ["x", "b", "y", "z"], {"a", "c", "x", "b", "z"})

    assert order == ["a", "b", "c", "x", "z"]


def test_the_lineup_fills_the_tiers_from_the_top():
    assert lineup(list("abcdefg"), tiers=3, tier_size=3) == [["a", "b", "c"], ["d", "e", "f"]]
    assert lineup(list("abcdefgh"), tiers=3, tier_size=3) == [
        ["a", "b", "c"],
        ["d", "e", "f"],
        ["g", "h"],
    ]
    assert lineup(list("abcdefghijk"), tiers=2, tier_size=4) == [list("abcd"), list("efgh")]
    assert lineup(["a"], tiers=1, tier_size=4) == []


def test_promotions_and_relegations_swap_places():
    seeds, outcomes = moves(
        [tier("a", "b", "c", "d"), tier("e", "f", "g", "h"), tier("i", "j", "k", "l")],
        promotions=1,
        tier_size=4,
    )

    assert seeds == [["a", "b", "c", "e"], ["f", "g", "d", "i"], ["j", "k", "l", "h"]]
    assert outcomes["d"] == outcomes["h"] == RELEGATED
    assert outcomes["e"] == outcomes["i"] == PROMOTED
    assert outcomes["a"] == outcomes["l"] == STAYED


def test_a_withdrawn_bot_saves_another_from_relegation():
    seeds, outcomes = moves(
        [tier("a", "b", "c", "d", gone="b"), tier("e", "f", "g", "h")],
        promotions=1,
        tier_size=4,
    )

    assert seeds == [["a", "c", "d", "e"], ["f", "g", "h"]]
    assert outcomes["b"] == WITHDRAWN
    assert outcomes["d"] == STAYED
    assert outcomes["e"] == PROMOTED


def test_more_withdrawals_bring_up_more_bots():
    seeds, _ = moves(
        [tier("a", "b", "c", "d", gone="bc"), tier("e", "f", "g", "h")],
        promotions=1,
        tier_size=4,
    )

    assert seeds == [["a", "d", "e", "f"], ["g", "h"]]


def test_a_short_tier_fills_up_from_below():
    seeds, outcomes = moves(
        [tier("a", "b", "c"), tier("d", "e", "f", "g")],
        promotions=1,
        tier_size=4,
    )

    assert seeds == [["a", "b", "d", "e"], ["f", "g", "c"]]
    assert outcomes["c"] == RELEGATED


def test_without_promotions_everybody_stays():
    seeds, outcomes = moves([tier("a", "b"), tier("c", "d")], promotions=0, tier_size=2)

    assert seeds == [["a", "b"], ["c", "d"]]
    assert set(outcomes.values()) == {STAYED}


def test_a_single_tier_keeps_its_order():
    seeds, outcomes = moves([tier("a", "b", "c", gone="b")], promotions=2, tier_size=3)

    assert seeds == [["a", "c"]]
    assert outcomes == {"a": STAYED, "b": WITHDRAWN, "c": STAYED}
