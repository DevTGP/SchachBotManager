"""The bracket of a knockout edition (E176)."""

from bson import ObjectId

from sbm_store import knockout_bracket as bracket


def entries(count: int) -> list[dict]:
    return [
        {"bot_id": ObjectId(), "name": f"Bot{seed}", "version": "1.0", "seed": seed}
        for seed in range(1, count + 1)
    ]


def test_the_bracket_has_the_next_power_of_two():
    assert [bracket.size(count) for count in (2, 3, 4, 5, 8, 9)] == [2, 4, 4, 8, 8, 16]
    assert [bracket.rounds(size) for size in (2, 4, 8, 16)] == [1, 2, 3, 4]


def test_seeds_stand_so_the_best_meet_last():
    assert bracket.seed_order(2) == [1, 2]
    assert bracket.seed_order(4) == [1, 4, 2, 3]
    assert bracket.seed_order(8) == [1, 8, 4, 5, 2, 7, 3, 6]


def test_the_best_seeds_get_the_byes():
    field = entries(5)
    duels = bracket.first_round(field, 8)

    seeds = [(duel["a"]["seed"], duel["b"] and duel["b"]["seed"]) for duel in duels]
    assert seeds == [(1, None), (4, 5), (2, None), (3, None)]
    assert [duel["decided_by"] for duel in duels] == [bracket.BYE, None, bracket.BYE, bracket.BYE]
    assert duels[0]["winner"] == field[0]["bot_id"]


def test_places_by_the_round_lost():
    field = entries(4)
    one, two, three, four = (entry["bot_id"] for entry in field)
    duels = bracket.first_round(field, 4)
    duels[0].update(decided=True, winner=one, decided_by=bracket.GAMES)
    duels[1].update(decided=True, winner=three, decided_by=bracket.WITHDRAWAL)
    final = bracket.new_duel(2, 1, bracket.side(field[0]), bracket.side(field[2]))
    final.update(decided=True, winner=three, decided_by=bracket.ARMAGEDDON)

    places = bracket.placements(field, [*duels, final], 4, withdrawn={two})

    assert [(each["bot"]["bot_id"], each["place"]) for each in places] == [
        (three, 1),
        (one, 2),
        (four, 3),
        (two, None),
    ]
    assert [each["withdrawn"] for each in places] == [False, False, False, True]
