from bson import ObjectId

from sbm_store import rating_values

BLITZ, RAPID = ObjectId(), ObjectId()


def holder(*entries: tuple[ObjectId, int, int]) -> dict:
    return {
        "ratings": {
            rating_values.key(discipline_id): {"value": value, "games": games, "seq": 1}
            for discipline_id, value, games in entries
        }
    }


def test_a_holder_without_games_stands_at_the_start():
    assert rating_values.in_discipline({}, BLITZ, 2500) == {"value": 2500, "games": 0}
    assert rating_values.overall({"ratings": {}}, 2500) == {"value": 2500, "games": 0}
    assert rating_values.overall(None, 1000) == {"value": 1000, "games": 0}


def test_a_discipline_is_read_by_its_id():
    rated = holder((BLITZ, 2600, 3))

    assert rating_values.in_discipline(rated, BLITZ, 2500) == {"value": 2600, "games": 3}
    assert rating_values.in_discipline(rated, RAPID, 2500) == {"value": 2500, "games": 0}


def test_the_overall_rating_is_weighted_by_games():
    rated = holder((BLITZ, 3000, 8), (RAPID, 2000, 92))

    assert rating_values.overall(rated, 2500) == {"value": 2080, "games": 100}


def test_the_overall_rating_rounds_half_up():
    assert rating_values.overall(holder((BLITZ, 2501, 1), (RAPID, 2500, 1)), 0)["value"] == 2501
    assert rating_values.overall(holder((BLITZ, -1, 1), (RAPID, 0, 1)), 0)["value"] == 0
    assert rating_values.overall(holder((BLITZ, 2500, 2), (RAPID, 2501, 1)), 0)["value"] == 2500
