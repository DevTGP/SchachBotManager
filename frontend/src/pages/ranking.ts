import { fetchPlayerRatings, fetchRatings } from "../api/endpoints";
import type { Bot, Rating } from "../api/types";

/** Which holders the ranking shows; undefined shows bots and players together (E118). */
export type RankingFilter = "bots" | "players" | undefined;
export const RANKING_FILTERS = ["bots", "players"] as const;

export type RankingRow =
  { kind: "bot"; bot: Bot; rating: Rating } | { kind: "player"; username: string; rating: Rating };

/** Loads the rows for the filter, highest rating first; on a tie bots keep their place first. */
export async function loadRanking(
  filter: RankingFilter,
  signal: AbortSignal,
): Promise<RankingRow[]> {
  const [bots, players] = await Promise.all([
    filter === "players" ? [] : fetchRatings(signal),
    filter === "bots" ? [] : fetchPlayerRatings(signal),
  ]);
  const rows: RankingRow[] = [
    ...bots.map((bot) => ({ kind: "bot" as const, bot, rating: bot.rating })),
    ...players.map((player) => ({ kind: "player" as const, ...player })),
  ];
  return rows.sort((a, b) => b.rating.value - a.rating.value);
}
