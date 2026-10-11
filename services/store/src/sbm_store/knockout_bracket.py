"""The bracket of a knockout edition (E176): its size, the first round and the placements.

Pure functions. The bracket has the next power of two of places; the seeds stand in the
standard order (1–8, 4–5, 2–7, 3–6 for eight), so the best seeds get the byes and meet last.
A duel is {round, slot, a, b, winner, decided, decided_by, games}; a and b are sides
{bot_id, name, version, seed} or None, a the better seed; winner is a bot id.
"""

from collections.abc import Sequence

GAMES = "games"
TIEBREAK = "tiebreak"
ARMAGEDDON = "armageddon"
BYE = "bye"
WITHDRAWAL = "withdrawal"


def size(participants: int) -> int:
    places = 2
    while places < participants:
        places *= 2
    return places


def rounds(bracket_size: int) -> int:
    return bracket_size.bit_length() - 1


def seed_order(bracket_size: int) -> list[int]:
    """The seeds in bracket order: [1, 2] → [1, 4, 2, 3] → [1, 8, 4, 5, 2, 7, 3, 6] …"""
    order = [1]
    while len(order) < bracket_size:
        count = 2 * len(order)
        order = [seed for each in order for seed in (each, count + 1 - each)]
    return order


def side(entry: dict | None) -> dict | None:
    if entry is None:
        return None
    return {key: entry[key] for key in ("bot_id", "name", "version", "seed")}


def new_duel(round_number: int, slot: int, first: dict | None, second: dict | None) -> dict:
    """A duel of two sides; one missing side makes it a bye, two make it empty."""
    a, b = sorted((first, second), key=lambda each: each["seed"] if each else float("inf"))
    duel = {
        "round": round_number,
        "slot": slot,
        "a": a,
        "b": b,
        "winner": None,
        "decided": False,
        "decided_by": None,
        "games": [],
    }
    if b is None:
        duel.update(decided=True, decided_by=BYE, winner=a["bot_id"] if a else None)
    return duel


def first_round(participants: Sequence[dict], bracket_size: int) -> list[dict]:
    """The duels of round 1; participants are the edition's entries by seed."""
    by_seed = {entry["seed"]: entry for entry in participants}
    order = seed_order(bracket_size)
    return [
        new_duel(
            1, slot, side(by_seed.get(order[2 * slot - 2])), side(by_seed.get(order[2 * slot - 1]))
        )
        for slot in range(1, bracket_size // 2 + 1)
    ]


def winner_side(duel: dict) -> dict | None:
    if duel["winner"] is None:
        return None
    return duel["a"] if duel["a"] and duel["a"]["bot_id"] == duel["winner"] else duel["b"]


def placements(
    participants: Sequence[dict], duels: Sequence[dict], bracket_size: int, withdrawn: set
) -> list[dict]:
    """Per participant the place reached: winner 1, finalist 2, semifinal 3, quarterfinal 5 …;
    None while still in or after losing by withdrawing. Sorted by place, then seed."""
    total = rounds(bracket_size)
    result = []
    for entry in participants:
        bot_id = entry["bot_id"]
        place = None
        for duel in duels:
            sides = {each["bot_id"] for each in (duel["a"], duel["b"]) if each}
            if bot_id not in sides or not duel["decided"]:
                continue
            if duel["winner"] == bot_id:
                if duel["round"] == total:
                    place = 1
                continue
            lost_by_leaving = duel["decided_by"] == WITHDRAWAL and bot_id in withdrawn
            place = None if lost_by_leaving else 2 ** (total - duel["round"]) + 1
            break
        bot = {key: entry[key] for key in ("bot_id", "name", "version")}
        result.append(
            {"bot": bot, "place": place, "withdrawn": bot_id in withdrawn, "seed": entry["seed"]}
        )
    result.sort(key=lambda each: (each["place"] is None, each["place"] or 0, each["seed"]))
    for each in result:
        del each["seed"]
    return result
