import { apiUrl, getJson } from "./client";
import type {
  Bot,
  Match,
  MatchKind,
  MatchPage,
  MatchStatus,
  Opponent,
  PlayerRating,
  Queue,
  Series,
  StoredDiscipline,
} from "./types";

export interface MatchQuery {
  status?: MatchStatus;
  kind?: MatchKind;
  botId?: string;
  /** Only with botId: the games of both bots against each other (E156). */
  opponentId?: string;
  disciplineId?: string;
  /** Only the games the signed-in account set; needs a session (E156). */
  mine?: boolean;
  /** The games of one season of a league, optionally of one tier (E137). */
  seasonId?: string;
  tier?: number;
  limit?: number;
  offset?: number;
}

export function fetchMatches(query: MatchQuery, signal?: AbortSignal): Promise<MatchPage> {
  const { status, kind, botId, opponentId, disciplineId, mine, seasonId, tier, limit, offset } =
    query;
  return getJson(
    "/matches",
    {
      status,
      kind,
      bot_id: botId,
      opponent_id: opponentId,
      discipline_id: disciplineId,
      mine: mine ? "true" : undefined,
      season_id: seasonId,
      tier: seasonId ? tier : undefined,
      limit,
      offset,
    },
    signal,
  );
}

/** The games of one request with two or more games and its score (E155). */
export function fetchSeries(id: string, signal?: AbortSignal): Promise<Series> {
  return getJson(`/series/${encodeURIComponent(id)}`, undefined, signal);
}

/** Every opponent bot of a bot with wins, draws and losses from its side (E161). */
export async function fetchOpponents(botId: string, signal?: AbortSignal): Promise<Opponent[]> {
  const path = `/bots/${encodeURIComponent(botId)}/opponents`;
  const list = await getJson<{ items: Opponent[] }>(path, undefined, signal);
  return list.items;
}

export function fetchMatch(id: string, signal?: AbortSignal): Promise<Match> {
  return getJson(`/matches/${encodeURIComponent(id)}`, undefined, signal);
}

export function matchPgnUrl(id: string): string {
  return apiUrl(`/matches/${encodeURIComponent(id)}/pgn`);
}

export async function fetchBots(signal?: AbortSignal): Promise<Bot[]> {
  const list = await getJson<{ items: Bot[] }>("/bots", undefined, signal);
  return list.items;
}

/**
 * Public bots with at least one counted match, highest rating first (E103); in one discipline,
 * or without one by the overall rating, the mean weighted by games (E163).
 */
export async function fetchRatings(disciplineId?: string, signal?: AbortSignal): Promise<Bot[]> {
  const query = { discipline_id: disciplineId };
  const list = await getJson<{ items: Bot[] }>("/ratings", query, signal);
  return list.items;
}

/** Active accounts with at least one counted game against bots, highest rating first (E118). */
export async function fetchPlayerRatings(
  disciplineId?: string,
  signal?: AbortSignal,
): Promise<PlayerRating[]> {
  const query = { discipline_id: disciplineId };
  const list = await getJson<{ items: PlayerRating[] }>("/ratings/players", query, signal);
  return list.items;
}

export function fetchQueue(signal?: AbortSignal): Promise<Queue> {
  return getJson("/queue", undefined, signal);
}

/** All disciplines by name, archived ones too (E100). */
export async function fetchDisciplines(signal?: AbortSignal): Promise<StoredDiscipline[]> {
  const list = await getJson<{ items: StoredDiscipline[] }>("/disciplines", undefined, signal);
  return list.items;
}
