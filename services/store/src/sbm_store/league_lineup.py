"""Who plays in which tier (E133): the lineup at a season start, the moves at its end.

Pure functions on bot ids. The lineup cuts one list from the top into tiers; the moves give the
next season's seeds, tier by tier, which the next start cuts again the same way.
"""

from collections.abc import Iterable, Sequence

from bson import ObjectId

PROMOTED = "promoted"
RELEGATED = "relegated"
STAYED = "stayed"
WITHDRAWN = "withdrawn"


def candidates(
    seeds: Sequence[Sequence[ObjectId]], waiting: Iterable[ObjectId], eligible: set[ObjectId]
) -> list[ObjectId]:
    """The seeds tier by tier, then the waiting list; only eligible bots, each once."""
    order = []
    for bot_id in [bot for tier in seeds for bot in tier] + list(waiting):
        if bot_id in eligible and bot_id not in order:
            order.append(bot_id)
    return order


def lineup(order: Sequence[ObjectId], *, tiers: int, tier_size: int) -> list[list[ObjectId]]:
    """At most tiers tiers of tier_size from the top; a last tier of one bot is dropped."""
    placed = list(order[: tiers * tier_size])
    cut = [placed[start : start + tier_size] for start in range(0, len(placed), tier_size)]
    if cut and len(cut[-1]) == 1:
        cut.pop()
    return cut


def moves(
    tables: Sequence[Sequence[tuple[ObjectId, bool]]], *, promotions: int, tier_size: int
) -> tuple[list[list[ObjectId]], dict[ObjectId, str]]:
    """The seeds of the next season and the outcome of each bot.

    tables holds per tier the bots in table order with whether they withdrew. From each tier
    but the bottom one, promotions minus its withdrawn bots go down; each tier is filled from
    the top of the tier below. A new tier keeps its bots by rank, then those relegated from
    above, then those promoted from below.
    """
    ranked = [[bot for bot, gone in tier if not gone] for tier in tables]
    outcomes = {bot: WITHDRAWN for tier in tables for bot, gone in tier if gone}
    seeds = []
    incoming: list[ObjectId] = []
    for number, tier in enumerate(ranked):
        gone = sum(withdrew for _, withdrew in tables[number])
        bottom = number == len(ranked) - 1
        down = 0 if bottom else min(len(tier), max(0, promotions - gone))
        keep, relegated = tier[: len(tier) - down], tier[len(tier) - down :]
        promoted = []
        if not bottom:
            need = max(0, tier_size - len(keep) - len(incoming))
            promoted, ranked[number + 1] = ranked[number + 1][:need], ranked[number + 1][need:]
        outcomes.update(dict.fromkeys(keep, STAYED))
        outcomes.update(dict.fromkeys(relegated, RELEGATED))
        outcomes.update(dict.fromkeys(promoted, PROMOTED))
        seeds.append(keep + incoming + promoted)
        incoming = relegated
    return seeds, outcomes
