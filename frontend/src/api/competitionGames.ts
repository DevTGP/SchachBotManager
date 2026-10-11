import { getJson, sendJson } from "./client";
import type { CompetitionGame, CompetitionGameList, PlaySeat } from "./types";

/** The own open league and tournament games, the released ones first by deadline (E183). */
export async function fetchCompetitionGames(signal?: AbortSignal): Promise<CompetitionGame[]> {
  const list = await getJson<CompetitionGameList>("/account/competition-games", undefined, signal);
  return list.items;
}

/**
 * Ready for a released game. Sent again while the page is open, it keeps the account present;
 * the seat it names stays, any other is replaced (E183).
 */
export function declareReady(matchId: string, seat?: string): Promise<PlaySeat> {
  const path = `/matches/${encodeURIComponent(matchId)}/ready`;
  return sendJson("POST", path, seat === undefined ? undefined : { seat });
}
